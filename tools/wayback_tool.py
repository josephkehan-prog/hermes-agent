"""Internet Archive Wayback Machine access (research/OSINT support).

Three keyless, free HTTP APIs — no vendored code, no API key:

* ``wayback_snapshots`` queries the CDX API
  (https://web.archive.org/cdx/search/cdx) for the list of snapshots the
  Wayback Machine holds for a URL.
* ``wayback_latest`` queries the availability API
  (https://archive.org/wayback/available) for the single closest snapshot.
* ``wayback_save`` requests a fresh capture via the keyless SPN2 endpoint
  (https://web.archive.org/save/<url>). This WRITES to an external service,
  so it is gated behind an explicit ``confirm=True`` and defaults to a no-op.

The API surface mirrors waybackpy (https://github.com/akamhy/waybackpy,
MIT License — Copyright (c) Akash Mahanty) for familiarity, but no code from
that project is vendored here; this module only shells out to urllib against
the public archive.org endpoints.
"""

import json
import urllib.error
import urllib.parse
import urllib.request
from typing import Any, Dict, List, Optional

from tools import _net_guard
from tools.registry import registry

_USER_AGENT = "hermes-agent-wayback-tool/1.0"
_TIMEOUT_S = 20
_CDX_ENDPOINT = "https://web.archive.org/cdx/search/cdx"
_AVAILABLE_ENDPOINT = "https://archive.org/wayback/available"
_SAVE_ENDPOINT = "https://web.archive.org/save/"
_MIN_LIMIT = 1
_MAX_LIMIT = 100
_DEFAULT_LIMIT = 25
_MAX_RESPONSE_BYTES = _net_guard.MAX_RESPONSE_BYTES


def _validate_url(url: Any) -> Optional[str]:
    """Return url stripped if it parses as http(s) with a hostname, else None."""
    candidate = (url or "").strip() if isinstance(url, str) else ""
    if not candidate:
        return None
    parsed = urllib.parse.urlparse(candidate)
    if parsed.scheme not in ("http", "https") or not parsed.netloc:
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
    req = urllib.request.Request(url, headers={"User-Agent": _USER_AGENT})
    with urllib.request.urlopen(req, timeout=_TIMEOUT_S) as resp:
        try:
            raw = _net_guard.read_capped(resp)
        except _net_guard.NetGuardError as exc:
            raise _ResponseTooLarge(str(exc)) from exc
    return json.loads(raw)


def wayback_snapshots(
    url: Any,
    limit: Any = _DEFAULT_LIMIT,
    from_year: Any = None,
    to_year: Any = None,
) -> Dict[str, Any]:
    """List archived snapshots of url via the CDX API.

    Returns {ok, snapshots: [{timestamp, original, statuscode, archive_url}]}
    on success, {ok: False, error} on invalid input or request failure.
    """
    target = _validate_url(url)
    if target is None:
        return {"ok": False, "error": f"invalid url: {url!r} (must be http:// or https://)"}

    params = {
        "url": target,
        "output": "json",
        "limit": str(_validate_limit(limit)),
    }
    if from_year:
        params["from"] = str(from_year)
    if to_year:
        params["to"] = str(to_year)
    query = urllib.parse.urlencode(params, quote_via=urllib.parse.quote)
    request_url = f"{_CDX_ENDPOINT}?{query}"

    try:
        rows = _get_json(request_url)
    except _ResponseTooLarge as exc:
        return {"ok": False, "error": str(exc)}
    except urllib.error.URLError as exc:
        return {"ok": False, "error": f"CDX request failed: {exc}"}
    except (json.JSONDecodeError, ValueError) as exc:
        return {"ok": False, "error": f"CDX response was not valid JSON: {exc}"}

    if not rows or len(rows) < 2:
        return {"ok": True, "snapshots": []}

    fields = rows[0]
    try:
        timestamp_idx = fields.index("timestamp")
        original_idx = fields.index("original")
        statuscode_idx = fields.index("statuscode")
    except ValueError as exc:
        return {"ok": False, "error": f"unexpected CDX field layout: {exc}"}

    snapshots = []
    for row in rows[1:]:
        timestamp = row[timestamp_idx]
        original = row[original_idx]
        snapshots.append({
            "timestamp": timestamp,
            "original": original,
            "statuscode": row[statuscode_idx],
            "archive_url": f"https://web.archive.org/web/{timestamp}/{original}",
        })
    return {"ok": True, "snapshots": snapshots}


def wayback_latest(url: Any) -> Dict[str, Any]:
    """Look up the closest archived snapshot of url via the availability API.

    Returns {ok, available, archive_url, timestamp, status} on success (with
    available=False when no snapshot exists), {ok: False, error} on invalid
    input or request failure.
    """
    target = _validate_url(url)
    if target is None:
        return {"ok": False, "error": f"invalid url: {url!r} (must be http:// or https://)"}

    query = urllib.parse.urlencode({"url": target}, quote_via=urllib.parse.quote)
    request_url = f"{_AVAILABLE_ENDPOINT}?{query}"

    try:
        data = _get_json(request_url)
    except _ResponseTooLarge as exc:
        return {"ok": False, "error": str(exc)}
    except urllib.error.URLError as exc:
        return {"ok": False, "error": f"availability request failed: {exc}"}
    except (json.JSONDecodeError, ValueError) as exc:
        return {"ok": False, "error": f"availability response was not valid JSON: {exc}"}

    closest = (data.get("archived_snapshots") or {}).get("closest") or {}
    if not closest.get("available"):
        return {"ok": True, "available": False}

    return {
        "ok": True,
        "available": True,
        "archive_url": closest.get("url"),
        "timestamp": closest.get("timestamp"),
        "status": closest.get("status"),
    }


def wayback_save(url: Any, confirm: bool = False) -> Dict[str, Any]:
    """Request a fresh Wayback Machine capture of url via keyless SPN2.

    This writes to an external service (archive.org will crawl and store the
    page), so it is a no-op unless the caller passes confirm=True.
    """
    if not confirm:
        return {"ok": False, "error": "pass confirm=True to request an archive save"}

    target = _validate_url(url)
    if target is None:
        return {"ok": False, "error": f"invalid url: {url!r} (must be http:// or https://)"}

    request_url = _SAVE_ENDPOINT + urllib.parse.quote(target, safe="")
    req = urllib.request.Request(request_url, headers={"User-Agent": _USER_AGENT})
    try:
        with urllib.request.urlopen(req, timeout=_TIMEOUT_S) as resp:
            final_url = resp.geturl()
            status = resp.status
    except urllib.error.URLError as exc:
        return {"ok": False, "error": f"save request failed: {exc}"}

    return {"ok": True, "status": status, "archive_url": final_url}


registry.register(
    name="wayback_snapshots",
    toolset="web",
    schema={
        "name": "wayback_snapshots",
        "description": (
            "List archived snapshots of a URL from the Internet Archive's "
            "Wayback Machine (CDX API). Returns timestamps, original URLs, "
            "status codes, and direct archive.org links. Use `wayback_latest` "
            "instead when only the single most recent/closest snapshot is needed."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "url": {"type": "string", "description": "URL to look up (http:// or https://)."},
                "limit": {
                    "type": "integer",
                    "description": f"Max snapshots to return ({_MIN_LIMIT}-{_MAX_LIMIT}). Defaults to {_DEFAULT_LIMIT}.",
                },
                "from_year": {"type": "integer", "description": "Only include snapshots from this year onward."},
                "to_year": {"type": "integer", "description": "Only include snapshots up to and including this year."},
            },
            "required": ["url"],
        },
    },
    handler=lambda args, **kw: json.dumps(
        wayback_snapshots(
            url=args.get("url", ""),
            limit=args.get("limit", _DEFAULT_LIMIT),
            from_year=args.get("from_year"),
            to_year=args.get("to_year"),
        ),
        ensure_ascii=False,
    ),
    emoji="🏛️",
)

registry.register(
    name="wayback_latest",
    toolset="web",
    schema={
        "name": "wayback_latest",
        "description": (
            "Look up the closest archived snapshot of a URL via the Wayback "
            "Machine's availability API — a fast single-result check. Use "
            "`wayback_snapshots` instead to list the full history of captures."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "url": {"type": "string", "description": "URL to look up (http:// or https://)."},
            },
            "required": ["url"],
        },
    },
    handler=lambda args, **kw: json.dumps(
        wayback_latest(url=args.get("url", "")),
        ensure_ascii=False,
    ),
    emoji="🏛️",
)

registry.register(
    name="wayback_save",
    toolset="web",
    schema={
        "name": "wayback_save",
        "description": (
            "Request that the Wayback Machine crawl and archive a fresh "
            "snapshot of a URL right now (SPN2 'Save Page Now', keyless). "
            "This writes to an external service, so it is a no-op unless "
            "`confirm=True` is passed explicitly."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "url": {"type": "string", "description": "URL to archive (http:// or https://)."},
                "confirm": {
                    "type": "boolean",
                    "description": "Must be true to actually request the save. Defaults to false.",
                },
            },
            "required": ["url"],
        },
    },
    handler=lambda args, **kw: json.dumps(
        wayback_save(url=args.get("url", ""), confirm=bool(args.get("confirm", False))),
        ensure_ascii=False,
    ),
    emoji="🏛️",
)
