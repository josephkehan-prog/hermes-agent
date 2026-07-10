"""Tests for skills/social-media/scrapecreators/scripts/scrapecreators.py — no network by default."""

from __future__ import annotations

import importlib.util
import io
import json
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT = REPO_ROOT / "skills" / "social-media" / "scrapecreators" / "scripts" / "scrapecreators.py"


def _load_script_module():
    spec = importlib.util.spec_from_file_location("scrapecreators_test_module", SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


sc = _load_script_module()


class TestNeedsKeyStub:
    def test_profile_without_key_prints_needs_key_and_exits_2_no_network(self, monkeypatch):
        monkeypatch.delenv(sc.ENV_VAR, raising=False)

        def _fail_if_called(*_args, **_kwargs):
            raise AssertionError("must not make a network call when key is unset")

        monkeypatch.setattr(sc.urllib.request, "urlopen", _fail_if_called)
        args = sc.build_parser().parse_args(["profile", "tiktok", "someuser"])
        buf = io.StringIO()
        with redirect_stderr(buf):
            code = args.func(args)

        assert code == 2
        assert "[NEEDS-KEY]" in buf.getvalue()
        assert "SCRAPECREATORS_API_KEY" in buf.getvalue()

    def test_posts_without_key_prints_needs_key_and_exits_2_no_network(self, monkeypatch):
        monkeypatch.delenv(sc.ENV_VAR, raising=False)

        def _fail_if_called(*_args, **_kwargs):
            raise AssertionError("must not make a network call when key is unset")

        monkeypatch.setattr(sc.urllib.request, "urlopen", _fail_if_called)
        args = sc.build_parser().parse_args(["posts", "instagram", "someuser"])
        buf = io.StringIO()
        with redirect_stderr(buf):
            code = args.func(args)

        assert code == 2
        assert "[NEEDS-KEY]" in buf.getvalue()

    def test_search_without_key_prints_needs_key_and_exits_2_no_network(self, monkeypatch):
        monkeypatch.delenv(sc.ENV_VAR, raising=False)

        def _fail_if_called(*_args, **_kwargs):
            raise AssertionError("must not make a network call when key is unset")

        monkeypatch.setattr(sc.urllib.request, "urlopen", _fail_if_called)
        args = sc.build_parser().parse_args(["search", "youtube", "some query"])
        buf = io.StringIO()
        with redirect_stderr(buf):
            code = args.func(args)

        assert code == 2
        assert "[NEEDS-KEY]" in buf.getvalue()

    def test_needs_key_message_never_contains_a_key_value(self, monkeypatch):
        monkeypatch.delenv(sc.ENV_VAR, raising=False)
        assert "SCRAPECREATORS_API_KEY" in sc._NEEDS_KEY_MESSAGE
        # sanity: the message is the static string, not interpolated from env
        assert "=" not in sc._NEEDS_KEY_MESSAGE.split("Set ")[1].split(" in")[0]


class TestPlatformValidation:
    def test_accepts_allowed_platforms(self):
        for platform in sc.ALLOWED_PLATFORMS:
            assert sc.validate_platform(platform) == platform

    def test_accepts_uppercase_and_strips(self):
        assert sc.validate_platform(" TikTok ") == "tiktok"

    @pytest.mark.parametrize(
        "bad",
        [
            "evil",
            "myspace",
            "tiktok;rm -rf",
            "../etc/passwd",
            "tiktok\ninjected",
            "",
        ],
    )
    def test_rejects_disallowed_or_injection_platforms(self, bad):
        with pytest.raises(sc.ScrapeCreatorsError):
            sc.validate_platform(bad)


class TestHandleValidation:
    def test_accepts_normal_handle(self):
        assert sc.validate_handle("some_user.99") == "some_user.99"

    def test_accepts_leading_at_sign(self):
        assert sc.validate_handle("@someuser") == "@someuser"

    @pytest.mark.parametrize(
        "bad",
        [
            "",
            "user\r\nX-Injected: true",
            "user\nname",
            "user name",
            "user/../x",
            "a" * 100,
        ],
    )
    def test_rejects_control_chars_crlf_and_injection(self, bad):
        with pytest.raises(sc.ScrapeCreatorsError):
            sc.validate_handle(bad)


class TestQueryValidation:
    def test_accepts_normal_query(self):
        assert sc.validate_query("some query") == "some query"

    @pytest.mark.parametrize("bad", ["", "bad\r\nquery", "bad\nquery"])
    def test_rejects_empty_or_control_chars(self, bad):
        with pytest.raises(sc.ScrapeCreatorsError):
            sc.validate_query(bad)


class TestRequestBuildingWithMockedKeyAndUrlopen:
    def test_profile_call_builds_expected_url_and_header(self, monkeypatch):
        monkeypatch.setenv(sc.ENV_VAR, "test-key-123")
        captured = {}

        class _FakeResponse:
            def __enter__(self):
                return self

            def __exit__(self, *exc):
                return False

            def read(self, _n):
                return json.dumps({"handle": "someuser", "followers": 42}).encode()

        def _fake_urlopen(req, timeout=None):
            captured["url"] = req.full_url
            captured["header"] = req.get_header("X-api-key")
            captured["timeout"] = timeout
            return _FakeResponse()

        monkeypatch.setattr(sc.urllib.request, "urlopen", _fake_urlopen)
        args = sc.build_parser().parse_args(["profile", "tiktok", "someuser"])
        buf = io.StringIO()
        with redirect_stdout(buf):
            code = args.func(args)

        assert code == 0
        assert captured["url"].startswith("https://api.scrapecreators.com/v1/tiktok/profile?")
        assert "handle=someuser" in captured["url"]
        assert captured["header"] == "test-key-123"
        payload = json.loads(buf.getvalue())
        assert payload == {"handle": "someuser", "followers": 42}

    def test_posts_call_includes_limit_param(self, monkeypatch):
        monkeypatch.setenv(sc.ENV_VAR, "test-key-123")
        captured = {}

        class _FakeResponse:
            def __enter__(self):
                return self

            def __exit__(self, *exc):
                return False

            def read(self, _n):
                return json.dumps({"posts": []}).encode()

        def _fake_urlopen(req, timeout=None):
            captured["url"] = req.full_url
            return _FakeResponse()

        monkeypatch.setattr(sc.urllib.request, "urlopen", _fake_urlopen)
        args = sc.build_parser().parse_args(["posts", "instagram", "someuser", "--limit", "5"])
        buf = io.StringIO()
        with redirect_stdout(buf):
            code = args.func(args)

        assert code == 0
        assert "limit=5" in captured["url"]
        assert "handle=someuser" in captured["url"]

    def test_never_logs_key_value_on_success(self, monkeypatch, capsys):
        monkeypatch.setenv(sc.ENV_VAR, "super-secret-key")

        class _FakeResponse:
            def __enter__(self):
                return self

            def __exit__(self, *exc):
                return False

            def read(self, _n):
                return json.dumps({"ok": True}).encode()

        monkeypatch.setattr(sc.urllib.request, "urlopen", lambda req, timeout=None: _FakeResponse())
        args = sc.build_parser().parse_args(["profile", "tiktok", "someuser"])
        args.func(args)

        captured = capsys.readouterr()
        assert "super-secret-key" not in captured.out
        assert "super-secret-key" not in captured.err


class TestHttpErrorHandling:
    def test_401_reports_check_your_key(self, monkeypatch):
        import urllib.error

        monkeypatch.setenv(sc.ENV_VAR, "bad-key")

        def _raise_401(req, timeout=None):
            raise urllib.error.HTTPError(req.full_url, 401, "Unauthorized", {}, None)

        monkeypatch.setattr(sc.urllib.request, "urlopen", _raise_401)
        args = sc.build_parser().parse_args(["profile", "tiktok", "someuser"])
        with pytest.raises(sc.ScrapeCreatorsError, match="401"):
            args.func(args)

    def test_429_reports_rate_limited(self, monkeypatch):
        import urllib.error

        monkeypatch.setenv(sc.ENV_VAR, "test-key")

        def _raise_429(req, timeout=None):
            raise urllib.error.HTTPError(req.full_url, 429, "Too Many Requests", {}, None)

        monkeypatch.setattr(sc.urllib.request, "urlopen", _raise_429)
        args = sc.build_parser().parse_args(["profile", "tiktok", "someuser"])
        with pytest.raises(sc.ScrapeCreatorsError, match="429"):
            args.func(args)

    def test_network_error_raises_scrapecreators_error(self, monkeypatch):
        import urllib.error

        monkeypatch.setenv(sc.ENV_VAR, "test-key")

        def _raise_network_error(req, timeout=None):
            raise urllib.error.URLError("connection refused")

        monkeypatch.setattr(sc.urllib.request, "urlopen", _raise_network_error)
        args = sc.build_parser().parse_args(["profile", "tiktok", "someuser"])
        with pytest.raises(sc.ScrapeCreatorsError, match="network error"):
            args.func(args)


class TestMainEntrypoint:
    def test_main_returns_2_on_invalid_platform(self, monkeypatch):
        monkeypatch.setenv(sc.ENV_VAR, "test-key")
        code = sc.main(["profile", "evil", "someuser"])
        assert code == 2

    def test_main_returns_2_when_key_unset(self, monkeypatch):
        monkeypatch.delenv(sc.ENV_VAR, raising=False)

        def _fail_if_called(*_args, **_kwargs):
            raise AssertionError("must not make a network call when key is unset")

        monkeypatch.setattr(sc.urllib.request, "urlopen", _fail_if_called)
        code = sc.main(["profile", "tiktok", "someuser"])
        assert code == 2


@pytest.mark.skip(reason="live network test — requires a real SCRAPECREATORS_API_KEY, run manually")
class TestLiveProfileLookup:
    def test_live_profile_lookup_against_real_api(self):
        code = sc.main(["profile", "tiktok", "someuser"])
        assert code == 0
