"""Tests for the uptime check tool (scheme/SSRF guards, bulk cap, mocked
status/substring logic — no network except in the opt-in live class)."""

import socket
from unittest.mock import MagicMock, patch

import pytest

from tools.uptime_check_tool import (
    _MAX_BULK_ITEMS,
    _require_http_scheme,
    _reject_private_target,
    check_url,
    check_urls,
)


def _mock_response(status=200, body=b"ok") -> MagicMock:
    """Build an opener.open()-context-manager mock returning body/status."""
    mock_response = MagicMock()
    mock_response.status = status
    mock_response.read.return_value = body
    mock_response.__enter__ = lambda s: s
    mock_response.__exit__ = MagicMock(return_value=False)
    return mock_response


class TestRequireHttpScheme:
    def test_http_ok(self):
        assert _require_http_scheme("http://example.com") is None

    def test_https_ok(self):
        assert _require_http_scheme("https://example.com") is None

    def test_rejects_file_scheme(self):
        assert _require_http_scheme("file:///etc/passwd") is not None

    def test_rejects_javascript_scheme(self):
        assert _require_http_scheme("javascript:alert(1)") is not None

    def test_rejects_ftp_scheme(self):
        assert _require_http_scheme("ftp://example.com") is not None


class TestRejectPrivateTarget:
    def test_rejects_loopback_ip(self):
        error = _reject_private_target("http://127.0.0.1/", timeout=5)
        assert error is not None
        assert "127.0.0.1" in error

    def test_rejects_localhost_hostname(self):
        with patch("tools.uptime_check_tool.socket.gethostbyname", return_value="127.0.0.1"):
            error = _reject_private_target("http://localhost/", timeout=5)
        assert error is not None

    def test_rejects_private_rfc1918(self):
        error = _reject_private_target("http://10.0.0.5/", timeout=5)
        assert error is not None

    def test_rejects_link_local_metadata_ip(self):
        error = _reject_private_target("http://169.254.169.254/", timeout=5)
        assert error is not None

    def test_allows_public_ip(self):
        error = _reject_private_target("http://93.184.216.34/", timeout=5)
        assert error is None

    def test_dns_failure_is_rejected(self):
        with patch(
            "tools.uptime_check_tool.socket.gethostbyname",
            side_effect=socket.gaierror("nope"),
        ):
            error = _reject_private_target("http://no-such-host.invalid/", timeout=5)
        assert error is not None
        assert "could not resolve" in error


class TestCheckUrlValidation:
    def test_invalid_url_no_network_call(self):
        with patch("tools.uptime_check_tool._build_safe_opener") as mock_opener:
            result = check_url("not-a-url")
        assert result["ok"] is False
        assert result["up"] is False
        mock_opener.assert_not_called()

    def test_disallowed_scheme_no_network_call(self):
        with patch("tools.uptime_check_tool._build_safe_opener") as mock_opener:
            result = check_url("file:///etc/passwd")
        assert result["ok"] is False
        assert result["up"] is False
        mock_opener.assert_not_called()

    def test_private_target_no_network_call(self):
        with patch("tools.uptime_check_tool._build_safe_opener") as mock_opener:
            result = check_url("http://127.0.0.1/")
        assert result["ok"] is False
        assert result["up"] is False
        assert "127.0.0.1" in result["error"]
        mock_opener.assert_not_called()


class TestCheckUrlMockedResponses:
    def test_up_when_status_and_substring_match(self):
        opener = MagicMock()
        opener.open.return_value = _mock_response(status=200, body=b"all good")
        with patch("tools.uptime_check_tool._reject_private_target", return_value=None), \
             patch("tools.uptime_check_tool._build_safe_opener", return_value=opener):
            result = check_url("http://example.com", expect_status=200, expect_substring="good")

        assert result["ok"] is True
        assert result["status"] == 200
        assert result["up"] is True
        assert result["checks"] == {"status_ok": True, "substring_found": True}
        assert isinstance(result["elapsed_ms"], float)

    def test_down_when_status_mismatches(self):
        opener = MagicMock()
        opener.open.return_value = _mock_response(status=500, body=b"error")
        with patch("tools.uptime_check_tool._reject_private_target", return_value=None), \
             patch("tools.uptime_check_tool._build_safe_opener", return_value=opener):
            result = check_url("http://example.com", expect_status=200)

        assert result["ok"] is True
        assert result["status"] == 500
        assert result["up"] is False
        assert result["checks"]["status_ok"] is False

    def test_down_when_substring_missing(self):
        opener = MagicMock()
        opener.open.return_value = _mock_response(status=200, body=b"nope not here")
        with patch("tools.uptime_check_tool._reject_private_target", return_value=None), \
             patch("tools.uptime_check_tool._build_safe_opener", return_value=opener):
            result = check_url("http://example.com", expect_substring="found-me")

        assert result["ok"] is True
        assert result["up"] is False
        assert result["checks"]["substring_found"] is False

    def test_up_true_with_no_expectations_when_reachable(self):
        opener = MagicMock()
        opener.open.return_value = _mock_response(status=503, body=b"whatever")
        with patch("tools.uptime_check_tool._reject_private_target", return_value=None), \
             patch("tools.uptime_check_tool._build_safe_opener", return_value=opener):
            result = check_url("http://example.com")

        assert result["ok"] is True
        assert result["up"] is True

    def test_unreachable_reports_down(self):
        import urllib.error

        opener = MagicMock()
        opener.open.side_effect = urllib.error.URLError("connection refused")
        with patch("tools.uptime_check_tool._reject_private_target", return_value=None), \
             patch("tools.uptime_check_tool._build_safe_opener", return_value=opener):
            result = check_url("http://example.com")

        assert result["ok"] is False
        assert result["up"] is False
        assert "connection refused" in result["error"]

    def test_http_error_status_is_captured(self):
        import urllib.error

        opener = MagicMock()
        http_error = urllib.error.HTTPError(
            "http://example.com", 404, "Not Found", {}, MagicMock()
        )
        http_error.read = MagicMock(return_value=b"missing")
        opener.open.side_effect = http_error
        with patch("tools.uptime_check_tool._reject_private_target", return_value=None), \
             patch("tools.uptime_check_tool._build_safe_opener", return_value=opener):
            result = check_url("http://example.com", expect_status=404)

        assert result["ok"] is True
        assert result["status"] == 404
        assert result["up"] is True


class TestCheckUrls:
    def test_rejects_non_list(self):
        result = check_urls("http://example.com")
        assert result["ok"] is False

    def test_rejects_over_bulk_cap(self):
        urls = [f"http://example{i}.com" for i in range(_MAX_BULK_ITEMS + 1)]
        result = check_urls(urls)
        assert result["ok"] is False
        assert str(_MAX_BULK_ITEMS) in result["error"]

    def test_per_url_isolation(self):
        def fake_check_url(url, **kwargs):
            if url == "http://bad.example.com":
                return {"ok": False, "url": url, "up": False, "error": "boom"}
            return {"ok": True, "url": url, "status": 200, "elapsed_ms": 1.0, "up": True,
                     "checks": {"status_ok": True, "substring_found": True}}

        with patch("tools.uptime_check_tool.check_url", side_effect=fake_check_url):
            result = check_urls(["http://good.example.com", "http://bad.example.com"])

        assert result["ok"] is True
        assert len(result["results"]) == 2
        assert result["results"][0]["up"] is True
        assert result["results"][1]["up"] is False


@pytest.mark.skip(reason="live network — run manually")
class TestLiveCheckUrl:
    """Live integration test against a real endpoint. Skipped by default."""

    def test_example_com_is_up(self):
        try:
            result = check_url("https://example.com", expect_status=200)
        except Exception:
            pytest.skip("network unreachable")
        if not result.get("ok"):
            pytest.skip("network unreachable")
        assert result["up"] is True
        assert isinstance(result["elapsed_ms"], float)

    def test_loopback_is_refused(self):
        result = check_url("http://127.0.0.1/")
        assert result["ok"] is False
        assert result["up"] is False


class TestStatusClassMatching:
    """expect_status accepts a class ('2xx'), a set ('200,204'), or an int."""

    def _check(self, status, expect):
        opener = MagicMock()
        opener.open.return_value = _mock_response(status=status, body=b"x")
        with patch("tools.uptime_check_tool._reject_private_target", return_value=None), \
             patch("tools.uptime_check_tool._build_safe_opener", return_value=opener):
            return check_url("http://example.com", expect_status=expect)

    def test_2xx_matches_204(self):
        assert self._check(204, "2xx")["up"] is True

    def test_2xx_rejects_301(self):
        assert self._check(301, "2xx")["up"] is False

    def test_3xx_matches_301(self):
        assert self._check(301, "3xx")["up"] is True

    def test_set_matches_member(self):
        assert self._check(204, "200,204")["up"] is True

    def test_set_rejects_non_member(self):
        assert self._check(500, "200,204")["up"] is False

    def test_mixed_set_with_class(self):
        assert self._check(302, "200,3xx")["up"] is True

    def test_int_still_exact(self):
        assert self._check(200, 200)["up"] is True
        assert self._check(201, 200)["up"] is False

    def test_numeric_string_still_exact(self):
        assert self._check(200, "200")["up"] is True

    def test_garbage_expect_is_not_up(self):
        r = self._check(200, "banana")
        assert r["ok"] is True
        assert r["up"] is False
        assert r["checks"]["status_ok"] is False


class TestSchemaExpectStatusType:
    """Both check_url and check_urls must accept string expect_status forms."""

    def test_both_schemas_accept_string_status(self):
        from tools.registry import registry

        for name in ("check_url", "check_urls"):
            entry = registry.get_entry(name)
            assert entry is not None, name
            prop = entry.schema["parameters"]["properties"]["expect_status"]
            assert prop["type"] == ["integer", "string"], name
