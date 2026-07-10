"""Tests for the DNS-over-HTTPS recon tool (domain/record-type validation,
request building, fallback behavior — no network except in the opt-in live
class)."""

import json
import urllib.error
from unittest.mock import MagicMock, patch

import pytest

from tools.dns_recon_tool import (
    _validate_domain,
    _validate_record_type,
    dns_lookup,
    dns_bulk,
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
        assert _validate_domain("www.example.co.uk") == "www.example.co.uk"

    def test_strips_whitespace(self):
        assert _validate_domain("  example.com  ") == "example.com"

    def test_rejects_empty(self):
        assert _validate_domain("") is None
        assert _validate_domain(None) is None

    def test_rejects_non_string(self):
        assert _validate_domain(12345) is None

    def test_rejects_path_traversal(self):
        assert _validate_domain("example.com/../x") is None

    def test_rejects_shell_metacharacter(self):
        assert _validate_domain("a;b.com") is None

    def test_rejects_space(self):
        assert _validate_domain("example .com") is None

    def test_rejects_leading_dot(self):
        assert _validate_domain(".example.com") is None

    def test_rejects_double_dot(self):
        assert _validate_domain("example..com") is None

    def test_rejects_leading_hyphen_label(self):
        assert _validate_domain("-example.com") is None

    def test_rejects_url_scheme(self):
        assert _validate_domain("https://example.com") is None

    def test_rejects_oversized_domain(self):
        assert _validate_domain("a" * 254) is None


class TestValidateRecordType:
    def test_allowed_type_ok(self):
        assert _validate_record_type("A") == "A"

    def test_lowercase_is_normalized(self):
        assert _validate_record_type("mx") == "MX"

    def test_rejects_unknown_type(self):
        assert _validate_record_type("ANY") is None

    def test_rejects_non_string(self):
        assert _validate_record_type(123) is None


class TestDnsLookupValidationNoNetwork:
    def test_invalid_domain_no_network_call(self):
        with patch("tools.dns_recon_tool.urllib.request.urlopen") as mock_urlopen:
            result = dns_lookup("example.com/../x", "A")
        assert result["ok"] is False
        assert "invalid domain" in result["error"]
        mock_urlopen.assert_not_called()

    def test_injection_attempt_semicolon_no_network_call(self):
        with patch("tools.dns_recon_tool.urllib.request.urlopen") as mock_urlopen:
            result = dns_lookup("a;b.com", "A")
        assert result["ok"] is False
        mock_urlopen.assert_not_called()

    def test_unsupported_record_type_no_network_call(self):
        with patch("tools.dns_recon_tool.urllib.request.urlopen") as mock_urlopen:
            result = dns_lookup("example.com", "ANY")
        assert result["ok"] is False
        assert "unsupported record_type" in result["error"]
        mock_urlopen.assert_not_called()


class TestDnsLookupRequestBuilding:
    def test_builds_cloudflare_url_with_encoded_params(self):
        payload = {
            "Status": 0,
            "Answer": [{"name": "example.com.", "type": 1, "TTL": 300, "data": "93.184.216.34"}],
        }
        with patch("tools.dns_recon_tool.urllib.request.urlopen", return_value=_mock_response(payload)) as mock_urlopen:
            result = dns_lookup("example.com", "A")

        req = mock_urlopen.call_args[0][0]
        assert req.full_url.startswith("https://cloudflare-dns.com/dns-query?")
        assert "name=example.com" in req.full_url
        assert "type=A" in req.full_url
        assert req.get_header("User-agent") == "hermes-agent-dns-recon-tool/1.0"
        assert req.get_header("Accept") == "application/dns-json"

        assert result["ok"] is True
        assert result["domain"] == "example.com"
        assert result["record_type"] == "A"
        assert result["records"] == ["93.184.216.34"]

    def test_filters_answers_to_requested_type(self):
        # A CNAME-fronted domain returns both CNAME and A records in Answer;
        # only the requested type's records should be surfaced.
        payload = {
            "Status": 0,
            "Answer": [
                {"name": "www.example.com.", "type": 5, "TTL": 300, "data": "example.com."},
                {"name": "example.com.", "type": 1, "TTL": 300, "data": "93.184.216.34"},
            ],
        }
        with patch("tools.dns_recon_tool.urllib.request.urlopen", return_value=_mock_response(payload)):
            result = dns_lookup("www.example.com", "A")
        assert result["records"] == ["93.184.216.34"]

    def test_no_answer_is_empty_records(self):
        payload = {"Status": 3}
        with patch("tools.dns_recon_tool.urllib.request.urlopen", return_value=_mock_response(payload)):
            result = dns_lookup("nonexistent.invalid", "A")
        assert result["ok"] is True
        assert result["records"] == []

    def test_record_type_lowercase_is_normalized_in_result(self):
        payload = {"Status": 0, "Answer": [{"name": "example.com.", "type": 16, "TTL": 300, "data": '"v=spf1 -all"'}]}
        with patch("tools.dns_recon_tool.urllib.request.urlopen", return_value=_mock_response(payload)):
            result = dns_lookup("example.com", "txt")
        assert result["record_type"] == "TXT"
        assert result["records"] == ['"v=spf1 -all"']


class TestDnsLookupFallback:
    def test_falls_back_to_google_on_cloudflare_failure(self):
        payload = {
            "Status": 0,
            "Answer": [{"name": "example.com.", "type": 1, "TTL": 300, "data": "93.184.216.34"}],
        }
        with patch(
            "tools.dns_recon_tool.urllib.request.urlopen",
            side_effect=[urllib.error.URLError("cloudflare down"), _mock_response(payload)],
        ) as mock_urlopen:
            result = dns_lookup("example.com", "A")

        assert result["ok"] is True
        assert result["records"] == ["93.184.216.34"]
        first_req = mock_urlopen.call_args_list[0][0][0]
        second_req = mock_urlopen.call_args_list[1][0][0]
        assert first_req.full_url.startswith("https://cloudflare-dns.com/dns-query?")
        assert second_req.full_url.startswith("https://dns.google/resolve?")

    def test_both_endpoints_failing_reports_error(self):
        with patch(
            "tools.dns_recon_tool.urllib.request.urlopen",
            side_effect=urllib.error.URLError("boom"),
        ):
            result = dns_lookup("example.com", "A")
        assert result["ok"] is False
        assert "DoH request to" in result["error"]

    def test_malformed_json_falls_back(self):
        bad_response = MagicMock()
        bad_response.read.return_value = b"not json"
        bad_response.__enter__ = lambda s: s
        bad_response.__exit__ = MagicMock(return_value=False)

        payload = {"Status": 0, "Answer": [{"name": "example.com.", "type": 1, "TTL": 300, "data": "1.2.3.4"}]}
        with patch(
            "tools.dns_recon_tool.urllib.request.urlopen",
            side_effect=[bad_response, _mock_response(payload)],
        ):
            result = dns_lookup("example.com", "A")
        assert result["ok"] is True
        assert result["records"] == ["1.2.3.4"]


class TestDnsLookupCapEnforcement:
    def test_oversized_response_falls_back_then_errors(self):
        import tools.dns_recon_tool as dns_recon_tool

        oversized = MagicMock()
        oversized.read.return_value = b"x" * (dns_recon_tool._MAX_RESPONSE_BYTES + 1)
        oversized.__enter__ = lambda s: s
        oversized.__exit__ = MagicMock(return_value=False)

        with patch("tools.dns_recon_tool.urllib.request.urlopen", return_value=oversized):
            result = dns_lookup("example.com", "A")

        assert result["ok"] is False
        assert "exceeds" in result["error"]

    def test_oversized_cloudflare_response_falls_back_to_google_success(self):
        import tools.dns_recon_tool as dns_recon_tool

        oversized = MagicMock()
        oversized.read.return_value = b"x" * (dns_recon_tool._MAX_RESPONSE_BYTES + 1)
        oversized.__enter__ = lambda s: s
        oversized.__exit__ = MagicMock(return_value=False)

        payload = {"Status": 0, "Answer": [{"name": "example.com.", "type": 1, "TTL": 300, "data": "1.2.3.4"}]}
        with patch(
            "tools.dns_recon_tool.urllib.request.urlopen",
            side_effect=[oversized, _mock_response(payload)],
        ):
            result = dns_lookup("example.com", "A")

        assert result["ok"] is True
        assert result["records"] == ["1.2.3.4"]


class TestDnsBulk:
    def test_invalid_domain_no_network_call(self):
        with patch("tools.dns_recon_tool.urllib.request.urlopen") as mock_urlopen:
            result = dns_bulk("a;b.com")
        assert result["ok"] is False
        assert "invalid domain" in result["error"]
        mock_urlopen.assert_not_called()

    def test_default_record_types_used_when_omitted(self):
        payload = {"Status": 0, "Answer": []}
        with patch("tools.dns_recon_tool.urllib.request.urlopen", return_value=_mock_response(payload)):
            result = dns_bulk("example.com")
        assert result["ok"] is True
        assert set(result["results"].keys()) == {"A", "AAAA", "MX", "NS", "TXT"}

    def test_per_type_isolation(self):
        import tools.dns_recon_tool as dns_recon_tool

        def fake_lookup(domain, record_type="A"):
            if record_type == "MX":
                return {"ok": False, "error": "simulated failure"}
            return {"ok": True, "domain": domain, "record_type": record_type, "records": []}

        with patch.object(dns_recon_tool, "dns_lookup", side_effect=fake_lookup):
            result = dns_recon_tool.dns_bulk("example.com", record_types=["A", "MX"])

        assert result["ok"] is True
        assert result["results"]["A"]["ok"] is True
        assert result["results"]["MX"]["ok"] is False

    def test_explicit_record_types_are_respected(self):
        payload = {"Status": 0, "Answer": [{"name": "example.com.", "type": 15, "TTL": 300, "data": "10 mail.example.com."}]}
        with patch("tools.dns_recon_tool.urllib.request.urlopen", return_value=_mock_response(payload)):
            result = dns_bulk("example.com", record_types=["MX"])
        assert result["ok"] is True
        assert list(result["results"].keys()) == ["MX"]
        assert result["results"]["MX"]["records"] == ["10 mail.example.com."]

    def test_over_limit_record_types_rejected_without_network_calls(self):
        import tools.dns_recon_tool as dns_recon_tool

        oversized_types = ["A"] * (dns_recon_tool._MAX_BULK_ITEMS + 1)
        with patch("tools.dns_recon_tool.urllib.request.urlopen") as mock_urlopen:
            result = dns_bulk("example.com", record_types=oversized_types)

        assert result["ok"] is False
        assert "too many items" in result["error"]
        mock_urlopen.assert_not_called()

    def test_exactly_at_limit_is_accepted(self):
        import tools.dns_recon_tool as dns_recon_tool

        with patch.object(dns_recon_tool, "dns_lookup", return_value={"ok": True}):
            result = dns_bulk("example.com", record_types=["A"] * dns_recon_tool._MAX_BULK_ITEMS)

        assert result["ok"] is True


@pytest.mark.skip(reason="live network — run manually")
class TestLiveDnsLookup:
    """Live integration test against the real DoH endpoints. Skipped if offline."""

    def test_example_com_has_an_a_record(self):
        try:
            result = dns_lookup("example.com", "A")
        except Exception:
            pytest.skip("DoH endpoints unreachable")
        if not result.get("ok"):
            pytest.skip("DoH endpoints unreachable")
        assert len(result["records"]) > 0
