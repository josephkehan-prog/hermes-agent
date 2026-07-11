"""Crypto Fear & Greed Index via the alternative.me public API (research/
market-sentiment support).

Keyless, free JSON API — no vendored code, no API key required:

* ``fear_greed`` queries the ``/fng/`` endpoint
  (https://api.alternative.me/fng/) for the current index value (0-100,
  "Extreme Fear" to "Extreme Greed") and, when ``limit`` > 1, the trailing
  history of daily values.

No official rate limit is published; alternative.me asks that it not be
hammered (https://alternative.me/crypto/fear-and-greed-index/).

Fixed endpoint, no SSRF guard needed: ``fear_greed`` only ever hits the
hardcoded ``api.alternative.me`` host baked into this module — there is no
caller-supplied URL or hostname for ``tools._net_guard.reject_private_target``
to validate, unlike ``rss_fetch_tool.py``/``wayback_tool.py`` which fetch
arbitrary caller-given URLs. The only caller-controlled input is ``limit``,
which is int-clamped before it ever reaches the query string — same posture
as ``crypto_price_tool.py``. This module still imports ``tools._net_guard``
for ``MAX_RESPONSE_BYTES`` and ``read_capped`` so the response-size cap stays
consistent across tools.
"""

import json
import urllib.error
import urllib.parse
import urllib.request
from typing import Any, Dict, List, Optional

from tools import _net_guard
from tools.registry import registry

_USER_AGENT = "hermes-agent-fear-greed-tool/1.0"
_TIMEOUT_S = 15
_FNG_ENDPOINT = "https://api.alternative.me/fng/"
_MAX_RESPONSE_BYTES = _net_guard.MAX_RESPONSE_BYTES
_MIN_LIMIT = 1
_MAX_LIMIT = 100
_DEFAULT_LIMIT = 1


def _validate_limit(limit: Any) -> int:
    """Clamp limit into [_MIN_LIMIT, _MAX_LIMIT]."""
    try:
        limit_int = int(limit)
    except (TypeError, ValueError):
        limit_int = _DEFAULT_LIMIT
    return max(_MIN_LIMIT, min(_MAX_LIMIT, limit_int))


def _classify_value(value: int) -> str:
    """Map a 0-100 index value to its classification bucket.

    alternative.me doesn't document its bucket boundaries formally, but this
    breakdown matches the labels observed in its own responses and is used
    as a defensive fallback for entries where ``value_classification`` is
    missing or blank.
    """
    if value <= 24:
        return "Extreme Fear"
    if value <= 44:
        return "Fear"
    if value <= 55:
        return "Neutral"
    if value <= 75:
        return "Greed"
    return "Extreme Greed"


def _parse_entry(raw: Any) -> Optional[Dict[str, Any]]:
    """Parse one raw {value, value_classification, timestamp} dict into
    {value: int, classification: str, timestamp}, or None if unparseable."""
    if not isinstance(raw, dict):
        return None
    try:
        value = int(raw.get("value"))
    except (TypeError, ValueError):
        return None

    classification = raw.get("value_classification")
    if not isinstance(classification, str) or not classification.strip():
        classification = _classify_value(value)

    return {
        "value": value,
        "classification": classification,
        "timestamp": raw.get("timestamp"),
    }


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


def fear_greed(limit: Any = _DEFAULT_LIMIT) -> Dict[str, Any]:
    """Look up the current Crypto Fear & Greed Index value, plus history when
    limit > 1.

    Returns {ok, current: {value, classification, timestamp}, history: [...]}
    on success (``history`` only included when limit > 1), {ok: False, error}
    on request failure or a malformed response.
    """
    limit_int = _validate_limit(limit)
    query = urllib.parse.urlencode({"limit": str(limit_int)})
    url = f"{_FNG_ENDPOINT}?{query}"

    try:
        data = _get_json(url)
    except _ResponseTooLarge as exc:
        return {"ok": False, "error": str(exc)}
    except urllib.error.HTTPError as exc:
        return {"ok": False, "error": f"http error {exc.code}: {exc.reason}"}
    except urllib.error.URLError as exc:
        return {"ok": False, "error": f"alternative.me request failed: {exc.reason}"}
    except (json.JSONDecodeError, ValueError) as exc:
        return {"ok": False, "error": f"alternative.me response was not valid JSON: {exc}"}

    raw_entries = data.get("data") if isinstance(data, dict) else None
    if not isinstance(raw_entries, list) or not raw_entries:
        return {"ok": False, "error": "malformed response: missing or empty 'data' list"}

    entries: List[Dict[str, Any]] = []
    for raw_entry in raw_entries:
        parsed = _parse_entry(raw_entry)
        if parsed is not None:
            entries.append(parsed)

    if not entries:
        return {"ok": False, "error": "malformed response: no parseable entries"}

    result: Dict[str, Any] = {"ok": True, "current": entries[0]}
    if limit_int > 1:
        result["history"] = entries
    return result


registry.register(
    name="fear_greed",
    toolset="finance",
    schema={
        "name": "fear_greed",
        "description": (
            "Look up the current Crypto Fear & Greed Index (0-100, "
            "'Extreme Fear' to 'Extreme Greed') via alternative.me "
            "(keyless, free). Set `limit` > 1 to also get the trailing "
            "daily history alongside the current reading."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "limit": {
                    "type": "integer",
                    "description": f"Number of daily readings to fetch ({_MIN_LIMIT}-{_MAX_LIMIT}). Defaults to {_DEFAULT_LIMIT} (current value only).",
                },
            },
        },
    },
    handler=lambda args, **kw: json.dumps(
        fear_greed(limit=args.get("limit", _DEFAULT_LIMIT)),
        ensure_ascii=False,
    ),
    emoji="\U0001F628",
)
