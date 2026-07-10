"""Tests for the ntfy push-notification tool (topic/server/priority
validation, request building, no network except in the opt-in live class)."""

import json
from unittest.mock import MagicMock, patch

import pytest

from tools.notify_tool import (
    _validate_topic,
    _validate_server,
    _validate_message,
    _validate_priority,
    notify,
)


def _mock_response() -> MagicMock:
    """Build an opener.open()-context-manager mock returning an empty body."""
    mock_response = MagicMock()
    mock_response.read.return_value = b""
    mock_response.__enter__ = lambda s: s
    mock_response.__exit__ = MagicMock(return_value=False)
    return mock_response


class TestValidateTopic:
    def test_alnum_ok(self):
        assert _validate_topic("hermes-alerts_1") == "hermes-alerts_1"

    def test_strips_whitespace(self):
        assert _validate_topic("  my-topic  ") == "my-topic"

    def test_rejects_empty(self):
        assert _validate_topic("") is None

    def test_rejects_non_string(self):
        assert _validate_topic(12345) is None

    def test_rejects_space(self):
        assert _validate_topic("my topic") is None

    def test_rejects_slash(self):
        assert _validate_topic("my/topic") is None

    def test_rejects_path_traversal(self):
        assert _validate_topic("../secret") is None

    def test_rejects_semicolon(self):
        assert _validate_topic("topic;rm -rf") is None

    def test_rejects_too_long(self):
        assert _validate_topic("a" * 65) is None

    def test_accepts_max_length(self):
        topic = "a" * 64
        assert _validate_topic(topic) == topic


class TestValidateServer:
    def test_default_ntfy_ok(self):
        assert _validate_server("https://ntfy.sh") == "https://ntfy.sh"

    def test_strips_trailing_slash(self):
        assert _validate_server("https://ntfy.sh/") == "https://ntfy.sh"

    def test_self_hosted_http_ok(self):
        assert _validate_server("http://ntfy.example.com") == "http://ntfy.example.com"

    def test_rejects_empty(self):
        assert _validate_server("") is None
        assert _validate_server(None) is None

    def test_rejects_file_scheme(self):
        assert _validate_server("file:///etc/passwd") is None

    def test_rejects_no_host(self):
        assert _validate_server("https://") is None

    def test_rejects_ftp_scheme(self):
        assert _validate_server("ftp://ntfy.sh") is None


class TestValidateMessage:
    def test_ok(self):
        assert _validate_message("hello") == "hello"

    def test_rejects_empty(self):
        assert _validate_message("") is None
        assert _validate_message("   ") is None

    def test_rejects_non_string(self):
        assert _validate_message(123) is None

    def test_rejects_over_length_cap(self):
        assert _validate_message("x" * 4097) is None

    def test_accepts_at_length_cap(self):
        msg = "x" * 4096
        assert _validate_message(msg) == msg


class TestValidatePriority:
    def test_none_passthrough(self):
        assert _validate_priority(None) is None

    def test_in_range_ok(self):
        assert _validate_priority(3) == 3
        assert _validate_priority("5") == 5

    def test_below_range_raises(self):
        with pytest.raises(ValueError):
            _validate_priority(0)

    def test_above_range_raises(self):
        with pytest.raises(ValueError):
            _validate_priority(6)

    def test_non_numeric_raises(self):
        with pytest.raises(ValueError):
            _validate_priority("urgent")


class TestNotifyValidationGating:
    def test_bad_topic_no_network_call(self):
        with patch("tools.notify_tool._net_guard.build_safe_opener") as mock_opener:
            result = notify("hi", "bad topic")
        assert result["ok"] is False
        assert "invalid topic" in result["error"]
        mock_opener.assert_not_called()

    def test_path_traversal_topic_rejected(self):
        with patch("tools.notify_tool._net_guard.build_safe_opener") as mock_opener:
            result = notify("hi", "../etc/passwd")
        assert result["ok"] is False
        mock_opener.assert_not_called()

    def test_bad_server_scheme_no_network_call(self):
        with patch("tools.notify_tool._net_guard.build_safe_opener") as mock_opener:
            result = notify("hi", "mytopic", server="file:///etc/passwd")
        assert result["ok"] is False
        assert "invalid or disallowed server url" in result["error"]
        mock_opener.assert_not_called()

    def test_oversized_message_no_network_call(self):
        with patch("tools.notify_tool._net_guard.build_safe_opener") as mock_opener:
            result = notify("x" * 5000, "mytopic")
        assert result["ok"] is False
        mock_opener.assert_not_called()

    def test_out_of_range_priority_no_network_call(self):
        with patch("tools.notify_tool._net_guard.build_safe_opener") as mock_opener:
            result = notify("hi", "mytopic", priority=9)
        assert result["ok"] is False
        assert "priority" in result["error"]
        mock_opener.assert_not_called()

    def test_private_target_rejected_no_network_call(self):
        import tools._net_guard as net_guard

        with patch(
            "tools.notify_tool._net_guard.reject_private_target",
            side_effect=net_guard.NetGuardError("refusing to fetch: private address"),
        ), patch("tools.notify_tool._net_guard.build_safe_opener") as mock_opener:
            result = notify("hi", "mytopic", server="http://127.0.0.1:8080")
        assert result["ok"] is False
        assert "private" in result["error"]
        mock_opener.assert_not_called()


class TestNotifySuccess:
    def test_posts_to_expected_url_with_headers(self):
        mock_opener = MagicMock()
        mock_opener.open.return_value = _mock_response()

        with patch("tools.notify_tool._net_guard.reject_private_target"), \
             patch("tools.notify_tool._net_guard.build_safe_opener", return_value=mock_opener):
            result = notify(
                "server is down",
                "hermes-alerts",
                title="Alert",
                priority=5,
                tags=["warning", "rotating_light"],
            )

        assert result == {"ok": True, "topic": "hermes-alerts"}
        req = mock_opener.open.call_args[0][0]
        assert req.full_url == "https://ntfy.sh/hermes-alerts"
        assert req.get_method() == "POST"
        assert req.data == b"server is down"
        assert req.get_header("X-title") == "Alert"
        assert req.get_header("X-priority") == "5"
        assert req.get_header("X-tags") == "warning,rotating_light"

    def test_custom_server_used(self):
        mock_opener = MagicMock()
        mock_opener.open.return_value = _mock_response()

        with patch("tools.notify_tool._net_guard.reject_private_target"), \
             patch("tools.notify_tool._net_guard.build_safe_opener", return_value=mock_opener):
            result = notify("hi", "mytopic", server="https://ntfy.example.com")

        assert result["ok"] is True
        req = mock_opener.open.call_args[0][0]
        assert req.full_url == "https://ntfy.example.com/mytopic"

    def test_http_error_is_reported(self):
        import urllib.error

        mock_opener = MagicMock()
        mock_opener.open.side_effect = urllib.error.HTTPError(
            "https://ntfy.sh/mytopic", 403, "Forbidden", {}, None
        )

        with patch("tools.notify_tool._net_guard.reject_private_target"), \
             patch("tools.notify_tool._net_guard.build_safe_opener", return_value=mock_opener):
            result = notify("hi", "mytopic")

        assert result["ok"] is False
        assert "403" in result["error"]

    def test_network_error_is_reported(self):
        import urllib.error

        mock_opener = MagicMock()
        mock_opener.open.side_effect = urllib.error.URLError("boom")

        with patch("tools.notify_tool._net_guard.reject_private_target"), \
             patch("tools.notify_tool._net_guard.build_safe_opener", return_value=mock_opener):
            result = notify("hi", "mytopic")

        assert result["ok"] is False
        assert "could not reach ntfy server" in result["error"]


@pytest.mark.skip(reason="live network — run manually")
class TestLiveNotify:
    """Live integration test against the real ntfy.sh service. Skipped by default."""

    def test_live_notify_succeeds(self):
        result = notify("hermes-agent live test", "hermes-selftest-9f31a2")
        if not result.get("ok"):
            pytest.skip("ntfy.sh unreachable")
        assert result["ok"] is True
