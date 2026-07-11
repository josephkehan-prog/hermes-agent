"""Polymarket CLOB order-book depth (research/market-data support).

Keyless, free JSON API — no vendored code, no API key required:

* ``polymarket_orderbook`` queries the ``/book`` endpoint
  (https://clob.polymarket.com/book) for a token's full bid/ask depth, and
  derives best_bid/best_ask/spread from the parsed levels.
* ``polymarket_midpoint`` queries the ``/midpoint`` endpoint
  (https://clob.polymarket.com/midpoint); if that response is unusable it
  falls back to computing the mid from ``polymarket_orderbook``'s best_bid/
  best_ask so a caller still gets an answer when the dedicated endpoint is
  flaky or shaped unexpectedly.

This complements ``polymarket_tool.py`` (Gamma market search/trending) with
the CLOB side of the same skill's CLI (``skills/research/polymarket/scripts/
polymarket.py``'s ``cmd_book``/``cmd_price``) — no code is shared between the
two, the endpoint shape is just replicated because it's API-shaped, not
CLI-shaped.

Fixed endpoint, no SSRF guard needed: both functions only ever hit the
hardcoded ``clob.polymarket.com`` host baked into this module — there is no
caller-supplied URL or hostname for ``tools._net_guard.reject_private_target``
to validate, unlike ``rss_fetch_tool.py``/``wayback_tool.py`` which fetch
arbitrary caller-given URLs. The only caller-controlled input is ``token_id``,
which is validated against a strict decimal/hex allowlist below before it
ever reaches the query string — this is the same posture as
``polymarket_tool.py``/``crypto_price_tool.py``/``ip_info_tool.py``. This
module still imports ``tools._net_guard`` for ``MAX_RESPONSE_BYTES`` and
``read_capped`` so the response-size cap stays consistent across tools.

CLOB book responses are parsed defensively: ``bids``/``asks`` are guarded as
lists, each level is guarded as a dict, and ``price``/``size`` are guarded as
coercible-to-float before use — an unexpected shape (missing field, null,
nested object) degrades to skipping that level rather than crashing the tool
call (crypto_price_tool.py lesson).
"""

import json
import re
import urllib.error
import urllib.request
from typing import Any, Dict, List, Optional, Tuple

from tools import _net_guard
from tools.registry import registry

_USER_AGENT = "hermes-agent-polymarket-orderbook-tool/1.0"
_TIMEOUT_S = 15
_CLOB_BASE = "https://clob.polymarket.com"
_BOOK_ENDPOINT = f"{_CLOB_BASE}/book"
_MIDPOINT_ENDPOINT = f"{_CLOB_BASE}/midpoint"
_MAX_RESPONSE_BYTES = _net_guard.MAX_RESPONSE_BYTES
_MAX_TOKEN_ID_CHARS = 100

# CLOB token IDs are big decimal strings; an optional 0x-prefixed hex form is
# accepted too (matches polymarket.py's validate_id posture) since some CLOB
# responses/tools surface ids either way. Anything else — including the
# obvious injection attempts (query strings, path traversal, whitespace) — is
# rejected before it ever reaches the request URL.
_TOKEN_ID_RE = re.compile(r"^(0x[0-9a-fA-F]+|[0-9]+)$")


def _validate_token_id(token_id: Any) -> Optional[str]:
    """Return token_id if it's a non-empty decimal or 0x-hex string within
    _MAX_TOKEN_ID_CHARS, else None."""
    if not isinstance(token_id, str):
        return None
    candidate = token_id.strip()
    if not candidate or len(candidate) > _MAX_TOKEN_ID_CHARS:
        return None
    if not _TOKEN_ID_RE.match(candidate):
        return None
    return candidate


class _ResponseTooLarge(Exception):
    """Raised by _get_json when a response body exceeds _MAX_RESPONSE_BYTES."""


def _get_json(url: str) -> Any:
    """GET url with an honest UA and a bounded timeout, decode JSON.

    Raises _ResponseTooLarge instead of buffering an unbounded body.
    """
    req = urllib.request.Request(url, headers={"User-Agent": _USER_AGENT, "Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=_TIMEOUT_S) as resp:
        try:
            raw = _net_guard.read_capped(resp)
        except _net_guard.NetGuardError as exc:
            raise _ResponseTooLarge(str(exc)) from exc
    return json.loads(raw)


def _to_float(val: Any) -> Optional[float]:
    """Coerce val to float, returning None instead of raising on failure."""
    try:
        return float(val)
    except (TypeError, ValueError):
        return None


def _parse_levels(raw_levels: Any) -> List[Dict[str, float]]:
    """Defensively parse a CLOB book's bids/asks array into [{price, size}].

    Guards against every shape the API could hand back other than the
    documented one: a non-list top level, non-dict entries, and
    missing/non-numeric price or size fields are all skipped rather than
    raised, so one malformed level never takes down the whole parse.
    """
    levels: List[Dict[str, float]] = []
    if not isinstance(raw_levels, list):
        return levels
    for entry in raw_levels:
        if not isinstance(entry, dict):
            continue
        price = _to_float(entry.get("price"))
        size = _to_float(entry.get("size"))
        if price is None or size is None:
            continue
        levels.append({"price": price, "size": size})
    return levels


def _best_bid_ask(bids: List[Dict[str, float]], asks: List[Dict[str, float]]) -> Tuple[Optional[float], Optional[float]]:
    """Return (best_bid, best_ask): highest bid price, lowest ask price."""
    best_bid = max((lvl["price"] for lvl in bids), default=None)
    best_ask = min((lvl["price"] for lvl in asks), default=None)
    return best_bid, best_ask


def polymarket_orderbook(token_id: Any) -> Dict[str, Any]:
    """Fetch full CLOB order-book depth for a Polymarket outcome token.

    Returns {ok, token_id, bids: [{price, size}], asks: [{price, size}],
    best_bid, best_ask, spread} on success (best_bid/best_ask/spread are
    None when that side of the book is empty), {ok: False, error} on
    invalid input or request failure.
    """
    valid_token_id = _validate_token_id(token_id)
    if valid_token_id is None:
        return {
            "ok": False,
            "error": f"invalid token_id: {token_id!r} (expected a decimal or 0x-hex identifier)",
        }

    url = f"{_BOOK_ENDPOINT}?token_id={valid_token_id}"
    try:
        data = _get_json(url)
    except _ResponseTooLarge as exc:
        return {"ok": False, "error": str(exc)}
    except urllib.error.HTTPError as exc:
        return {"ok": False, "error": f"http error {exc.code}: {exc.reason}"}
    except urllib.error.URLError as exc:
        return {"ok": False, "error": f"Polymarket CLOB request failed: {exc.reason}"}
    except (json.JSONDecodeError, ValueError) as exc:
        return {"ok": False, "error": f"Polymarket CLOB response was not valid JSON: {exc}"}

    if not isinstance(data, dict):
        return {"ok": False, "error": "Polymarket CLOB response was not a JSON object"}

    bids = _parse_levels(data.get("bids"))
    asks = _parse_levels(data.get("asks"))
    best_bid, best_ask = _best_bid_ask(bids, asks)
    spread = (best_ask - best_bid) if (best_bid is not None and best_ask is not None) else None

    return {
        "ok": True,
        "token_id": valid_token_id,
        "bids": bids,
        "asks": asks,
        "best_bid": best_bid,
        "best_ask": best_ask,
        "spread": spread,
    }


def polymarket_midpoint(token_id: Any) -> Dict[str, Any]:
    """Fetch the midpoint price for a Polymarket outcome token.

    Tries the dedicated CLOB /midpoint endpoint first; if that response is
    missing/non-numeric, falls back to computing mid = (best_bid + best_ask)
    / 2 from ``polymarket_orderbook``. Returns {ok, token_id, mid} on
    success, {ok: False, error} on invalid input or when neither source
    yields a usable mid.
    """
    valid_token_id = _validate_token_id(token_id)
    if valid_token_id is None:
        return {
            "ok": False,
            "error": f"invalid token_id: {token_id!r} (expected a decimal or 0x-hex identifier)",
        }

    url = f"{_MIDPOINT_ENDPOINT}?token_id={valid_token_id}"
    try:
        data = _get_json(url)
    except _ResponseTooLarge as exc:
        return {"ok": False, "error": str(exc)}
    except urllib.error.HTTPError as exc:
        return {"ok": False, "error": f"http error {exc.code}: {exc.reason}"}
    except urllib.error.URLError as exc:
        return {"ok": False, "error": f"Polymarket CLOB request failed: {exc.reason}"}
    except (json.JSONDecodeError, ValueError) as exc:
        return {"ok": False, "error": f"Polymarket CLOB response was not valid JSON: {exc}"}

    mid = _to_float(data.get("mid")) if isinstance(data, dict) else None
    if mid is not None:
        return {"ok": True, "token_id": valid_token_id, "mid": mid}

    # /midpoint didn't give us a usable value — fall back to the order book.
    book = polymarket_orderbook(valid_token_id)
    if not book.get("ok"):
        return {"ok": False, "error": book.get("error", "could not determine midpoint")}
    best_bid, best_ask = book.get("best_bid"), book.get("best_ask")
    if best_bid is None or best_ask is None:
        return {"ok": False, "error": "midpoint unavailable: order book has no bid/ask on one or both sides"}
    return {"ok": True, "token_id": valid_token_id, "mid": (best_bid + best_ask) / 2}


registry.register(
    name="polymarket_orderbook",
    toolset="finance",
    schema={
        "name": "polymarket_orderbook",
        "description": (
            "Fetch full CLOB order-book depth for a Polymarket outcome token "
            "(keyless). Returns bids/asks as [{price, size}] lists plus "
            "best_bid, best_ask, and spread. Use `polymarket_search`/"
            "`polymarket_trending` first to find a market's token id."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "token_id": {
                    "type": "string",
                    "description": "CLOB outcome token id (decimal or 0x-hex string).",
                },
            },
            "required": ["token_id"],
        },
    },
    handler=lambda args, **kw: json.dumps(
        polymarket_orderbook(token_id=args.get("token_id", "")),
        ensure_ascii=False,
    ),
    emoji="\U0001F4D6",
)

registry.register(
    name="polymarket_midpoint",
    toolset="finance",
    schema={
        "name": "polymarket_midpoint",
        "description": (
            "Fetch the midpoint price for a Polymarket outcome token "
            "(keyless). Falls back to computing the mid from the order book "
            "if the dedicated midpoint endpoint doesn't return a usable "
            "value. Use `polymarket_search`/`polymarket_trending` first to "
            "find a market's token id."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "token_id": {
                    "type": "string",
                    "description": "CLOB outcome token id (decimal or 0x-hex string).",
                },
            },
            "required": ["token_id"],
        },
    },
    handler=lambda args, **kw: json.dumps(
        polymarket_midpoint(token_id=args.get("token_id", "")),
        ensure_ascii=False,
    ),
    emoji="\U0001F4D6",
)
