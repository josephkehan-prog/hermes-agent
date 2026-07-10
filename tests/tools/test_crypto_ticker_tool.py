"""Tests for the crypto ticker tool (symbol/exchange validation, defensive
Binance/Kraken parsing, request building, no network except in the opt-in
live class)."""

import json
from unittest.mock import MagicMock, patch

import pytest

from tools.crypto_ticker_tool import (
    _validate_symbol,
    _validate_exchange,
    _normalize_symbols,
    ticker,
    ticker_bulk,
)


def _mock_response(payload) -> MagicMock:
    """Build a urlopen()-context-manager mock returning payload as JSON bytes."""
    mock_response = MagicMock()
    mock_response.read.return_value = json.dumps(payload).encode()
    mock_response.__enter__ = lambda s: s
    mock_response.__exit__ = MagicMock(return_value=False)
    return mock_response


class TestValidateSymbol:
    def test_accepts_plain_symbol(self):
        assert _validate_symbol("BTCUSDT") == "BTCUSDT"

    def test_uppercases_and_strips(self):
        assert _validate_symbol("  btcusdt  ") == "BTCUSDT"

    def test_rejects_non_string(self):
        assert _validate_symbol(12345) is None

    def test_rejects_empty(self):
        assert _validate_symbol("") is None

    def test_rejects_too_short(self):
        assert _validate_symbol("B") is None

    def test_rejects_query_injection(self):
        assert _validate_symbol("BTCUSDT&pair=ETHUSDT") is None

    def test_rejects_path_injection(self):
        assert _validate_symbol("../../etc/passwd") is None

    def test_rejects_whitespace_inside(self):
        assert _validate_symbol("BTC USDT") is None

    def test_rejects_too_long(self):
        assert _validate_symbol("A" * 21) is None


class TestValidateExchange:
    def test_accepts_binance(self):
        assert _validate_exchange("binance") == "binance"

    def test_accepts_kraken(self):
        assert _validate_exchange("kraken") == "kraken"

    def test_lowercases_and_strips(self):
        assert _validate_exchange("  BINANCE  ") == "binance"

    def test_rejects_non_string(self):
        assert _validate_exchange(None) is None

    def test_rejects_unknown_exchange(self):
        assert _validate_exchange("coinbase") is None

    def test_rejects_injection(self):
        assert _validate_exchange("binance;drop") is None


class TestNormalizeSymbols:
    def test_accepts_list(self):
        symbols, error = _normalize_symbols(["BTCUSDT", "ETHUSDT"])
        assert error is None
        assert symbols == ["BTCUSDT", "ETHUSDT"]

    def test_accepts_comma_string(self):
        symbols, error = _normalize_symbols("BTCUSDT,ETHUSDT")
        assert error is None
        assert symbols == ["BTCUSDT", "ETHUSDT"]

    def test_rejects_empty(self):
        symbols, error = _normalize_symbols([])
        assert symbols is None
        assert "empty" in error

    def test_rejects_wrong_type(self):
        symbols, error = _normalize_symbols(12345)
        assert symbols is None
        assert "list or comma-separated string" in error

    def test_rejects_too_many(self):
        symbols, error = _normalize_symbols([f"SYM{i}USDT" for i in range(51)])
        assert symbols is None
        assert "too many" in error


class TestTickerValidation:
    def test_invalid_symbol_no_network_call(self):
        with patch("tools.crypto_ticker_tool.urllib.request.urlopen") as mock_urlopen:
            result = ticker("BTC;DROP TABLE")
        assert result["ok"] is False
        assert "invalid symbol" in result["error"]
        mock_urlopen.assert_not_called()

    def test_invalid_exchange_no_network_call(self):
        with patch("tools.crypto_ticker_tool.urllib.request.urlopen") as mock_urlopen:
            result = ticker("BTCUSDT", exchange="coinbase")
        assert result["ok"] is False
        assert "invalid exchange" in result["error"]
        mock_urlopen.assert_not_called()

    def test_non_string_symbol_no_network_call(self):
        with patch("tools.crypto_ticker_tool.urllib.request.urlopen") as mock_urlopen:
            result = ticker(12345)
        assert result["ok"] is False
        mock_urlopen.assert_not_called()


class TestBinanceTicker:
    def test_parses_price(self):
        payload = {"symbol": "BTCUSDT", "price": "65000.50000000"}
        with patch("tools.crypto_ticker_tool.urllib.request.urlopen", return_value=_mock_response(payload)) as mock_urlopen:
            result = ticker("btcusdt", exchange="binance")

        req = mock_urlopen.call_args[0][0]
        assert req.full_url == "https://api.binance.com/api/v3/ticker/price?symbol=BTCUSDT"
        assert req.get_header("User-agent") == "hermes-agent-crypto-ticker-tool/1.0"

        assert result == {"ok": True, "symbol": "BTCUSDT", "exchange": "binance", "price": 65000.5}

    def test_binance_error_payload_is_reported(self):
        payload = {"code": -1121, "msg": "Invalid symbol."}
        with patch("tools.crypto_ticker_tool.urllib.request.urlopen", return_value=_mock_response(payload)):
            result = ticker("ZZZZZ", exchange="binance")
        assert result["ok"] is False
        assert "binance error" in result["error"]

    def test_geoblock_451_is_reported_cleanly(self):
        import urllib.error
        with patch(
            "tools.crypto_ticker_tool.urllib.request.urlopen",
            side_effect=urllib.error.HTTPError("url", 451, "Unavailable For Legal Reasons", {}, None),
        ):
            result = ticker("BTCUSDT", exchange="binance")
        assert result["ok"] is False
        assert "geoblocked" in result["error"]

    def test_network_error_is_reported(self):
        import urllib.error
        with patch("tools.crypto_ticker_tool.urllib.request.urlopen", side_effect=urllib.error.URLError("boom")):
            result = ticker("BTCUSDT", exchange="binance")
        assert result["ok"] is False
        assert "binance request failed" in result["error"]

    def test_oversized_response_is_rejected(self):
        import tools.crypto_ticker_tool as crypto_ticker_tool

        oversized = MagicMock()
        oversized.read.return_value = b"x" * (crypto_ticker_tool._MAX_RESPONSE_BYTES + 1)
        oversized.__enter__ = lambda s: s
        oversized.__exit__ = MagicMock(return_value=False)

        with patch("tools.crypto_ticker_tool.urllib.request.urlopen", return_value=oversized):
            result = ticker("BTCUSDT", exchange="binance")

        assert result["ok"] is False
        assert "exceeds" in result["error"]

    def test_defensive_parse_non_dict_response(self):
        with patch("tools.crypto_ticker_tool.urllib.request.urlopen", return_value=_mock_response(["not", "a", "dict"])):
            result = ticker("BTCUSDT", exchange="binance")
        assert result["ok"] is False
        assert "unexpected binance response shape" in result["error"]

    def test_defensive_parse_missing_price(self):
        with patch("tools.crypto_ticker_tool.urllib.request.urlopen", return_value=_mock_response({"symbol": "BTCUSDT"})):
            result = ticker("BTCUSDT", exchange="binance")
        assert result["ok"] is False
        assert "missing price" in result["error"]

    def test_defensive_parse_non_numeric_price(self):
        with patch("tools.crypto_ticker_tool.urllib.request.urlopen", return_value=_mock_response({"symbol": "BTCUSDT", "price": "not-a-number"})):
            result = ticker("BTCUSDT", exchange="binance")
        assert result["ok"] is False
        assert "not numeric" in result["error"]


class TestKrakenTicker:
    def test_parses_price_with_renamed_pair(self):
        # Kraken renames "XBTUSD" -> "XXBTZUSD" in the result key.
        payload = {"error": [], "result": {"XXBTZUSD": {"c": ["30300.10000", "0.00080000"]}}}
        with patch("tools.crypto_ticker_tool.urllib.request.urlopen", return_value=_mock_response(payload)) as mock_urlopen:
            result = ticker("xbtusd", exchange="kraken")

        req = mock_urlopen.call_args[0][0]
        assert req.full_url == "https://api.kraken.com/0/public/Ticker?pair=XBTUSD"

        assert result == {"ok": True, "symbol": "XBTUSD", "exchange": "kraken", "price": 30300.1}

    def test_kraken_error_list_is_reported(self):
        payload = {"error": ["EQuery:Unknown asset pair"], "result": {}}
        with patch("tools.crypto_ticker_tool.urllib.request.urlopen", return_value=_mock_response(payload)):
            result = ticker("ZZZZZ", exchange="kraken")
        assert result["ok"] is False
        assert "kraken error" in result["error"]

    def test_defensive_parse_non_dict_response(self):
        with patch("tools.crypto_ticker_tool.urllib.request.urlopen", return_value=_mock_response("not a dict")):
            result = ticker("XBTUSD", exchange="kraken")
        assert result["ok"] is False
        assert "unexpected kraken response shape" in result["error"]

    def test_defensive_parse_missing_result(self):
        with patch("tools.crypto_ticker_tool.urllib.request.urlopen", return_value=_mock_response({"error": []})):
            result = ticker("XBTUSD", exchange="kraken")
        assert result["ok"] is False
        assert "missing result" in result["error"]

    def test_defensive_parse_malformed_pair_data(self):
        payload = {"error": [], "result": {"XXBTZUSD": "not-a-dict"}}
        with patch("tools.crypto_ticker_tool.urllib.request.urlopen", return_value=_mock_response(payload)):
            result = ticker("XBTUSD", exchange="kraken")
        assert result["ok"] is False
        assert "unexpected kraken pair data shape" in result["error"]

    def test_defensive_parse_missing_close(self):
        payload = {"error": [], "result": {"XXBTZUSD": {}}}
        with patch("tools.crypto_ticker_tool.urllib.request.urlopen", return_value=_mock_response(payload)):
            result = ticker("XBTUSD", exchange="kraken")
        assert result["ok"] is False
        assert "missing close price" in result["error"]

    def test_defensive_parse_non_numeric_close(self):
        payload = {"error": [], "result": {"XXBTZUSD": {"c": ["not-a-number"]}}}
        with patch("tools.crypto_ticker_tool.urllib.request.urlopen", return_value=_mock_response(payload)):
            result = ticker("XBTUSD", exchange="kraken")
        assert result["ok"] is False
        assert "not numeric" in result["error"]


class TestTickerBulk:
    def test_invalid_symbols_no_network_call(self):
        with patch("tools.crypto_ticker_tool.urllib.request.urlopen") as mock_urlopen:
            result = ticker_bulk([])
        assert result["ok"] is False
        assert "empty" in result["error"]
        mock_urlopen.assert_not_called()

    def test_invalid_exchange_no_network_call(self):
        with patch("tools.crypto_ticker_tool.urllib.request.urlopen") as mock_urlopen:
            result = ticker_bulk(["BTCUSDT"], exchange="coinbase")
        assert result["ok"] is False
        assert "invalid exchange" in result["error"]
        mock_urlopen.assert_not_called()

    def test_too_many_symbols_rejected(self):
        with patch("tools.crypto_ticker_tool.urllib.request.urlopen") as mock_urlopen:
            result = ticker_bulk([f"SYM{i}USDT" for i in range(51)])
        assert result["ok"] is False
        assert "too many" in result["error"]
        mock_urlopen.assert_not_called()

    def test_per_symbol_isolation(self):
        # One bad symbol (Binance error payload) must not prevent the other
        # (valid) symbol's price from coming back.
        responses = {
            "BTCUSDT": _mock_response({"symbol": "BTCUSDT", "price": "65000.0"}),
            "ZZZZZ": _mock_response({"code": -1121, "msg": "Invalid symbol."}),
        }

        def fake_urlopen(req, timeout=None):
            for symbol, response in responses.items():
                if f"symbol={symbol}" in req.full_url:
                    return response
            raise AssertionError(f"unexpected url: {req.full_url}")

        with patch("tools.crypto_ticker_tool.urllib.request.urlopen", side_effect=fake_urlopen):
            result = ticker_bulk(["BTCUSDT", "ZZZZZ"], exchange="binance")

        assert result["ok"] is True
        assert result["exchange"] == "binance"
        assert result["tickers"]["BTCUSDT"]["ok"] is True
        assert result["tickers"]["BTCUSDT"]["price"] == 65000.0
        assert result["tickers"]["ZZZZZ"]["ok"] is False
        assert "binance error" in result["tickers"]["ZZZZZ"]["error"]

    def test_comma_string_symbols(self):
        payload = {"symbol": "BTCUSDT", "price": "65000.0"}
        with patch("tools.crypto_ticker_tool.urllib.request.urlopen", return_value=_mock_response(payload)):
            result = ticker_bulk("BTCUSDT,ETHUSDT", exchange="binance")
        assert result["ok"] is True
        assert set(result["tickers"].keys()) == {"BTCUSDT", "ETHUSDT"}


@pytest.mark.skip(reason="live network — run manually")
class TestLiveCryptoTicker:
    """Live integration test against the real Binance/Kraken APIs."""

    def test_btcusdt_has_a_price_on_binance_or_kraken(self):
        result = ticker("BTCUSDT", exchange="binance")
        if not result.get("ok"):
            # Binance geoblocks some source IPs (451); fall back to Kraken.
            result = ticker("XBTUSD", exchange="kraken")
        if not result.get("ok"):
            pytest.skip("neither Binance nor Kraken reachable")
        assert result["price"] > 0
