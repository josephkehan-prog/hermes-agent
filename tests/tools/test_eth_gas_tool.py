"""Tests for the ETH gas price tool (request building, defensive response
parsing, no network except in the opt-in live class)."""

import json
import urllib.error
from unittest.mock import MagicMock, patch

import pytest

from tools.eth_gas_tool import eth_gas_price


def _mock_response(payload) -> MagicMock:
    """Build a urlopen()-context-manager mock returning payload as JSON bytes."""
    mock_response = MagicMock()
    mock_response.read.return_value = json.dumps(payload).encode()
    mock_response.__enter__ = lambda s: s
    mock_response.__exit__ = MagicMock(return_value=False)
    return mock_response


class TestEthGasPriceRequestBuilding:
    def test_wei_to_gwei_conversion(self):
        payload = {"jsonrpc": "2.0", "id": 1, "result": "0x4a817c800"}  # 20e9 wei = 20 gwei
        with patch("tools.eth_gas_tool.urllib.request.urlopen", return_value=_mock_response(payload)) as mock_urlopen:
            result = eth_gas_price()

        req = mock_urlopen.call_args[0][0]
        assert req.full_url == "https://cloudflare-eth.com"
        body = json.loads(req.data.decode())
        assert body["method"] == "eth_gasPrice"
        assert body["params"] == []
        assert req.get_header("User-agent") == "hermes-agent-eth-gas-tool/1.0"

        assert result["ok"] is True
        assert result["gas_price_wei"] == 20 * 10**9
        assert result["gas_price_gwei"] == 20.0

    def test_zero_gas_price(self):
        payload = {"jsonrpc": "2.0", "id": 1, "result": "0x0"}
        with patch("tools.eth_gas_tool.urllib.request.urlopen", return_value=_mock_response(payload)):
            result = eth_gas_price()
        assert result["ok"] is True
        assert result["gas_price_wei"] == 0
        assert result["gas_price_gwei"] == 0.0

    def test_non_string_result_is_reported_gracefully(self):
        payload = {"jsonrpc": "2.0", "id": 1, "result": 12345}
        with patch("tools.eth_gas_tool.urllib.request.urlopen", return_value=_mock_response(payload)):
            result = eth_gas_price()
        assert result["ok"] is False
        assert "missing result field" in result["error"]

    def test_non_hex_string_result_is_reported_gracefully(self):
        payload = {"jsonrpc": "2.0", "id": 1, "result": "not-hex"}
        with patch("tools.eth_gas_tool.urllib.request.urlopen", return_value=_mock_response(payload)):
            result = eth_gas_price()
        assert result["ok"] is False
        assert "non-hex gas price" in result["error"]

    @pytest.mark.parametrize("body", [["error", "boom"], "just-a-string", None, 42])
    def test_non_dict_top_level_response_is_reported_gracefully(self, body):
        # A non-JSON-object RPC body (list/string/null/number, e.g. an upstream
        # error page or MITM) must return a clean error dict, not crash.
        with patch("tools.eth_gas_tool.urllib.request.urlopen", return_value=_mock_response(body)):
            result = eth_gas_price()
        assert result["ok"] is False
        assert "not a JSON object" in result["error"]

    def test_rpc_error_is_reported(self):
        payload = {"jsonrpc": "2.0", "id": 1, "error": {"code": -32603, "message": "internal error"}}
        with patch("tools.eth_gas_tool.urllib.request.urlopen", return_value=_mock_response(payload)):
            result = eth_gas_price()
        assert result["ok"] is False
        assert "internal error" in result["error"]

    def test_rpc_error_as_bare_string_is_reported(self):
        payload = {"jsonrpc": "2.0", "id": 1, "error": "boom"}
        with patch("tools.eth_gas_tool.urllib.request.urlopen", return_value=_mock_response(payload)):
            result = eth_gas_price()
        assert result["ok"] is False
        assert "boom" in result["error"]

    def test_malformed_json_is_reported(self):
        mock_response = MagicMock()
        mock_response.read.return_value = b"not json"
        mock_response.__enter__ = lambda s: s
        mock_response.__exit__ = MagicMock(return_value=False)
        with patch("tools.eth_gas_tool.urllib.request.urlopen", return_value=mock_response):
            result = eth_gas_price()
        assert result["ok"] is False
        assert "not valid JSON" in result["error"]

    def test_rate_limit_is_reported(self):
        with patch(
            "tools.eth_gas_tool.urllib.request.urlopen",
            side_effect=urllib.error.HTTPError("url", 429, "Too Many Requests", {}, None),
        ):
            result = eth_gas_price()
        assert result["ok"] is False
        assert "rate limit" in result["error"]

    def test_network_error_is_reported(self):
        with patch("tools.eth_gas_tool.urllib.request.urlopen", side_effect=urllib.error.URLError("boom")):
            result = eth_gas_price()
        assert result["ok"] is False
        assert "could not reach eth rpc endpoint" in result["error"]

    def test_oversized_response_is_rejected(self):
        import tools.eth_gas_tool as eth_gas_tool

        oversized = MagicMock()
        oversized.read.return_value = b"x" * (eth_gas_tool._MAX_RESPONSE_BYTES + 1)
        oversized.__enter__ = lambda s: s
        oversized.__exit__ = MagicMock(return_value=False)

        with patch("tools.eth_gas_tool.urllib.request.urlopen", return_value=oversized):
            result = eth_gas_price()

        assert result["ok"] is False
        assert "exceeds" in result["error"]


@pytest.mark.skip(reason="live network — run manually")
class TestLiveEthGasPrice:
    """Live integration test against the real Cloudflare ETH RPC gateway."""

    def test_gas_price_is_non_negative(self):
        try:
            result = eth_gas_price()
        except Exception:
            pytest.skip("eth rpc endpoint unreachable")
        if not result.get("ok"):
            pytest.skip("eth rpc endpoint unreachable")
        assert result["gas_price_wei"] >= 0
        assert result["gas_price_gwei"] >= 0.0
