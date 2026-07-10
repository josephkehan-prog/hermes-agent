"""Current Ethereum gas price, keyless, via Cloudflare's public JSON-RPC gateway.

Complements ``wallet_tool.py``'s ``eth_balance`` — same fixed-endpoint
(``https://cloudflare-eth.com``) keyless Ethereum JSON-RPC gateway any
MetaMask-connected dapp can reach, this time reading the network's current
gas price (``eth_gasPrice``) rather than an address balance.

``eth_gas_price`` takes no caller input at all — no parameters, nothing to
validate, nothing to smuggle into the request — so unlike ``rss_fetch_tool``/
``wayback_tool`` there is no ``_net_guard.reject_private_target`` call here:
that guard exists to stop a caller-supplied URL from targeting a private/
internal address, and the endpoint here is a fixed constant, never derived
from caller input.

The RPC response's hex ``result`` field is parsed defensively (isinstance
string guard + ``int(result, 16)`` inside try/except ValueError) rather than
trusted blindly — a malformed or unexpected response should produce a clean
``{"ok": False, "error": ...}`` rather than crash the caller.
"""

import json
import urllib.error
import urllib.request
from typing import Any, Dict

from tools import _net_guard
from tools.registry import registry

_USER_AGENT = "hermes-agent-eth-gas-tool/1.0"
_TIMEOUT_S = 15
_MAX_RESPONSE_BYTES = _net_guard.MAX_RESPONSE_BYTES

_ETH_RPC_ENDPOINT = "https://cloudflare-eth.com"
_WEI_PER_GWEI = 10**9


def eth_gas_price() -> Dict[str, Any]:
    """Look up the current Ethereum gas price via Cloudflare's keyless
    JSON-RPC gateway (``eth_gasPrice``).

    Takes no input — nothing to validate, nothing caller-controlled reaches
    the network. Returns {ok, gas_price_wei, gas_price_gwei} on success,
    {ok: False, error} on network failure, an RPC error, or a malformed
    response.
    """
    payload = json.dumps({
        "jsonrpc": "2.0",
        "method": "eth_gasPrice",
        "params": [],
        "id": 1,
    }).encode("utf-8")

    req = urllib.request.Request(
        _ETH_RPC_ENDPOINT,
        data=payload,
        headers={"User-Agent": _USER_AGENT, "Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=_TIMEOUT_S) as resp:
            raw = _net_guard.read_capped(resp)
    except _net_guard.NetGuardError:
        return {"ok": False, "error": f"response exceeds {_MAX_RESPONSE_BYTES} byte limit"}
    except urllib.error.HTTPError as exc:
        if exc.code == 429:
            return {"ok": False, "error": f"eth rpc rate limit hit (http {exc.code}); try again later"}
        return {"ok": False, "error": f"http error {exc.code}: {exc.reason}"}
    except urllib.error.URLError as exc:
        return {"ok": False, "error": f"could not reach eth rpc endpoint: {exc.reason}"}
    except (TimeoutError, OSError) as exc:
        return {"ok": False, "error": str(exc)}

    try:
        data = json.loads(raw)
    except (json.JSONDecodeError, ValueError) as exc:
        return {"ok": False, "error": f"eth rpc response was not valid JSON: {exc}"}

    if not isinstance(data, dict):
        return {"ok": False, "error": "eth rpc response was not a JSON object"}

    if "error" in data:
        rpc_error = data["error"]
        message = rpc_error.get("message", "unknown rpc error") if isinstance(rpc_error, dict) else str(rpc_error)
        return {"ok": False, "error": f"eth rpc error: {message}"}

    result_hex = data.get("result")
    if not isinstance(result_hex, str):
        return {"ok": False, "error": "eth rpc response missing result field"}

    try:
        gas_price_wei = int(result_hex, 16)
    except ValueError:
        return {"ok": False, "error": f"eth rpc returned non-hex gas price: {result_hex!r}"}

    return {
        "ok": True,
        "gas_price_wei": gas_price_wei,
        "gas_price_gwei": gas_price_wei / _WEI_PER_GWEI,
    }


registry.register(
    name="eth_gas_price",
    toolset="web",
    schema={
        "name": "eth_gas_price",
        "description": (
            "Look up the current Ethereum network gas price via Cloudflare's "
            "keyless JSON-RPC gateway. Read-only, keyless, no input required. "
            "Returns gas price in both wei and gwei."
        ),
        "parameters": {
            "type": "object",
            "properties": {},
            "required": [],
        },
    },
    handler=lambda args, **kw: json.dumps(eth_gas_price(), ensure_ascii=False),
    emoji="⛽",
)
