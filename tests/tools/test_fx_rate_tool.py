"""Tests for the Frankfurter FX rate tool (currency-code validation, request
building, defensive JSON parsing, no network except in the opt-in live class)."""

import json
from unittest.mock import MagicMock, patch

import pytest

from tools.fx_rate_tool import (
    _validate_currency,
    _normalize_symbols,
    fx_rate,
    fx_convert,
)


def _mock_response(payload) -> MagicMock:
    """Build a urlopen()-context-manager mock returning payload as JSON bytes."""
    mock_response = MagicMock()
    mock_response.read.return_value = json.dumps(payload).encode()
    mock_response.__enter__ = lambda s: s
    mock_response.__exit__ = MagicMock(return_value=False)
    return mock_response


class TestValidateCurrency:
    def test_valid_code(self):
        assert _validate_currency("usd") == "USD"

    def test_strips_and_uppercases(self):
        assert _validate_currency("  eur  ") == "EUR"

    def test_rejects_non_string(self):
        assert _validate_currency(123) is None
        assert _validate_currency(None) is None

    def test_rejects_wrong_length(self):
        assert _validate_currency("US") is None
        assert _validate_currency("USDD") is None

    def test_rejects_non_alpha(self):
        assert _validate_currency("US1") is None

    def test_rejects_injection_attempt(self):
        assert _validate_currency("USD&foo=bar") is None
        assert _validate_currency("USD\r\nX-Evil: 1") is None


class TestNormalizeSymbols:
    def test_none_returns_empty_list(self):
        assert _normalize_symbols(None) == []

    def test_csv_string(self):
        assert _normalize_symbols("eur,gbp") == ["EUR", "GBP"]

    def test_list(self):
        assert _normalize_symbols(["eur", "gbp"]) == ["EUR", "GBP"]

    def test_invalid_type(self):
        result = _normalize_symbols(123)
        assert "error" in result

    def test_invalid_symbol_charset(self):
        result = _normalize_symbols(["EUR", "US"])
        assert "error" in result
        assert "US" in result["error"]

    def test_too_many_symbols(self):
        result = _normalize_symbols(["USD"] * 51)
        assert "error" in result
        assert "too many" in result["error"]


class TestFxRateRequestBuilding:
    def test_invalid_base_no_network_call(self):
        with patch("tools.fx_rate_tool.urllib.request.urlopen") as mock_urlopen:
            result = fx_rate(base="US", symbols=["EUR"])
        assert result["ok"] is False
        assert "invalid base currency" in result["error"]
        mock_urlopen.assert_not_called()

    def test_invalid_symbol_no_network_call(self):
        with patch("tools.fx_rate_tool.urllib.request.urlopen") as mock_urlopen:
            result = fx_rate(base="USD", symbols=["EURO"])
        assert result["ok"] is False
        assert "invalid currency code" in result["error"]
        mock_urlopen.assert_not_called()

    def test_injection_charset_rejected_no_network_call(self):
        with patch("tools.fx_rate_tool.urllib.request.urlopen") as mock_urlopen:
            result = fx_rate(base="USD;DROP", symbols=["EUR"])
        assert result["ok"] is False
        mock_urlopen.assert_not_called()

    def test_builds_url_with_base_and_symbols(self):
        payload = {"amount": 1.0, "base": "USD", "date": "2024-01-01", "rates": {"EUR": 0.9, "GBP": 0.8}}
        with patch("tools.fx_rate_tool.urllib.request.urlopen", return_value=_mock_response(payload)) as mock_urlopen:
            result = fx_rate(base="usd", symbols=["eur", "gbp"])

        req = mock_urlopen.call_args[0][0]
        assert req.full_url.startswith("https://api.frankfurter.dev/v1/latest?")
        assert "base=USD" in req.full_url
        assert "symbols=EUR%2CGBP" in req.full_url
        assert req.get_header("User-agent") == "hermes-agent-fx-rate-tool/1.0"

        assert result == {"ok": True, "base": "USD", "date": "2024-01-01", "rates": {"EUR": 0.9, "GBP": 0.8}}

    def test_no_symbols_omits_param(self):
        payload = {"amount": 1.0, "base": "USD", "date": "2024-01-01", "rates": {"EUR": 0.9}}
        with patch("tools.fx_rate_tool.urllib.request.urlopen", return_value=_mock_response(payload)) as mock_urlopen:
            fx_rate(base="USD")

        req = mock_urlopen.call_args[0][0]
        assert "symbols=" not in req.full_url

    def test_network_error_is_reported(self):
        import urllib.error
        with patch("tools.fx_rate_tool.urllib.request.urlopen", side_effect=urllib.error.URLError("boom")):
            result = fx_rate(base="USD")
        assert result["ok"] is False
        assert "Frankfurter request failed" in result["error"]

    def test_oversized_response_is_rejected(self):
        import tools.fx_rate_tool as fx_rate_tool

        oversized = MagicMock()
        oversized.read.return_value = b"x" * (fx_rate_tool._MAX_RESPONSE_BYTES + 1)
        oversized.__enter__ = lambda s: s
        oversized.__exit__ = MagicMock(return_value=False)

        with patch("tools.fx_rate_tool.urllib.request.urlopen", return_value=oversized):
            result = fx_rate(base="USD")

        assert result["ok"] is False
        assert "exceeds" in result["error"]


class TestFxRateDefensiveParsing:
    def test_non_dict_response(self):
        with patch("tools.fx_rate_tool.urllib.request.urlopen", return_value=_mock_response([1, 2, 3])):
            result = fx_rate(base="USD")
        assert result["ok"] is False
        assert "not a JSON object" in result["error"]

    def test_rates_not_a_dict(self):
        payload = {"base": "USD", "date": "2024-01-01", "rates": "not-a-dict"}
        with patch("tools.fx_rate_tool.urllib.request.urlopen", return_value=_mock_response(payload)):
            result = fx_rate(base="USD")
        assert result["ok"] is True
        assert result["rates"] == {}

    def test_malformed_rate_values_are_skipped(self):
        payload = {"base": "USD", "date": "2024-01-01", "rates": {"EUR": 0.9, "GBP": "bad", "JPY": None, "FOO": True}}
        with patch("tools.fx_rate_tool.urllib.request.urlopen", return_value=_mock_response(payload)):
            result = fx_rate(base="USD")
        assert result["ok"] is True
        assert result["rates"] == {"EUR": 0.9}

    def test_missing_rates_key(self):
        payload = {"base": "USD", "date": "2024-01-01"}
        with patch("tools.fx_rate_tool.urllib.request.urlopen", return_value=_mock_response(payload)):
            result = fx_rate(base="USD")
        assert result["ok"] is True
        assert result["rates"] == {}


class TestFxConvert:
    def test_negative_amount_rejected_no_network_call(self):
        with patch("tools.fx_rate_tool.urllib.request.urlopen") as mock_urlopen:
            result = fx_convert(amount=-5, base="USD", to="EUR")
        assert result["ok"] is False
        assert "amount must be" in result["error"]
        mock_urlopen.assert_not_called()

    def test_non_number_amount_rejected_no_network_call(self):
        with patch("tools.fx_rate_tool.urllib.request.urlopen") as mock_urlopen:
            result = fx_convert(amount="100", base="USD", to="EUR")
        assert result["ok"] is False
        assert "amount must be a number" in result["error"]
        mock_urlopen.assert_not_called()

    def test_bool_amount_rejected(self):
        with patch("tools.fx_rate_tool.urllib.request.urlopen") as mock_urlopen:
            result = fx_convert(amount=True, base="USD", to="EUR")
        assert result["ok"] is False
        mock_urlopen.assert_not_called()

    def test_invalid_to_currency_no_network_call(self):
        with patch("tools.fx_rate_tool.urllib.request.urlopen") as mock_urlopen:
            result = fx_convert(amount=100, base="USD", to="EURO")
        assert result["ok"] is False
        mock_urlopen.assert_not_called()

    def test_convert_math(self):
        payload = {"amount": 1.0, "base": "USD", "date": "2024-01-01", "rates": {"EUR": 0.9}}
        with patch("tools.fx_rate_tool.urllib.request.urlopen", return_value=_mock_response(payload)):
            result = fx_convert(amount=100, base="USD", to="EUR")
        assert result == {
            "ok": True,
            "amount": 100,
            "base": "USD",
            "to": "EUR",
            "rate": 0.9,
            "result": 90.0,
            "date": "2024-01-01",
        }

    def test_zero_amount_allowed(self):
        payload = {"amount": 1.0, "base": "USD", "date": "2024-01-01", "rates": {"EUR": 0.9}}
        with patch("tools.fx_rate_tool.urllib.request.urlopen", return_value=_mock_response(payload)):
            result = fx_convert(amount=0, base="USD", to="EUR")
        assert result["ok"] is True
        assert result["result"] == 0.0

    def test_missing_rate_for_target(self):
        payload = {"amount": 1.0, "base": "USD", "date": "2024-01-01", "rates": {}}
        with patch("tools.fx_rate_tool.urllib.request.urlopen", return_value=_mock_response(payload)):
            result = fx_convert(amount=100, base="USD", to="EUR")
        assert result["ok"] is False
        assert "no rate available" in result["error"]


@pytest.mark.skip(reason="live network — run manually")
class TestLiveFxRate:
    """Live integration tests against the real Frankfurter API. Skipped if offline."""

    def test_usd_to_eur_gbp(self):
        try:
            result = fx_rate("USD", ["EUR", "GBP"])
        except Exception:
            pytest.skip("Frankfurter API unreachable")
        if not result.get("ok"):
            pytest.skip("Frankfurter API unreachable")
        assert result["base"] == "USD"
        assert "EUR" in result["rates"]
        assert "GBP" in result["rates"]

    def test_convert_usd_to_eur(self):
        try:
            result = fx_convert(100, "USD", "EUR")
        except Exception:
            pytest.skip("Frankfurter API unreachable")
        if not result.get("ok"):
            pytest.skip("Frankfurter API unreachable")
        assert result["result"] > 0
