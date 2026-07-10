"""Tests for the Polymarket CLOB order-book tool (token_id validation,
defensive book parsing, no network except in the opt-in live class)."""

import json
from unittest.mock import MagicMock, patch

import pytest

from tools.polymarket_orderbook_tool import (
    _validate_token_id,
    _parse_levels,
    polymarket_orderbook,
    polymarket_midpoint,
)


def _mock_response(payload) -> MagicMock:
    """Build a urlopen()-context-manager mock returning payload as JSON bytes."""
    mock_response = MagicMock()
    mock_response.read.return_value = json.dumps(payload).encode()
    mock_response.__enter__ = lambda s: s
    mock_response.__exit__ = MagicMock(return_value=False)
    return mock_response


class TestValidateTokenId:
    def test_decimal_ok(self):
        assert _validate_token_id("123456789") == "123456789"

    def test_hex_ok(self):
        assert _validate_token_id("0xabc123") == "0xabc123"

    def test_strips_whitespace(self):
        assert _validate_token_id("  123  ") == "123"

    def test_rejects_empty(self):
        assert _validate_token_id("") is None
        assert _validate_token_id(None) is None

    def test_rejects_non_string(self):
        assert _validate_token_id(123456) is None

    def test_rejects_injection(self):
        assert _validate_token_id("123; rm -rf /") is None
        assert _validate_token_id("123&side=buy") is None
        assert _validate_token_id("../../etc/passwd") is None
        assert _validate_token_id("123 OR 1=1") is None

    def test_rejects_non_numeric(self):
        assert _validate_token_id("not-a-token") is None
        assert _validate_token_id("123abc") is None

    def test_rejects_oversized(self):
        assert _validate_token_id("1" * 101) is None


class TestParseLevels:
    def test_parses_valid_levels(self):
        levels = _parse_levels([{"price": "0.42", "size": "100.5"}, {"price": "0.43", "size": "50"}])
        assert levels == [{"price": 0.42, "size": 100.5}, {"price": 0.43, "size": 50.0}]

    def test_non_list_returns_empty(self):
        assert _parse_levels(None) == []
        assert _parse_levels("not-a-list") == []
        assert _parse_levels({"price": "0.5"}) == []

    def test_non_dict_entries_skipped(self):
        assert _parse_levels(["oops", 123, None, {"price": "0.5", "size": "1"}]) == [{"price": 0.5, "size": 1.0}]

    def test_missing_or_bad_fields_skipped(self):
        levels = _parse_levels([
            {"price": "0.5"},  # missing size
            {"size": "1"},  # missing price
            {"price": "not-a-number", "size": "1"},
            {"price": "0.5", "size": "1"},
        ])
        assert levels == [{"price": 0.5, "size": 1.0}]

    def test_empty_list(self):
        assert _parse_levels([]) == []


class TestPolymarketOrderbook:
    def test_invalid_token_id_no_network_call(self):
        with patch("tools.polymarket_orderbook_tool.urllib.request.urlopen") as mock_urlopen:
            result = polymarket_orderbook("not; valid")
        assert result["ok"] is False
        assert "invalid token_id" in result["error"]
        mock_urlopen.assert_not_called()

    def test_builds_book_url_and_parses_levels(self):
        payload = {
            "bids": [{"price": "0.40", "size": "100"}, {"price": "0.45", "size": "50"}],
            "asks": [{"price": "0.55", "size": "80"}, {"price": "0.52", "size": "20"}],
        }
        with patch("tools.polymarket_orderbook_tool.urllib.request.urlopen", return_value=_mock_response(payload)) as mock_urlopen:
            result = polymarket_orderbook("123456789")

        req = mock_urlopen.call_args[0][0]
        assert req.full_url == "https://clob.polymarket.com/book?token_id=123456789"
        assert req.get_header("User-agent") == "hermes-agent-polymarket-orderbook-tool/1.0"

        assert result["ok"] is True
        assert result["token_id"] == "123456789"
        assert result["bids"] == [{"price": 0.40, "size": 100.0}, {"price": 0.45, "size": 50.0}]
        assert result["asks"] == [{"price": 0.55, "size": 80.0}, {"price": 0.52, "size": 20.0}]
        assert result["best_bid"] == 0.45
        assert result["best_ask"] == 0.52
        assert result["spread"] == pytest.approx(0.07)

    def test_malformed_book_does_not_crash(self):
        payload = {"bids": "not-a-list", "asks": None}
        with patch("tools.polymarket_orderbook_tool.urllib.request.urlopen", return_value=_mock_response(payload)):
            result = polymarket_orderbook("123")
        assert result["ok"] is True
        assert result["bids"] == []
        assert result["asks"] == []
        assert result["best_bid"] is None
        assert result["best_ask"] is None
        assert result["spread"] is None

    def test_empty_book_is_no_crash(self):
        payload = {"bids": [], "asks": []}
        with patch("tools.polymarket_orderbook_tool.urllib.request.urlopen", return_value=_mock_response(payload)):
            result = polymarket_orderbook("123")
        assert result["ok"] is True
        assert result["best_bid"] is None
        assert result["best_ask"] is None
        assert result["spread"] is None

    def test_non_dict_response_is_reported(self):
        with patch("tools.polymarket_orderbook_tool.urllib.request.urlopen", return_value=_mock_response(["oops"])):
            result = polymarket_orderbook("123")
        assert result["ok"] is False
        assert "not a JSON object" in result["error"]

    def test_network_error_is_reported(self):
        import urllib.error
        with patch("tools.polymarket_orderbook_tool.urllib.request.urlopen", side_effect=urllib.error.URLError("boom")):
            result = polymarket_orderbook("123")
        assert result["ok"] is False
        assert "CLOB request failed" in result["error"]

    def test_http_error_is_reported(self):
        import urllib.error
        with patch(
            "tools.polymarket_orderbook_tool.urllib.request.urlopen",
            side_effect=urllib.error.HTTPError("url", 429, "Too Many Requests", {}, None),
        ):
            result = polymarket_orderbook("123")
        assert result["ok"] is False
        assert "429" in result["error"]

    def test_oversized_response_is_rejected(self):
        import tools.polymarket_orderbook_tool as pob_tool

        oversized = MagicMock()
        oversized.read.return_value = b"x" * (pob_tool._MAX_RESPONSE_BYTES + 1)
        oversized.__enter__ = lambda s: s
        oversized.__exit__ = MagicMock(return_value=False)

        with patch("tools.polymarket_orderbook_tool.urllib.request.urlopen", return_value=oversized):
            result = polymarket_orderbook("123")

        assert result["ok"] is False
        assert "exceeds" in result["error"]


class TestPolymarketMidpoint:
    def test_invalid_token_id_no_network_call(self):
        with patch("tools.polymarket_orderbook_tool.urllib.request.urlopen") as mock_urlopen:
            result = polymarket_midpoint("../etc/passwd")
        assert result["ok"] is False
        assert "invalid token_id" in result["error"]
        mock_urlopen.assert_not_called()

    def test_uses_dedicated_midpoint_endpoint(self):
        with patch("tools.polymarket_orderbook_tool.urllib.request.urlopen", return_value=_mock_response({"mid": "0.48"})) as mock_urlopen:
            result = polymarket_midpoint("123")

        req = mock_urlopen.call_args[0][0]
        assert req.full_url == "https://clob.polymarket.com/midpoint?token_id=123"
        assert result == {"ok": True, "token_id": "123", "mid": 0.48}

    def test_falls_back_to_orderbook_when_mid_missing(self):
        # First call (midpoint) returns junk, second call (book, via
        # polymarket_orderbook fallback) returns a usable book.
        midpoint_payload = {"mid": None}
        book_payload = {
            "bids": [{"price": "0.40", "size": "1"}],
            "asks": [{"price": "0.60", "size": "1"}],
        }
        responses = [_mock_response(midpoint_payload), _mock_response(book_payload)]
        with patch("tools.polymarket_orderbook_tool.urllib.request.urlopen", side_effect=responses):
            result = polymarket_midpoint("123")

        assert result == {"ok": True, "token_id": "123", "mid": 0.50}

    def test_falls_back_and_reports_when_book_also_empty(self):
        responses = [_mock_response({}), _mock_response({"bids": [], "asks": []})]
        with patch("tools.polymarket_orderbook_tool.urllib.request.urlopen", side_effect=responses):
            result = polymarket_midpoint("123")
        assert result["ok"] is False
        assert "midpoint unavailable" in result["error"]

    def test_midpoint_endpoint_network_error_is_reported(self):
        import urllib.error
        with patch("tools.polymarket_orderbook_tool.urllib.request.urlopen", side_effect=urllib.error.URLError("boom")):
            result = polymarket_midpoint("123")
        assert result["ok"] is False
        assert "CLOB request failed" in result["error"]


@pytest.mark.skip(reason="live network — run manually")
class TestLivePolymarketOrderbook:
    """Live integration test against the real CLOB API. Skipped by default."""

    def test_real_token_has_a_book(self):
        # Replace with a real active token_id (e.g. from `polymarket.py
        # trending --limit 1`) before running manually.
        token_id = "REPLACE_WITH_REAL_TOKEN_ID"
        try:
            result = polymarket_orderbook(token_id)
        except Exception:
            pytest.skip("Polymarket CLOB API unreachable")
        if not result.get("ok"):
            pytest.skip("Polymarket CLOB API unreachable or rate-limited")
        assert isinstance(result["bids"], list)
        assert isinstance(result["asks"], list)
