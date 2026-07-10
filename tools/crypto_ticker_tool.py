"""Real-time crypto spot prices via exchange public tickers (complements
``crypto_price_tool``'s CoinGecko aggregate with a live exchange quote).

Keyless, free public JSON APIs — no vendored code, no API key required:

* ``ticker`` queries a single exchange's public ticker endpoint for the
  current spot price of a trading pair symbol (e.g. ``BTCUSDT`` on Binance,
  ``XBTUSD`` on Kraken).
* ``ticker_bulk`` looks up several symbols on the same exchange, isolating
  each lookup so one bad/unknown symbol doesn't abort the batch.

Only two exchanges are supported, both allowlisted by name — ``binance``
(https://api.binance.com/api/v3/ticker/price) and ``kraken``
(https://api.kraken.com/0/public/Ticker). There is no caller-supplied
exchange host, only a caller-supplied symbol, which is validated against a
strict uppercase-alnum charset before it ever reaches the query string —
this is the same posture as ``crypto_price_tool.py``/``ip_info_tool.py``/
``dns_recon_tool.py``. Fixed-endpoint, no SSRF guard needed: both exchange
hosts are hardcoded, so ``tools._net_guard.reject_private_target`` (for
caller-supplied hostnames) doesn't apply here. This module still imports
``tools._net_guard`` for ``MAX_RESPONSE_BYTES`` and ``read_capped`` so the
response-size cap stays consistent across tools.

Response parsing is defensively isinstance-guarded at every step: Binance
and Kraken return very different (and occasionally error-shaped) JSON
bodies, and a malformed or unexpected shape must produce a clean error
dict rather than crash the caller (the lesson from earlier crypto-tool
work — never trust an external API's shape, even a well-known one).
"""

import json
import re
import urllib.error
import urllib.parse
import urllib.request
from typing import Any, Dict, List, Optional, Tuple, Union

from tools import _net_guard
from tools.registry import registry

_USER_AGENT = "hermes-agent-crypto-ticker-tool/1.0"
_TIMEOUT_S = 15
_MAX_RESPONSE_BYTES = _net_guard.MAX_RESPONSE_BYTES
_MAX_BULK = 50

_BINANCE_TICKER_ENDPOINT = "https://api.binance.com/api/v3/ticker/price"
_KRAKEN_TICKER_ENDPOINT = "https://api.kraken.com/0/public/Ticker"

_EXCHANGES = {"binance", "kraken"}
_DEFAULT_EXCHANGE = "binance"

# Trading pair symbols across both exchanges are uppercase alphanumerics
# (e.g. "BTCUSDT", "XBTUSD") — this charset rejects anything that could
# smuggle extra query parameters or control characters into the request URL.
_SYMBOL_RE = re.compile(r"^[A-Z0-9]{2,20}$")


def _validate_symbol(symbol: Any) -> Optional[str]:
    """Return symbol uppercased/stripped if it matches the symbol charset, else None."""
    if not isinstance(symbol, str):
        return None
    candidate = symbol.strip().upper()
    return candidate if _SYMBOL_RE.match(candidate) else None


def _validate_exchange(exchange: Any) -> Optional[str]:
    """Return exchange lowercased/stripped if it's in the allowlist, else None."""
    if not isinstance(exchange, str):
        return None
    candidate = exchange.strip().lower()
    return candidate if candidate in _EXCHANGES else None


def _normalize_symbols(symbols: Any) -> Tuple[Optional[List[str]], Optional[str]]:
    """Parse symbols (list or comma-separated string) into a raw, non-empty, capped list.

    Returns (raw_symbols, None) on success, (None, error) if symbols is
    empty, the wrong type, or exceeds _MAX_BULK. Per-symbol charset
    validation happens later in ``ticker`` — this only bounds the batch.
    """
    if isinstance(symbols, str):
        raw_symbols = symbols.split(",")
    elif isinstance(symbols, (list, tuple)):
        raw_symbols = list(symbols)
    else:
        return None, "symbols must be a list or comma-separated string"

    if not raw_symbols:
        return None, "symbols must not be empty"
    if len(raw_symbols) > _MAX_BULK:
        return None, f"too many symbols (max {_MAX_BULK})"

    return raw_symbols, None


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


def _fetch_json(url: str, exchange_label: str) -> Tuple[Optional[Any], Optional[str]]:
    """Shared fetch + error-translation for both exchanges.

    Returns (data, None) on success, (None, error) on any request failure.
    A Binance 451 (geoblocked) is called out explicitly since it's a known,
    non-transient response some callers will hit depending on source IP.
    """
    try:
        return _get_json(url), None
    except _ResponseTooLarge as exc:
        return None, str(exc)
    except urllib.error.HTTPError as exc:
        if exc.code == 451:
            return None, f"{exchange_label} request blocked (451 unavailable for legal reasons, likely geoblocked): {exc.reason}"
        return None, f"http error {exc.code}: {exc.reason}"
    except urllib.error.URLError as exc:
        return None, f"{exchange_label} request failed: {exc.reason}"
    except (json.JSONDecodeError, ValueError) as exc:
        return None, f"{exchange_label} response was not valid JSON: {exc}"


def _binance_price(symbol: str) -> Dict[str, Any]:
    """Look up symbol's price via Binance's ticker/price endpoint.

    Returns {ok: True, price} or {ok: False, error}. Every field access on
    the parsed body is isinstance-guarded — Binance returns
    {"symbol": ..., "price": "..."} on success but
    {"code": ..., "msg": ...} on an unknown symbol or other API error.
    """
    query = urllib.parse.urlencode({"symbol": symbol})
    url = f"{_BINANCE_TICKER_ENDPOINT}?{query}"
    data, error = _fetch_json(url, "binance")
    if error is not None:
        return {"ok": False, "error": error}

    if not isinstance(data, dict):
        return {"ok": False, "error": "unexpected binance response shape"}
    if "code" in data and "msg" in data:
        return {"ok": False, "error": f"binance error {data.get('code')}: {data.get('msg')}"}

    price_raw = data.get("price")
    if not isinstance(price_raw, (str, int, float)):
        return {"ok": False, "error": "binance response missing price"}
    try:
        price = float(price_raw)
    except (TypeError, ValueError):
        return {"ok": False, "error": "binance response price was not numeric"}

    return {"ok": True, "price": price}


def _kraken_price(symbol: str) -> Dict[str, Any]:
    """Look up symbol's price via Kraken's public Ticker endpoint.

    Returns {ok: True, price} or {ok: False, error}. Kraken often renames
    the requested pair in its result (e.g. "XBTUSD" -> "XXBTZUSD"), so the
    first (and normally only) entry in `result` is used rather than an
    exact key match. Every field access is isinstance-guarded — Kraken
    reports errors via a top-level "error" list rather than an HTTP status.
    """
    query = urllib.parse.urlencode({"pair": symbol})
    url = f"{_KRAKEN_TICKER_ENDPOINT}?{query}"
    data, error = _fetch_json(url, "kraken")
    if error is not None:
        return {"ok": False, "error": error}

    if not isinstance(data, dict):
        return {"ok": False, "error": "unexpected kraken response shape"}

    errors = data.get("error")
    if isinstance(errors, list) and errors:
        return {"ok": False, "error": f"kraken error: {'; '.join(str(e) for e in errors)}"}

    result = data.get("result")
    if not isinstance(result, dict) or not result:
        return {"ok": False, "error": "kraken response missing result"}

    _pair_key, pair_data = next(iter(result.items()))
    if not isinstance(pair_data, dict):
        return {"ok": False, "error": "unexpected kraken pair data shape"}

    close = pair_data.get("c")
    if not isinstance(close, list) or not close:
        return {"ok": False, "error": "kraken response missing close price"}
    try:
        price = float(close[0])
    except (TypeError, ValueError):
        return {"ok": False, "error": "kraken response price was not numeric"}

    return {"ok": True, "price": price}


def ticker(symbol: Any, exchange: Any = _DEFAULT_EXCHANGE) -> Dict[str, Any]:
    """Look up the current spot price of symbol on exchange.

    symbol is a trading pair like "BTCUSDT" (Binance) or "XBTUSD" (Kraken),
    validated against an uppercase-alnum charset before any request is
    made. exchange must be one of "binance" (default) or "kraken". Returns
    {ok, symbol, exchange, price} on success, {ok: False, error} on invalid
    input, and {ok: False, symbol, exchange, error} on a request failure
    (unknown symbol, geoblock, network error, etc).
    """
    valid_symbol = _validate_symbol(symbol)
    if valid_symbol is None:
        return {"ok": False, "error": f"invalid symbol: {symbol!r} (must match {_SYMBOL_RE.pattern})"}

    valid_exchange = _validate_exchange(exchange)
    if valid_exchange is None:
        return {"ok": False, "error": f"invalid exchange: {exchange!r} (must be one of {sorted(_EXCHANGES)})"}

    outcome = _binance_price(valid_symbol) if valid_exchange == "binance" else _kraken_price(valid_symbol)

    result: Dict[str, Any] = {"ok": outcome["ok"], "symbol": valid_symbol, "exchange": valid_exchange}
    if outcome["ok"]:
        result["price"] = outcome["price"]
    else:
        result["error"] = outcome["error"]
    return result


def ticker_bulk(symbols: Union[str, List[str]], exchange: Any = _DEFAULT_EXCHANGE) -> Dict[str, Any]:
    """Look up spot prices for several symbols on the same exchange.

    symbols may be a list or comma-separated string, capped at
    _MAX_BULK entries. Each symbol is looked up independently via `ticker`
    so one invalid or unknown symbol doesn't abort the rest of the batch.
    Returns {ok: True, exchange, tickers: {symbol: <ticker() result>}} on
    success, {ok: False, error} if symbols/exchange themselves are invalid.
    """
    raw_symbols, error = _normalize_symbols(symbols)
    if error is not None:
        return {"ok": False, "error": error}

    valid_exchange = _validate_exchange(exchange)
    if valid_exchange is None:
        return {"ok": False, "error": f"invalid exchange: {exchange!r} (must be one of {sorted(_EXCHANGES)})"}

    tickers: Dict[str, Any] = {}
    for raw_symbol in raw_symbols:
        outcome = ticker(raw_symbol, exchange=valid_exchange)
        key = raw_symbol.strip().upper() if isinstance(raw_symbol, str) else str(raw_symbol)
        tickers[key] = outcome

    return {"ok": True, "exchange": valid_exchange, "tickers": tickers}


registry.register(
    name="crypto_ticker",
    toolset="web",
    schema={
        "name": "crypto_ticker",
        "description": (
            "Look up the current live spot price of a trading pair symbol "
            "directly from an exchange's public ticker (keyless). "
            "`symbol` is the exchange's own pair format, e.g. 'BTCUSDT' on "
            "Binance or 'XBTUSD' on Kraken. `exchange` is 'binance' "
            "(default) or 'kraken'. Complements `crypto_price` (CoinGecko "
            "aggregate) when a live exchange quote is needed instead."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "symbol": {
                    "type": "string",
                    "description": "Exchange trading pair symbol, e.g. 'BTCUSDT' (Binance) or 'XBTUSD' (Kraken).",
                },
                "exchange": {
                    "type": "string",
                    "description": f"Exchange to query: 'binance' or 'kraken'. Defaults to '{_DEFAULT_EXCHANGE}'.",
                },
            },
            "required": ["symbol"],
        },
    },
    handler=lambda args, **kw: json.dumps(
        ticker(symbol=args.get("symbol", ""), exchange=args.get("exchange", _DEFAULT_EXCHANGE)),
        ensure_ascii=False,
    ),
    emoji="\U0001FA99",
)

registry.register(
    name="crypto_ticker_bulk",
    toolset="web",
    schema={
        "name": "crypto_ticker_bulk",
        "description": (
            "Look up live spot prices for several trading pair symbols on "
            "the same exchange in one call (keyless, max "
            f"{_MAX_BULK} symbols). Each symbol is resolved independently, "
            "so one unknown/invalid symbol doesn't fail the whole batch. "
            "See `crypto_ticker` for the single-symbol version."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "symbols": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Exchange trading pair symbols, e.g. ['BTCUSDT', 'ETHUSDT']. A comma-separated string also works.",
                },
                "exchange": {
                    "type": "string",
                    "description": f"Exchange to query: 'binance' or 'kraken'. Defaults to '{_DEFAULT_EXCHANGE}'.",
                },
            },
            "required": ["symbols"],
        },
    },
    handler=lambda args, **kw: json.dumps(
        ticker_bulk(symbols=args.get("symbols", ""), exchange=args.get("exchange", _DEFAULT_EXCHANGE)),
        ensure_ascii=False,
    ),
    emoji="\U0001FA99",
)
