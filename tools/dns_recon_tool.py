"""DNS-over-HTTPS lookups (research/recon/defensive OSINT support).

Two keyless, free DNS-over-HTTPS (RFC 8484) JSON APIs — no vendored code, no
API key:

* Cloudflare (https://cloudflare-dns.com/dns-query) — tried first.
* Google (https://dns.google/resolve) — fallback if Cloudflare fails.

Both speak the same "DNS JSON" response shape (``Status``, ``Answer: [{name,
type, TTL, data}, ...]``), so a single parser handles either. This module
only shells out to urllib against those two public endpoints; nothing from
either vendor's client library is vendored here.

Input hardening: ``domain`` is checked against a strict hostname regex
*before* it ever reaches ``urlencode``/the request URL, so path-traversal or
shell-metacharacter payloads riding in the domain field (e.g.
``example.com/../x``, ``a;b.com``) are rejected outright rather than relying
on URL-encoding alone. ``record_type`` is checked against a fixed allowlist
for the same reason.
"""

import json
import re
import urllib.error
import urllib.parse
import urllib.request
from typing import Any, Dict, List, Optional

from tools import _net_guard
from tools.registry import registry

_USER_AGENT = "hermes-agent-dns-recon-tool/1.0"
_TIMEOUT_S = 15
_MAX_RESPONSE_BYTES = _net_guard.MAX_RESPONSE_BYTES
_CLOUDFLARE_ENDPOINT = "https://cloudflare-dns.com/dns-query"
_GOOGLE_ENDPOINT = "https://dns.google/resolve"
_MAX_BULK_ITEMS = 100
# Cloudflare first, Google as fallback if Cloudflare fails.
_DOH_ENDPOINTS = (_CLOUDFLARE_ENDPOINT, _GOOGLE_ENDPOINT)

# RFC 1035 TYPE values, used to filter Answer records down to the requested
# type (a query for A on a CNAME-fronted domain returns both the CNAME and A
# records in Answer; without filtering, records would mix record types).
_RECORD_TYPE_NUMS = {
    "A": 1,
    "NS": 2,
    "CNAME": 5,
    "SOA": 6,
    "PTR": 12,
    "MX": 15,
    "TXT": 16,
    "AAAA": 28,
    "CAA": 257,
}
_RECORD_TYPES = frozenset(_RECORD_TYPE_NUMS)
_DEFAULT_BULK_TYPES = ("A", "AAAA", "MX", "NS", "TXT")

_MAX_DOMAIN_LENGTH = 253
# Kept local rather than swapped for _net_guard.validate_hostname: this
# regex's exact permissiveness (vs. cert_transparency_tool's stricter one)
# is intentional per-tool and shouldn't change as a side effect of the
# _net_guard adoption pass.
_HOSTNAME_RE = re.compile(
    r"^[a-zA-Z0-9]([a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?"
    r"(\.[a-zA-Z0-9]([a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?)*$"
)


def _validate_domain(domain: Any) -> Optional[str]:
    """Return domain stripped if it matches the hostname allowlist regex, else None."""
    if not isinstance(domain, str) or not domain.strip():
        return None
    candidate = domain.strip()
    if len(candidate) > _MAX_DOMAIN_LENGTH:
        return None
    if not _HOSTNAME_RE.match(candidate):
        return None
    return candidate


def _validate_record_type(record_type: Any) -> Optional[str]:
    """Return record_type upper-cased if it's in the allowlist, else None."""
    if not isinstance(record_type, str):
        return None
    candidate = record_type.strip().upper()
    return candidate if candidate in _RECORD_TYPES else None


class _ResponseTooLarge(Exception):
    """Raised by _doh_query when a response body exceeds _MAX_RESPONSE_BYTES."""


def _doh_query(endpoint: str, domain: str, record_type: str) -> Any:
    """GET a DoH JSON answer for domain/record_type from endpoint.

    Raises _ResponseTooLarge instead of buffering an unbounded body, and lets
    urllib.error.URLError / json errors propagate to the caller.
    """
    query = urllib.parse.urlencode({"name": domain, "type": record_type})
    request_url = f"{endpoint}?{query}"
    req = urllib.request.Request(
        request_url,
        headers={"User-Agent": _USER_AGENT, "Accept": "application/dns-json"},
    )
    with urllib.request.urlopen(req, timeout=_TIMEOUT_S) as resp:
        try:
            raw = _net_guard.read_capped(resp)
        except _net_guard.NetGuardError as exc:
            raise _ResponseTooLarge(str(exc)) from exc
    return json.loads(raw)


def dns_lookup(domain: Any, record_type: Any = "A") -> Dict[str, Any]:
    """Resolve domain's record_type records via DNS-over-HTTPS.

    Tries Cloudflare's DoH endpoint first, falling back to Google's if the
    Cloudflare request fails (network error, oversized response, bad JSON).

    Returns {ok, domain, record_type, records: [str, ...]} on success,
    {ok: False, error} on invalid input or when both endpoints fail.
    """
    valid_type = _validate_record_type(record_type)
    if valid_type is None:
        return {
            "ok": False,
            "error": f"unsupported record_type: {record_type!r} (allowed: {sorted(_RECORD_TYPES)})",
        }

    valid_domain = _validate_domain(domain)
    if valid_domain is None:
        return {"ok": False, "error": f"invalid domain: {domain!r}"}

    want_type_num = _RECORD_TYPE_NUMS[valid_type]
    last_error = "all DoH endpoints failed"
    for endpoint in _DOH_ENDPOINTS:
        try:
            data = _doh_query(endpoint, valid_domain, valid_type)
        except _ResponseTooLarge as exc:
            last_error = f"{endpoint}: {exc}"
            continue
        except urllib.error.URLError as exc:
            last_error = f"DoH request to {endpoint} failed: {exc}"
            continue
        except (json.JSONDecodeError, ValueError) as exc:
            last_error = f"DoH response from {endpoint} was not valid JSON: {exc}"
            continue

        answers = data.get("Answer") or []
        records = [a.get("data", "") for a in answers if a.get("type") == want_type_num]
        return {
            "ok": True,
            "domain": valid_domain,
            "record_type": valid_type,
            "records": records,
        }

    return {"ok": False, "domain": domain, "record_type": record_type, "error": last_error}


def dns_bulk(domain: Any, record_types: Any = None) -> Dict[str, Any]:
    """Resolve multiple record types for domain in one call.

    Each record type is looked up independently — one failing type doesn't
    abort the batch. Returns {ok, domain, results: {record_type: lookup_result}}
    on valid input, {ok: False, error} if domain itself is invalid or
    record_types exceeds the batch cap.
    """
    valid_domain = _validate_domain(domain)
    if valid_domain is None:
        return {"ok": False, "error": f"invalid domain: {domain!r}"}

    if not isinstance(record_types, (list, tuple)) or not record_types:
        record_types = _DEFAULT_BULK_TYPES
    if len(record_types) > _MAX_BULK_ITEMS:
        return {"ok": False, "error": f"too many items (max {_MAX_BULK_ITEMS})"}

    results: Dict[str, Any] = {}
    for record_type in record_types:
        results[str(record_type)] = dns_lookup(valid_domain, record_type=record_type)

    return {"ok": True, "domain": valid_domain, "results": results}


registry.register(
    name="dns_lookup",
    toolset="recon",
    schema={
        "name": "dns_lookup",
        "description": (
            "Resolve a single DNS record type for a domain via DNS-over-HTTPS "
            "(Cloudflare, falling back to Google). Keyless. Returns the raw "
            "record values in `records`. Use `dns_bulk` instead to look up "
            "several record types for one domain in a single call."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "domain": {"type": "string", "description": "Domain to look up (e.g. 'example.com')."},
                "record_type": {
                    "type": "string",
                    "enum": sorted(_RECORD_TYPES),
                    "description": "DNS record type to query. Defaults to 'A'.",
                },
            },
            "required": ["domain"],
        },
    },
    handler=lambda args, **kw: json.dumps(
        dns_lookup(domain=args.get("domain", ""), record_type=args.get("record_type", "A")),
        ensure_ascii=False,
    ),
    emoji="🔍",
)

registry.register(
    name="dns_bulk",
    toolset="recon",
    schema={
        "name": "dns_bulk",
        "description": (
            "Resolve multiple DNS record types for a domain via DNS-over-HTTPS "
            "in one call. Each record type is isolated — one failing type "
            "doesn't abort the others. Defaults to "
            f"{list(_DEFAULT_BULK_TYPES)} when `record_types` is omitted."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "domain": {"type": "string", "description": "Domain to look up (e.g. 'example.com')."},
                "record_types": {
                    "type": "array",
                    "items": {"type": "string", "enum": sorted(_RECORD_TYPES)},
                    "description": f"Record types to query. Defaults to {list(_DEFAULT_BULK_TYPES)}.",
                },
            },
            "required": ["domain"],
        },
    },
    handler=lambda args, **kw: json.dumps(
        dns_bulk(domain=args.get("domain", ""), record_types=args.get("record_types")),
        ensure_ascii=False,
    ),
    emoji="🔍",
)
