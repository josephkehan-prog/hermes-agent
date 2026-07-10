"""Tests for skills/research/market-pulse/scripts/pulse.py — no network, no external services."""

from __future__ import annotations

import argparse
import importlib.util
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT = REPO_ROOT / "skills" / "research" / "market-pulse" / "scripts" / "pulse.py"


def _load_script_module():
    spec = importlib.util.spec_from_file_location("market_pulse_pulse_test_module", SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


pulse = _load_script_module()


class _RecordingFetchJson:
    """Stand-in for pulse.fetch_json — records how it was called, no network.

    Supports either a single payload (returned for every call) or a
    dict keyed by URL substring, so a test can make different sources
    behave differently within one gather.
    """

    def __init__(self, payload=None, by_url=None):
        self._payload = payload
        self._by_url = by_url or {}
        self.calls = []

    def __call__(self, url):
        self.calls.append(url)
        for substring, result in self._by_url.items():
            if substring in url:
                if isinstance(result, Exception):
                    raise result
                return result
        if isinstance(self._payload, Exception):
            raise self._payload
        return self._payload


class TestGatherCrypto:
    def test_parses_coin_list_into_symbol_price_change(self, monkeypatch):
        payload = [
            {"id": "bitcoin", "symbol": "btc", "name": "Bitcoin", "current_price": 65000.5, "price_change_percentage_24h": 2.34},
            {"id": "ethereum", "symbol": "eth", "name": "Ethereum", "current_price": 3200.1, "price_change_percentage_24h": -1.1},
        ]
        monkeypatch.setattr(pulse, "fetch_json", _RecordingFetchJson(payload))

        result = pulse.gather_crypto()

        assert result["ok"] is True
        assert result["coins"][0]["symbol"] == "BTC"
        assert result["coins"][0]["price"] == 65000.5
        assert result["coins"][1]["symbol"] == "ETH"
        assert result["coins"][1]["change_24h"] == -1.1

    def test_fetch_error_is_isolated_as_not_ok(self, monkeypatch):
        monkeypatch.setattr(
            pulse, "fetch_json", _RecordingFetchJson(pulse.PulseFetchError("HTTP 429 for coingecko"))
        )

        result = pulse.gather_crypto()

        assert result["ok"] is False
        assert "429" in result["error"]

    def test_non_list_top_level_response_is_isolated_as_not_ok(self, monkeypatch):
        # Arrange: CoinGecko returns a dict instead of the expected list
        monkeypatch.setattr(pulse, "fetch_json", _RecordingFetchJson({"unexpected": "shape"}))

        result = pulse.gather_crypto()

        assert result["ok"] is False
        assert "shape" in result["error"]

    def test_non_dict_coin_entries_are_skipped_without_crashing(self, monkeypatch):
        payload = ["not-a-dict", {"symbol": "btc", "current_price": 1.0, "price_change_percentage_24h": 0.5}]
        monkeypatch.setattr(pulse, "fetch_json", _RecordingFetchJson(payload))

        result = pulse.gather_crypto()

        assert result["ok"] is True
        assert len(result["coins"]) == 1
        assert result["coins"][0]["symbol"] == "BTC"


class TestGatherFearGreed:
    def test_parses_value_and_classification(self, monkeypatch):
        payload = {"data": [{"value": "72", "value_classification": "Greed"}]}
        monkeypatch.setattr(pulse, "fetch_json", _RecordingFetchJson(payload))

        result = pulse.gather_feargreed()

        assert result["ok"] is True
        assert result["value"] == "72"
        assert result["classification"] == "Greed"

    def test_empty_data_list_is_isolated_as_not_ok(self, monkeypatch):
        monkeypatch.setattr(pulse, "fetch_json", _RecordingFetchJson({"data": []}))

        result = pulse.gather_feargreed()

        assert result["ok"] is False

    def test_non_dict_top_level_response_is_isolated_as_not_ok(self, monkeypatch):
        monkeypatch.setattr(pulse, "fetch_json", _RecordingFetchJson(["unexpected", "list"]))

        result = pulse.gather_feargreed()

        assert result["ok"] is False

    def test_non_list_data_field_is_isolated_as_not_ok(self, monkeypatch):
        monkeypatch.setattr(pulse, "fetch_json", _RecordingFetchJson({"data": "not-a-list"}))

        result = pulse.gather_feargreed()

        assert result["ok"] is False


class TestGatherPolymarket:
    def test_parses_events_into_title_volume_slug(self, monkeypatch):
        payload = [
            {"title": "Will X happen?", "volume": 1_234_567, "slug": "will-x-happen"},
        ]
        monkeypatch.setattr(pulse, "fetch_json", _RecordingFetchJson(payload))

        result = pulse.gather_polymarket()

        assert result["ok"] is True
        assert result["events"][0]["title"] == "Will X happen?"
        assert result["events"][0]["slug"] == "will-x-happen"

    def test_non_list_top_level_response_is_isolated_as_not_ok(self, monkeypatch):
        monkeypatch.setattr(pulse, "fetch_json", _RecordingFetchJson({"unexpected": "shape"}))

        result = pulse.gather_polymarket()

        assert result["ok"] is False

    def test_non_dict_event_entries_are_skipped_without_crashing(self, monkeypatch):
        payload = ["not-a-dict", {"title": "Real event", "volume": 100, "slug": "real-event"}]
        monkeypatch.setattr(pulse, "fetch_json", _RecordingFetchJson(payload))

        result = pulse.gather_polymarket()

        assert result["ok"] is True
        assert len(result["events"]) == 1
        assert result["events"][0]["title"] == "Real event"

    def test_fetch_error_is_isolated_as_not_ok(self, monkeypatch):
        monkeypatch.setattr(
            pulse, "fetch_json", _RecordingFetchJson(pulse.PulseFetchError("request failed: timed out"))
        )

        result = pulse.gather_polymarket()

        assert result["ok"] is False
        assert "timed out" in result["error"]


class TestSnapshotPerSourceIsolation:
    """One source failing must never prevent the other two from appearing."""

    def _patch_gathers(self, monkeypatch, *, crypto_ok, feargreed_ok, polymarket_ok):
        monkeypatch.setattr(
            pulse,
            "gather_crypto",
            lambda: {"ok": True, "coins": [{"symbol": "BTC", "name": "Bitcoin", "price": 1.0, "change_24h": 1.0}]}
            if crypto_ok
            else {"ok": False, "error": "coingecko down"},
        )
        monkeypatch.setattr(
            pulse,
            "gather_feargreed",
            lambda: {"ok": True, "value": "50", "classification": "Neutral"}
            if feargreed_ok
            else {"ok": False, "error": "alternative.me down"},
        )
        monkeypatch.setattr(
            pulse,
            "gather_polymarket",
            lambda: {"ok": True, "events": [{"title": "Event", "volume": 100, "slug": "event"}]}
            if polymarket_ok
            else {"ok": False, "error": "polymarket down"},
        )

    def test_one_source_down_still_prints_the_other_two_and_exits_zero(self, monkeypatch, capsys):
        self._patch_gathers(monkeypatch, crypto_ok=False, feargreed_ok=True, polymarket_ok=True)
        args = argparse.Namespace(json=False)

        pulse.cmd_snapshot(args)  # must not raise SystemExit

        captured = capsys.readouterr()
        assert "coingecko down" in captured.out
        assert "50/100" in captured.out
        assert "Event" in captured.out

    def test_all_sources_down_exits_with_code_2(self, monkeypatch):
        self._patch_gathers(monkeypatch, crypto_ok=False, feargreed_ok=False, polymarket_ok=False)
        args = argparse.Namespace(json=False)

        with pytest.raises(SystemExit) as exc_info:
            pulse.cmd_snapshot(args)

        assert exc_info.value.code == 2

    def test_json_output_includes_all_three_sections(self, monkeypatch, capsys):
        import json as json_module

        self._patch_gathers(monkeypatch, crypto_ok=True, feargreed_ok=True, polymarket_ok=True)
        args = argparse.Namespace(json=True)

        pulse.cmd_snapshot(args)

        payload = json_module.loads(capsys.readouterr().out)
        assert set(payload) >= {"crypto", "feargreed", "polymarket", "generated_at"}
        assert payload["crypto"]["ok"] is True
        assert payload["feargreed"]["ok"] is True
        assert payload["polymarket"]["ok"] is True


class TestResponseCap:
    def test_fetch_json_rejects_oversized_response(self, monkeypatch):
        class _OversizedResponse:
            def __enter__(self):
                return self

            def __exit__(self, *exc):
                return False

            def read(self, _n):
                return b"x" * (pulse.MAX_RESPONSE_BYTES + 1)

        monkeypatch.setattr(pulse.urllib.request, "urlopen", lambda *a, **k: _OversizedResponse())

        with pytest.raises(pulse.PulseFetchError):
            pulse.fetch_json("https://api.coingecko.com/api/v3/coins/markets")


class TestArgparseWiring:
    def test_snapshot_subcommand_defaults_json_to_false(self):
        parser = pulse.build_parser()
        args = parser.parse_args(["snapshot"])
        assert args.command == "snapshot"
        assert args.json is False

    def test_snapshot_subcommand_accepts_json_flag(self):
        parser = pulse.build_parser()
        args = parser.parse_args(["snapshot", "--json"])
        assert args.json is True

    def test_command_handlers_cover_every_subparser_choice(self):
        parser = pulse.build_parser()
        subparsers_action = next(
            a for a in parser._actions if isinstance(a, argparse._SubParsersAction)
        )
        assert set(subparsers_action.choices) == set(pulse.COMMAND_HANDLERS)


@pytest.mark.skip(reason="live network call — run manually, not in CI")
class TestLiveRequests:
    def test_live_snapshot(self, capsys):
        pulse.cmd_snapshot(argparse.Namespace(json=False))
        assert "Market Pulse" in capsys.readouterr().out
