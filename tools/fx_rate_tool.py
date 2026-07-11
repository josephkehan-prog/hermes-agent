"""Foreign-exchange reference rates via Frankfurter (frankfurter.dev, ECB data).

Keyless, free JSON API — no vendored code, no API key required:

* ``fx_rate`` queries the ``/v1/latest`` endpoint
  (https://api.frankfurter.dev/v1/latest) for the current exchange rate of
  one base currency against one or more target currencies (or all of them
  if none are given).
* ``fx_convert`` uses the same endpoint to convert a given amount from one
  currency to another.

Frankfurter tracks the European Central Bank's daily reference rates
(https://www.frankfurter.app/docs/) and updates once per weekday around
16:00 CET. No rate limit is published; the host is keyless and
robots-friendly (``Allow: /``).

Fixed endpoint, no SSRF guard needed: both functions only ever hit the
hardcoded ``api.frankfurter.dev`` host baked into this module — there is no
caller-supplied URL or hostname for ``tools._net_guard.reject_private_target``
to validate, unlike ``rss_fetch_tool.py``/``wayback_tool.py`` which fetch
arbitrary caller-given URLs. The only caller-controlled input is the
currency code(s), which are validated against a strict ISO 4217 charset
below before they ever reach the query string — this is the same posture as
``crypto_price_tool.py``/``ip_info_tool.py``/``dns_recon_tool.py``. This
module still imports ``tools._net_guard`` for ``MAX_RESPONSE_BYTES`` and
``read_capped`` so the response-size cap stays consistent across tools.
"""

import json
import re
import urllib.error
import urllib.parse
import urllib.request
from typing import Any, Dict, List, Optional, Union

from tools import _net_guard
from tools.registry import registry

_USER_AGENT = "hermes-agent-fx-rate-tool/1.0"
_TIMEOUT_S = 15
_LATEST_ENDPOINT = "https://api.frankfurter.dev/v1/latest"
_MAX_RESPONSE_BYTES = _net_guard.MAX_RESPONSE_BYTES
_DEFAULT_BASE = "USD"
_MAX_SYMBOLS = 50

# ISO 4217 currency codes are exactly 3 letters (e.g. "USD", "EUR", "JPY").
# This charset rejects anything that could smuggle extra query parameters or
# control characters into the request URL.
_CURRENCY_RE = re.compile(r"^[A-Za-z]{3}$")


def _validate_currency(code: Any) -> Optional[str]:
    """Return code uppercased/stripped if it matches the ISO 4217 charset, else None."""
    if not isinstance(code, str):
        return None
    candidate = code.strip().upper()
    return candidate if _CURRENCY_RE.match(candidate) else None


def _normalize_symbols(symbols: Any) -> Union[List[str], Dict[str, str]]:
    """Parse symbols (None, list, or comma-separated string) into a validated list.

    Returns the validated list on success, or {"error": ...} on invalid input
    (an unrecognized symbol or too many symbols).
    """
    if symbols is None:
        return []
    if isinstance(symbols, str):
        raw_symbols = [s for s in symbols.split(",") if s.strip()]
    elif isinstance(symbols, (list, tuple)):
        raw_symbols = list(symbols)
    else:
        return {"error": "symbols must be a list or comma-separated string"}

    if len(raw_symbols) > _MAX_SYMBOLS:
        return {"error": f"too many symbols (max {_MAX_SYMBOLS})"}

    valid_symbols: List[str] = []
    for raw_symbol in raw_symbols:
        valid_symbol = _validate_currency(raw_symbol)
        if valid_symbol is None:
            return {"error": f"invalid currency code: {raw_symbol!r} (must match {_CURRENCY_RE.pattern})"}
        valid_symbols.append(valid_symbol)

    return valid_symbols


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


def fx_rate(base: Any = _DEFAULT_BASE, symbols: Any = None) -> Dict[str, Any]:
    """Look up the current ECB reference rate of base against one or more currencies.

    base is an ISO 4217 currency code (e.g. "USD"). symbols may be a
    currency code, a list/comma-separated string of several, or None for
    all currencies Frankfurter tracks. Returns
    {ok, base, date, rates: {CCY: rate}} on success, {ok: False, error} on
    invalid input or request failure.
    """
    valid_base = _validate_currency(base)
    if valid_base is None:
        return {"ok": False, "error": f"invalid base currency: {base!r} (must match {_CURRENCY_RE.pattern})"}

    valid_symbols = _normalize_symbols(symbols)
    if isinstance(valid_symbols, dict):
        return {"ok": False, "error": valid_symbols["error"]}

    params = {"base": valid_base}
    if valid_symbols:
        params["symbols"] = ",".join(valid_symbols)
    query = urllib.parse.urlencode(params)
    url = f"{_LATEST_ENDPOINT}?{query}"

    try:
        data = _get_json(url)
    except _ResponseTooLarge as exc:
        return {"ok": False, "error": str(exc)}
    except urllib.error.HTTPError as exc:
        return {"ok": False, "error": f"http error {exc.code}: {exc.reason}"}
    except urllib.error.URLError as exc:
        return {"ok": False, "error": f"Frankfurter request failed: {exc.reason}"}
    except (json.JSONDecodeError, ValueError) as exc:
        return {"ok": False, "error": f"Frankfurter response was not valid JSON: {exc}"}

    if not isinstance(data, dict):
        return {"ok": False, "error": "Frankfurter response was not a JSON object"}

    raw_rates = data.get("rates")
    rates: Dict[str, float] = {}
    if isinstance(raw_rates, dict):
        for ccy, value in raw_rates.items():
            if isinstance(ccy, str) and isinstance(value, (int, float)) and not isinstance(value, bool):
                rates[ccy] = value

    return {
        "ok": True,
        "base": data.get("base", valid_base),
        "date": data.get("date"),
        "rates": rates,
    }


def fx_convert(amount: Any, base: Any, to: Any) -> Dict[str, Any]:
    """Convert amount from base currency to to currency at the current ECB reference rate.

    amount must be a non-negative number. base and to are ISO 4217 currency
    codes. Returns {ok, amount, base, to, rate, result, date} on success,
    {ok: False, error} on invalid input, an unrecognized currency, or
    request failure.
    """
    if not isinstance(amount, (int, float)) or isinstance(amount, bool):
        return {"ok": False, "error": f"amount must be a number, got {amount!r}"}
    if amount < 0:
        return {"ok": False, "error": f"amount must be >= 0, got {amount!r}"}

    valid_to = _validate_currency(to)
    if valid_to is None:
        return {"ok": False, "error": f"invalid target currency: {to!r} (must match {_CURRENCY_RE.pattern})"}

    rate_result = fx_rate(base=base, symbols=[valid_to])
    if not rate_result["ok"]:
        return rate_result

    rate = rate_result["rates"].get(valid_to)
    if rate is None:
        return {"ok": False, "error": f"no rate available for {valid_to!r} against {rate_result['base']!r}"}

    return {
        "ok": True,
        "amount": amount,
        "base": rate_result["base"],
        "to": valid_to,
        "rate": rate,
        "result": amount * rate,
        "date": rate_result["date"],
    }


registry.register(
    name="fx_rate",
    toolset="finance",
    schema={
        "name": "fx_rate",
        "description": (
            "Look up current foreign-exchange reference rates via "
            "Frankfurter (keyless, ECB daily reference rates). `base` is an "
            "ISO 4217 currency code (e.g. 'USD'), `symbols` are the target "
            "currency codes to report (list or comma-separated string; "
            "omit for all tracked currencies). Use `fx_convert` instead to "
            "convert a specific amount."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "base": {
                    "type": "string",
                    "description": f"Base currency ISO 4217 code, e.g. 'USD'. Defaults to '{_DEFAULT_BASE}'.",
                },
                "symbols": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Target currency ISO 4217 codes, e.g. ['EUR', 'GBP']. A comma-separated string also works. Omit for all currencies.",
                },
            },
        },
    },
    handler=lambda args, **kw: json.dumps(
        fx_rate(base=args.get("base", _DEFAULT_BASE), symbols=args.get("symbols")),
        ensure_ascii=False,
    ),
    emoji="\U0001F4B1",
)

registry.register(
    name="fx_convert",
    toolset="finance",
    schema={
        "name": "fx_convert",
        "description": (
            "Convert an amount from one currency to another at the current "
            "ECB reference rate via Frankfurter (keyless). `base` and `to` "
            "are ISO 4217 currency codes (e.g. 'USD', 'EUR')."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "amount": {
                    "type": "number",
                    "description": "Amount to convert, in the base currency. Must be >= 0.",
                },
                "base": {
                    "type": "string",
                    "description": "Source currency ISO 4217 code, e.g. 'USD'.",
                },
                "to": {
                    "type": "string",
                    "description": "Target currency ISO 4217 code, e.g. 'EUR'.",
                },
            },
            "required": ["amount", "base", "to"],
        },
    },
    handler=lambda args, **kw: json.dumps(
        fx_convert(amount=args.get("amount"), base=args.get("base", _DEFAULT_BASE), to=args.get("to")),
        ensure_ascii=False,
    ),
    emoji="\U0001F4B1",
)
