"""Tests for the wallet lookup tool (address validation, request building, no
network except in the opt-in live class)."""

import json
import urllib.error
from unittest.mock import MagicMock, patch

import pytest

from tools.wallet_tool import (
    _validate_eth_address,
    _validate_btc_address,
    eth_balance,
    btc_address,
)


def _mock_response(payload) -> MagicMock:
    """Build a urlopen()-context-manager mock returning payload as JSON bytes."""
    mock_response = MagicMock()
    mock_response.read.return_value = json.dumps(payload).encode()
    mock_response.__enter__ = lambda s: s
    mock_response.__exit__ = MagicMock(return_value=False)
    return mock_response


class TestValidateEthAddress:
    def test_valid_checksummed_address(self):
        addr = "0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045"
        assert _validate_eth_address(addr) == addr

    def test_strips_whitespace(self):
        addr = "0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045"
        assert _validate_eth_address(f"  {addr}  ") == addr

    def test_rejects_empty(self):
        assert _validate_eth_address("") is None
        assert _validate_eth_address(None) is None

    def test_rejects_non_string(self):
        assert _validate_eth_address(12345) is None

    def test_rejects_missing_prefix(self):
        assert _validate_eth_address("d8dA6BF26964aF9D7eEd9e03E53415D37aA96045") is None

    def test_rejects_too_short(self):
        assert _validate_eth_address("0xd8dA6BF26964aF9D7eEd9e03E53415D37aA") is None

    def test_rejects_too_long(self):
        assert _validate_eth_address("0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045FF") is None

    def test_rejects_non_hex_chars(self):
        assert _validate_eth_address("0xZZZZ6BF26964aF9D7eEd9e03E53415D37aA9604") is None

    def test_rejects_shell_injection_attempt(self):
        assert _validate_eth_address("0x0000000000000000000000000000000000000; rm -rf /") is None

    def test_rejects_url_injection_attempt(self):
        assert _validate_eth_address("http://169.254.169.254/latest/meta-data/") is None


class TestValidateBtcAddress:
    def test_valid_base58_p2pkh(self):
        addr = "1BvBMSEYstWetqTFn5Au4m4GFg7xJaNVN2"
        assert _validate_btc_address(addr) == addr

    def test_valid_base58_p2sh(self):
        addr = "3J98t1WpEZ73CNmQviecrnyiWrnqRhWNLy"
        assert _validate_btc_address(addr) == addr

    def test_valid_bech32(self):
        addr = "bc1qar0srrr7xfkvy5l643lydnw9re59gtzzwf5mdq"
        assert _validate_btc_address(addr) == addr

    def test_strips_whitespace(self):
        addr = "1BvBMSEYstWetqTFn5Au4m4GFg7xJaNVN2"
        assert _validate_btc_address(f"  {addr}  ") == addr

    def test_rejects_empty(self):
        assert _validate_btc_address("") is None
        assert _validate_btc_address(None) is None

    def test_rejects_non_string(self):
        assert _validate_btc_address(12345) is None

    def test_rejects_ambiguous_prefix(self):
        assert _validate_btc_address("0BvBMSEYstWetqTFn5Au4m4GFg7xJaNVN2") is None

    def test_rejects_disallowed_base58_chars(self):
        # base58 excludes 0, O, I, l
        assert _validate_btc_address("1BvBMSEYstWetqTFn5Au4m4GFg7xJa0VN2") is None

    def test_rejects_injection_attempt(self):
        assert _validate_btc_address("1BvBMSEYstWetqTFn5Au4m4GFg7x; rm -rf /") is None


class TestEthBalanceNoNetworkOnInvalid:
    def test_invalid_address_no_network_call(self):
        with patch("tools.wallet_tool.urllib.request.urlopen") as mock_urlopen:
            result = eth_balance("not-an-address")
        assert result["ok"] is False
        assert "invalid ethereum address" in result["error"]
        mock_urlopen.assert_not_called()

    def test_injection_attempt_no_network_call(self):
        with patch("tools.wallet_tool.urllib.request.urlopen") as mock_urlopen:
            result = eth_balance("0x0000000000000000000000000000000000000; curl evil.com")
        assert result["ok"] is False
        mock_urlopen.assert_not_called()


class TestEthBalanceRequestBuilding:
    def test_wei_to_eth_conversion(self):
        addr = "0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045"
        payload = {"jsonrpc": "2.0", "id": 1, "result": "0xde0b6b3a7640000"}  # 1e18 wei = 1 ETH
        with patch("tools.wallet_tool.urllib.request.urlopen", return_value=_mock_response(payload)) as mock_urlopen:
            result = eth_balance(addr)

        req = mock_urlopen.call_args[0][0]
        assert req.full_url == "https://cloudflare-eth.com"
        body = json.loads(req.data.decode())
        assert body["method"] == "eth_getBalance"
        assert body["params"] == [addr, "latest"]
        assert req.get_header("User-agent") == "hermes-agent-wallet-tool/1.0"

        assert result["ok"] is True
        assert result["address"] == addr
        assert result["balance_wei"] == 10**18
        assert result["balance_eth"] == 1.0

    def test_zero_balance(self):
        addr = "0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045"
        payload = {"jsonrpc": "2.0", "id": 1, "result": "0x0"}
        with patch("tools.wallet_tool.urllib.request.urlopen", return_value=_mock_response(payload)):
            result = eth_balance(addr)
        assert result["ok"] is True
        assert result["balance_wei"] == 0
        assert result["balance_eth"] == 0.0

    def test_rpc_error_is_reported(self):
        addr = "0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045"
        payload = {"jsonrpc": "2.0", "id": 1, "error": {"code": -32602, "message": "invalid params"}}
        with patch("tools.wallet_tool.urllib.request.urlopen", return_value=_mock_response(payload)):
            result = eth_balance(addr)
        assert result["ok"] is False
        assert "invalid params" in result["error"]

    def test_network_error_is_reported(self):
        addr = "0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045"
        with patch("tools.wallet_tool.urllib.request.urlopen", side_effect=urllib.error.URLError("boom")):
            result = eth_balance(addr)
        assert result["ok"] is False
        assert "could not reach eth rpc endpoint" in result["error"]

    def test_oversized_response_is_rejected(self):
        import tools.wallet_tool as wallet_tool

        addr = "0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045"
        oversized = MagicMock()
        oversized.read.return_value = b"x" * (wallet_tool._MAX_RESPONSE_BYTES + 1)
        oversized.__enter__ = lambda s: s
        oversized.__exit__ = MagicMock(return_value=False)

        with patch("tools.wallet_tool.urllib.request.urlopen", return_value=oversized):
            result = eth_balance(addr)

        assert result["ok"] is False
        assert "exceeds" in result["error"]


class TestBtcAddressNoNetworkOnInvalid:
    def test_invalid_address_no_network_call(self):
        with patch("tools.wallet_tool.urllib.request.urlopen") as mock_urlopen:
            result = btc_address("not-an-address")
        assert result["ok"] is False
        assert "invalid bitcoin address" in result["error"]
        mock_urlopen.assert_not_called()

    def test_injection_attempt_no_network_call(self):
        with patch("tools.wallet_tool.urllib.request.urlopen") as mock_urlopen:
            result = btc_address("1BvBMSEYstWetqTFn5Au4m4GFg7x; rm -rf /")
        assert result["ok"] is False
        mock_urlopen.assert_not_called()


class TestBtcAddressRequestBuilding:
    def test_satoshi_to_btc_conversion(self):
        addr = "1BvBMSEYstWetqTFn5Au4m4GFg7xJaNVN2"
        payload = {
            "data": {
                addr: {
                    "address": {"balance": 150000000, "transaction_count": 42},
                }
            },
            "context": {},
        }
        with patch("tools.wallet_tool.urllib.request.urlopen", return_value=_mock_response(payload)) as mock_urlopen:
            result = btc_address(addr)

        req = mock_urlopen.call_args[0][0]
        assert req.full_url.startswith("https://api.blockchair.com/bitcoin/dashboards/address/")
        assert req.get_header("User-agent") == "hermes-agent-wallet-tool/1.0"

        assert result["ok"] is True
        assert result["address"] == addr
        assert result["balance_btc"] == 1.5
        assert result["tx_count"] == 42

    def test_blockchair_context_error_is_reported(self):
        addr = "1BvBMSEYstWetqTFn5Au4m4GFg7xJaNVN2"
        payload = {"data": {}, "context": {"error": "something went wrong"}}
        with patch("tools.wallet_tool.urllib.request.urlopen", return_value=_mock_response(payload)):
            result = btc_address(addr)
        assert result["ok"] is False
        assert "something went wrong" in result["error"]

    def test_rate_limit_is_reported(self):
        addr = "1BvBMSEYstWetqTFn5Au4m4GFg7xJaNVN2"
        with patch(
            "tools.wallet_tool.urllib.request.urlopen",
            side_effect=urllib.error.HTTPError("url", 402, "Payment Required", {}, None),
        ):
            result = btc_address(addr)
        assert result["ok"] is False
        assert "rate limit" in result["error"]

    def test_blockchair_ip_blacklist_status_is_reported_as_rate_limit(self):
        # Blockchair's own custom status code for a temporary IP blacklist
        # from exceeding the free-tier rate limit.
        addr = "1BvBMSEYstWetqTFn5Au4m4GFg7xJaNVN2"
        with patch(
            "tools.wallet_tool.urllib.request.urlopen",
            side_effect=urllib.error.HTTPError("url", 430, "Unknown", {}, None),
        ):
            result = btc_address(addr)
        assert result["ok"] is False
        assert "rate limit" in result["error"]

    def test_network_error_is_reported(self):
        addr = "1BvBMSEYstWetqTFn5Au4m4GFg7xJaNVN2"
        with patch("tools.wallet_tool.urllib.request.urlopen", side_effect=urllib.error.URLError("boom")):
            result = btc_address(addr)
        assert result["ok"] is False
        assert "could not reach blockchair" in result["error"]

    def test_oversized_response_is_rejected(self):
        import tools.wallet_tool as wallet_tool

        addr = "1BvBMSEYstWetqTFn5Au4m4GFg7xJaNVN2"
        oversized = MagicMock()
        oversized.read.return_value = b"x" * (wallet_tool._MAX_RESPONSE_BYTES + 1)
        oversized.__enter__ = lambda s: s
        oversized.__exit__ = MagicMock(return_value=False)

        with patch("tools.wallet_tool.urllib.request.urlopen", return_value=oversized):
            result = btc_address(addr)

        assert result["ok"] is False
        assert "exceeds" in result["error"]


@pytest.mark.skip(reason="live network — run manually")
class TestLiveEthBalance:
    """Live integration test against the real Cloudflare ETH RPC gateway."""

    def test_vitalik_address_has_a_balance(self):
        addr = "0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045"
        try:
            result = eth_balance(addr)
        except Exception:
            pytest.skip("eth rpc endpoint unreachable")
        if not result.get("ok"):
            pytest.skip("eth rpc endpoint unreachable")
        assert result["address"] == addr
        assert result["balance_wei"] >= 0


@pytest.mark.skip(reason="live network — run manually")
class TestLiveBtcAddress:
    """Live integration test against the real Blockchair dashboard API."""

    def test_genesis_address_has_transactions(self):
        addr = "1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa"
        try:
            result = btc_address(addr)
        except Exception:
            pytest.skip("blockchair api unreachable")
        if not result.get("ok"):
            pytest.skip("blockchair api unreachable")
        assert result["address"] == addr
        assert result["tx_count"] >= 1
