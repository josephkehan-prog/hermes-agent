"""Tests for skills/research/network-recon/scripts/recon.py — no network, no external services."""

from __future__ import annotations

import argparse
import importlib.util
import json
import urllib.request
from http.client import HTTPMessage
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT = REPO_ROOT / "skills" / "research" / "network-recon" / "scripts" / "recon.py"


def _load_script_module():
    spec = importlib.util.spec_from_file_location("network_recon_test_module", SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


recon = _load_script_module()


class TestValidateDomain:
    def test_valid_domain_passes_through_unchanged(self):
        assert recon.validate_domain("example.com") == "example.com"

    def test_subdomain_is_valid(self):
        assert recon.validate_domain("dev.api.example.co.uk") == "dev.api.example.co.uk"

    def test_shell_injection_attempt_exits_with_code_2(self):
        with pytest.raises(SystemExit) as exc_info:
            recon.validate_domain("evil.com; rm -rf /")

        assert exc_info.value.code == 2

    def test_bare_word_without_a_dot_is_rejected(self):
        with pytest.raises(SystemExit) as exc_info:
            recon.validate_domain("localhost")

        assert exc_info.value.code == 2

    def test_leading_hyphen_label_is_rejected(self):
        with pytest.raises(SystemExit) as exc_info:
            recon.validate_domain("-evil.example.com")

        assert exc_info.value.code == 2

    def test_embedded_whitespace_is_rejected(self):
        with pytest.raises(SystemExit) as exc_info:
            recon.validate_domain("example .com")

        assert exc_info.value.code == 2


class TestRequireHttpScheme:
    def test_file_scheme_exits_with_code_2(self):
        with pytest.raises(SystemExit) as exc_info:
            recon._require_http_scheme("file:///etc/passwd")

        assert exc_info.value.code == 2

    def test_http_and_https_schemes_are_allowed(self):
        recon._require_http_scheme("http://example.com")
        recon._require_http_scheme("https://example.com")


class TestBuildPtrName:
    def test_ipv4_address_reverses_octets_into_in_addr_arpa(self):
        assert recon._build_ptr_name("93.184.216.34") == "34.216.184.93.in-addr.arpa"

    def test_ipv6_address_produces_ip6_arpa_suffix(self):
        name = recon._build_ptr_name("2001:db8::1")

        assert name == (
            "1.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.8.b.d.0.1.0.0.2.ip6.arpa"
        )

    def test_hostname_instead_of_ip_exits_with_code_2(self):
        with pytest.raises(SystemExit) as exc_info:
            recon._build_ptr_name("example.com")

        assert exc_info.value.code == 2

    def test_ptr_with_hostname_via_cmd_dns_exits_cleanly(self, monkeypatch):
        monkeypatch.setattr(recon, "_http_get_json", lambda url, headers=None: {"Answer": []})
        args = argparse.Namespace(domain="example.com", types="PTR")

        with pytest.raises(SystemExit) as exc_info:
            recon.cmd_dns(args)

        assert exc_info.value.code == 2


class TestIsIpAddress:
    def test_ipv4_is_detected(self):
        assert recon.is_ip_address("93.184.216.34") is True

    def test_domain_is_not_an_ip(self):
        assert recon.is_ip_address("example.com") is False


class TestResolveDnsParsesDohJson:
    def test_parses_mocked_google_doh_a_record_response(self, monkeypatch):
        mocked_payload = {
            "Status": 0,
            "Answer": [{"name": "example.com.", "type": 1, "TTL": 300, "data": "93.184.216.34"}],
        }
        monkeypatch.setattr(recon, "_http_get_json", lambda url, headers=None: mocked_payload)

        results = recon.resolve_dns("example.com", ["A"])

        assert results == {"A": ["93.184.216.34"]}

    def test_empty_answer_section_yields_empty_list(self, monkeypatch):
        monkeypatch.setattr(recon, "_http_get_json", lambda url, headers=None: {"Status": 0})

        results = recon.resolve_dns("example.com", ["TXT"])

        assert results == {"TXT": []}

    def test_doh_fallback_tries_second_provider_when_first_fails(self, monkeypatch):
        import urllib.error

        calls = []

        def fake_get(url, headers=None):
            calls.append(url)
            if recon.DOH_PROVIDERS[0] in url:
                raise urllib.error.URLError("first provider down")
            return {"Answer": [{"data": "93.184.216.34"}]}

        monkeypatch.setattr(recon, "_http_get_json", fake_get)

        result = recon.query_doh("example.com", "A")

        assert result == {"Answer": [{"data": "93.184.216.34"}]}
        assert len(calls) == 2


class TestRejectPrivateTarget:
    def test_loopback_literal_ip_exits_with_code_2(self):
        with pytest.raises(SystemExit) as exc_info:
            recon._reject_private_target("http://127.0.0.1:18299/")

        assert exc_info.value.code == 2

    def test_link_local_literal_ip_exits_with_code_2(self):
        with pytest.raises(SystemExit) as exc_info:
            recon._reject_private_target("http://169.254.169.254/latest/meta-data/")

        assert exc_info.value.code == 2

    def test_private_range_literal_ip_exits_with_code_2(self):
        with pytest.raises(SystemExit) as exc_info:
            recon._reject_private_target("http://10.0.0.5/")

        assert exc_info.value.code == 2

    def test_hostname_resolving_to_loopback_exits_with_code_2(self, monkeypatch):
        monkeypatch.setattr(recon.socket, "gethostbyname", lambda host: "127.0.0.1")

        with pytest.raises(SystemExit) as exc_info:
            recon._reject_private_target("http://internal.example.com/")

        assert exc_info.value.code == 2

    def test_public_ip_does_not_exit(self, monkeypatch):
        monkeypatch.setattr(recon.socket, "gethostbyname", lambda host: "93.184.216.34")

        recon._reject_private_target("http://example.com/")

    def test_fingerprint_on_loopback_url_exits_with_code_2(self, monkeypatch):
        with pytest.raises(SystemExit) as exc_info:
            recon.fetch_fingerprint("http://127.0.0.1/")

        assert exc_info.value.code == 2


class TestSafeRedirectHandler:
    """A public URL that 30x-redirects to a private/loopback/metadata address
    must not be followed — the redirect handler has to re-validate each hop,
    not just the original request URL."""

    def test_redirect_to_loopback_target_is_refused(self):
        handler = recon._SafeRedirectHandler()
        req = urllib.request.Request("https://public.example.com/")

        with pytest.raises(SystemExit) as exc_info:
            handler.redirect_request(
                req, None, 302, "Found", HTTPMessage(), "http://127.0.0.1/"
            )

        assert exc_info.value.code == 2

    def test_redirect_to_metadata_target_is_refused(self):
        handler = recon._SafeRedirectHandler()
        req = urllib.request.Request("https://public.example.com/")

        with pytest.raises(SystemExit) as exc_info:
            handler.redirect_request(
                req,
                None,
                302,
                "Found",
                HTTPMessage(),
                "http://169.254.169.254/latest/meta-data/",
            )

        assert exc_info.value.code == 2

    def test_redirect_to_public_target_is_followed(self, monkeypatch):
        monkeypatch.setattr(recon.socket, "gethostbyname", lambda host: "93.184.216.34")
        handler = recon._SafeRedirectHandler()
        req = urllib.request.Request("https://public.example.com/")

        new_request = handler.redirect_request(
            req, None, 302, "Found", HTTPMessage(), "https://example.com/next"
        )

        assert new_request.full_url == "https://example.com/next"

    def test_fetch_fingerprint_follows_redirect_to_public_host_and_returns_response(
        self, monkeypatch
    ):
        """End-to-end: a public URL that redirects to another public URL still
        resolves normally through fetch_fingerprint's opener."""
        monkeypatch.setattr(recon.socket, "gethostbyname", lambda host: "93.184.216.34")

        class FakeResponse:
            status = 200
            headers = HTTPMessage()

            def read(self, n=-1):
                return b""

            def __enter__(self):
                return self

            def __exit__(self, *exc_info):
                return False

        def fake_open(self, req, timeout=None):
            return FakeResponse()

        monkeypatch.setattr(urllib.request.OpenerDirector, "open", fake_open)

        result = recon.fetch_fingerprint("https://public.example.com/")

        assert result["status"] == 200

    def test_fetch_fingerprint_rejects_redirect_chain_to_private_host(self, monkeypatch):
        """Simulate the opener actually walking a redirect hop to a private
        target: the _SafeRedirectHandler must refuse it mid-chain rather
        than returning a fetched response."""
        monkeypatch.setattr(recon.socket, "gethostbyname", lambda host: "93.184.216.34")

        def fake_open(opener_self, req, timeout=None):
            handler = recon._SafeRedirectHandler()
            handler.redirect_request(
                req, None, 302, "Found", HTTPMessage(), "http://127.0.0.1/admin"
            )
            raise AssertionError("should not reach here — redirect must be refused")

        monkeypatch.setattr(urllib.request.OpenerDirector, "open", fake_open)

        with pytest.raises(SystemExit) as exc_info:
            recon.fetch_fingerprint("https://public.example.com/")

        assert exc_info.value.code == 2


class TestRunWhoisOutputCap:
    def test_whois_output_is_truncated_to_max_bytes(self, monkeypatch, tmp_path):
        fake_whois = tmp_path / "whois"
        fake_whois.write_text("#!/bin/sh\necho fake output\n")
        fake_whois.chmod(0o755)
        monkeypatch.setattr(recon.shutil, "which", lambda name: str(fake_whois))
        monkeypatch.setattr(recon, "MAX_WHOIS_BYTES", 5)

        output = recon.run_whois("example.com")

        assert len(output) == 5


class TestFetchCrtshSubdomains:
    def test_parses_mocked_crtsh_json_and_dedupes(self, monkeypatch):
        mocked_entries = [
            {"name_value": "www.example.com\nexample.com"},
            {"name_value": "DEV.example.com"},
            {"name_value": "*.example.com"},
            {"name_value": "www.example.com"},
        ]
        monkeypatch.setattr(recon, "_http_get_json", lambda url, headers=None: mocked_entries)

        subdomains = recon.fetch_crtsh_subdomains("example.com")

        assert subdomains == ["dev.example.com", "example.com", "www.example.com"]

    def test_junk_entries_that_are_not_valid_hostnames_are_dropped(self, monkeypatch):
        mocked_entries = [
            {"name_value": "www.example.com"},
            {"name_value": "not a hostname"},
            {"name_value": "evil.com; rm -rf /"},
            {"name_value": "*"},
            {"name_value": ""},
        ]
        monkeypatch.setattr(recon, "_http_get_json", lambda url, headers=None: mocked_entries)

        subdomains = recon.fetch_crtsh_subdomains("example.com")

        assert subdomains == ["www.example.com"]

    def test_query_url_is_percent_encoded_via_urllib_quote(self, monkeypatch):
        captured_url = {}

        def fake_get(url, headers=None):
            captured_url["url"] = url
            return []

        monkeypatch.setattr(recon, "_http_get_json", fake_get)

        recon.fetch_crtsh_subdomains("example.com")

        assert "q=%25.example.com" in captured_url["url"]
        assert captured_url["url"].startswith(recon.CRT_SH_URL)


class TestAuditSecurityHeaders:
    def test_flags_all_headers_missing_on_bare_response(self):
        audit = recon.audit_security_headers({"Server": "nginx"})

        assert audit["missing"] == recon.SECURITY_HEADERS
        assert audit["present"] == []

    def test_matches_header_names_case_insensitively(self):
        audit = recon.audit_security_headers({"strict-transport-security": "max-age=1"})

        assert "Strict-Transport-Security" in audit["present"]
        assert "Strict-Transport-Security" not in audit["missing"]


class TestRunWhoisWhenBinaryAbsent:
    def test_missing_whois_binary_exits_with_code_2(self, monkeypatch):
        monkeypatch.setattr(recon.shutil, "which", lambda name: None)

        with pytest.raises(SystemExit) as exc_info:
            recon.run_whois("example.com")

        assert exc_info.value.code == 2

    def test_present_whois_binary_is_invoked_without_shell(self, monkeypatch, tmp_path):
        fake_whois = tmp_path / "whois"
        fake_whois.write_text("#!/bin/sh\necho fake output\n")
        fake_whois.chmod(0o755)
        monkeypatch.setattr(recon.shutil, "which", lambda name: str(fake_whois))

        output = recon.run_whois("example.com")

        assert "fake output" in output
