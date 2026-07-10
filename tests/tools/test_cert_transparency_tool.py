"""Tests for the Certificate Transparency tool (domain validation, crt.sh JSON
parsing, subdomain dedupe/wildcard-strip, no network except in the opt-in
live class)."""

import json
from unittest.mock import MagicMock, patch

import pytest

from tools.cert_transparency_tool import (
    _validate_domain,
    _validate_limit,
    ct_subdomains,
    ct_certificates,
)


def _mock_response(payload) -> MagicMock:
    """Build a urlopen()-context-manager mock returning payload as JSON bytes."""
    mock_response = MagicMock()
    mock_response.read.return_value = json.dumps(payload).encode()
    mock_response.__enter__ = lambda s: s
    mock_response.__exit__ = MagicMock(return_value=False)
    return mock_response


class TestValidateDomain:
    def test_simple_domain_ok(self):
        assert _validate_domain("example.com") == "example.com"

    def test_subdomain_ok(self):
        assert _validate_domain("sub.example.com") == "sub.example.com"

    def test_strips_whitespace_and_lowercases(self):
        assert _validate_domain("  Example.COM  ") == "example.com"

    def test_strips_trailing_dot(self):
        assert _validate_domain("example.com.") == "example.com"

    def test_rejects_empty(self):
        assert _validate_domain("") is None
        assert _validate_domain(None) is None

    def test_rejects_non_string(self):
        assert _validate_domain(12345) is None

    def test_rejects_no_dot(self):
        assert _validate_domain("localhost") is None

    def test_rejects_wildcard(self):
        assert _validate_domain("*.example.com") is None

    def test_rejects_injection_characters(self):
        assert _validate_domain("example.com/../../etc") is None
        assert _validate_domain("example.com; rm -rf /") is None
        assert _validate_domain("example.com?q=%.evil.com") is None
        assert _validate_domain("example.com\nHost: evil") is None

    def test_rejects_leading_or_trailing_hyphen_label(self):
        assert _validate_domain("-example.com") is None
        assert _validate_domain("example-.com") is None

    def test_rejects_overlong_domain(self):
        assert _validate_domain("a" * 250 + ".com") is None


class TestValidateLimit:
    def test_default_on_invalid(self):
        assert _validate_limit("not-a-number", 200, 1000) == 200

    def test_clamps_high(self):
        assert _validate_limit(99999, 200, 1000) == 1000

    def test_clamps_low(self):
        assert _validate_limit(0, 200, 1000) == 1

    def test_passthrough(self):
        assert _validate_limit(10, 200, 1000) == 10


class TestCtSubdomains:
    def test_invalid_domain_no_network_call(self):
        with patch("tools.cert_transparency_tool.urllib.request.urlopen") as mock_urlopen:
            result = ct_subdomains("not a domain; rm -rf /")
        assert result["ok"] is False
        assert "invalid domain" in result["error"]
        mock_urlopen.assert_not_called()

    def test_builds_wildcard_query_url_encoded(self):
        with patch("tools.cert_transparency_tool.urllib.request.urlopen", return_value=_mock_response([])) as mock_urlopen:
            ct_subdomains("example.com")

        req = mock_urlopen.call_args[0][0]
        assert req.full_url.startswith("https://crt.sh/?q=")
        assert "q=%25.example.com" in req.full_url
        assert "output=json" in req.full_url
        assert req.get_header("User-agent") == "hermes-agent-cert-transparency-tool/1.0"

    def test_parses_dedupes_sorts_and_strips_wildcards(self):
        payload = [
            {"name_value": "*.example.com\nwww.example.com"},
            {"name_value": "api.example.com\nwww.example.com"},
            {"name_value": "Api.Example.com"},
        ]
        with patch("tools.cert_transparency_tool.urllib.request.urlopen", return_value=_mock_response(payload)):
            result = ct_subdomains("example.com")

        assert result["ok"] is True
        assert result["domain"] == "example.com"
        assert result["subdomains"] == ["api.example.com", "example.com", "www.example.com"]
        assert result["count"] == 3

    def test_empty_result_is_no_subdomains(self):
        with patch("tools.cert_transparency_tool.urllib.request.urlopen", return_value=_mock_response([])):
            result = ct_subdomains("example.com")
        assert result == {"ok": True, "domain": "example.com", "subdomains": [], "count": 0}

    def test_limit_truncates_results(self):
        payload = [{"name_value": f"host{i}.example.com"} for i in range(10)]
        with patch("tools.cert_transparency_tool.urllib.request.urlopen", return_value=_mock_response(payload)):
            result = ct_subdomains("example.com", limit=3)
        assert result["ok"] is True
        assert result["count"] == 3
        assert result["subdomains"] == sorted(result["subdomains"])

    def test_ignores_non_dict_entries_and_junk_lines(self):
        payload = ["not-a-dict", {"name_value": "not a hostname !!\n\nvalid.example.com"}]
        with patch("tools.cert_transparency_tool.urllib.request.urlopen", return_value=_mock_response(payload)):
            result = ct_subdomains("example.com")
        assert result["ok"] is True
        assert result["subdomains"] == ["valid.example.com"]

    def test_network_error_is_reported(self):
        import urllib.error
        with patch("tools.cert_transparency_tool.urllib.request.urlopen", side_effect=urllib.error.URLError("boom")):
            result = ct_subdomains("example.com")
        assert result["ok"] is False
        assert "crt.sh request failed" in result["error"]

    def test_oversized_response_is_rejected_with_hint(self):
        import tools.cert_transparency_tool as ct_tool

        oversized = MagicMock()
        oversized.read.return_value = b"x" * (ct_tool._MAX_RESPONSE_BYTES + 1)
        oversized.__enter__ = lambda s: s
        oversized.__exit__ = MagicMock(return_value=False)

        with patch("tools.cert_transparency_tool.urllib.request.urlopen", return_value=oversized):
            result = ct_subdomains("example.com")

        assert result["ok"] is False
        assert "exceeds" in result["error"]
        assert "more specific" in result["error"]

    def test_malformed_json_is_reported(self):
        mock_response = MagicMock()
        mock_response.read.return_value = b"not json"
        mock_response.__enter__ = lambda s: s
        mock_response.__exit__ = MagicMock(return_value=False)

        with patch("tools.cert_transparency_tool.urllib.request.urlopen", return_value=mock_response):
            result = ct_subdomains("example.com")
        assert result["ok"] is False
        assert "not valid JSON" in result["error"]

    def test_unexpected_response_shape_is_reported(self):
        with patch("tools.cert_transparency_tool.urllib.request.urlopen", return_value=_mock_response({"not": "a list"})):
            result = ct_subdomains("example.com")
        assert result["ok"] is False
        assert "unexpected crt.sh response shape" in result["error"]


class TestCtCertificates:
    def test_invalid_domain_no_network_call(self):
        with patch("tools.cert_transparency_tool.urllib.request.urlopen") as mock_urlopen:
            result = ct_certificates("not a domain")
        assert result["ok"] is False
        mock_urlopen.assert_not_called()

    def test_parses_and_sorts_most_recent_first(self):
        payload = [
            {
                "issuer_name": "C=US, O=Let's Encrypt, CN=R3",
                "name_value": "old.example.com",
                "not_before": "2020-01-01T00:00:00",
                "not_after": "2020-04-01T00:00:00",
            },
            {
                "issuer_name": "C=US, O=Let's Encrypt, CN=R3",
                "name_value": "new.example.com",
                "not_before": "2024-01-01T00:00:00",
                "not_after": "2024-04-01T00:00:00",
            },
        ]
        with patch("tools.cert_transparency_tool.urllib.request.urlopen", return_value=_mock_response(payload)):
            result = ct_certificates("example.com")

        assert result["ok"] is True
        assert result["count"] == 2
        assert result["certificates"][0]["name_value"] == "new.example.com"
        assert result["certificates"][1]["name_value"] == "old.example.com"

    def test_empty_result_is_no_certificates(self):
        with patch("tools.cert_transparency_tool.urllib.request.urlopen", return_value=_mock_response([])):
            result = ct_certificates("example.com")
        assert result == {"ok": True, "domain": "example.com", "certificates": [], "count": 0}

    def test_limit_truncates_results(self):
        payload = [
            {"issuer_name": "CA", "name_value": f"h{i}.example.com", "not_before": "2024-01-01T00:00:00", "not_after": "2024-04-01T00:00:00"}
            for i in range(10)
        ]
        with patch("tools.cert_transparency_tool.urllib.request.urlopen", return_value=_mock_response(payload)):
            result = ct_certificates("example.com", limit=4)
        assert result["ok"] is True
        assert result["count"] == 4


@pytest.mark.skip(reason="live network — run manually")
class TestLiveCtSubdomains:
    """Live integration test against the real crt.sh API. Skipped if offline/rate-limited."""

    def test_example_com_has_at_least_one_subdomain(self):
        try:
            result = ct_subdomains("example.com")
        except Exception:
            pytest.skip("crt.sh unreachable")
        if not result.get("ok"):
            pytest.skip("crt.sh unreachable or rate-limited")
        assert result["count"] >= 1
        assert "example.com" in result["subdomains"]
