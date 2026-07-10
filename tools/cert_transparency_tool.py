"""Certificate Transparency log lookup (recon/defensive/security-research support).

Keyless, free HTTP wrapper over crt.sh (https://crt.sh/), a public Certificate
Transparency log aggregator run by Sectigo. No account, no API key, no code
vendored from any project — this module only issues ``urllib`` GETs against
``https://crt.sh/?q=...&output=json`` and parses the JSON response.

* ``ct_subdomains`` finds subdomains of a domain by searching CT logs for
  certificates covering ``%.domain`` and extracting/deduping the hostnames
  named on those certs (a common recon technique: any subdomain that ever
  got a publicly-logged TLS cert shows up here, even ones with no public DNS
  record pointing at them).
* ``ct_certificates`` returns the raw recent certificate entries themselves
  (issuer, names, validity window) for the same query.

Input note: ``domain`` is validated against a strict hostname regex *before*
it is used to build the crt.sh query string, rejecting anything that isn't a
plain dotted hostname (no wildcards, no shell/URL metacharacters). crt.sh is
a fixed, hardcoded endpoint — there's no caller-supplied URL/host here — so
this isn't an SSRF guard so much as an injection/garbage-input guard, but the
validate-before-building-the-request shape matches the other web tools in
this package (see ``wayback_tool._validate_url``).

crt.sh has no documented rate limit but is a shared community resource that
occasionally throttles or times out under load; callers should expect
occasional failures and retry sparingly, not hammer it.
"""

import json
import re
import urllib.error
import urllib.request
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import quote

from tools.registry import registry

_USER_AGENT = "hermes-agent-cert-transparency-tool/1.0"
_TIMEOUT_S = 20
_CRT_SH_ENDPOINT = "https://crt.sh/"
_MAX_RESPONSE_BYTES = 10_000_000

_MIN_LIMIT = 1
_DEFAULT_SUBDOMAIN_LIMIT = 200
_MAX_SUBDOMAIN_LIMIT = 1000
_DEFAULT_CERT_LIMIT = 50
_MAX_CERT_LIMIT = 500

# Plain dotted hostname: labels of 1-63 chars (letters/digits/hyphen, no
# leading/trailing hyphen), at least one dot, 253 chars max overall. No
# wildcards, no scheme, no path — rejects anything that isn't a hostname.
_HOSTNAME_RE = re.compile(
    r"^(?!-)[A-Za-z0-9-]{1,63}(?<!-)(\.(?!-)[A-Za-z0-9-]{1,63}(?<!-))+$"
)


def _validate_domain(domain: Any) -> Optional[str]:
    """Return domain lowercased/trimmed if it's a well-formed hostname, else None."""
    if not isinstance(domain, str) or not domain.strip():
        return None
    candidate = domain.strip().rstrip(".").lower()
    if len(candidate) > 253 or not _HOSTNAME_RE.match(candidate):
        return None
    return candidate


def _validate_limit(limit: Any, default: int, max_limit: int) -> int:
    """Clamp limit into [_MIN_LIMIT, max_limit]."""
    try:
        limit_int = int(limit)
    except (TypeError, ValueError):
        limit_int = default
    return max(_MIN_LIMIT, min(max_limit, limit_int))


class _ResponseTooLarge(Exception):
    """Raised when a crt.sh response body exceeds _MAX_RESPONSE_BYTES."""


def _fetch_crt_sh_json(query: str) -> Any:
    """GET crt.sh's JSON search results for query, bounded by timeout/size.

    Raises _ResponseTooLarge, urllib.error.HTTPError/URLError, OSError, or
    json.JSONDecodeError on failure — callers translate these into {ok: False}.
    """
    url = f"{_CRT_SH_ENDPOINT}?q={quote(query, safe='')}&output=json"
    req = urllib.request.Request(url, headers={"User-Agent": _USER_AGENT})
    with urllib.request.urlopen(req, timeout=_TIMEOUT_S) as resp:
        raw = resp.read(_MAX_RESPONSE_BYTES + 1)
    if len(raw) > _MAX_RESPONSE_BYTES:
        raise _ResponseTooLarge(
            f"response exceeds {_MAX_RESPONSE_BYTES} byte limit — use a more specific query"
        )
    if not raw.strip():
        return []
    return json.loads(raw)


def _query_crt_sh(valid_domain: str) -> Tuple[Optional[List[Any]], Optional[str]]:
    """Query crt.sh for %.valid_domain, returning (rows, None) or (None, error)."""
    try:
        rows = _fetch_crt_sh_json(f"%.{valid_domain}")
    except _ResponseTooLarge as exc:
        return None, str(exc)
    except urllib.error.HTTPError as exc:
        return None, f"http error {exc.code}: {exc.reason}"
    except urllib.error.URLError as exc:
        return None, f"crt.sh request failed: {exc.reason}"
    except (TimeoutError, OSError) as exc:
        return None, str(exc)
    except (json.JSONDecodeError, ValueError) as exc:
        return None, f"crt.sh response was not valid JSON: {exc}"

    if not isinstance(rows, list):
        return None, "unexpected crt.sh response shape"
    return rows, None


def ct_subdomains(domain: Any, limit: Any = _DEFAULT_SUBDOMAIN_LIMIT) -> Dict[str, Any]:
    """Find subdomains of domain by mining Certificate Transparency logs via crt.sh.

    Returns {ok, domain, subdomains: [sorted unique hostnames], count} on
    success, {ok: False, error} on invalid input, network failure, or an
    oversized response.
    """
    valid_domain = _validate_domain(domain)
    if valid_domain is None:
        return {"ok": False, "error": f"invalid domain: {domain!r}"}

    limit_int = _validate_limit(limit, _DEFAULT_SUBDOMAIN_LIMIT, _MAX_SUBDOMAIN_LIMIT)

    rows, error = _query_crt_sh(valid_domain)
    if error is not None:
        return {"ok": False, "domain": valid_domain, "error": error}

    names = set()
    for entry in rows:
        if not isinstance(entry, dict):
            continue
        name_value = entry.get("name_value") or ""
        for line in name_value.splitlines():
            name = line.strip().lower()
            if name.startswith("*."):
                name = name[2:]
            if name and _HOSTNAME_RE.match(name):
                names.add(name)

    subdomains = sorted(names)[:limit_int]
    return {"ok": True, "domain": valid_domain, "subdomains": subdomains, "count": len(subdomains)}


def ct_certificates(domain: Any, limit: Any = _DEFAULT_CERT_LIMIT) -> Dict[str, Any]:
    """Return recent certificate log entries covering domain, via crt.sh.

    Returns {ok, domain, certificates: [{issuer, name_value, not_before,
    not_after}], count} on success, sorted most-recently-issued first,
    {ok: False, error} on invalid input, network failure, or an oversized
    response.
    """
    valid_domain = _validate_domain(domain)
    if valid_domain is None:
        return {"ok": False, "error": f"invalid domain: {domain!r}"}

    limit_int = _validate_limit(limit, _DEFAULT_CERT_LIMIT, _MAX_CERT_LIMIT)

    rows, error = _query_crt_sh(valid_domain)
    if error is not None:
        return {"ok": False, "domain": valid_domain, "error": error}

    certificates = []
    for entry in rows:
        if not isinstance(entry, dict):
            continue
        certificates.append({
            "issuer": entry.get("issuer_name") or "",
            "name_value": entry.get("name_value") or "",
            "not_before": entry.get("not_before") or "",
            "not_after": entry.get("not_after") or "",
        })

    certificates.sort(key=lambda cert: cert["not_before"], reverse=True)
    certificates = certificates[:limit_int]
    return {"ok": True, "domain": valid_domain, "certificates": certificates, "count": len(certificates)}


registry.register(
    name="ct_subdomains",
    toolset="web",
    schema={
        "name": "ct_subdomains",
        "description": (
            "Find subdomains of a domain by mining public Certificate "
            "Transparency logs via crt.sh (free, keyless). Returns sorted, "
            "deduplicated, wildcard-stripped hostnames pulled from certs "
            "covering `%.domain` — useful recon for subdomains that never "
            "showed up in DNS enumeration but got a public TLS cert. Use "
            "`ct_certificates` instead for the raw certificate entries."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "domain": {"type": "string", "description": "Base domain to search, e.g. 'example.com'."},
                "limit": {
                    "type": "integer",
                    "description": f"Max subdomains to return ({_MIN_LIMIT}-{_MAX_SUBDOMAIN_LIMIT}). Defaults to {_DEFAULT_SUBDOMAIN_LIMIT}.",
                },
            },
            "required": ["domain"],
        },
    },
    handler=lambda args, **kw: json.dumps(
        ct_subdomains(domain=args.get("domain", ""), limit=args.get("limit", _DEFAULT_SUBDOMAIN_LIMIT)),
        ensure_ascii=False,
    ),
    emoji="📜",
)

registry.register(
    name="ct_certificates",
    toolset="web",
    schema={
        "name": "ct_certificates",
        "description": (
            "List recent Certificate Transparency log entries for a domain "
            "via crt.sh (free, keyless) — issuer, logged names, and validity "
            "window for each cert, most recent first. Use `ct_subdomains` "
            "instead when only the deduplicated hostname list is needed."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "domain": {"type": "string", "description": "Base domain to search, e.g. 'example.com'."},
                "limit": {
                    "type": "integer",
                    "description": f"Max certificate entries to return ({_MIN_LIMIT}-{_MAX_CERT_LIMIT}). Defaults to {_DEFAULT_CERT_LIMIT}.",
                },
            },
            "required": ["domain"],
        },
    },
    handler=lambda args, **kw: json.dumps(
        ct_certificates(domain=args.get("domain", ""), limit=args.get("limit", _DEFAULT_CERT_LIMIT)),
        ensure_ascii=False,
    ),
    emoji="📜",
)
