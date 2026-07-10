"""Tests for the Crypto Fear & Greed Index tool (limit clamp, classification
fallback, response parsing, no network except in the opt-in live class)."""

import json
from unittest.mock import MagicMock, patch

import pytest

from tools.fear_greed_tool import (
    _validate_limit,
    _classify_value,
    _parse_entry,
    fear_greed,
)


def _mock_response(payload) -> MagicMock:
    """Build a urlopen()-context-manager mock returning payload as JSON bytes."""
    mock_response = MagicMock()
    mock_response.read.return_value = json.dumps(payload).encode()
    mock_response.__enter__ = lambda s: s
    mock_response.__exit__ = MagicMock(return_value=False)
    return mock_response


class TestValidateLimit:
    def test_default_on_invalid(self):
        assert _validate_limit("not-a-number") == 1

    def test_clamps_high(self):
        assert _validate_limit(9999) == 100

    def test_clamps_low(self):
        assert _validate_limit(0) == 1

    def test_passthrough(self):
        assert _validate_limit(10) == 10


class TestClassifyValue:
    def test_extreme_fear(self):
        assert _classify_value(0) == "Extreme Fear"
        assert _classify_value(24) == "Extreme Fear"

    def test_fear(self):
        assert _classify_value(25) == "Fear"
        assert _classify_value(44) == "Fear"

    def test_neutral(self):
        assert _classify_value(45) == "Neutral"
        assert _classify_value(55) == "Neutral"

    def test_greed(self):
        assert _classify_value(56) == "Greed"
        assert _classify_value(75) == "Greed"

    def test_extreme_greed(self):
        assert _classify_value(76) == "Extreme Greed"
        assert _classify_value(100) == "Extreme Greed"


class TestParseEntry:
    def test_parses_well_formed_entry(self):
        entry = _parse_entry({"value": "23", "value_classification": "Extreme Fear", "timestamp": "1700000000"})
        assert entry == {"value": 23, "classification": "Extreme Fear", "timestamp": "1700000000"}

    def test_missing_classification_falls_back_to_derived(self):
        entry = _parse_entry({"value": "80", "timestamp": "1700000000"})
        assert entry == {"value": 80, "classification": "Extreme Greed", "timestamp": "1700000000"}

    def test_blank_classification_falls_back_to_derived(self):
        entry = _parse_entry({"value": "10", "value_classification": "   ", "timestamp": "1700000000"})
        assert entry["classification"] == "Extreme Fear"

    def test_non_dict_is_none(self):
        assert _parse_entry("not-a-dict") is None
        assert _parse_entry(None) is None

    def test_unparseable_value_is_none(self):
        assert _parse_entry({"value": "not-a-number"}) is None
        assert _parse_entry({}) is None


class TestFearGreedRequestBuilding:
    def test_builds_fng_url_with_limit(self):
        payload = {
            "data": [{"value": "23", "value_classification": "Extreme Fear", "timestamp": "1700000000"}],
        }
        with patch("tools.fear_greed_tool.urllib.request.urlopen", return_value=_mock_response(payload)) as mock_urlopen:
            result = fear_greed(limit=1)

        req = mock_urlopen.call_args[0][0]
        assert req.full_url.startswith("https://api.alternative.me/fng/?")
        assert "limit=1" in req.full_url
        assert req.get_header("User-agent") == "hermes-agent-fear-greed-tool/1.0"

        assert result["ok"] is True
        assert result["current"] == {"value": 23, "classification": "Extreme Fear", "timestamp": "1700000000"}
        assert "history" not in result

    def test_limit_greater_than_one_includes_history(self):
        payload = {
            "data": [
                {"value": "23", "value_classification": "Extreme Fear", "timestamp": "1700000000"},
                {"value": "30", "value_classification": "Fear", "timestamp": "1699913600"},
            ],
        }
        with patch("tools.fear_greed_tool.urllib.request.urlopen", return_value=_mock_response(payload)) as mock_urlopen:
            result = fear_greed(limit=2)

        req = mock_urlopen.call_args[0][0]
        assert "limit=2" in req.full_url

        assert result["ok"] is True
        assert result["current"] == {"value": 23, "classification": "Extreme Fear", "timestamp": "1700000000"}
        assert result["history"] == [
            {"value": 23, "classification": "Extreme Fear", "timestamp": "1700000000"},
            {"value": 30, "classification": "Fear", "timestamp": "1699913600"},
        ]

    def test_limit_is_clamped_before_request(self):
        payload = {"data": [{"value": "50", "timestamp": "1700000000"}]}
        with patch("tools.fear_greed_tool.urllib.request.urlopen", return_value=_mock_response(payload)) as mock_urlopen:
            fear_greed(limit=9999)
        req = mock_urlopen.call_args[0][0]
        assert "limit=100" in req.full_url

    def test_network_error_is_reported(self):
        import urllib.error
        with patch("tools.fear_greed_tool.urllib.request.urlopen", side_effect=urllib.error.URLError("boom")):
            result = fear_greed()
        assert result["ok"] is False
        assert "alternative.me request failed" in result["error"]

    def test_http_error_is_reported(self):
        import urllib.error
        with patch(
            "tools.fear_greed_tool.urllib.request.urlopen",
            side_effect=urllib.error.HTTPError("url", 503, "Service Unavailable", {}, None),
        ):
            result = fear_greed()
        assert result["ok"] is False
        assert "503" in result["error"]

    def test_oversized_response_is_rejected(self):
        import tools.fear_greed_tool as fear_greed_tool

        oversized = MagicMock()
        oversized.read.return_value = b"x" * (fear_greed_tool._MAX_RESPONSE_BYTES + 1)
        oversized.__enter__ = lambda s: s
        oversized.__exit__ = MagicMock(return_value=False)

        with patch("tools.fear_greed_tool.urllib.request.urlopen", return_value=oversized):
            result = fear_greed()

        assert result["ok"] is False
        assert "exceeds" in result["error"]


class TestFearGreedMalformedResponse:
    def test_missing_data_key(self):
        with patch("tools.fear_greed_tool.urllib.request.urlopen", return_value=_mock_response({"metadata": {}})):
            result = fear_greed()
        assert result["ok"] is False
        assert "malformed response" in result["error"]

    def test_empty_data_list(self):
        with patch("tools.fear_greed_tool.urllib.request.urlopen", return_value=_mock_response({"data": []})):
            result = fear_greed()
        assert result["ok"] is False
        assert "malformed response" in result["error"]

    def test_data_not_a_list(self):
        with patch("tools.fear_greed_tool.urllib.request.urlopen", return_value=_mock_response({"data": "oops"})):
            result = fear_greed()
        assert result["ok"] is False
        assert "malformed response" in result["error"]

    def test_all_entries_unparseable(self):
        payload = {"data": [{"value": "not-a-number"}, "also-bad"]}
        with patch("tools.fear_greed_tool.urllib.request.urlopen", return_value=_mock_response(payload)):
            result = fear_greed()
        assert result["ok"] is False
        assert "no parseable entries" in result["error"]

    def test_not_valid_json(self):
        mock_response = MagicMock()
        mock_response.read.return_value = b"not json"
        mock_response.__enter__ = lambda s: s
        mock_response.__exit__ = MagicMock(return_value=False)
        with patch("tools.fear_greed_tool.urllib.request.urlopen", return_value=mock_response):
            result = fear_greed()
        assert result["ok"] is False
        assert "not valid JSON" in result["error"]


@pytest.mark.skip(reason="live network — run manually")
class TestLiveFearGreed:
    """Live integration test against the real alternative.me API. Skipped if offline."""

    def test_current_index_has_value_and_classification(self):
        try:
            result = fear_greed()
        except Exception:
            pytest.skip("alternative.me API unreachable")
        if not result.get("ok"):
            pytest.skip("alternative.me API unreachable")
        assert 0 <= result["current"]["value"] <= 100
        assert result["current"]["classification"]
