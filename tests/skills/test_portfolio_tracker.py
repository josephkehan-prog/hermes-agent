"""Tests for skills/research/portfolio-tracker/scripts/portfolio.py — no network, no external services."""

from __future__ import annotations

import argparse
import importlib.util
import json
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT = REPO_ROOT / "skills" / "research" / "portfolio-tracker" / "scripts" / "portfolio.py"
SAMPLE_HOLDINGS = REPO_ROOT / "skills" / "research" / "portfolio-tracker" / "scripts" / "sample-holdings.json"


def _load_script_module():
    spec = importlib.util.spec_from_file_location("portfolio_tracker_portfolio_test_module", SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


portfolio = _load_script_module()


class _RecordingFetchJson:
    """Stand-in for portfolio.fetch_json — records how it was called, no network."""

    def __init__(self, payload):
        self._payload = payload
        self.calls = []

    def __call__(self, url):
        self.calls.append({"url": url})
        return self._payload


class TestHoldingsFilePathValidation:
    def test_missing_file_exits_with_code_2(self, tmp_path):
        missing = tmp_path / "does-not-exist.json"

        with pytest.raises(SystemExit) as exc_info:
            portfolio.load_holdings(str(missing))

        assert exc_info.value.code == 2

    def test_directory_path_exits_with_code_2(self, tmp_path):
        with pytest.raises(SystemExit) as exc_info:
            portfolio.load_holdings(str(tmp_path))

        assert exc_info.value.code == 2

    def test_malformed_json_exits_with_code_2(self, tmp_path):
        bad_file = tmp_path / "holdings.json"
        bad_file.write_text("{not valid json", encoding="utf-8")

        with pytest.raises(SystemExit) as exc_info:
            portfolio.load_holdings(str(bad_file))

        assert exc_info.value.code == 2


class TestHoldingsShapeValidation:
    def test_non_list_top_level_exits_with_code_2(self):
        with pytest.raises(SystemExit) as exc_info:
            portfolio.validate_holdings({"coin_id": "bitcoin", "amount": 1})

        assert exc_info.value.code == 2

    def test_empty_list_exits_with_code_2(self):
        with pytest.raises(SystemExit) as exc_info:
            portfolio.validate_holdings([])

        assert exc_info.value.code == 2

    def test_non_object_entry_exits_with_code_2(self):
        with pytest.raises(SystemExit) as exc_info:
            portfolio.validate_holdings(["bitcoin"])

        assert exc_info.value.code == 2

    @pytest.mark.parametrize(
        "coin_id",
        [
            "Bitcoin",  # uppercase not allowed
            "bitcoin; rm -rf /",  # injection attempt
            "bitcoin?ids=all",  # URL metacharacters
            "",  # empty
            "a" * 65,  # too long
            123,  # wrong type
            None,  # wrong type
        ],
    )
    def test_rejects_bad_coin_id(self, coin_id):
        with pytest.raises(SystemExit) as exc_info:
            portfolio.validate_holdings([{"coin_id": coin_id, "amount": 1}])

        assert exc_info.value.code == 2

    @pytest.mark.parametrize(
        "amount",
        [
            -1,  # negative
            -0.5,  # negative float
            "1.0",  # wrong type (string)
            None,  # wrong type
            True,  # bool must not pass as a number despite being an int subclass
            [1],  # wrong type
        ],
    )
    def test_rejects_bad_amount(self, amount):
        with pytest.raises(SystemExit) as exc_info:
            portfolio.validate_holdings([{"coin_id": "bitcoin", "amount": amount}])

        assert exc_info.value.code == 2

    def test_accepts_well_formed_holdings(self):
        data = [{"coin_id": "bitcoin", "amount": 0.5}, {"coin_id": "usd-coin", "amount": 100}]

        holdings = portfolio.validate_holdings(data)

        assert holdings == data

    def test_accepts_zero_amount(self):
        holdings = portfolio.validate_holdings([{"coin_id": "bitcoin", "amount": 0}])

        assert holdings == [{"coin_id": "bitcoin", "amount": 0}]


class TestCheckCommand:
    def test_valid_holdings_file_prints_summary(self, tmp_path, capsys):
        holdings_file = tmp_path / "holdings.json"
        holdings_file.write_text(json.dumps([{"coin_id": "bitcoin", "amount": 1}]), encoding="utf-8")

        portfolio.cmd_check(argparse.Namespace(holdings_file=str(holdings_file)))

        out = capsys.readouterr().out
        assert "1 holding(s)" in out
        assert "bitcoin" in out

    def test_check_never_calls_fetch_json(self, tmp_path, monkeypatch):
        recorder = _RecordingFetchJson({})
        monkeypatch.setattr(portfolio, "fetch_json", recorder)
        holdings_file = tmp_path / "holdings.json"
        holdings_file.write_text(json.dumps([{"coin_id": "bitcoin", "amount": 1}]), encoding="utf-8")

        portfolio.cmd_check(argparse.Namespace(holdings_file=str(holdings_file)))

        assert recorder.calls == []

    def test_malformed_holdings_file_exits_2_without_network_call(self, tmp_path, monkeypatch):
        recorder = _RecordingFetchJson({})
        monkeypatch.setattr(portfolio, "fetch_json", recorder)
        holdings_file = tmp_path / "holdings.json"
        holdings_file.write_text(json.dumps([{"coin_id": "NOT VALID", "amount": -5}]), encoding="utf-8")

        with pytest.raises(SystemExit) as exc_info:
            portfolio.cmd_check(argparse.Namespace(holdings_file=str(holdings_file)))

        assert exc_info.value.code == 2
        assert recorder.calls == []


class TestValueCommand:
    def test_computes_per_holding_and_total_value(self, tmp_path, monkeypatch, capsys):
        holdings_file = tmp_path / "holdings.json"
        holdings_file.write_text(
            json.dumps([{"coin_id": "bitcoin", "amount": 2}, {"coin_id": "ethereum", "amount": 10}]),
            encoding="utf-8",
        )
        payload = {"bitcoin": {"usd": 50_000.0}, "ethereum": {"usd": 3_000.0}}
        recorder = _RecordingFetchJson(payload)
        monkeypatch.setattr(portfolio, "fetch_json", recorder)

        portfolio.cmd_value(argparse.Namespace(holdings_file=str(holdings_file), vs="usd"))

        out = capsys.readouterr().out
        # bitcoin: 2 * 50,000 = 100,000; ethereum: 10 * 3,000 = 30,000; total = 130,000
        assert "100,000.00" in out
        assert "30,000.00" in out
        assert "total: 130,000.00 USD" in out
        # bitcoin (higher value) must be sorted before ethereum
        assert out.index("bitcoin") < out.index("ethereum")
        # one batched call, not one per coin
        assert len(recorder.calls) == 1

    def test_batches_unique_coin_ids_into_one_call(self, tmp_path, monkeypatch):
        holdings_file = tmp_path / "holdings.json"
        holdings_file.write_text(
            json.dumps([{"coin_id": "bitcoin", "amount": 1}, {"coin_id": "bitcoin", "amount": 1}]),
            encoding="utf-8",
        )
        recorder = _RecordingFetchJson({"bitcoin": {"usd": 1000.0}})
        monkeypatch.setattr(portfolio, "fetch_json", recorder)

        portfolio.cmd_value(argparse.Namespace(holdings_file=str(holdings_file), vs="usd"))

        assert len(recorder.calls) == 1
        assert recorder.calls[0]["url"].count("bitcoin") == 1


class TestValueCrashRegressions:
    """Regression tests for defensive isinstance-guard handling of malformed CoinGecko responses."""

    def test_non_dict_top_level_response_exits_with_code_2(self, tmp_path, monkeypatch):
        holdings_file = tmp_path / "holdings.json"
        holdings_file.write_text(json.dumps([{"coin_id": "bitcoin", "amount": 1}]), encoding="utf-8")
        monkeypatch.setattr(portfolio, "fetch_json", _RecordingFetchJson(["unexpected", "list"]))

        with pytest.raises(SystemExit) as exc_info:
            portfolio.cmd_value(argparse.Namespace(holdings_file=str(holdings_file), vs="usd"))

        assert exc_info.value.code == 2

    def test_non_dict_coin_entry_is_skipped_not_crashing(self, tmp_path, monkeypatch, capsys):
        holdings_file = tmp_path / "holdings.json"
        holdings_file.write_text(json.dumps([{"coin_id": "bitcoin", "amount": 1}]), encoding="utf-8")
        payload = {"bitcoin": ["not", "a", "dict"]}
        monkeypatch.setattr(portfolio, "fetch_json", _RecordingFetchJson(payload))

        with pytest.raises(SystemExit) as exc_info:
            portfolio.cmd_value(argparse.Namespace(holdings_file=str(holdings_file), vs="usd"))

        # all holdings unpriceable -> no rows -> clean exit 2, not a crash
        assert exc_info.value.code == 2
        assert "price not found" in capsys.readouterr().err

    def test_non_numeric_price_field_is_skipped_not_crashing(self, tmp_path, monkeypatch, capsys):
        holdings_file = tmp_path / "holdings.json"
        holdings_file.write_text(
            json.dumps([{"coin_id": "bitcoin", "amount": 1}, {"coin_id": "ethereum", "amount": 1}]),
            encoding="utf-8",
        )
        payload = {"bitcoin": {"usd": "not-a-number"}, "ethereum": {"usd": 100.0}}
        monkeypatch.setattr(portfolio, "fetch_json", _RecordingFetchJson(payload))

        portfolio.cmd_value(argparse.Namespace(holdings_file=str(holdings_file), vs="usd"))

        captured = capsys.readouterr()
        assert "bitcoin: no usd price" in captured.err
        assert "total: 100.00 USD" in captured.out


class TestArgparseWiring:
    def test_value_subcommand_defaults_vs_to_usd(self):
        parser = portfolio.build_parser()
        args = parser.parse_args(["value", "holdings.json"])
        assert args.command == "value"
        assert args.holdings_file == "holdings.json"
        assert args.vs == "usd"

    def test_value_subcommand_accepts_vs_override(self):
        parser = portfolio.build_parser()
        args = parser.parse_args(["value", "holdings.json", "--vs", "eur"])
        assert args.vs == "eur"

    def test_check_subcommand_requires_holdings_file(self):
        parser = portfolio.build_parser()
        args = parser.parse_args(["check", "holdings.json"])
        assert args.command == "check"
        assert args.holdings_file == "holdings.json"

    def test_command_handlers_cover_every_subparser_choice(self):
        parser = portfolio.build_parser()
        subparsers_action = next(
            a for a in parser._actions if isinstance(a, argparse._SubParsersAction)
        )
        assert set(subparsers_action.choices) == set(portfolio.COMMAND_HANDLERS)


class TestResponseCap:
    def test_fetch_json_rejects_oversized_response(self, monkeypatch):
        class _OversizedResponse:
            def __enter__(self):
                return self

            def __exit__(self, *exc):
                return False

            def read(self, _n):
                return b"x" * (portfolio.MAX_RESPONSE_BYTES + 1)

        monkeypatch.setattr(portfolio.urllib.request, "urlopen", lambda *a, **k: _OversizedResponse())

        with pytest.raises(SystemExit) as exc_info:
            portfolio.fetch_json("https://api.coingecko.com/api/v3/simple/price")

        assert exc_info.value.code == 2


@pytest.mark.skip(reason="live network call — run manually, not in CI")
class TestLiveRequests:
    def test_live_value_lookup(self, capsys):
        portfolio.cmd_value(argparse.Namespace(holdings_file=str(SAMPLE_HOLDINGS), vs="usd"))
        assert "total:" in capsys.readouterr().out
