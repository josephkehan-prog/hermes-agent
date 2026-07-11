"""Read-only public-chain wallet/address lookup (Ethereum + Bitcoin), keyless.

This module NEVER handles private keys, seed phrases, or signing — it only
reads public address balances off public blockchain data via keyless HTTP
APIs, the same data any block explorer or MetaMask-connected dapp can see:

* ``eth_balance`` queries Cloudflare's keyless Ethereum JSON-RPC gateway
  (https://cloudflare-eth.com) via ``eth_getBalance`` — a MetaMask-style
  balance read, no wallet or signing capability involved.
* ``btc_address`` queries Blockchair's keyless dashboard API
  (https://api.blockchair.com) for a Bitcoin address's balance and
  transaction count.

Both validate the address format BEFORE any network call — malformed input
never reaches the network, so there's no way to smuggle a non-address string
into an outbound request.

The Ethereum endpoint is a fixed, hardcoded constant (``_ETH_RPC_ENDPOINT``),
not derived from caller input, so unlike ``rss_fetch_tool``/``wayback_tool``
there is no ``_net_guard.reject_private_target`` call here — that guard
exists to stop a caller-supplied URL from targeting a private/internal
address, and no caller-supplied URL is ever dereferenced by this module.

Monero (XMR) is intentionally NOT supported and never will be: it's a
privacy chain by design, and its addresses do not expose a publicly
queryable balance the way Ethereum/Bitcoin addresses do — no public ledger
scan can recover a balance without the account's private view key. Do not
add an XMR balance function here. If asked for one, the crypto-market skill
documents why it isn't possible without the view key.
"""

import json
import re
import urllib.error
import urllib.request
from typing import Any, Dict, Optional
from urllib.parse import quote

from tools import _net_guard
from tools.registry import registry

_USER_AGENT = "hermes-agent-wallet-tool/1.0"
_TIMEOUT_S = 15
_MAX_RESPONSE_BYTES = _net_guard.MAX_RESPONSE_BYTES

_ETH_RPC_ENDPOINT = "https://cloudflare-eth.com"
_BLOCKCHAIR_ADDRESS_ENDPOINT = "https://api.blockchair.com/bitcoin/dashboards/address/"

_WEI_PER_ETH = 10**18
_SATOSHI_PER_BTC = 10**8

_ETH_ADDRESS_RE = re.compile(r"^0x[0-9a-fA-F]{40}$")
_BTC_BASE58_RE = re.compile(r"^[13][a-km-zA-HJ-NP-Z1-9]{25,34}$")
_BTC_BECH32_RE = re.compile(r"^bc1[a-z0-9]{25,62}$")


def _validate_eth_address(address: Any) -> Optional[str]:
    """Return address stripped if it matches ^0x[0-9a-fA-F]{40}$, else None."""
    if not isinstance(address, str):
        return None
    candidate = address.strip()
    return candidate if _ETH_ADDRESS_RE.match(candidate) else None


def _validate_btc_address(address: Any) -> Optional[str]:
    """Return address stripped if it's a plausible base58 or bech32 BTC
    address, else None."""
    if not isinstance(address, str):
        return None
    candidate = address.strip()
    if _BTC_BASE58_RE.match(candidate) or _BTC_BECH32_RE.match(candidate):
        return candidate
    return None


def eth_balance(address: Any) -> Dict[str, Any]:
    """Look up an Ethereum address's ETH balance via Cloudflare's keyless
    JSON-RPC gateway (``eth_getBalance``, "latest" block).

    Public on-chain data only — a MetaMask-style balance read, no private
    key ever touches this function. The address is validated against
    ``^0x[0-9a-fA-F]{40}$`` before any network call; invalid input never
    reaches the network.

    Returns {ok, address, balance_eth, balance_wei} on success,
    {ok: False, error} on invalid input, network failure, or an RPC error.
    """
    valid_address = _validate_eth_address(address)
    if valid_address is None:
        return {"ok": False, "error": f"invalid ethereum address: {address!r} (expected 0x + 40 hex chars)"}

    payload = json.dumps({
        "jsonrpc": "2.0",
        "method": "eth_getBalance",
        "params": [valid_address, "latest"],
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

    if "error" in data:
        rpc_error = data["error"]
        message = rpc_error.get("message", "unknown rpc error") if isinstance(rpc_error, dict) else str(rpc_error)
        return {"ok": False, "error": f"eth rpc error: {message}"}

    result_hex = data.get("result")
    if not isinstance(result_hex, str):
        return {"ok": False, "error": "eth rpc response missing result field"}

    try:
        balance_wei = int(result_hex, 16)
    except ValueError:
        return {"ok": False, "error": f"eth rpc returned non-hex balance: {result_hex!r}"}

    return {
        "ok": True,
        "address": valid_address,
        "balance_eth": balance_wei / _WEI_PER_ETH,
        "balance_wei": balance_wei,
    }


def btc_address(address: Any) -> Dict[str, Any]:
    """Look up a Bitcoin address's balance and transaction count via
    Blockchair's keyless dashboard API.

    Public on-chain data only. The address is validated against Bitcoin's
    base58 (P2PKH/P2SH) or bech32 (SegWit) formats before any network call;
    invalid input never reaches the network.

    Returns {ok, address, balance_btc, tx_count} on success,
    {ok: False, error} on invalid input, network failure, or an API error
    (including rate limiting).
    """
    valid_address = _validate_btc_address(address)
    if valid_address is None:
        return {"ok": False, "error": f"invalid bitcoin address: {address!r} (expected base58 or bech32 format)"}

    request_url = _BLOCKCHAIR_ADDRESS_ENDPOINT + quote(valid_address, safe="")
    req = urllib.request.Request(request_url, headers={"User-Agent": _USER_AGENT})
    try:
        with urllib.request.urlopen(req, timeout=_TIMEOUT_S) as resp:
            raw = _net_guard.read_capped(resp)
    except _net_guard.NetGuardError:
        return {"ok": False, "error": f"response exceeds {_MAX_RESPONSE_BYTES} byte limit"}
    except urllib.error.HTTPError as exc:
        # Blockchair uses 402 for "no credits"/paid-tier-required and its own
        # custom 430 for a temporary IP blacklist from exceeding the free
        # rate limit; treat 429 (the generic HTTP rate-limit code) the same.
        if exc.code in (402, 429, 430):
            return {"ok": False, "error": f"blockchair rate limit hit (http {exc.code}); try again later"}
        return {"ok": False, "error": f"http error {exc.code}: {exc.reason}"}
    except urllib.error.URLError as exc:
        return {"ok": False, "error": f"could not reach blockchair: {exc.reason}"}
    except (TimeoutError, OSError) as exc:
        return {"ok": False, "error": str(exc)}

    try:
        data = json.loads(raw)
    except (json.JSONDecodeError, ValueError) as exc:
        return {"ok": False, "error": f"blockchair response was not valid JSON: {exc}"}

    context = data.get("context") or {}
    if context.get("error"):
        return {"ok": False, "error": f"blockchair error: {context['error']}"}

    address_data = (data.get("data") or {}).get(valid_address) or {}
    info = address_data.get("address") or {}
    balance_satoshi = info.get("balance")
    if not isinstance(balance_satoshi, (int, float)):
        return {"ok": False, "error": "blockchair response missing or malformed balance data"}

    return {
        "ok": True,
        "address": valid_address,
        "balance_btc": balance_satoshi / _SATOSHI_PER_BTC,
        "tx_count": info.get("transaction_count", 0),
    }


registry.register(
    name="eth_balance",
    toolset="finance",
    schema={
        "name": "eth_balance",
        "description": (
            "Look up an Ethereum address's ETH balance (public on-chain data "
            "only, MetaMask-style read) via Cloudflare's keyless JSON-RPC "
            "gateway. Read-only, keyless, no private key ever involved. "
            "Address must match 0x + 40 hex chars; invalid input is rejected "
            "before any network call."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "address": {
                    "type": "string",
                    "description": "Ethereum address, e.g. '0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045'.",
                },
            },
            "required": ["address"],
        },
    },
    handler=lambda args, **kw: json.dumps(
        eth_balance(address=args.get("address", "")),
        ensure_ascii=False,
    ),
    emoji="💰",
)

registry.register(
    name="btc_address",
    toolset="finance",
    schema={
        "name": "btc_address",
        "description": (
            "Look up a Bitcoin address's balance and transaction count "
            "(public on-chain data only) via Blockchair's keyless dashboard "
            "API. Read-only, keyless, no private key ever involved. Address "
            "must be a valid base58 (P2PKH/P2SH) or bech32 (SegWit) address; "
            "invalid input is rejected before any network call."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "address": {
                    "type": "string",
                    "description": "Bitcoin address, base58 (starts with 1 or 3) or bech32 (starts with bc1).",
                },
            },
            "required": ["address"],
        },
    },
    handler=lambda args, **kw: json.dumps(
        btc_address(address=args.get("address", "")),
        ensure_ascii=False,
    ),
    emoji="💰",
)
