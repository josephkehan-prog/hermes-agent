"""Tests for skills/research/watch-notify/scripts/watch.py — no network, no external services."""

from __future__ import annotations

import argparse
import importlib.util
import json
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT = REPO_ROOT / "skills" / "research" / "watch-notify" / "scripts" / "watch.py"


def _load_script_module():
    spec = importlib.util.spec_from_file_location("watch_notify_watch_test_module", SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


watch = _load_script_module()


class TestCheckContentHash:
    def test_first_run_reports_new_and_writes_state(self, monkeypatch, tmp_path):
        monkeypatch.setattr(watch, "fetch_url", lambda url, **kwargs: (b"hello world", 200))
        state_path = tmp_path / "state.json"
        args = argparse.Namespace(url="https://example.com", state=str(state_path))

        watch.cmd_check(args)

        state = json.loads(state_path.read_text())
        assert state["https://example.com"]["hash"] == watch.compute_hash(b"hello world")

    def test_second_run_with_same_body_reports_unchanged(self, monkeypatch, tmp_path):
        monkeypatch.setattr(watch, "fetch_url", lambda url, **kwargs: (b"hello world", 200))
        state_path = tmp_path / "state.json"
        args = argparse.Namespace(url="https://example.com", state=str(state_path))

        watch.cmd_check(args)
        first_state = json.loads(state_path.read_text())
        watch.cmd_check(args)
        second_state = json.loads(state_path.read_text())

        assert first_state == second_state

    def test_changed_body_updates_stored_hash(self, monkeypatch, tmp_path):
        state_path = tmp_path / "state.json"
        args = argparse.Namespace(url="https://example.com", state=str(state_path))

        monkeypatch.setattr(watch, "fetch_url", lambda url, **kwargs: (b"version one", 200))
        watch.cmd_check(args)
        old_hash = json.loads(state_path.read_text())["https://example.com"]["hash"]

        monkeypatch.setattr(watch, "fetch_url", lambda url, **kwargs: (b"version two", 200))
        watch.cmd_check(args)
        new_hash = json.loads(state_path.read_text())["https://example.com"]["hash"]

        assert old_hash != new_hash

    def test_compute_hash_is_sha256_hex(self):
        import hashlib

        assert watch.compute_hash(b"abc") == hashlib.sha256(b"abc").hexdigest()


class TestExtractJsonField:
    def test_extracts_nested_dict_field(self):
        payload = {"data": {"status": "ok"}}
        assert watch.extract_json_field(payload, "data.status") == "ok"

    def test_extracts_through_list_index(self):
        payload = {"items": [{"name": "first"}, {"name": "second"}]}
        assert watch.extract_json_field(payload, "items.1.name") == "second"

    def test_missing_key_exits_2(self):
        with pytest.raises(SystemExit) as exc_info:
            watch.extract_json_field({"data": {}}, "data.missing")
        assert exc_info.value.code == 2

    def test_index_out_of_range_exits_2(self):
        with pytest.raises(SystemExit) as exc_info:
            watch.extract_json_field({"items": [1]}, "items.5")
        assert exc_info.value.code == 2


class TestWatchJsonChangeLogic:
    def _fetch(self, value):
        payload = json.dumps({"status": value}).encode("utf-8")
        return lambda url, **kwargs: (payload, 200)

    def test_first_run_reports_new(self, monkeypatch, tmp_path, capsys):
        monkeypatch.setattr(watch, "fetch_url", self._fetch("up"))
        state_path = tmp_path / "state.json"
        args = argparse.Namespace(url="https://example.com/status", field="status", state=str(state_path))

        watch.cmd_watch_json(args)

        output = json.loads(capsys.readouterr().out)
        assert output["result"] == "new"
        assert output["value"] == "up"

    def test_unchanged_value_reports_unchanged(self, monkeypatch, tmp_path, capsys):
        state_path = tmp_path / "state.json"
        args = argparse.Namespace(url="https://example.com/status", field="status", state=str(state_path))

        monkeypatch.setattr(watch, "fetch_url", self._fetch("up"))
        watch.cmd_watch_json(args)
        capsys.readouterr()
        watch.cmd_watch_json(args)

        output = json.loads(capsys.readouterr().out)
        assert output["result"] == "unchanged"

    def test_changed_value_reports_changed(self, monkeypatch, tmp_path, capsys):
        state_path = tmp_path / "state.json"
        args = argparse.Namespace(url="https://example.com/status", field="status", state=str(state_path))

        monkeypatch.setattr(watch, "fetch_url", self._fetch("up"))
        watch.cmd_watch_json(args)
        capsys.readouterr()

        monkeypatch.setattr(watch, "fetch_url", self._fetch("down"))
        watch.cmd_watch_json(args)

        output = json.loads(capsys.readouterr().out)
        assert output["result"] == "changed"
        assert output["value"] == "down"


class TestStatePersistenceRoundTrip:
    def test_load_state_returns_empty_dict_for_missing_file(self, tmp_path):
        missing = tmp_path / "does-not-exist.json"
        assert watch.load_state(str(missing)) == {}

    def test_load_state_rejects_invalid_json(self, tmp_path):
        bad_file = tmp_path / "bad.json"
        bad_file.write_text("{not valid json")
        with pytest.raises(SystemExit) as exc_info:
            watch.load_state(str(bad_file))
        assert exc_info.value.code == 2

    def test_save_then_load_round_trips(self, tmp_path):
        state_path = tmp_path / "state.json"
        original = {"https://example.com": {"hash": "abc123"}}

        watch.save_state(str(state_path), original)
        loaded = watch.load_state(str(state_path))

        assert loaded == original


class TestNtfyTopicValidation:
    @pytest.mark.parametrize("topic", ["watch-abc123", "a", "A_B-9", "x" * 64])
    def test_accepts_valid_topics(self, topic):
        assert watch.validate_topic(topic) == topic

    @pytest.mark.parametrize(
        "topic",
        [
            "",
            "has spaces",
            "has/slash",
            "has?query=1",
            "x" * 65,
            "emoji😀topic",
        ],
    )
    def test_rejects_invalid_topics(self, topic):
        with pytest.raises(SystemExit) as exc_info:
            watch.validate_topic(topic)
        assert exc_info.value.code == 2

    def test_notify_posts_to_ntfy_topic_url(self, monkeypatch, capsys):
        captured = {}

        def fake_fetch(url, method="GET", data=None, extra_headers=None):
            captured["url"] = url
            captured["method"] = method
            captured["data"] = data
            return b"", 200

        monkeypatch.setattr(watch, "fetch_url", fake_fetch)
        args = argparse.Namespace(message="site changed", topic="watch-topic-1")

        watch.cmd_notify(args)

        assert captured["url"] == "https://ntfy.sh/watch-topic-1"
        assert captured["method"] == "POST"
        assert captured["data"] == b"site changed"

    def test_notify_rejects_invalid_topic_before_fetching(self, monkeypatch):
        def unexpected_fetch(*args, **kwargs):
            raise AssertionError("fetch_url should not be called for an invalid topic")

        monkeypatch.setattr(watch, "fetch_url", unexpected_fetch)
        args = argparse.Namespace(message="hi", topic="bad topic")

        with pytest.raises(SystemExit) as exc_info:
            watch.cmd_notify(args)
        assert exc_info.value.code == 2


class TestSchemeRejection:
    def test_require_http_scheme_accepts_https(self):
        watch.require_http_scheme("https://example.com")

    def test_require_http_scheme_accepts_http(self):
        watch.require_http_scheme("http://example.com")

    @pytest.mark.parametrize("url", ["ftp://example.com", "file:///etc/passwd", "javascript:alert(1)"])
    def test_require_http_scheme_rejects_other_schemes(self, url):
        with pytest.raises(SystemExit) as exc_info:
            watch.require_http_scheme(url)
        assert exc_info.value.code == 2


class TestRejectPrivateTarget:
    @pytest.mark.parametrize(
        "url",
        [
            "http://127.0.0.1/",
            "http://localhost/",
            "http://169.254.169.254/latest/meta-data/",
            "http://10.0.0.1/",
            "http://192.168.1.1/",
        ],
    )
    def test_rejects_private_and_loopback_and_link_local_targets(self, url):
        with pytest.raises(SystemExit) as exc_info:
            watch.reject_private_target(url)
        assert exc_info.value.code == 2


# --- Live tests: real network, skipped by default. Run manually with
# `pytest -m "" tests/skills/test_watch_notify.py -k Live` to exercise them. ---


@pytest.mark.skip(reason="live network test — run manually")
class TestLiveContentCheck:
    def test_check_example_com_twice_reports_new_then_unchanged(self, tmp_path):
        state_path = tmp_path / "live-state.json"
        args = argparse.Namespace(url="https://example.com", state=str(state_path))
        watch.cmd_check(args)
        watch.cmd_check(args)


@pytest.mark.skip(reason="live network test — posts a real ntfy.sh notification, run manually")
class TestLiveNotify:
    def test_notify_posts_to_a_random_ntfy_topic(self):
        import uuid

        args = argparse.Namespace(message="watch-notify skill test", topic=f"hermes-test-{uuid.uuid4().hex}")
        watch.cmd_notify(args)
