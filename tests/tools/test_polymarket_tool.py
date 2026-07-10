"""Tests for the Polymarket tool (query/limit validation, double-encoded-odds
parsing, no network on bad input except in the opt-in live class)."""

import json
from unittest.mock import MagicMock, patch

import pytest

from tools.polymarket_tool import (
    _validate_query,
    _validate_limit,
    _parse_json_field,
    _market_odds,
    _flatten_markets,
    polymarket_search,
    polymarket_trending,
)


def _mock_response(payload) -> MagicMock:
    """Build a urlopen()-context-manager mock returning payload as JSON bytes."""
    mock_response = MagicMock()
    mock_response.read.return_value = json.dumps(payload).encode()
    mock_response.__enter__ = lambda s: s
    mock_response.__exit__ = MagicMock(return_value=False)
    return mock_response


_SAMPLE_MARKET = {
    "question": "Will BTC hit $100k in 2026?",
    "slug": "btc-100k-2026",
    "outcomePrices": "[\"0.42\", \"0.58\"]",
    "outcomes": "[\"Yes\", \"No\"]",
    "volume": 123456.78,
    "endDate": "2026-12-31T00:00:00Z",
    "closed": False,
}


class TestValidateQuery:
    def test_strips_and_accepts(self):
        assert _validate_query("  bitcoin  ") == "bitcoin"

    def test_rejects_empty(self):
        assert _validate_query("") is None
        assert _validate_query("   ") is None

    def test_rejects_non_string(self):
        assert _validate_query(12345) is None
        assert _validate_query(None) is None

    def test_rejects_too_long(self):
        assert _validate_query("x" * 201) is None

    def test_accepts_max_length(self):
        assert _validate_query("x" * 200) == "x" * 200

    def test_rejects_control_chars(self):
        assert _validate_query("bitcoin\x00election") is None
        assert _validate_query("bitcoin\nelection") is None
        assert _validate_query("bitcoin\telection") is None


class TestValidateLimit:
    def test_default_on_invalid(self):
        assert _validate_limit("not-a-number") == 10

    def test_clamps_high(self):
        assert _validate_limit(9999) == 50

    def test_clamps_low(self):
        assert _validate_limit(0) == 1

    def test_passthrough(self):
        assert _validate_limit(5) == 5


class TestParseJsonField:
    def test_parses_double_encoded_string(self):
        assert _parse_json_field("[\"0.42\", \"0.58\"]") == ["0.42", "0.58"]

    def test_passes_through_non_string(self):
        assert _parse_json_field(["0.42", "0.58"]) == ["0.42", "0.58"]

    def test_passes_through_unparseable_string(self):
        assert _parse_json_field("not json") == "not json"


class TestMarketOdds:
    def test_parses_double_encoded_odds(self):
        odds = _market_odds(_SAMPLE_MARKET)
        assert odds == {"Yes": 0.42, "No": 0.58}

    def test_missing_fields_yield_empty_odds(self):
        assert _market_odds({}) == {}

    def test_mismatched_lengths_uses_shorter(self):
        market = {"outcomePrices": "[\"0.42\"]", "outcomes": "[\"Yes\", \"No\"]"}
        assert _market_odds(market) == {"Yes": 0.42}

    def test_non_numeric_price_falls_back_to_raw(self):
        market = {"outcomePrices": "[\"n/a\"]", "outcomes": "[\"Yes\"]"}
        assert _market_odds(market) == {"Yes": "n/a"}


class TestFlattenMarkets:
    def test_flattens_and_caps(self):
        events = [
            {"markets": [_SAMPLE_MARKET, _SAMPLE_MARKET]},
            {"markets": [_SAMPLE_MARKET]},
        ]
        markets = _flatten_markets(events, limit=2)
        assert len(markets) == 2
        assert markets[0]["question"] == "Will BTC hit $100k in 2026?"
        assert markets[0]["odds"] == {"Yes": 0.42, "No": 0.58}

    def test_non_list_events_is_empty(self):
        assert _flatten_markets({"not": "a list"}, limit=5) == []

    def test_no_markets_is_empty(self):
        assert _flatten_markets([{"markets": []}], limit=5) == []


class TestPolymarketSearchRequestBuilding:
    def test_invalid_query_no_network_call(self):
        with patch("tools.polymarket_tool.urllib.request.urlopen") as mock_urlopen:
            result = polymarket_search("")
        assert result["ok"] is False
        assert "invalid query" in result["error"]
        mock_urlopen.assert_not_called()

    def test_control_char_query_no_network_call(self):
        with patch("tools.polymarket_tool.urllib.request.urlopen") as mock_urlopen:
            result = polymarket_search("bitcoin\x00election")
        assert result["ok"] is False
        mock_urlopen.assert_not_called()

    def test_builds_search_url_and_parses_markets(self):
        payload = {"events": [{"title": "BTC 2026", "markets": [_SAMPLE_MARKET]}]}
        with patch("tools.polymarket_tool.urllib.request.urlopen", return_value=_mock_response(payload)) as mock_urlopen:
            result = polymarket_search("bitcoin", limit=5)

        req = mock_urlopen.call_args[0][0]
        assert req.full_url.startswith("https://gamma-api.polymarket.com/public-search?q=bitcoin")
        assert req.get_header("User-agent") == "hermes-agent-polymarket-tool/1.0"

        assert result["ok"] is True
        assert result["markets"] == [{
            "question": "Will BTC hit $100k in 2026?",
            "slug": "btc-100k-2026",
            "odds": {"Yes": 0.42, "No": 0.58},
            "volume": 123456.78,
            "end_date": "2026-12-31T00:00:00Z",
            "closed": False,
        }]

    def test_query_is_url_encoded(self):
        payload = {"events": []}
        with patch("tools.polymarket_tool.urllib.request.urlopen", return_value=_mock_response(payload)) as mock_urlopen:
            polymarket_search("us election 2026")
        req = mock_urlopen.call_args[0][0]
        assert "q=us%20election%202026" in req.full_url or "q=us+election+2026" in req.full_url

    def test_empty_events_is_empty_markets(self):
        with patch("tools.polymarket_tool.urllib.request.urlopen", return_value=_mock_response({"events": []})):
            result = polymarket_search("nothingburger")
        assert result == {"ok": True, "markets": []}

    def test_network_error_is_reported(self):
        import urllib.error
        with patch(
            "tools.polymarket_tool.urllib.request.urlopen",
            side_effect=urllib.error.URLError("boom"),
        ):
            result = polymarket_search("bitcoin")
        assert result["ok"] is False
        assert "Polymarket request failed" in result["error"]

    def test_oversized_response_is_rejected(self):
        import tools.polymarket_tool as polymarket_tool

        oversized = MagicMock()
        oversized.read.return_value = b"x" * (polymarket_tool._MAX_RESPONSE_BYTES + 1)
        oversized.__enter__ = lambda s: s
        oversized.__exit__ = MagicMock(return_value=False)

        with patch("tools.polymarket_tool.urllib.request.urlopen", return_value=oversized):
            result = polymarket_search("bitcoin")

        assert result["ok"] is False
        assert "exceeds" in result["error"]


class TestPolymarketTrendingRequestBuilding:
    def test_builds_events_url_ordered_by_volume(self):
        payload = [{"title": "BTC 2026", "markets": [_SAMPLE_MARKET]}]
        with patch("tools.polymarket_tool.urllib.request.urlopen", return_value=_mock_response(payload)) as mock_urlopen:
            result = polymarket_trending(limit=3)

        req = mock_urlopen.call_args[0][0]
        assert req.full_url.startswith("https://gamma-api.polymarket.com/events?")
        assert "limit=3" in req.full_url
        assert "active=true" in req.full_url
        assert "closed=false" in req.full_url
        assert "order=volume" in req.full_url
        assert "ascending=false" in req.full_url

        assert result["ok"] is True
        assert result["markets"][0]["volume"] == 123456.78
        assert result["markets"][0]["odds"] == {"Yes": 0.42, "No": 0.58}

    def test_limit_clamped_in_url(self):
        with patch("tools.polymarket_tool.urllib.request.urlopen", return_value=_mock_response([])) as mock_urlopen:
            polymarket_trending(limit=9999)
        req = mock_urlopen.call_args[0][0]
        assert "limit=50" in req.full_url

    def test_non_list_response_is_empty_markets(self):
        with patch("tools.polymarket_tool.urllib.request.urlopen", return_value=_mock_response({"unexpected": "shape"})):
            result = polymarket_trending()
        assert result == {"ok": True, "markets": []}


@pytest.mark.skip(reason="live network — run manually")
class TestLivePolymarketTrending:
    """Live integration test against the real Gamma API. Skipped if offline."""

    def test_trending_returns_markets_with_odds_and_volume(self):
        try:
            result = polymarket_trending(3)
        except Exception:
            pytest.skip("Polymarket Gamma API unreachable")
        if not result.get("ok"):
            pytest.skip("Polymarket Gamma API unreachable")
        assert isinstance(result["markets"], list)
