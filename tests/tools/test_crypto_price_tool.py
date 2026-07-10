"""Tests for the crypto price tool (coin-id/currency validation, request
building, no network except in the opt-in live class)."""

import json
from unittest.mock import MagicMock, patch

import pytest

from tools.crypto_price_tool import (
    _validate_coin_id,
    _normalize_coin_ids,
    _validate_vs_currency,
    crypto_price,
    crypto_trending,
)


def _mock_response(payload) -> MagicMock:
    """Build a urlopen()-context-manager mock returning payload as JSON bytes."""
    mock_response = MagicMock()
    mock_response.read.return_value = json.dumps(payload).encode()
    mock_response.__enter__ = lambda s: s
    mock_response.__exit__ = MagicMock(return_value=False)
    return mock_response


class TestValidateCoinId:
    def test_accepts_plain_id(self):
        assert _validate_coin_id("bitcoin") == "bitcoin"

    def test_accepts_hyphenated_id(self):
        assert _validate_coin_id("usd-coin") == "usd-coin"

    def test_lowercases_and_strips(self):
        assert _validate_coin_id("  Monero  ") == "monero"

    def test_rejects_non_string(self):
        assert _validate_coin_id(12345) is None

    def test_rejects_empty(self):
        assert _validate_coin_id("") is None

    def test_rejects_query_injection(self):
        assert _validate_coin_id("bitcoin&ids=ethereum") is None

    def test_rejects_path_injection(self):
        assert _validate_coin_id("../../etc/passwd") is None

    def test_rejects_whitespace_inside(self):
        assert _validate_coin_id("bit coin") is None

    def test_rejects_too_long(self):
        assert _validate_coin_id("a" * 65) is None


class TestNormalizeCoinIds:
    def test_accepts_list(self):
        ids, error = _normalize_coin_ids(["bitcoin", "ethereum"])
        assert error is None
        assert ids == ["bitcoin", "ethereum"]

    def test_accepts_comma_string(self):
        ids, error = _normalize_coin_ids("bitcoin,monero")
        assert error is None
        assert ids == ["bitcoin", "monero"]

    def test_dedupes_preserving_order(self):
        ids, error = _normalize_coin_ids(["bitcoin", "ethereum", "bitcoin"])
        assert error is None
        assert ids == ["bitcoin", "ethereum"]

    def test_rejects_empty(self):
        ids, error = _normalize_coin_ids([])
        assert ids is None
        assert "empty" in error

    def test_rejects_wrong_type(self):
        ids, error = _normalize_coin_ids(12345)
        assert ids is None
        assert "list or comma-separated string" in error

    def test_rejects_invalid_id_in_list(self):
        ids, error = _normalize_coin_ids(["bitcoin", "bad id!"])
        assert ids is None
        assert "invalid coin id" in error

    def test_rejects_too_many(self):
        ids, error = _normalize_coin_ids([f"coin{i}" for i in range(51)])
        assert ids is None
        assert "too many" in error


class TestValidateVsCurrency:
    def test_accepts_usd(self):
        assert _validate_vs_currency("usd") == "usd"

    def test_lowercases(self):
        assert _validate_vs_currency("EUR") == "eur"

    def test_rejects_injection(self):
        assert _validate_vs_currency("usd&ids=x") is None

    def test_rejects_non_string(self):
        assert _validate_vs_currency(None) is None

    def test_rejects_too_long(self):
        assert _validate_vs_currency("a" * 11) is None


class TestCryptoPriceRequestBuilding:
    def test_invalid_coin_id_no_network_call(self):
        with patch("tools.crypto_price_tool.urllib.request.urlopen") as mock_urlopen:
            result = crypto_price(["bitcoin;drop"])
        assert result["ok"] is False
        assert "invalid coin id" in result["error"]
        mock_urlopen.assert_not_called()

    def test_invalid_vs_currency_no_network_call(self):
        with patch("tools.crypto_price_tool.urllib.request.urlopen") as mock_urlopen:
            result = crypto_price(["bitcoin"], vs="usd$")
        assert result["ok"] is False
        assert "invalid vs currency" in result["error"]
        mock_urlopen.assert_not_called()

    def test_builds_simple_price_url(self):
        payload = {
            "bitcoin": {"usd": 65000.5, "usd_24h_change": 1.23, "usd_market_cap": 1_200_000_000_000},
            "monero": {"usd": 150.0, "usd_24h_change": -0.5, "usd_market_cap": 2_700_000_000},
        }
        with patch("tools.crypto_price_tool.urllib.request.urlopen", return_value=_mock_response(payload)) as mock_urlopen:
            result = crypto_price(["bitcoin", "monero"], vs="usd")

        req = mock_urlopen.call_args[0][0]
        assert req.full_url.startswith("https://api.coingecko.com/api/v3/simple/price?")
        assert "ids=bitcoin%2Cmonero" in req.full_url
        assert "vs_currencies=usd" in req.full_url
        assert "include_24hr_change=true" in req.full_url
        assert "include_market_cap=true" in req.full_url
        assert req.get_header("User-agent") == "hermes-agent-crypto-price-tool/1.0"

        assert result["ok"] is True
        assert result["prices"] == {
            "bitcoin": {"price": 65000.5, "change_24h": 1.23, "market_cap": 1_200_000_000_000},
            "monero": {"price": 150.0, "change_24h": -0.5, "market_cap": 2_700_000_000},
        }
        assert "not_found" not in result

    def test_accepts_comma_string_coin_ids(self):
        payload = {"bitcoin": {"usd": 65000.0, "usd_24h_change": 0.1, "usd_market_cap": 1}}
        with patch("tools.crypto_price_tool.urllib.request.urlopen", return_value=_mock_response(payload)):
            result = crypto_price("bitcoin", vs="usd")
        assert result["ok"] is True
        assert "bitcoin" in result["prices"]

    def test_unknown_coin_id_reported_as_not_found(self):
        payload = {"bitcoin": {"usd": 65000.0, "usd_24h_change": 0.1, "usd_market_cap": 1}}
        with patch("tools.crypto_price_tool.urllib.request.urlopen", return_value=_mock_response(payload)):
            result = crypto_price(["bitcoin", "not-a-real-coin"], vs="usd")
        assert result["ok"] is True
        assert "bitcoin" in result["prices"]
        assert result["not_found"] == ["not-a-real-coin"]

    def test_network_error_is_reported(self):
        import urllib.error
        with patch("tools.crypto_price_tool.urllib.request.urlopen", side_effect=urllib.error.URLError("boom")):
            result = crypto_price(["bitcoin"])
        assert result["ok"] is False
        assert "CoinGecko request failed" in result["error"]

    def test_oversized_response_is_rejected(self):
        import tools.crypto_price_tool as crypto_price_tool

        oversized = MagicMock()
        oversized.read.return_value = b"x" * (crypto_price_tool._MAX_RESPONSE_BYTES + 1)
        oversized.__enter__ = lambda s: s
        oversized.__exit__ = MagicMock(return_value=False)

        with patch("tools.crypto_price_tool.urllib.request.urlopen", return_value=oversized):
            result = crypto_price(["bitcoin"])

        assert result["ok"] is False
        assert "exceeds" in result["error"]


class TestCryptoTrending:
    def test_parses_trending_coins(self):
        payload = {
            "coins": [
                {"item": {"id": "bitcoin", "name": "Bitcoin", "symbol": "btc", "market_cap_rank": 1}},
                {"item": {"id": "monero", "name": "Monero", "symbol": "xmr", "market_cap_rank": 30}},
            ]
        }
        with patch("tools.crypto_price_tool.urllib.request.urlopen", return_value=_mock_response(payload)) as mock_urlopen:
            result = crypto_trending()

        req = mock_urlopen.call_args[0][0]
        assert req.full_url == "https://api.coingecko.com/api/v3/search/trending"
        assert result["ok"] is True
        assert result["coins"] == [
            {"id": "bitcoin", "name": "Bitcoin", "symbol": "btc", "market_cap_rank": 1},
            {"id": "monero", "name": "Monero", "symbol": "xmr", "market_cap_rank": 30},
        ]

    def test_empty_coins_list(self):
        with patch("tools.crypto_price_tool.urllib.request.urlopen", return_value=_mock_response({"coins": []})):
            result = crypto_trending()
        assert result == {"ok": True, "coins": []}

    def test_network_error_is_reported(self):
        import urllib.error
        with patch("tools.crypto_price_tool.urllib.request.urlopen", side_effect=urllib.error.URLError("boom")):
            result = crypto_trending()
        assert result["ok"] is False
        assert "CoinGecko request failed" in result["error"]


@pytest.mark.skip(reason="live network — run manually")
class TestLiveCryptoPrice:
    """Live integration test against the real CoinGecko API."""

    def test_bitcoin_ethereum_monero_have_prices(self):
        try:
            result = crypto_price(["bitcoin", "ethereum", "monero"])
        except Exception:
            pytest.skip("CoinGecko API unreachable")
        if not result.get("ok"):
            pytest.skip("CoinGecko API unreachable")
        assert set(result["prices"].keys()) == {"bitcoin", "ethereum", "monero"}
        for entry in result["prices"].values():
            assert entry["price"] > 0
