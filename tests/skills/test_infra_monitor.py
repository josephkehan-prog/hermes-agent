"""Tests for skills/research/infra-monitor/scripts/infra_snapshot.py — no network, no external services."""

from __future__ import annotations

import argparse
import importlib.util
import json
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT = REPO_ROOT / "skills" / "research" / "infra-monitor" / "scripts" / "infra_snapshot.py"


def _load_script_module():
    spec = importlib.util.spec_from_file_location("infra_snapshot_test_module", SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


infra = _load_script_module()


class TestValidateDomain:
    def test_valid_domain_passes_through_unchanged(self):
        assert infra.validate_domain("example.com") == "example.com"

    def test_subdomain_is_valid(self):
        assert infra.validate_domain("dev.api.example.co.uk") == "dev.api.example.co.uk"

    def test_shell_injection_attempt_exits_with_code_2(self):
        with pytest.raises(SystemExit) as exc_info:
            infra.validate_domain("evil.com; rm -rf /")

        assert exc_info.value.code == 2

    def test_bare_word_without_a_dot_is_rejected(self):
        with pytest.raises(SystemExit) as exc_info:
            infra.validate_domain("localhost")

        assert exc_info.value.code == 2

    def test_leading_hyphen_label_is_rejected(self):
        with pytest.raises(SystemExit) as exc_info:
            infra.validate_domain("-evil.example.com")

        assert exc_info.value.code == 2

    def test_embedded_whitespace_is_rejected(self):
        with pytest.raises(SystemExit) as exc_info:
            infra.validate_domain("example .com")

        assert exc_info.value.code == 2


class TestResolveDnsParsesDohJson:
    def test_parses_mocked_a_and_mx_records(self, monkeypatch):
        def fake_get(url, headers=None):
            if "type=A" in url:
                return {"Answer": [{"data": "93.184.216.34"}]}
            if "type=MX" in url:
                return {"Answer": [{"data": "10 mail.example.com."}]}
            return {"Answer": []}

        monkeypatch.setattr(infra, "_http_get_json", fake_get)

        results = infra.resolve_dns("example.com", ["A", "MX", "NS", "TXT"])

        assert results == {
            "A": ["93.184.216.34"],
            "MX": ["10 mail.example.com."],
            "NS": [],
            "TXT": [],
        }

    def test_doh_fallback_tries_second_provider_when_first_fails(self, monkeypatch):
        import urllib.error

        calls = []

        def fake_get(url, headers=None):
            calls.append(url)
            if infra.DOH_PROVIDERS[0] in url:
                raise urllib.error.URLError("first provider down")
            return {"Answer": [{"data": "93.184.216.34"}]}

        monkeypatch.setattr(infra, "_http_get_json", fake_get)

        result = infra.query_doh("example.com", "A")

        assert result == {"Answer": [{"data": "93.184.216.34"}]}
        assert len(calls) == 2


class TestFetchCrtshSubdomains:
    def test_parses_mocked_crtsh_json_and_dedupes(self, monkeypatch):
        mocked_entries = [
            {"name_value": "www.example.com\nexample.com"},
            {"name_value": "DEV.example.com"},
            {"name_value": "*.example.com"},
        ]
        monkeypatch.setattr(infra, "_http_get_json", lambda url, headers=None: mocked_entries)

        subdomains = infra.fetch_crtsh_subdomains("example.com")

        assert subdomains == ["dev.example.com", "example.com", "www.example.com"]

    def test_junk_entries_are_dropped(self, monkeypatch):
        mocked_entries = [
            {"name_value": "www.example.com"},
            {"name_value": "not a hostname"},
            {"name_value": "evil.com; rm -rf /"},
        ]
        monkeypatch.setattr(infra, "_http_get_json", lambda url, headers=None: mocked_entries)

        subdomains = infra.fetch_crtsh_subdomains("example.com")

        assert subdomains == ["www.example.com"]


class TestBuildSnapshot:
    def test_snapshot_structure_has_expected_fields(self, monkeypatch):
        monkeypatch.setattr(
            infra,
            "resolve_dns",
            lambda domain, types: {"A": ["93.184.216.34"], "MX": [], "NS": ["ns1.example.com"], "TXT": []},
        )
        monkeypatch.setattr(infra, "fetch_crtsh_subdomains", lambda domain: ["www.example.com"])

        snapshot = infra.build_snapshot("example.com")

        assert snapshot["domain"] == "example.com"
        assert "timestamp" in snapshot
        assert snapshot["dns"]["A"] == ["93.184.216.34"]
        assert snapshot["resolved_ip"] == "93.184.216.34"
        assert snapshot["subdomain_count"] == 1
        assert snapshot["subdomains"] == ["www.example.com"]

    def test_resolved_ip_is_none_when_no_a_record(self, monkeypatch):
        monkeypatch.setattr(
            infra, "resolve_dns", lambda domain, types: {"A": [], "MX": [], "NS": [], "TXT": []}
        )
        monkeypatch.setattr(infra, "fetch_crtsh_subdomains", lambda domain: [])

        snapshot = infra.build_snapshot("example.com")

        assert snapshot["resolved_ip"] is None


class TestCmdSnapshotWritesFile:
    def test_snapshot_written_to_out_file_is_valid_json(self, monkeypatch, tmp_path):
        monkeypatch.setattr(
            infra, "build_snapshot", lambda domain: {"domain": domain, "dns": {}, "subdomains": []}
        )
        out_path = tmp_path / "snap.json"
        args = argparse.Namespace(domain="example.com", out=str(out_path))

        infra.cmd_snapshot(args)

        written = json.loads(out_path.read_text())
        assert written["domain"] == "example.com"


class TestLoadSnapshot:
    def test_missing_file_exits_with_code_2(self, tmp_path):
        with pytest.raises(SystemExit) as exc_info:
            infra.load_snapshot(str(tmp_path / "does-not-exist.json"))

        assert exc_info.value.code == 2

    def test_invalid_json_exits_with_code_2(self, tmp_path):
        bad_file = tmp_path / "bad.json"
        bad_file.write_text("{not valid json")

        with pytest.raises(SystemExit) as exc_info:
            infra.load_snapshot(str(bad_file))

        assert exc_info.value.code == 2

    def test_missing_required_field_exits_with_code_2(self, tmp_path):
        incomplete = tmp_path / "incomplete.json"
        incomplete.write_text(json.dumps({"domain": "example.com"}))

        with pytest.raises(SystemExit) as exc_info:
            infra.load_snapshot(str(incomplete))

        assert exc_info.value.code == 2

    def test_valid_snapshot_round_trips(self, tmp_path):
        snapshot = {
            "domain": "example.com",
            "timestamp": "2026-07-01T00:00:00+00:00",
            "dns": {"A": ["93.184.216.34"], "MX": [], "NS": [], "TXT": []},
            "resolved_ip": "93.184.216.34",
            "subdomain_count": 1,
            "subdomains": ["www.example.com"],
        }
        path = tmp_path / "snap.json"
        path.write_text(json.dumps(snapshot))

        loaded = infra.load_snapshot(str(path))

        assert loaded == snapshot


class TestDiffDns:
    def test_detects_added_and_removed_records_per_type(self):
        old_dns = {"A": ["1.1.1.1"], "MX": ["10 mail.old.com"], "NS": ["ns1.example.com"], "TXT": []}
        new_dns = {"A": ["2.2.2.2"], "MX": ["10 mail.old.com"], "NS": ["ns1.example.com"], "TXT": ["v=spf1"]}

        changes = infra.diff_dns(old_dns, new_dns)

        assert changes == {
            "A": {"added": ["2.2.2.2"], "removed": ["1.1.1.1"]},
            "TXT": {"added": ["v=spf1"], "removed": []},
        }

    def test_no_changes_yields_empty_dict(self):
        dns = {"A": ["1.1.1.1"], "MX": [], "NS": [], "TXT": []}

        assert infra.diff_dns(dns, dict(dns)) == {}


class TestDiffSnapshots:
    def _snapshot(self, ip, dns_a, subdomains):
        return {
            "domain": "example.com",
            "timestamp": "2026-07-01T00:00:00+00:00",
            "dns": {"A": dns_a, "MX": [], "NS": [], "TXT": []},
            "resolved_ip": ip,
            "subdomain_count": len(subdomains),
            "subdomains": subdomains,
        }

    def test_identical_snapshots_have_no_changes(self):
        snap = self._snapshot("1.1.1.1", ["1.1.1.1"], ["www.example.com"])

        diff = infra.diff_snapshots(snap, dict(snap))

        assert diff["has_changes"] is False
        assert diff["ip_changed"] is False
        assert diff["dns_changes"] == {}
        assert diff["subdomain_changes"] == {"added": [], "removed": []}

    def test_ip_change_and_new_subdomain_are_detected(self):
        old = self._snapshot("1.1.1.1", ["1.1.1.1"], ["www.example.com"])
        new = self._snapshot("2.2.2.2", ["2.2.2.2"], ["www.example.com", "shadow.example.com"])

        diff = infra.diff_snapshots(old, new)

        assert diff["has_changes"] is True
        assert diff["ip_changed"] is True
        assert diff["old_ip"] == "1.1.1.1"
        assert diff["new_ip"] == "2.2.2.2"
        assert diff["subdomain_changes"] == {"added": ["shadow.example.com"], "removed": []}


class TestFormatDiffHuman:
    def test_no_changes_message(self):
        diff = {
            "domain": "example.com",
            "dns_changes": {},
            "ip_changed": False,
            "old_ip": "1.1.1.1",
            "new_ip": "1.1.1.1",
            "subdomain_changes": {"added": [], "removed": []},
            "has_changes": False,
        }

        text = infra.format_diff_human(diff)

        assert "No infrastructure changes detected for example.com" in text

    def test_changes_are_listed(self):
        diff = {
            "domain": "example.com",
            "dns_changes": {"A": {"added": ["2.2.2.2"], "removed": ["1.1.1.1"]}},
            "ip_changed": True,
            "old_ip": "1.1.1.1",
            "new_ip": "2.2.2.2",
            "subdomain_changes": {"added": ["shadow.example.com"], "removed": []},
            "has_changes": True,
        }

        text = infra.format_diff_human(diff)

        assert "A added: 2.2.2.2" in text
        assert "A removed: 1.1.1.1" in text
        assert "resolved IP changed: 1.1.1.1 -> 2.2.2.2" in text
        assert "subdomains added: shadow.example.com" in text


class TestCmdDiffFailOnChange:
    def test_no_changes_exits_zero(self, tmp_path, capsys):
        snapshot = {
            "domain": "example.com",
            "timestamp": "t",
            "dns": {"A": [], "MX": [], "NS": [], "TXT": []},
            "resolved_ip": None,
            "subdomain_count": 0,
            "subdomains": [],
        }
        old_path, new_path = tmp_path / "old.json", tmp_path / "new.json"
        old_path.write_text(json.dumps(snapshot))
        new_path.write_text(json.dumps(snapshot))
        args = argparse.Namespace(old=str(old_path), new=str(new_path), json=False, fail_on_change=True)

        infra.cmd_diff(args)  # should not raise/exit

        assert "No infrastructure changes" in capsys.readouterr().out

    def test_changes_with_fail_on_change_exits_one(self, tmp_path):
        old_snapshot = {
            "domain": "example.com",
            "timestamp": "t1",
            "dns": {"A": ["1.1.1.1"], "MX": [], "NS": [], "TXT": []},
            "resolved_ip": "1.1.1.1",
            "subdomain_count": 0,
            "subdomains": [],
        }
        new_snapshot = json.loads(json.dumps(old_snapshot))
        new_snapshot["dns"]["A"] = ["2.2.2.2"]
        new_snapshot["resolved_ip"] = "2.2.2.2"
        old_path, new_path = tmp_path / "old.json", tmp_path / "new.json"
        old_path.write_text(json.dumps(old_snapshot))
        new_path.write_text(json.dumps(new_snapshot))
        args = argparse.Namespace(old=str(old_path), new=str(new_path), json=True, fail_on_change=True)

        with pytest.raises(SystemExit) as exc_info:
            infra.cmd_diff(args)

        assert exc_info.value.code == 1


@pytest.mark.skip(reason="hits live network services (dns.google/crt.sh) — run manually")
class TestLiveSnapshot:
    def test_live_snapshot_of_example_com(self):
        snapshot = infra.build_snapshot("example.com")

        assert snapshot["domain"] == "example.com"
        assert snapshot["resolved_ip"]
