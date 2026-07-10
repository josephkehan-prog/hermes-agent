"""Tests for skills/research/crypto-market/scripts/crypto.py — no network, no external services."""

from __future__ import annotations

import argparse
import importlib.util
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT = REPO_ROOT / "skills" / "research" / "crypto-market" / "scripts" / "crypto.py"


def _load_script_module():
    spec = importlib.util.spec_from_file_location("crypto_market_crypto_test_module", SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


crypto = _load_script_module()


class _RecordingFetchJson:
    """Stand-in for crypto.fetch_json — records how it was called, no network."""

    def __init__(self, payload):
        self._payload = payload
        self.calls = []

    def __call__(self, url, *, method="GET", data=None):
        self.calls.append({"url": url, "method": method, "data": data})
        return self._payload


class TestCoinIdValidation:
    def test_accepts_plain_coin_id(self):
        assert crypto.validate_coin_ids(["bitcoin"]) == ["bitcoin"]

    def test_accepts_hyphenated_coin_id(self):
        assert crypto.validate_coin_ids(["usd-coin"]) == ["usd-coin"]

    def test_rejects_shell_injection_attempt_with_exit_code_2(self):
        with pytest.raises(SystemExit) as exc_info:
            crypto.validate_coin_ids(["bitcoin; rm -rf /"])
        assert exc_info.value.code == 2

    def test_rejects_id_with_uppercase(self):
        with pytest.raises(SystemExit) as exc_info:
            crypto.validate_coin_ids(["Bitcoin"])
        assert exc_info.value.code == 2

    def test_rejects_id_with_url_metacharacters(self):
        with pytest.raises(SystemExit) as exc_info:
            crypto.validate_coin_ids(["bitcoin?ids=all"])
        assert exc_info.value.code == 2

    def test_rejects_empty_string(self):
        with pytest.raises(SystemExit) as exc_info:
            crypto.validate_coin_ids([""])
        assert exc_info.value.code == 2

    def test_price_command_never_calls_fetch_json_when_a_coin_id_is_invalid(self, monkeypatch):
        recorder = _RecordingFetchJson({})
        monkeypatch.setattr(crypto, "fetch_json", recorder)
        args = argparse.Namespace(coins=["bitcoin", "../../etc/passwd"])

        with pytest.raises(SystemExit) as exc_info:
            crypto.cmd_price(args)

        assert exc_info.value.code == 2
        assert recorder.calls == []


class TestEthAddressValidation:
    @pytest.mark.parametrize(
        "address",
        [
            "0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045",  # correct shape (40 hex chars)
        ],
    )
    def test_accepts_well_formed_address(self, address):
        assert crypto.ETH_ADDRESS_RE.match(address)

    @pytest.mark.parametrize(
        "address",
        [
            "0xd8dA6BF26964aF9D7eEd9e03E53415D37aA960",  # too short (39 hex chars)
            "0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045A",  # too long (41 hex chars)
            "d8dA6BF26964aF9D7eEd9e03E53415D37aA9604",  # missing 0x prefix
            "0xZZZa6BF26964aF9D7eEd9e03E53415D37aA9604",  # non-hex chars
            "0xd8dA6BF26964aF9D7eEd9e03E53415D37aA9604; DROP TABLE wallets;--",  # injection
            "",
        ],
    )
    def test_rejects_malformed_address(self, address):
        assert not crypto.ETH_ADDRESS_RE.match(address)

    def test_eth_balance_never_calls_fetch_json_for_a_bad_address(self, monkeypatch):
        recorder = _RecordingFetchJson({"result": "0x0"})
        monkeypatch.setattr(crypto, "fetch_json", recorder)
        args = argparse.Namespace(address="not-an-address")

        with pytest.raises(SystemExit) as exc_info:
            crypto.cmd_eth_balance(args)

        assert exc_info.value.code == 2
        assert recorder.calls == [], "no network call should happen for an invalid address"


class TestPriceParsing:
    def test_parses_price_change_and_market_cap(self, monkeypatch, capsys):
        payload = {
            "bitcoin": {"usd": 65000.5, "usd_24h_change": 2.345, "usd_market_cap": 1_280_000_000_000},
        }
        monkeypatch.setattr(crypto, "fetch_json", _RecordingFetchJson(payload))
        args = argparse.Namespace(coins=["bitcoin"])

        crypto.cmd_price(args)

        out = capsys.readouterr().out
        assert "bitcoin" in out
        assert "$65,000.50" in out
        assert "+2.35%" in out
        assert "$1,280,000,000,000" in out

    def test_reports_missing_coin_on_stderr_without_aborting_others(self, monkeypatch, capsys):
        payload = {"bitcoin": {"usd": 65000.5, "usd_24h_change": 1.0, "usd_market_cap": 100}}
        monkeypatch.setattr(crypto, "fetch_json", _RecordingFetchJson(payload))
        args = argparse.Namespace(coins=["bitcoin", "not-a-real-coin"])

        crypto.cmd_price(args)

        captured = capsys.readouterr()
        assert "bitcoin" in captured.out
        assert "not-a-real-coin: not found" in captured.err


class TestFearGreedParsing:
    def test_parses_value_and_classification(self, monkeypatch, capsys):
        payload = {"data": [{"value": "72", "value_classification": "Greed"}]}
        monkeypatch.setattr(crypto, "fetch_json", _RecordingFetchJson(payload))

        crypto.cmd_feargreed(argparse.Namespace())

        out = capsys.readouterr().out
        assert "72/100" in out
        assert "Greed" in out

    def test_empty_data_exits_with_code_2(self, monkeypatch):
        monkeypatch.setattr(crypto, "fetch_json", _RecordingFetchJson({"data": []}))

        with pytest.raises(SystemExit) as exc_info:
            crypto.cmd_feargreed(argparse.Namespace())

        assert exc_info.value.code == 2


class TestEthBalanceConversion:
    def test_converts_wei_to_eth(self, monkeypatch, capsys):
        # 1.5 ETH = 1_500_000_000_000_000_000 wei
        payload = {"jsonrpc": "2.0", "id": 1, "result": hex(1_500_000_000_000_000_000)}
        recorder = _RecordingFetchJson(payload)
        monkeypatch.setattr(crypto, "fetch_json", recorder)
        args = argparse.Namespace(address="0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045")

        crypto.cmd_eth_balance(args)

        out = capsys.readouterr().out
        assert "1.500000 ETH" in out
        assert "1500000000000000000 wei" in out
        # validated address must reach the RPC call, as a POST with a JSON body
        assert len(recorder.calls) == 1
        assert recorder.calls[0]["method"] == "POST"
        assert recorder.calls[0]["data"]["method"] == "eth_getBalance"
        assert recorder.calls[0]["data"]["params"][0] == args.address

    def test_rpc_error_field_exits_with_code_2(self, monkeypatch):
        payload = {"jsonrpc": "2.0", "id": 1, "error": {"code": -32602, "message": "invalid params"}}
        monkeypatch.setattr(crypto, "fetch_json", _RecordingFetchJson(payload))
        args = argparse.Namespace(address="0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045")

        with pytest.raises(SystemExit) as exc_info:
            crypto.cmd_eth_balance(args)

        assert exc_info.value.code == 2

    def test_missing_result_exits_with_code_2(self, monkeypatch):
        monkeypatch.setattr(crypto, "fetch_json", _RecordingFetchJson({"jsonrpc": "2.0", "id": 1}))
        args = argparse.Namespace(address="0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045")

        with pytest.raises(SystemExit) as exc_info:
            crypto.cmd_eth_balance(args)

        assert exc_info.value.code == 2


class TestResponseCap:
    def test_fetch_json_rejects_oversized_response(self, monkeypatch):
        class _OversizedResponse:
            def __enter__(self):
                return self

            def __exit__(self, *exc):
                return False

            def read(self, _n):
                return b"x" * (crypto.MAX_RESPONSE_BYTES + 1)

        monkeypatch.setattr(crypto.urllib.request, "urlopen", lambda *a, **k: _OversizedResponse())

        with pytest.raises(SystemExit) as exc_info:
            crypto.fetch_json("https://api.coingecko.com/api/v3/simple/price")

        assert exc_info.value.code == 2


class TestTrendingParsing:
    def test_parses_trending_coins(self, monkeypatch, capsys):
        payload = {
            "coins": [
                {"item": {"name": "Dogwifhat", "symbol": "WIF", "market_cap_rank": 45}},
            ]
        }
        monkeypatch.setattr(crypto, "fetch_json", _RecordingFetchJson(payload))

        crypto.cmd_trending(argparse.Namespace())

        out = capsys.readouterr().out
        assert "Dogwifhat" in out
        assert "WIF" in out


class TestArgparseWiring:
    def test_price_subcommand_accepts_multiple_coins(self):
        parser = crypto.build_parser()
        args = parser.parse_args(["price", "bitcoin", "ethereum", "monero"])
        assert args.command == "price"
        assert args.coins == ["bitcoin", "ethereum", "monero"]

    def test_eth_balance_subcommand_requires_address(self):
        parser = crypto.build_parser()
        args = parser.parse_args(["eth-balance", "0xabc"])
        assert args.command == "eth-balance"
        assert args.address == "0xabc"

    def test_command_handlers_cover_every_subparser_choice(self):
        parser = crypto.build_parser()
        subparsers_action = next(
            a for a in parser._actions if isinstance(a, argparse._SubParsersAction)
        )
        assert set(subparsers_action.choices) == set(crypto.COMMAND_HANDLERS)


@pytest.mark.skip(reason="live network call — run manually, not in CI")
class TestLiveRequests:
    def test_live_price_lookup(self, capsys):
        crypto.cmd_price(argparse.Namespace(coins=["bitcoin", "ethereum", "monero"]))
        assert "bitcoin" in capsys.readouterr().out

    def test_live_feargreed_lookup(self, capsys):
        crypto.cmd_feargreed(argparse.Namespace())
        assert "Fear & Greed Index" in capsys.readouterr().out
