"""Tests for the Wayback Machine tool (URL validation, request building, no
network except in the opt-in live class)."""

import json
from unittest.mock import MagicMock, patch

import pytest

from tools.wayback_tool import (
    _validate_url,
    _validate_limit,
    wayback_snapshots,
    wayback_latest,
    wayback_save,
)


def _mock_response(payload) -> MagicMock:
    """Build a urlopen()-context-manager mock returning payload as JSON bytes."""
    mock_response = MagicMock()
    mock_response.read.return_value = json.dumps(payload).encode()
    mock_response.__enter__ = lambda s: s
    mock_response.__exit__ = MagicMock(return_value=False)
    return mock_response


class TestValidateUrl:
    def test_http_ok(self):
        assert _validate_url("http://example.com") == "http://example.com"

    def test_https_ok(self):
        assert _validate_url("https://example.com/page") == "https://example.com/page"

    def test_strips_whitespace(self):
        assert _validate_url("  https://example.com  ") == "https://example.com"

    def test_rejects_empty(self):
        assert _validate_url("") is None
        assert _validate_url(None) is None

    def test_rejects_non_string(self):
        assert _validate_url(12345) is None

    def test_rejects_no_scheme(self):
        assert _validate_url("example.com") is None

    def test_rejects_javascript_scheme(self):
        assert _validate_url("javascript:alert(1)") is None

    def test_rejects_file_scheme(self):
        assert _validate_url("file:///etc/passwd") is None

    def test_rejects_scheme_with_no_host(self):
        assert _validate_url("https://") is None


class TestValidateLimit:
    def test_default_on_invalid(self):
        assert _validate_limit("not-a-number") == 25

    def test_clamps_high(self):
        assert _validate_limit(9999) == 100

    def test_clamps_low(self):
        assert _validate_limit(0) == 1

    def test_passthrough(self):
        assert _validate_limit(10) == 10


class TestWaybackSnapshotsRequestBuilding:
    def test_invalid_url_no_network_call(self):
        with patch("tools.wayback_tool.urllib.request.urlopen") as mock_urlopen:
            result = wayback_snapshots("not-a-url")
        assert result["ok"] is False
        assert "invalid url" in result["error"]
        mock_urlopen.assert_not_called()

    def test_builds_cdx_url_with_encoded_params(self):
        payload = [
            ["timestamp", "original", "statuscode"],
            ["20200101000000", "https://example.com/", "200"],
        ]
        with patch("tools.wayback_tool.urllib.request.urlopen", return_value=_mock_response(payload)) as mock_urlopen:
            result = wayback_snapshots("https://example.com/a b", limit=5, from_year=2019, to_year=2021)

        req = mock_urlopen.call_args[0][0]
        assert req.full_url.startswith("https://web.archive.org/cdx/search/cdx?")
        assert "url=https%3A%2F%2Fexample.com%2Fa%20b" in req.full_url or "url=https%3A%2F%2Fexample.com%2Fa+b" in req.full_url
        assert "limit=5" in req.full_url
        assert "from=2019" in req.full_url
        assert "to=2021" in req.full_url
        assert req.get_header("User-agent") == "hermes-agent-wayback-tool/1.0"

        assert result["ok"] is True
        assert result["snapshots"] == [{
            "timestamp": "20200101000000",
            "original": "https://example.com/",
            "statuscode": "200",
            "archive_url": "https://web.archive.org/web/20200101000000/https://example.com/",
        }]

    def test_empty_cdx_result_is_no_snapshots(self):
        with patch("tools.wayback_tool.urllib.request.urlopen", return_value=_mock_response([])):
            result = wayback_snapshots("https://example.com")
        assert result == {"ok": True, "snapshots": []}

    def test_network_error_is_reported(self):
        import urllib.error
        with patch("tools.wayback_tool.urllib.request.urlopen", side_effect=urllib.error.URLError("boom")):
            result = wayback_snapshots("https://example.com")
        assert result["ok"] is False
        assert "CDX request failed" in result["error"]


class TestWaybackLatest:
    def test_invalid_url_no_network_call(self):
        with patch("tools.wayback_tool.urllib.request.urlopen") as mock_urlopen:
            result = wayback_latest("ftp://example.com")
        assert result["ok"] is False
        mock_urlopen.assert_not_called()

    def test_available_snapshot(self):
        payload = {
            "url": "https://example.com",
            "archived_snapshots": {
                "closest": {
                    "available": True,
                    "url": "https://web.archive.org/web/20220101000000/https://example.com",
                    "timestamp": "20220101000000",
                    "status": "200",
                }
            },
        }
        with patch("tools.wayback_tool.urllib.request.urlopen", return_value=_mock_response(payload)) as mock_urlopen:
            result = wayback_latest("https://example.com")

        req = mock_urlopen.call_args[0][0]
        assert req.full_url.startswith("https://archive.org/wayback/available?")
        assert result["ok"] is True
        assert result["available"] is True
        assert result["archive_url"] == "https://web.archive.org/web/20220101000000/https://example.com"
        assert result["timestamp"] == "20220101000000"

    def test_no_snapshot_available(self):
        payload = {"url": "https://example.com", "archived_snapshots": {}}
        with patch("tools.wayback_tool.urllib.request.urlopen", return_value=_mock_response(payload)):
            result = wayback_latest("https://example.com")
        assert result == {"ok": True, "available": False}


class TestWaybackSaveConfirmGate:
    def test_defaults_to_no_op_without_confirm(self):
        with patch("tools.wayback_tool.urllib.request.urlopen") as mock_urlopen:
            result = wayback_save("https://example.com")
        assert result["ok"] is False
        assert "confirm=True" in result["error"]
        mock_urlopen.assert_not_called()

    def test_explicit_confirm_false_is_still_a_no_op(self):
        with patch("tools.wayback_tool.urllib.request.urlopen") as mock_urlopen:
            result = wayback_save("https://example.com", confirm=False)
        assert result["ok"] is False
        mock_urlopen.assert_not_called()

    def test_confirm_true_invalid_url_still_no_network_call(self):
        with patch("tools.wayback_tool.urllib.request.urlopen") as mock_urlopen:
            result = wayback_save("not-a-url", confirm=True)
        assert result["ok"] is False
        assert "invalid url" in result["error"]
        mock_urlopen.assert_not_called()

    def test_confirm_true_requests_save(self):
        mock_response = MagicMock()
        mock_response.geturl.return_value = "https://web.archive.org/web/20240101000000/https://example.com"
        mock_response.status = 200
        mock_response.__enter__ = lambda s: s
        mock_response.__exit__ = MagicMock(return_value=False)

        with patch("tools.wayback_tool.urllib.request.urlopen", return_value=mock_response) as mock_urlopen:
            result = wayback_save("https://example.com", confirm=True)

        req = mock_urlopen.call_args[0][0]
        assert req.full_url.startswith("https://web.archive.org/save/")
        assert result["ok"] is True
        assert result["archive_url"] == "https://web.archive.org/web/20240101000000/https://example.com"


class TestLiveWaybackLatest:
    """Live integration test against the real availability API. Skipped if offline."""

    def test_example_com_has_a_snapshot(self):
        try:
            result = wayback_latest("https://example.com")
        except Exception:
            pytest.skip("Wayback Machine API unreachable")
        if not result.get("ok"):
            pytest.skip("Wayback Machine API unreachable")
        assert result["available"] is True
        assert result["archive_url"].startswith("https://web.archive.org/web/")
