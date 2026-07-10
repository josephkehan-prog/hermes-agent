"""Polymarket prediction-market lookups via the Gamma API (research/market-data support).

Keyless, free JSON API — no vendored code, no API key required:

* ``polymarket_search`` queries the ``/public-search`` endpoint
  (https://gamma-api.polymarket.com/public-search) for events/markets
  matching a text query.
* ``polymarket_trending`` queries the ``/events`` endpoint
  (https://gamma-api.polymarket.com/events) for the highest-volume open
  events, ordered by volume descending.

This is a focused, registry-integrated subset of the full CLI at
``skills/research/polymarket/scripts/polymarket.py`` (Gamma + CLOB, search/
trending/market/event/price/book/history/trades) — that skill stays the
human-facing CLI for the full surface; this tool covers just the two most
common agent-callable lookups. The double-encoded-JSON quirk in Gamma's
``outcomePrices``/``outcomes`` fields (each is itself a JSON *string* that
needs a second ``json.loads``) is handled the same way as that CLI's
``_parse_json_field`` helper — no code is shared between the two, the parsing
logic is just replicated because the quirk is API-shaped, not CLI-shaped.

Fixed endpoint, no SSRF guard needed: both functions only ever hit the
hardcoded ``gamma-api.polymarket.com`` host baked into this module — there is
no caller-supplied URL or hostname for ``tools._net_guard.reject_private_target``
to validate, unlike ``rss_fetch_tool.py``/``wayback_tool.py`` which fetch
arbitrary caller-given URLs. The only caller-controlled input is the search
query (and limit), which is validated against a strict charset/length check
below before it ever reaches the query string — this is the same posture as
``crypto_price_tool.py``/``ip_info_tool.py``/``dns_recon_tool.py``. This
module still imports ``tools._net_guard`` for ``MAX_RESPONSE_BYTES`` and
``read_capped`` so the response-size cap stays consistent across tools.
"""

import json
import urllib.error
import urllib.parse
import urllib.request
from typing import Any, Dict, List, Optional

from tools import _net_guard
from tools.registry import registry

_USER_AGENT = "hermes-agent-polymarket-tool/1.0"
_TIMEOUT_S = 15
_GAMMA_BASE = "https://gamma-api.polymarket.com"
_SEARCH_ENDPOINT = f"{_GAMMA_BASE}/public-search"
_EVENTS_ENDPOINT = f"{_GAMMA_BASE}/events"
_MAX_RESPONSE_BYTES = _net_guard.MAX_RESPONSE_BYTES
_MIN_LIMIT = 1
_MAX_LIMIT = 50
_DEFAULT_LIMIT = 10
_MAX_QUERY_CHARS = 200


def _validate_query(query: Any) -> Optional[str]:
    """Return query stripped if it's a non-empty, control-char-free string
    within _MAX_QUERY_CHARS, else None."""
    if not isinstance(query, str):
        return None
    candidate = query.strip()
    if not candidate or len(candidate) > _MAX_QUERY_CHARS:
        return None
    if any(ord(ch) < 0x20 for ch in candidate):
        return None
    # Defense-in-depth: URL-structural metacharacters never belong in a
    # free-text market search term. urllib.parse.quote already escapes them
    # (inert), but rejecting them outright keeps the query safe even if a
    # future refactor changes the encoding path.
    if any(ch in candidate for ch in "/\\?#&"):
        return None
    return candidate


def _validate_limit(limit: Any) -> int:
    """Clamp limit into [_MIN_LIMIT, _MAX_LIMIT]."""
    try:
        limit_int = int(limit)
    except (TypeError, ValueError):
        limit_int = _DEFAULT_LIMIT
    return max(_MIN_LIMIT, min(_MAX_LIMIT, limit_int))


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


def _parse_json_field(val: Any) -> Any:
    """Parse a Gamma field that's double-encoded JSON (outcomePrices, outcomes).

    Gamma returns these as a JSON *string* (e.g. '["0.42", "0.58"]') rather
    than a native array, so a plain ``market["outcomePrices"]`` is still text
    that needs a second ``json.loads`` to become a usable list. Mirrors
    ``polymarket.py``'s ``_parse_json_field`` — same quirk, independently
    implemented rather than imported (this tool has no dependency on the
    CLI script).
    """
    if isinstance(val, str):
        try:
            return json.loads(val)
        except (json.JSONDecodeError, TypeError):
            return val
    return val


def _market_odds(market: Dict[str, Any]) -> Dict[str, Any]:
    """Build an {outcome_label: price} dict from a market's outcomePrices/outcomes."""
    prices = _parse_json_field(market.get("outcomePrices", "[]"))
    outcomes = _parse_json_field(market.get("outcomes", "[]"))
    odds: Dict[str, Any] = {}
    if not (isinstance(prices, list) and isinstance(outcomes, list)):
        return odds
    for i in range(min(len(prices), len(outcomes))):
        label = outcomes[i]
        try:
            odds[label] = float(prices[i])
        except (TypeError, ValueError):
            odds[label] = prices[i]
    return odds


def _summarize_market(market: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "question": market.get("question", ""),
        "slug": market.get("slug", ""),
        "odds": _market_odds(market),
        "volume": market.get("volume"),
        "end_date": market.get("endDate"),
        "closed": bool(market.get("closed", False)),
    }


def _flatten_markets(events: Any, limit: int) -> List[Dict[str, Any]]:
    """Flatten markets out of a list of Gamma events, capped at limit."""
    markets: List[Dict[str, Any]] = []
    if not isinstance(events, list):
        return markets
    for evt in events:
        if not isinstance(evt, dict):
            continue
        for m in evt.get("markets", []) or []:
            if not isinstance(m, dict):
                continue
            markets.append(_summarize_market(m))
            if len(markets) >= limit:
                return markets
    return markets


def polymarket_search(query: Any, limit: Any = _DEFAULT_LIMIT) -> Dict[str, Any]:
    """Search Polymarket events/markets by text query via Gamma's public-search.

    Returns {ok, markets: [{question, slug, odds, volume, end_date, closed}]}
    on success, {ok: False, error} on invalid input or request failure.
    """
    valid_query = _validate_query(query)
    if valid_query is None:
        return {
            "ok": False,
            "error": f"invalid query: {query!r} (must be non-empty, <= {_MAX_QUERY_CHARS} chars, no control characters)",
        }
    limit_int = _validate_limit(limit)

    url = f"{_SEARCH_ENDPOINT}?q={urllib.parse.quote(valid_query)}"
    try:
        data = _get_json(url)
    except _ResponseTooLarge as exc:
        return {"ok": False, "error": str(exc)}
    except urllib.error.HTTPError as exc:
        return {"ok": False, "error": f"http error {exc.code}: {exc.reason}"}
    except urllib.error.URLError as exc:
        return {"ok": False, "error": f"Polymarket request failed: {exc.reason}"}
    except (json.JSONDecodeError, ValueError) as exc:
        return {"ok": False, "error": f"Polymarket response was not valid JSON: {exc}"}

    events = data.get("events", []) if isinstance(data, dict) else []
    return {"ok": True, "markets": _flatten_markets(events, limit_int)}


def polymarket_trending(limit: Any = _DEFAULT_LIMIT) -> Dict[str, Any]:
    """List the highest-volume open Polymarket markets, ordered by volume descending.

    Returns {ok, markets: [{question, slug, odds, volume, end_date, closed}]}
    on success, {ok: False, error} on request failure.
    """
    limit_int = _validate_limit(limit)

    query = urllib.parse.urlencode({
        "limit": limit_int,
        "active": "true",
        "closed": "false",
        "order": "volume",
        "ascending": "false",
    })
    url = f"{_EVENTS_ENDPOINT}?{query}"
    try:
        data = _get_json(url)
    except _ResponseTooLarge as exc:
        return {"ok": False, "error": str(exc)}
    except urllib.error.HTTPError as exc:
        return {"ok": False, "error": f"http error {exc.code}: {exc.reason}"}
    except urllib.error.URLError as exc:
        return {"ok": False, "error": f"Polymarket request failed: {exc.reason}"}
    except (json.JSONDecodeError, ValueError) as exc:
        return {"ok": False, "error": f"Polymarket response was not valid JSON: {exc}"}

    events = data if isinstance(data, list) else []
    return {"ok": True, "markets": _flatten_markets(events, limit_int)}


registry.register(
    name="polymarket_search",
    toolset="web",
    schema={
        "name": "polymarket_search",
        "description": (
            "Search Polymarket prediction markets by text query (keyless, "
            "Gamma API). Returns up to `limit` markets, each with question, "
            "slug, current odds (outcome -> price), volume, end date, and "
            "closed status. Use `polymarket_trending` instead to see the "
            "current highest-volume open markets without a search query."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Search text, e.g. 'bitcoin' or 'election'."},
                "limit": {
                    "type": "integer",
                    "description": f"Max markets to return ({_MIN_LIMIT}-{_MAX_LIMIT}). Defaults to {_DEFAULT_LIMIT}.",
                },
            },
            "required": ["query"],
        },
    },
    handler=lambda args, **kw: json.dumps(
        polymarket_search(query=args.get("query", ""), limit=args.get("limit", _DEFAULT_LIMIT)),
        ensure_ascii=False,
    ),
    emoji="\U0001F52E",
)

registry.register(
    name="polymarket_trending",
    toolset="web",
    schema={
        "name": "polymarket_trending",
        "description": (
            "List the highest-volume open Polymarket markets (keyless, "
            "Gamma API), ordered by volume descending. Returns up to `limit` "
            "markets, each with question, slug, current odds (outcome -> "
            "price), volume, end date, and closed status. Use "
            "`polymarket_search` instead to look up markets by topic."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "limit": {
                    "type": "integer",
                    "description": f"Max markets to return ({_MIN_LIMIT}-{_MAX_LIMIT}). Defaults to {_DEFAULT_LIMIT}.",
                },
            },
        },
    },
    handler=lambda args, **kw: json.dumps(
        polymarket_trending(limit=args.get("limit", _DEFAULT_LIMIT)),
        ensure_ascii=False,
    ),
    emoji="\U0001F52E",
)
