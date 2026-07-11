"""HTTP endpoint health/uptime checking for monitoring and alerting.

``check_url`` issues a single GET against a caller-supplied URL and reports
whether it's up: reachable, and (if requested) matching an expected status
code and/or containing an expected substring in the body. ``check_urls``
runs the same check over a bounded batch of URLs, isolating failures
per-URL so one bad target doesn't abort the rest.

SSRF note: the URL to check is caller-supplied, exactly like
``fetch_fingerprint`` in skills/research/network-recon/scripts/recon.py.
This module delegates its guards to ``tools._net_guard`` (the shared
implementation): only http/https schemes are accepted, the resolved host is
rejected if it's private/reserved/loopback/link-local/multicast/unspecified
(blocks loopback, RFC1918, and cloud metadata endpoints like
169.254.169.254), and redirects are re-validated hop-by-hop via
``_net_guard.build_safe_opener`` rather than followed blindly. The
module-level ``_require_http_scheme``/``_reject_private_target``/
``_build_safe_opener`` helpers below are thin adapters that translate
between this module's return-a-string-or-None convention and
``_net_guard``'s raise-``NetGuardError`` convention — the actual checks
live in one place so a fix there covers every adopter.
"""

import json
import socket
import time
import urllib.error
import urllib.request
from typing import Any, Dict, List, Optional

from tools import _net_guard
from tools.registry import registry

_USER_AGENT = "Hermes-Agent (https://github.com/NousResearch/hermes-agent)"
_DEFAULT_TIMEOUT_S = 15
_ALLOWED_SCHEMES = _net_guard.ALLOWED_SCHEMES
_MAX_REDIRECTS = _net_guard.MAX_REDIRECTS
_MAX_RESPONSE_BYTES = _net_guard.MAX_RESPONSE_BYTES
_MAX_BULK_ITEMS = 100


def _require_http_scheme(url: str) -> Optional[str]:
    """Return an error string if url's scheme isn't http/https, else None."""
    try:
        _net_guard.require_http_scheme(url)
    except _net_guard.NetGuardError as exc:
        return str(exc)
    return None


def _reject_private_target(url: str, timeout: float) -> Optional[str]:
    """Return an error string if url's host resolves to a private/reserved/
    loopback/link-local/multicast/unspecified address, else None.

    ``timeout`` is accepted for call-site compatibility but isn't threaded
    through to ``_net_guard.reject_private_target`` — DNS resolution there
    uses ``_net_guard.DEFAULT_TIMEOUT_SECONDS`` regardless of the caller's
    per-request timeout.
    """
    try:
        _net_guard.reject_private_target(url)
    except _net_guard.NetGuardError as exc:
        return str(exc)
    return None


def _build_safe_opener(timeout: float) -> urllib.request.OpenerDirector:
    """Return an opener whose redirect hops are re-validated by
    _net_guard.SafeRedirectHandler. ``timeout`` is accepted for call-site
    compatibility (the actual per-request timeout is passed separately to
    ``opener.open(request, timeout=...)``)."""
    return _net_guard.build_safe_opener()


def check_url(
    url: Any,
    expect_status: Any = None,
    expect_substring: Any = None,
    timeout: Any = _DEFAULT_TIMEOUT_S,
) -> Dict[str, Any]:
    """Check a single URL's reachability, status code, and body content.

    Returns {ok, url, status, elapsed_ms, up, checks: {status_ok,
    substring_found}} on a completed request (``ok`` is True even when
    ``up`` is False — a reachable-but-failing endpoint is still a valid
    check result). Returns {ok: False, url, up: False, error} when the URL
    is rejected outright (bad scheme, private target) or the request
    couldn't complete at all (DNS failure, connection refused, timeout).

    ``up`` is True iff the endpoint was reachable AND (expect_status
    matches, if given) AND (expect_substring is found in the capped
    response body, if given).
    """
    if not isinstance(url, str) or not url.strip():
        return {"ok": False, "url": url, "up": False, "error": f"invalid url: {url!r}"}
    target = url.strip()
    timeout_s = float(timeout) if isinstance(timeout, (int, float)) else _DEFAULT_TIMEOUT_S

    scheme_error = _require_http_scheme(target)
    if scheme_error:
        return {"ok": False, "url": target, "up": False, "error": scheme_error}

    target_error = _reject_private_target(target, timeout_s)
    if target_error:
        return {"ok": False, "url": target, "up": False, "error": target_error}

    request = urllib.request.Request(target, headers={"User-Agent": _USER_AGENT}, method="GET")
    opener = _build_safe_opener(timeout_s)
    start = time.perf_counter()
    try:
        with opener.open(request, timeout=timeout_s) as response:
            status = response.status
            body = _net_guard.read_capped(response)
    except urllib.error.HTTPError as exc:
        status = exc.code
        try:
            body = _net_guard.read_capped(exc)
        except (_net_guard.NetGuardError, OSError, ValueError):
            body = b""
    except _net_guard.NetGuardError as exc:
        return {"ok": False, "url": target, "up": False, "error": str(exc)}
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        return {"ok": False, "url": target, "up": False, "error": str(exc)}
    elapsed_ms = round((time.perf_counter() - start) * 1000, 1)

    try:
        status_ok = status == int(expect_status) if expect_status is not None else True
    except (TypeError, ValueError):
        status_ok = False
    substring_found = (
        isinstance(expect_substring, str) and expect_substring.encode("utf-8", errors="replace") in body
        if expect_substring is not None
        else True
    )

    return {
        "ok": True,
        "url": target,
        "status": status,
        "elapsed_ms": elapsed_ms,
        "up": bool(status_ok and substring_found),
        "checks": {"status_ok": status_ok, "substring_found": substring_found},
    }


def check_urls(urls: Any, **kwargs: Any) -> Dict[str, Any]:
    """Check multiple URLs sequentially, isolating failures per-URL.

    Returns {ok, results: [check_url(...) per url]}. ``ok`` at the top
    level is True as long as urls was a valid list within the size cap; a
    per-URL failure only marks that entry's own ``ok``/``up`` False.
    """
    if not isinstance(urls, (list, tuple)):
        return {"ok": False, "error": "urls must be a list of urls"}
    if len(urls) > _MAX_BULK_ITEMS:
        return {"ok": False, "error": f"too many urls: {len(urls)} (max {_MAX_BULK_ITEMS})"}

    results = [check_url(url, **kwargs) for url in urls]
    return {"ok": True, "results": results}


registry.register(
    name="check_url",
    toolset="monitoring",
    schema={
        "name": "check_url",
        "description": (
            "Check whether an HTTP(S) endpoint is up — reachable, and "
            "optionally matching an expected status code and/or containing "
            "an expected substring in the response body. Returns status, "
            "elapsed_ms, and an `up: bool` verdict. Use `check_urls` "
            "instead to check several endpoints in one call."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "url": {"type": "string", "description": "URL to check (http:// or https://)."},
                "expect_status": {
                    "type": "integer",
                    "description": "Expected HTTP status code, e.g. 200. Omit to skip this check.",
                },
                "expect_substring": {
                    "type": "string",
                    "description": "Substring expected in the response body. Omit to skip this check.",
                },
                "timeout": {
                    "type": "number",
                    "description": f"Request timeout in seconds. Defaults to {_DEFAULT_TIMEOUT_S}.",
                },
            },
            "required": ["url"],
        },
    },
    handler=lambda args, **kw: json.dumps(
        check_url(
            url=args.get("url", ""),
            expect_status=args.get("expect_status"),
            expect_substring=args.get("expect_substring"),
            timeout=args.get("timeout", _DEFAULT_TIMEOUT_S),
        ),
        ensure_ascii=False,
    ),
    emoji="📶",
)

registry.register(
    name="check_urls",
    toolset="monitoring",
    schema={
        "name": "check_urls",
        "description": (
            f"Check multiple HTTP(S) endpoints for uptime (max {_MAX_BULK_ITEMS} "
            "per call). Each URL is isolated — one failing endpoint doesn't "
            "abort the rest. Same expect_status/expect_substring/timeout "
            "checks as `check_url`, applied uniformly to every URL. Returns "
            "a list of per-URL results in `results`."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "urls": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": f"URLs to check (http/https only, max {_MAX_BULK_ITEMS}).",
                },
                "expect_status": {
                    "type": "integer",
                    "description": "Expected HTTP status code applied to every URL. Omit to skip this check.",
                },
                "expect_substring": {
                    "type": "string",
                    "description": "Substring expected in every response body. Omit to skip this check.",
                },
                "timeout": {
                    "type": "number",
                    "description": f"Per-request timeout in seconds. Defaults to {_DEFAULT_TIMEOUT_S}.",
                },
            },
            "required": ["urls"],
        },
    },
    handler=lambda args, **kw: json.dumps(
        check_urls(
            urls=args.get("urls", []),
            expect_status=args.get("expect_status"),
            expect_substring=args.get("expect_substring"),
            timeout=args.get("timeout", _DEFAULT_TIMEOUT_S),
        ),
        ensure_ascii=False,
    ),
    emoji="📶",
)
