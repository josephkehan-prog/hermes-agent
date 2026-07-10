"""Tests for the IP geolocation/ASN recon tool (IP validation, private-range
short-circuiting, request building, fallback behavior — no network except in
the opt-in live class)."""

import json
import urllib.error
from unittest.mock import MagicMock, patch

import pytest

from tools.ip_info_tool import (
    _validate_ip,
    _is_private,
    ip_info,
    ip_bulk,
)


def _mock_response(payload) -> MagicMock:
    """Build a urlopen()-context-manager mock returning payload as JSON bytes."""
    mock_response = MagicMock()
    mock_response.read.return_value = json.dumps(payload).encode()
    mock_response.__enter__ = lambda s: s
    mock_response.__exit__ = MagicMock(return_value=False)
    return mock_response


class TestValidateIp:
    def test_valid_ipv4_ok(self):
        assert _validate_ip("8.8.8.8") == "8.8.8.8"

    def test_valid_ipv6_ok(self):
        assert _validate_ip("2001:4860:4860::8888") == "2001:4860:4860::8888"

    def test_strips_whitespace(self):
        assert _validate_ip("  8.8.8.8  ") == "8.8.8.8"

    def test_rejects_empty(self):
        assert _validate_ip("") is None
        assert _validate_ip(None) is None

    def test_rejects_non_string(self):
        assert _validate_ip(12345) is None

    def test_rejects_hostname(self):
        assert _validate_ip("example.com") is None

    def test_rejects_injection_semicolon(self):
        assert _validate_ip("8.8.8.8;whoami") is None

    def test_rejects_injection_path_traversal(self):
        assert _validate_ip("8.8.8.8/../x") is None

    def test_rejects_garbage(self):
        assert _validate_ip("not-an-ip") is None

    def test_rejects_out_of_range_octet(self):
        assert _validate_ip("999.999.999.999") is None

    def test_rejects_incomplete_ipv4(self):
        assert _validate_ip("8.8.8") is None


class TestIsPrivate:
    def test_private_ipv4_range(self):
        assert _is_private("192.168.1.1") is True

    def test_loopback_ipv4(self):
        assert _is_private("127.0.0.1") is True

    def test_link_local_ipv4(self):
        assert _is_private("169.254.1.1") is True

    def test_loopback_ipv6(self):
        assert _is_private("::1") is True

    def test_public_ipv4_is_not_private(self):
        assert _is_private("8.8.8.8") is False


class TestIpInfoValidationNoNetwork:
    def test_invalid_ip_no_network_call(self):
        with patch("tools.ip_info_tool.urllib.request.urlopen") as mock_urlopen:
            result = ip_info("not-an-ip")
        assert result["ok"] is False
        assert "invalid ip" in result["error"]
        mock_urlopen.assert_not_called()

    def test_hostname_rejected_no_network_call(self):
        with patch("tools.ip_info_tool.urllib.request.urlopen") as mock_urlopen:
            result = ip_info("example.com")
        assert result["ok"] is False
        mock_urlopen.assert_not_called()

    def test_injection_attempt_no_network_call(self):
        with patch("tools.ip_info_tool.urllib.request.urlopen") as mock_urlopen:
            result = ip_info("8.8.8.8;rm -rf /")
        assert result["ok"] is False
        mock_urlopen.assert_not_called()


class TestIpInfoPrivateHandling:
    def test_private_ip_no_network_call(self):
        with patch("tools.ip_info_tool.urllib.request.urlopen") as mock_urlopen:
            result = ip_info("192.168.1.1")
        assert result["ok"] is True
        assert result["is_private"] is True
        assert result["ip"] == "192.168.1.1"
        mock_urlopen.assert_not_called()

    def test_loopback_no_network_call(self):
        with patch("tools.ip_info_tool.urllib.request.urlopen") as mock_urlopen:
            result = ip_info("127.0.0.1")
        assert result["ok"] is True
        assert result["is_private"] is True
        mock_urlopen.assert_not_called()


class TestIpInfoRequestBuilding:
    def test_builds_ipapi_co_url_and_parses_result(self):
        payload = {
            "ip": "8.8.8.8",
            "city": "Mountain View",
            "region": "California",
            "country_name": "United States",
            "asn": "AS15169",
            "org": "GOOGLE",
        }
        with patch("tools.ip_info_tool.urllib.request.urlopen", return_value=_mock_response(payload)) as mock_urlopen:
            result = ip_info("8.8.8.8")

        req = mock_urlopen.call_args[0][0]
        assert req.full_url == "https://ipapi.co/8.8.8.8/json/"
        assert req.get_header("User-agent") == "hermes-agent-ip-info-tool/1.0"

        assert result["ok"] is True
        assert result["ip"] == "8.8.8.8"
        assert result["city"] == "Mountain View"
        assert result["country"] == "United States"
        assert result["asn"] == "AS15169"
        assert result["org"] == "GOOGLE"
        assert result["source"] == "ipapi.co"
        assert result["is_private"] is False

    def test_ipapi_co_error_response_falls_back(self):
        error_payload = {"error": True, "reason": "Rate limited"}
        fallback_payload = {
            "status": "success",
            "query": "8.8.8.8",
            "city": "Mountain View",
            "regionName": "California",
            "country": "United States",
            "as": "AS15169 Google LLC",
            "isp": "Google LLC",
        }
        with patch(
            "tools.ip_info_tool.urllib.request.urlopen",
            side_effect=[_mock_response(error_payload), _mock_response(fallback_payload)],
        ) as mock_urlopen:
            result = ip_info("8.8.8.8")

        assert result["ok"] is True
        assert result["source"] == "ip-api.com"
        first_req = mock_urlopen.call_args_list[0][0][0]
        second_req = mock_urlopen.call_args_list[1][0][0]
        assert first_req.full_url.startswith("https://ipapi.co/")
        assert second_req.full_url.startswith("http://ip-api.com/json/")


class TestIpInfoFallback:
    def test_falls_back_to_ip_api_com_on_network_error(self):
        fallback_payload = {
            "status": "success",
            "query": "1.1.1.1",
            "city": "Sydney",
            "regionName": "New South Wales",
            "country": "Australia",
            "as": "AS13335 Cloudflare, Inc.",
            "isp": "Cloudflare, Inc.",
        }
        with patch(
            "tools.ip_info_tool.urllib.request.urlopen",
            side_effect=[urllib.error.URLError("ipapi.co down"), _mock_response(fallback_payload)],
        ):
            result = ip_info("1.1.1.1")

        assert result["ok"] is True
        assert result["source"] == "ip-api.com"
        assert result["city"] == "Sydney"

    def test_both_endpoints_failing_reports_error(self):
        with patch(
            "tools.ip_info_tool.urllib.request.urlopen",
            side_effect=urllib.error.URLError("boom"),
        ):
            result = ip_info("8.8.8.8")
        assert result["ok"] is False
        assert "request failed" in result["error"]

    def test_ip_api_com_status_fail_reports_error(self):
        with patch(
            "tools.ip_info_tool.urllib.request.urlopen",
            side_effect=[
                urllib.error.URLError("ipapi.co down"),
                _mock_response({"status": "fail", "message": "invalid query"}),
            ],
        ):
            result = ip_info("8.8.8.8")
        assert result["ok"] is False
        assert "invalid query" in result["error"]

    def test_malformed_json_falls_back(self):
        bad_response = MagicMock()
        bad_response.read.return_value = b"not json"
        bad_response.__enter__ = lambda s: s
        bad_response.__exit__ = MagicMock(return_value=False)

        fallback_payload = {
            "status": "success",
            "query": "8.8.8.8",
            "city": "Mountain View",
            "regionName": "California",
            "country": "United States",
            "as": "AS15169",
            "isp": "Google LLC",
        }
        with patch(
            "tools.ip_info_tool.urllib.request.urlopen",
            side_effect=[bad_response, _mock_response(fallback_payload)],
        ):
            result = ip_info("8.8.8.8")
        assert result["ok"] is True
        assert result["source"] == "ip-api.com"


class TestIpInfoCapEnforcement:
    def test_oversized_response_falls_back_then_errors(self):
        import tools.ip_info_tool as ip_info_tool

        oversized = MagicMock()
        oversized.read.return_value = b"x" * (ip_info_tool._MAX_RESPONSE_BYTES + 1)
        oversized.__enter__ = lambda s: s
        oversized.__exit__ = MagicMock(return_value=False)

        with patch("tools.ip_info_tool.urllib.request.urlopen", return_value=oversized):
            result = ip_info("8.8.8.8")

        assert result["ok"] is False
        assert "exceeds" in result["error"]

    def test_oversized_ipapi_co_response_falls_back_to_ip_api_com_success(self):
        import tools.ip_info_tool as ip_info_tool

        oversized = MagicMock()
        oversized.read.return_value = b"x" * (ip_info_tool._MAX_RESPONSE_BYTES + 1)
        oversized.__enter__ = lambda s: s
        oversized.__exit__ = MagicMock(return_value=False)

        fallback_payload = {
            "status": "success",
            "query": "8.8.8.8",
            "city": "Mountain View",
            "regionName": "California",
            "country": "United States",
            "as": "AS15169",
            "isp": "Google LLC",
        }
        with patch(
            "tools.ip_info_tool.urllib.request.urlopen",
            side_effect=[oversized, _mock_response(fallback_payload)],
        ):
            result = ip_info("8.8.8.8")

        assert result["ok"] is True
        assert result["source"] == "ip-api.com"


class TestIpBulk:
    def test_rejects_non_list(self):
        result = ip_bulk("8.8.8.8")
        assert result["ok"] is False
        assert "must be a non-empty list" in result["error"]

    def test_rejects_empty_list(self):
        result = ip_bulk([])
        assert result["ok"] is False

    def test_per_ip_isolation(self):
        import tools.ip_info_tool as ip_info_tool

        def fake_ip_info(ip):
            if ip == "bad-ip":
                return {"ok": False, "error": "simulated failure"}
            return {"ok": True, "ip": ip, "is_private": False}

        with patch.object(ip_info_tool, "ip_info", side_effect=fake_ip_info):
            result = ip_info_tool.ip_bulk(["8.8.8.8", "bad-ip"])

        assert result["ok"] is True
        assert result["results"]["8.8.8.8"]["ok"] is True
        assert result["results"]["bad-ip"]["ok"] is False

    def test_no_network_call_for_all_invalid_ips(self):
        with patch("tools.ip_info_tool.urllib.request.urlopen") as mock_urlopen:
            result = ip_bulk(["not-an-ip", "8.8.8.8;whoami"])
        assert result["ok"] is True
        assert result["results"]["not-an-ip"]["ok"] is False
        assert result["results"]["8.8.8.8;whoami"]["ok"] is False
        mock_urlopen.assert_not_called()

    def test_over_limit_list_rejected_without_network_calls(self):
        import tools.ip_info_tool as ip_info_tool

        oversized_list = [f"1.2.3.{i % 256}" for i in range(ip_info_tool._MAX_BULK_ITEMS + 1)]
        with patch("tools.ip_info_tool.urllib.request.urlopen") as mock_urlopen:
            result = ip_bulk(oversized_list)

        assert result["ok"] is False
        assert "too many items" in result["error"]
        mock_urlopen.assert_not_called()

    def test_exactly_at_limit_is_accepted(self):
        import tools.ip_info_tool as ip_info_tool

        with patch.object(ip_info_tool, "ip_info", return_value={"ok": True}):
            result = ip_bulk(["8.8.8.8"] * ip_info_tool._MAX_BULK_ITEMS)

        assert result["ok"] is True


@pytest.mark.skip(reason="live network — run manually")
class TestLiveIpInfo:
    """Live integration test against the real geolocation endpoints. Skipped if offline."""

    def test_google_dns_ip_has_country_and_asn(self):
        try:
            result = ip_info("8.8.8.8")
        except Exception:
            pytest.skip("geolocation endpoints unreachable")
        if not result.get("ok"):
            pytest.skip("geolocation endpoints unreachable")
        assert result.get("country")
        assert result.get("asn")
