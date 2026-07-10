"""IP geolocation and ASN lookup (research/recon/defensive OSINT support).

Two keyless, free IP geolocation JSON APIs — no vendored code, no API key:

* ipapi.co (https://ipapi.co/<ip>/json/) — HTTPS, keyless, tried first.
* ip-api.com (http://ip-api.com/json/<ip>) — the free tier does *not* offer
  HTTPS (that requires a paid plan), so this is used only as a fallback when
  ipapi.co fails. Because the lookup is a plain HTTP GET, the response can be
  observed/tampered with in transit; callers that need a hard HTTPS guarantee
  should treat a `source: "ip-api.com"` result as lower-assurance than
  `source: "ipapi.co"`.

Input hardening: `ip` is parsed with the stdlib `ipaddress.ip_address()`
*before* it ever reaches a request URL, so hostnames, shell metacharacters,
or other injection payloads riding in the ip field are rejected outright
rather than relying on URL-encoding alone. Private/reserved/loopback/
link-local/multicast addresses are recognized via the same stdlib module and
short-circuited before any network call — public geolocation APIs can't
meaningfully resolve them, and there's no reason to leak internal-looking
addresses to a third-party service.
"""

import ipaddress
import json
import urllib.error
import urllib.parse
import urllib.request
from typing import Any, Callable, Dict, List, Optional

from tools import _net_guard
from tools.registry import registry

_USER_AGENT = "hermes-agent-ip-info-tool/1.0"
_TIMEOUT_S = 15
_MAX_RESPONSE_BYTES = _net_guard.MAX_RESPONSE_BYTES
_MAX_BULK_ITEMS = 100
_IPAPI_CO_ENDPOINT = "https://ipapi.co/{ip}/json/"
_IP_API_COM_ENDPOINT = "http://ip-api.com/json/{ip}"
_IP_API_COM_FIELDS = "status,message,country,regionName,city,isp,org,as,query"


def _validate_ip(ip: Any) -> Optional[str]:
    """Return ip stripped if it's a syntactically valid IPv4/IPv6 address, else None."""
    if not isinstance(ip, str) or not ip.strip():
        return None
    candidate = ip.strip()
    try:
        ipaddress.ip_address(candidate)
    except ValueError:
        return None
    return candidate


def _is_private(ip: str) -> bool:
    """True if ip is private, reserved, loopback, link-local, multicast, or unspecified.

    Assumes ip has already passed _validate_ip.
    """
    addr = ipaddress.ip_address(ip)
    return (
        addr.is_private
        or addr.is_reserved
        or addr.is_loopback
        or addr.is_link_local
        or addr.is_multicast
        or addr.is_unspecified
    )


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


def _query_ipapi_co(ip: str) -> Dict[str, Any]:
    """Query ipapi.co (HTTPS). Raises ValueError if the API reports an error."""
    url = _IPAPI_CO_ENDPOINT.format(ip=urllib.parse.quote(ip, safe=""))
    data = _get_json(url)
    if data.get("error"):
        raise ValueError(data.get("reason") or "ipapi.co returned an error")
    return {
        "ok": True,
        "ip": data.get("ip", ip),
        "city": data.get("city"),
        "region": data.get("region"),
        "country": data.get("country_name"),
        "asn": data.get("asn"),
        "org": data.get("org"),
        "source": "ipapi.co",
    }


def _query_ip_api_com(ip: str) -> Dict[str, Any]:
    """Query ip-api.com (HTTP-only on the free tier). Raises ValueError on API error."""
    query = urllib.parse.urlencode({"fields": _IP_API_COM_FIELDS})
    url = f"{_IP_API_COM_ENDPOINT.format(ip=urllib.parse.quote(ip, safe=''))}?{query}"
    data = _get_json(url)
    if data.get("status") != "success":
        raise ValueError(data.get("message") or "ip-api.com returned an error")
    return {
        "ok": True,
        "ip": data.get("query", ip),
        "city": data.get("city"),
        "region": data.get("regionName"),
        "country": data.get("country"),
        "asn": data.get("as"),
        "org": data.get("isp") or data.get("org"),
        "source": "ip-api.com",
    }


_ENDPOINTS: tuple = (_query_ipapi_co, _query_ip_api_com)


def ip_info(ip: Any) -> Dict[str, Any]:
    """Geolocate and ASN-lookup a public IP address.

    Tries ipapi.co (HTTPS) first, falling back to ip-api.com (HTTP, see
    module docstring) if ipapi.co fails. Returns {ok, ip, city, region,
    country, asn, org, source, is_private} on success, {ok: False, error} on
    invalid input or when both endpoints fail.

    Private/reserved/loopback/link-local/multicast addresses are not sent to
    either API — returns {ok: True, ip, is_private: True, note} instead.
    """
    valid_ip = _validate_ip(ip)
    if valid_ip is None:
        return {"ok": False, "error": f"invalid ip: {ip!r} (must be a valid IPv4/IPv6 address)"}

    if _is_private(valid_ip):
        return {
            "ok": True,
            "ip": valid_ip,
            "is_private": True,
            "note": "private/reserved/loopback/link-local/multicast address; not looked up",
        }

    last_error = "all IP geolocation endpoints failed"
    for query_fn in _ENDPOINTS:
        try:
            result = query_fn(valid_ip)
        except _ResponseTooLarge as exc:
            last_error = f"{query_fn.__name__}: {exc}"
            continue
        except urllib.error.URLError as exc:
            last_error = f"{query_fn.__name__} request failed: {exc}"
            continue
        except (json.JSONDecodeError, ValueError) as exc:
            last_error = f"{query_fn.__name__} response error: {exc}"
            continue

        result["is_private"] = False
        return result

    return {"ok": False, "ip": valid_ip, "error": last_error}


def ip_bulk(ips: Any) -> Dict[str, Any]:
    """Look up multiple IPs in one call.

    Each IP is looked up independently — one failing lookup doesn't abort
    the batch. Returns {ok, results: {ip: ip_info_result}} on valid input,
    {ok: False, error} if ips isn't a non-empty list or exceeds the batch cap.
    """
    if not isinstance(ips, (list, tuple)) or not ips:
        return {"ok": False, "error": "ips must be a non-empty list"}
    if len(ips) > _MAX_BULK_ITEMS:
        return {"ok": False, "error": f"too many items (max {_MAX_BULK_ITEMS})"}

    results: Dict[str, Any] = {}
    for raw_ip in ips:
        results[str(raw_ip)] = ip_info(raw_ip)

    return {"ok": True, "results": results}


registry.register(
    name="ip_info",
    toolset="web",
    schema={
        "name": "ip_info",
        "description": (
            "Geolocate an IP address and look up its ASN/organization "
            "(ipapi.co over HTTPS, falling back to ip-api.com over HTTP if "
            "that fails). Keyless. Private/reserved/loopback addresses are "
            "flagged via `is_private` rather than sent to either API. Use "
            "`ip_bulk` instead to look up several IPs in one call."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "ip": {"type": "string", "description": "IPv4 or IPv6 address to look up (e.g. '8.8.8.8')."},
            },
            "required": ["ip"],
        },
    },
    handler=lambda args, **kw: json.dumps(
        ip_info(ip=args.get("ip", "")),
        ensure_ascii=False,
    ),
    emoji="🌐",
)

registry.register(
    name="ip_bulk",
    toolset="web",
    schema={
        "name": "ip_bulk",
        "description": (
            "Geolocate and ASN-lookup multiple IP addresses in one call. "
            "Each IP is isolated — one failing lookup doesn't abort the others."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "ips": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "IPv4/IPv6 addresses to look up.",
                },
            },
            "required": ["ips"],
        },
    },
    handler=lambda args, **kw: json.dumps(
        ip_bulk(ips=args.get("ips")),
        ensure_ascii=False,
    ),
    emoji="🌐",
)
