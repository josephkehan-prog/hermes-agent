"""Crypto spot prices via the CoinGecko public API (research/market-data support).

Keyless, free JSON API — no vendored code, no API key required:

* ``crypto_price`` queries the ``/simple/price`` endpoint
  (https://api.coingecko.com/api/v3/simple/price) for the current price,
  24h change, and market cap of one or more coins in a given fiat/crypto
  denomination.
* ``crypto_trending`` queries the ``/search/trending`` endpoint
  (https://api.coingecko.com/api/v3/search/trending) for the coins CoinGecko
  currently ranks as most-searched.

The free tier is rate-limited to roughly 30 requests/minute and needs no
API key or account (https://docs.coingecko.com/reference/introduction).

Fixed endpoint, no SSRF guard needed: both functions only ever hit the
hardcoded ``api.coingecko.com`` host baked into this module — there is no
caller-supplied URL or hostname for ``tools._net_guard.reject_private_target``
to validate, unlike ``rss_fetch_tool.py``/``wayback_tool.py`` which fetch
arbitrary caller-given URLs. The only caller-controlled input is the coin id
(and vs-currency) list, which is validated against a strict charset below
before it ever reaches the query string — this is the same posture as
``ip_info_tool.py``/``dns_recon_tool.py``/``cert_transparency_tool.py``. This
module still imports ``tools._net_guard`` for ``MAX_RESPONSE_BYTES`` and
``read_capped`` so the response-size cap stays consistent across tools.
"""

import json
import re
import urllib.error
import urllib.parse
import urllib.request
from typing import Any, Dict, List, Optional, Tuple, Union

from tools import _net_guard
from tools.registry import registry

_USER_AGENT = "hermes-agent-crypto-price-tool/1.0"
_TIMEOUT_S = 15
_BASE_URL = "https://api.coingecko.com/api/v3"
_SIMPLE_PRICE_ENDPOINT = f"{_BASE_URL}/simple/price"
_TRENDING_ENDPOINT = f"{_BASE_URL}/search/trending"
_MAX_RESPONSE_BYTES = _net_guard.MAX_RESPONSE_BYTES
_DEFAULT_VS_CURRENCY = "usd"
_MAX_COIN_IDS = 50

# CoinGecko coin ids are lowercase slugs (e.g. "bitcoin", "usd-coin"). This
# charset rejects anything that could smuggle extra query parameters or
# control characters into the request URL.
_COIN_ID_RE = re.compile(r"^[a-z0-9-]{1,64}$")
# vs-currencies are short lowercase codes, fiat ("usd") or crypto ("btc").
_VS_CURRENCY_RE = re.compile(r"^[a-z0-9]{2,10}$")


def _validate_coin_id(coin_id: Any) -> Optional[str]:
    """Return coin_id lowercased/stripped if it matches the coin-id charset, else None."""
    if not isinstance(coin_id, str):
        return None
    candidate = coin_id.strip().lower()
    return candidate if _COIN_ID_RE.match(candidate) else None


def _normalize_coin_ids(coin_ids: Any) -> Tuple[Optional[List[str]], Optional[str]]:
    """Parse coin_ids (list or comma-separated string) into a validated, deduped list.

    Returns (ids, None) on success, (None, error) if coin_ids is empty,
    contains an id that fails the charset check, or exceeds _MAX_COIN_IDS.
    """
    if isinstance(coin_ids, str):
        raw_ids = coin_ids.split(",")
    elif isinstance(coin_ids, (list, tuple)):
        raw_ids = list(coin_ids)
    else:
        return None, "coin_ids must be a list or comma-separated string"

    if not raw_ids:
        return None, "coin_ids must not be empty"
    if len(raw_ids) > _MAX_COIN_IDS:
        return None, f"too many coin_ids (max {_MAX_COIN_IDS})"

    seen: Dict[str, None] = {}
    for raw_id in raw_ids:
        valid_id = _validate_coin_id(raw_id)
        if valid_id is None:
            return None, f"invalid coin id: {raw_id!r} (must match {_COIN_ID_RE.pattern})"
        seen.setdefault(valid_id, None)

    return list(seen.keys()), None


def _validate_vs_currency(vs: Any) -> Optional[str]:
    """Return vs lowercased/stripped if it matches the currency-code charset, else None."""
    if not isinstance(vs, str):
        return None
    candidate = vs.strip().lower()
    return candidate if _VS_CURRENCY_RE.match(candidate) else None


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


def crypto_price(coin_ids: Union[str, List[str]], vs: Any = _DEFAULT_VS_CURRENCY) -> Dict[str, Any]:
    """Look up current spot price, 24h change, and market cap for one or more coins.

    coin_ids may be a CoinGecko coin id (e.g. "bitcoin", "ethereum",
    "monero") or a list/comma-separated string of several. Returns
    {ok, prices: {id: {price, change_24h, market_cap}}} on success,
    {ok: False, error} on invalid input or request failure. A coin id that
    CoinGecko doesn't recognize is silently omitted by the API, and is
    reported back via `not_found` rather than as a hard error.
    """
    ids, error = _normalize_coin_ids(coin_ids)
    if error is not None:
        return {"ok": False, "error": error}

    valid_vs = _validate_vs_currency(vs)
    if valid_vs is None:
        return {"ok": False, "error": f"invalid vs currency: {vs!r} (must match {_VS_CURRENCY_RE.pattern})"}

    query = urllib.parse.urlencode({
        "ids": ",".join(ids),
        "vs_currencies": valid_vs,
        "include_24hr_change": "true",
        "include_market_cap": "true",
    })
    url = f"{_SIMPLE_PRICE_ENDPOINT}?{query}"

    try:
        data = _get_json(url)
    except _ResponseTooLarge as exc:
        return {"ok": False, "error": str(exc)}
    except urllib.error.HTTPError as exc:
        return {"ok": False, "error": f"http error {exc.code}: {exc.reason}"}
    except urllib.error.URLError as exc:
        return {"ok": False, "error": f"CoinGecko request failed: {exc.reason}"}
    except (json.JSONDecodeError, ValueError) as exc:
        return {"ok": False, "error": f"CoinGecko response was not valid JSON: {exc}"}

    prices: Dict[str, Any] = {}
    not_found: List[str] = []
    for coin_id in ids:
        entry = data.get(coin_id) if isinstance(data, dict) else None
        if not isinstance(entry, dict):
            not_found.append(coin_id)
            continue
        prices[coin_id] = {
            "price": entry.get(valid_vs),
            "change_24h": entry.get(f"{valid_vs}_24h_change"),
            "market_cap": entry.get(f"{valid_vs}_market_cap"),
        }

    result: Dict[str, Any] = {"ok": True, "prices": prices}
    if not_found:
        result["not_found"] = not_found
    return result


def crypto_trending() -> Dict[str, Any]:
    """List coins CoinGecko currently ranks as most-searched/trending.

    Returns {ok, coins: [{id, name, symbol, market_cap_rank}, ...]} on
    success, {ok: False, error} on request failure.
    """
    try:
        data = _get_json(_TRENDING_ENDPOINT)
    except _ResponseTooLarge as exc:
        return {"ok": False, "error": str(exc)}
    except urllib.error.HTTPError as exc:
        return {"ok": False, "error": f"http error {exc.code}: {exc.reason}"}
    except urllib.error.URLError as exc:
        return {"ok": False, "error": f"CoinGecko request failed: {exc.reason}"}
    except (json.JSONDecodeError, ValueError) as exc:
        return {"ok": False, "error": f"CoinGecko response was not valid JSON: {exc}"}

    raw_coins = data.get("coins", []) if isinstance(data, dict) else []
    coins = []
    for entry in raw_coins:
        item = entry.get("item", {}) if isinstance(entry, dict) else {}
        coins.append({
            "id": item.get("id"),
            "name": item.get("name"),
            "symbol": item.get("symbol"),
            "market_cap_rank": item.get("market_cap_rank"),
        })

    return {"ok": True, "coins": coins}


registry.register(
    name="crypto_price",
    toolset="web",
    schema={
        "name": "crypto_price",
        "description": (
            "Look up current spot price, 24h change, and market cap for one "
            "or more cryptocurrencies via CoinGecko (keyless, free tier "
            "~30 req/min). `coin_ids` are CoinGecko coin ids (e.g. "
            "'bitcoin', 'ethereum', 'monero'), given as a list or "
            "comma-separated string. Use `crypto_trending` instead to see "
            "which coins are currently most-searched."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "coin_ids": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "CoinGecko coin ids, e.g. ['bitcoin', 'monero']. A comma-separated string also works.",
                },
                "vs": {
                    "type": "string",
                    "description": f"Denomination currency code, e.g. 'usd', 'eur', 'btc'. Defaults to '{_DEFAULT_VS_CURRENCY}'.",
                },
            },
            "required": ["coin_ids"],
        },
    },
    handler=lambda args, **kw: json.dumps(
        crypto_price(coin_ids=args.get("coin_ids", ""), vs=args.get("vs", _DEFAULT_VS_CURRENCY)),
        ensure_ascii=False,
    ),
    emoji="\U0001FA99",
)

registry.register(
    name="crypto_trending",
    toolset="web",
    schema={
        "name": "crypto_trending",
        "description": (
            "List the coins CoinGecko currently ranks as most-searched/"
            "trending. Keyless, no parameters. Use `crypto_price` to look "
            "up an actual spot price for coins found here."
        ),
        "parameters": {
            "type": "object",
            "properties": {},
        },
    },
    handler=lambda args, **kw: json.dumps(crypto_trending(), ensure_ascii=False),
    emoji="\U0001FA99",
)
