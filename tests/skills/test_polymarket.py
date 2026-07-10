"""Tests for skills/research/polymarket/scripts/polymarket.py — no network, mocked JSON only."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT = REPO_ROOT / "skills" / "research" / "polymarket" / "scripts" / "polymarket.py"


def _load_script_module():
    spec = importlib.util.spec_from_file_location("polymarket_test_module", SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


poly = _load_script_module()


class _FakeResponse:
    """Minimal stand-in for the context-manager object urlopen() returns."""

    def __init__(self, data: bytes):
        self._data = data

    def __enter__(self):
        return self

    def __exit__(self, *exc_info):
        return False

    def read(self, n=-1):
        if n is None or n < 0:
            return self._data
        return self._data[:n]


# --------------------------------------------------------------------------
# Param validation rejects injection attempts
# --------------------------------------------------------------------------


class TestValidateSlug:
    def test_accepts_lowercase_alnum_and_hyphens(self):
        assert poly.validate_slug("will-x-happen-2026") == "will-x-happen-2026"

    def test_rejects_path_traversal(self):
        with pytest.raises(ValueError, match="invalid slug"):
            poly.validate_slug("../etc/passwd")

    def test_rejects_uppercase_and_spaces(self):
        with pytest.raises(ValueError, match="invalid slug"):
            poly.validate_slug("Bad Slug!")

    def test_rejects_empty_string(self):
        with pytest.raises(ValueError):
            poly.validate_slug("")

    def test_rejects_oversized_slug(self):
        with pytest.raises(ValueError):
            poly.validate_slug("a" * (poly.MAX_SLUG_CHARS + 1))


class TestValidateId:
    def test_accepts_decimal_token_id(self):
        token_id = "71321045679252212594626385532706912750332728571942532289631379312455583992563"
        assert poly.validate_id(token_id, "token_id") == token_id

    def test_accepts_hex_condition_id(self):
        assert poly.validate_id("0xabc123", "condition_id") == "0xabc123"

    def test_rejects_shell_injection_attempt(self):
        with pytest.raises(ValueError, match="invalid token_id"):
            poly.validate_id("123; rm -rf /", "token_id")

    def test_rejects_empty_id(self):
        with pytest.raises(ValueError):
            poly.validate_id("", "token_id")

    def test_rejects_oversized_id(self):
        with pytest.raises(ValueError):
            poly.validate_id("0" * (poly.MAX_ID_CHARS + 1), "token_id")


class TestValidateQuery:
    def test_accepts_normal_query(self):
        assert poly.validate_query("  bitcoin price  ") == "bitcoin price"

    def test_rejects_empty_query(self):
        with pytest.raises(ValueError, match="must not be empty"):
            poly.validate_query("   ")

    def test_rejects_control_characters(self):
        with pytest.raises(ValueError, match="control characters"):
            poly.validate_query("bad\x01query")

    def test_rejects_oversized_query(self):
        with pytest.raises(ValueError, match="too long"):
            poly.validate_query("x" * (poly.MAX_QUERY_CHARS + 1))


class TestValidateInterval:
    def test_accepts_known_interval(self):
        assert poly.validate_interval("1w") == "1w"

    def test_rejects_unknown_interval(self):
        with pytest.raises(ValueError, match="invalid interval"):
            poly.validate_interval("1y; DROP TABLE")


class TestValidateLimit:
    def test_clamps_to_max(self):
        assert poly.validate_limit(10_000) == poly.MAX_LIMIT

    def test_falls_back_to_default_on_none(self):
        assert poly.validate_limit(None, default=7) == 7

    def test_falls_back_to_default_on_non_positive(self):
        assert poly.validate_limit(0, default=7) == 7
        assert poly.validate_limit(-5, default=7) == 7

    def test_passes_through_valid_value(self):
        assert poly.validate_limit(25) == 25


class TestMainRejectsInjection:
    def test_bad_slug_exits_2(self, monkeypatch, capsys):
        monkeypatch.setattr(sys, "argv", ["polymarket.py", "market", "../etc/passwd"])
        with pytest.raises(SystemExit) as exc_info:
            poly.main()
        assert exc_info.value.code == 2
        assert "invalid slug" in capsys.readouterr().err

    def test_bad_token_id_exits_2(self, monkeypatch, capsys):
        monkeypatch.setattr(sys, "argv", ["polymarket.py", "price", "123; rm -rf /"])
        with pytest.raises(SystemExit) as exc_info:
            poly.main()
        assert exc_info.value.code == 2
        assert "invalid token_id" in capsys.readouterr().err

    def test_control_char_query_exits_2(self, monkeypatch, capsys):
        monkeypatch.setattr(sys, "argv", ["polymarket.py", "search", "bad\x01query"])
        with pytest.raises(SystemExit) as exc_info:
            poly.main()
        assert exc_info.value.code == 2
        assert "control characters" in capsys.readouterr().err


# --------------------------------------------------------------------------
# Response byte-cap
# --------------------------------------------------------------------------


class TestResponseCap:
    def test_get_rejects_oversized_response(self, monkeypatch):
        oversized = b"[" + b"1" * (poly.MAX_RESPONSE_BYTES + 10) + b"]"
        monkeypatch.setattr(
            poly.urllib.request, "urlopen", lambda req, timeout=None: _FakeResponse(oversized)
        )
        with pytest.raises(SystemExit) as exc_info:
            poly._get(f"{poly.GAMMA}/events")
        assert exc_info.value.code == 1

    def test_get_accepts_response_under_cap(self, monkeypatch):
        small = b'{"ok": true}'
        monkeypatch.setattr(
            poly.urllib.request, "urlopen", lambda req, timeout=None: _FakeResponse(small)
        )
        assert poly._get(f"{poly.GAMMA}/events") == {"ok": True}


# --------------------------------------------------------------------------
# closing-soon on mocked Gamma JSON
# --------------------------------------------------------------------------


class TestClosingSoon:
    def test_parses_mocked_events_and_prints_summary(self, capsys):
        events = [
            {
                "title": "Will it rain tomorrow?",
                "slug": "will-it-rain-tomorrow",
                "volume": 125_000,
                "endDate": "2000-01-01T00:00:00Z",  # far in the past -> "closed"
                "markets": [
                    {
                        "question": "Will it rain tomorrow?",
                        "outcomePrices": '["0.30", "0.70"]',
                        "outcomes": '["Yes", "No"]',
                        "volume": 125_000,
                        "closed": False,
                        "slug": "will-it-rain-tomorrow",
                    }
                ],
            }
        ]
        with patch.object(poly, "_get", return_value=events):
            poly.cmd_closing_soon(5)

        out = capsys.readouterr().out
        assert "Will it rain tomorrow?" in out
        assert "Closes:" in out
        assert "closed" in out
        assert "Yes: 30.0% / No: 70.0%" in out
        assert "slug: will-it-rain-tomorrow" in out

    def test_time_to_close_formats_future_date(self):
        from datetime import datetime, timedelta, timezone

        future = (datetime.now(timezone.utc) + timedelta(days=2, hours=3)).isoformat()
        result = poly._fmt_time_to_close(future)
        assert "d" in result

    def test_time_to_close_handles_missing_date(self):
        assert poly._fmt_time_to_close("") == "?"


# --------------------------------------------------------------------------
# Existing subcommands on mocked JSON
# --------------------------------------------------------------------------


class TestTrending:
    def test_parses_mocked_events(self, capsys):
        events = [
            {
                "title": "US Election Winner",
                "slug": "us-election-winner",
                "volume": 5_000_000,
                "markets": [
                    {
                        "question": "Will X win?",
                        "outcomePrices": '["0.65", "0.35"]',
                        "outcomes": '["Yes", "No"]',
                        "volume": 2_000_000,
                        "closed": False,
                        "slug": "will-x-win",
                    }
                ],
            }
        ]
        with patch.object(poly, "_get", return_value=events):
            poly.cmd_trending(1)

        out = capsys.readouterr().out
        assert "US Election Winner" in out
        assert "Yes: 65.0% / No: 35.0%" in out
        assert "$5.0M" in out


class TestSearch:
    def test_parses_mocked_search_results(self, capsys):
        payload = {
            "events": [
                {
                    "title": "Bitcoin above $100k?",
                    "slug": "btc-100k",
                    "volume": 900_000,
                    "markets": [
                        {
                            "question": "Will BTC exceed $100k?",
                            "outcomePrices": '["0.80", "0.20"]',
                            "outcomes": '["Yes", "No"]',
                            "volume": 900_000,
                            "closed": False,
                            "slug": "btc-100k-market",
                        }
                    ],
                }
            ],
            "pagination": {"totalResults": 1},
        }
        with patch.object(poly, "_get", return_value=payload):
            poly.cmd_search("bitcoin")

        out = capsys.readouterr().out
        assert 'Found 1 results for "bitcoin"' in out
        assert "Bitcoin above $100k?" in out
        assert "Yes: 80.0% / No: 20.0%" in out


class TestMarket:
    def test_parses_mocked_market_with_double_encoded_fields(self, capsys):
        market = {
            "question": "Will Y happen?",
            "closed": False,
            "outcomePrices": '["0.42", "0.58"]',
            "outcomes": '["Yes", "No"]',
            "volume": 10_000,
            "slug": "will-y-happen",
            "conditionId": "0xdeadbeef",
            "clobTokenIds": '["111", "222"]',
            "description": "A test market.",
        }
        with patch.object(poly, "_get", return_value=[market]):
            poly.cmd_market("will-y-happen")

        out = capsys.readouterr().out
        assert "Will Y happen?" in out
        assert "Status: ACTIVE" in out
        assert "conditionId: 0xdeadbeef" in out
        assert "token (Yes): 111" in out
        assert "token (No): 222" in out


class TestPrintMarketHelpers:
    def test_parse_json_field_decodes_double_encoded_string(self):
        assert poly._parse_json_field('["0.1", "0.9"]') == ["0.1", "0.9"]

    def test_parse_json_field_passes_through_non_string(self):
        assert poly._parse_json_field(["already", "a", "list"]) == ["already", "a", "list"]

    def test_fmt_pct_formats_probability(self):
        assert poly._fmt_pct("0.653") == "65.3%"

    def test_fmt_volume_formats_millions_and_thousands(self):
        assert poly._fmt_volume(2_500_000) == "$2.5M"
        assert poly._fmt_volume(4_200) == "$4.2K"
        assert poly._fmt_volume(50) == "$50"


# --------------------------------------------------------------------------
# Defensive shape guards — unexpected _get() shapes exit 2, never crash raw
# --------------------------------------------------------------------------


class TestUnexpectedResponseShapes:
    """cmd_search/trending/closing_soon/price/book/market/event must not let a
    wrong-shaped _get() return crash with a raw AttributeError/TypeError/KeyError —
    they should raise ValueError, which main()'s except ValueError turns into a
    clean SystemExit(2), same convention as cmd_trades already follows."""

    def test_search_exits_2_when_response_is_a_list(self, monkeypatch, capsys):
        monkeypatch.setattr(sys, "argv", ["polymarket.py", "search", "bitcoin"])
        with patch.object(poly, "_get", return_value=["not", "a", "dict"]):
            with pytest.raises(SystemExit) as exc_info:
                poly.main()
        assert exc_info.value.code == 2
        assert "unexpected response shape" in capsys.readouterr().err

    def test_search_exits_2_when_events_field_is_not_a_list(self, monkeypatch, capsys):
        monkeypatch.setattr(sys, "argv", ["polymarket.py", "search", "bitcoin"])
        with patch.object(poly, "_get", return_value={"events": "nope"}):
            with pytest.raises(SystemExit) as exc_info:
                poly.main()
        assert exc_info.value.code == 2
        assert "unexpected response shape" in capsys.readouterr().err

    def test_trending_exits_2_when_response_is_a_dict(self, monkeypatch, capsys):
        monkeypatch.setattr(sys, "argv", ["polymarket.py", "trending"])
        with patch.object(poly, "_get", return_value={"not": "a list"}):
            with pytest.raises(SystemExit) as exc_info:
                poly.main()
        assert exc_info.value.code == 2
        assert "unexpected response shape" in capsys.readouterr().err

    def test_closing_soon_exits_2_when_response_is_a_dict(self, monkeypatch, capsys):
        monkeypatch.setattr(sys, "argv", ["polymarket.py", "closing-soon"])
        with patch.object(poly, "_get", return_value={"not": "a list"}):
            with pytest.raises(SystemExit) as exc_info:
                poly.main()
        assert exc_info.value.code == 2
        assert "unexpected response shape" in capsys.readouterr().err

    def test_price_exits_2_when_response_is_a_list(self, monkeypatch, capsys):
        monkeypatch.setattr(sys, "argv", ["polymarket.py", "price", "123"])
        with patch.object(poly, "_get", return_value=["not", "a", "dict"]):
            with pytest.raises(SystemExit) as exc_info:
                poly.main()
        assert exc_info.value.code == 2
        assert "unexpected response shape" in capsys.readouterr().err

    def test_book_exits_2_when_response_is_a_list(self, monkeypatch, capsys):
        monkeypatch.setattr(sys, "argv", ["polymarket.py", "book", "123"])
        with patch.object(poly, "_get", return_value=["not", "a", "dict"]):
            with pytest.raises(SystemExit) as exc_info:
                poly.main()
        assert exc_info.value.code == 2
        assert "unexpected response shape" in capsys.readouterr().err

    def test_market_exits_2_when_response_is_a_dict(self, monkeypatch, capsys):
        monkeypatch.setattr(sys, "argv", ["polymarket.py", "market", "will-x-happen"])
        with patch.object(poly, "_get", return_value={"0": "not a list"}):
            with pytest.raises(SystemExit) as exc_info:
                poly.main()
        assert exc_info.value.code == 2
        assert "unexpected response shape" in capsys.readouterr().err

    def test_market_exits_2_when_first_element_is_not_a_dict(self, monkeypatch, capsys):
        monkeypatch.setattr(sys, "argv", ["polymarket.py", "market", "will-x-happen"])
        with patch.object(poly, "_get", return_value=["not a dict"]):
            with pytest.raises(SystemExit) as exc_info:
                poly.main()
        assert exc_info.value.code == 2
        assert "unexpected response shape" in capsys.readouterr().err

    def test_event_exits_2_when_response_is_a_dict(self, monkeypatch, capsys):
        monkeypatch.setattr(sys, "argv", ["polymarket.py", "event", "will-x-happen"])
        with patch.object(poly, "_get", return_value={"not": "a list"}):
            with pytest.raises(SystemExit) as exc_info:
                poly.main()
        assert exc_info.value.code == 2
        assert "unexpected response shape" in capsys.readouterr().err

    def test_search_skips_malformed_list_items_without_crashing(self, capsys):
        payload = {"events": ["not-a-dict", {"title": "OK", "slug": "ok", "markets": []}]}
        with patch.object(poly, "_get", return_value=payload):
            poly.cmd_search("bitcoin")
        out = capsys.readouterr().out
        assert "=== OK ===" in out

    def test_book_handles_non_dict_orderbook_entries(self, capsys):
        book = {"bids": ["bad-entry", {"price": "0.4", "size": "10"}], "asks": []}
        with patch.object(poly, "_get", return_value=book):
            poly.cmd_book("123")
        out = capsys.readouterr().out
        assert "Top bids (1 total)" in out


# --------------------------------------------------------------------------
# Live smoke test — network, run manually / sparingly, never in CI
# --------------------------------------------------------------------------


@pytest.mark.skip(reason="hits the live Polymarket API; run manually, not in CI")
def test_live_closing_soon_smoke(capsys):
    poly.cmd_closing_soon(3)
    out = capsys.readouterr().out
    assert "closing soonest" in out
