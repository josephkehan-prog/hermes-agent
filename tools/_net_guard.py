"""Shared SSRF / fetch-safety helpers for stdlib-urllib-based fetch tools.

Consolidates the security contract used by ``rss_fetch_tool.py``,
``wayback_tool.py``, and ``skills/research/network-recon/scripts/recon.py``:
scheme allowlisting, hostname validation, private/reserved-IP rejection,
capped response reads, and a redirect handler that re-validates every hop.
Fetch tools should import from here instead of re-implementing these checks,
so the security contract only needs to be gotten right once.

Library-style API: every check here returns a value or raises
``NetGuardError`` rather than calling ``sys.exit`` — this lets library code
(tool handlers that return ``{"ok": False, "error": ...}``) catch and
translate the error, while CLI scripts can still catch ``NetGuardError`` and
turn it into their own exit-code convention.

Adopted by: ``rss_fetch_tool.py``, ``wayback_tool.py``, ``dns_recon_tool.py``,
``cert_transparency_tool.py``, ``ip_info_tool.py`` (for ``MAX_RESPONSE_BYTES`` +
``read_capped``), and the caller-URL fetchers ``notify_tool.py`` /
``uptime_check_tool.py`` (full guard set incl. ``reject_private_target`` +
``SafeRedirectHandler``). The 3 fixed-endpoint recon tools keep their own
hostname regexes (dns/cert regexes differ intentionally) rather than
``validate_hostname``.
"""

import ipaddress
import re
import socket
import urllib.request
from urllib.parse import urlparse

MAX_RESPONSE_BYTES = 10_000_000
DEFAULT_TIMEOUT_SECONDS = 15
MAX_REDIRECTS = 3
ALLOWED_SCHEMES = {"http", "https"}

# One or more dot-separated labels, 1-63 chars each, no leading/trailing
# hyphen, total length <= 253. Rejects shell metacharacters, spaces, and
# anything that isn't a plausible hostname.
HOSTNAME_RE = re.compile(
    r"^(?=.{1,253}$)(?!-)[A-Za-z0-9-]{1,63}(?<!-)(\.(?!-)[A-Za-z0-9-]{1,63}(?<!-))+$"
)


class NetGuardError(Exception):
    """Raised when a _net_guard check fails.

    Callers decide how to surface it: library-style tools catch this and
    return ``{"ok": False, "error": str(exc)}``; CLI scripts catch it and
    ``sys.exit(2)``.
    """


def validate_hostname(host) -> bool:
    """Return True if host is a plausible, injection-free hostname."""
    if not isinstance(host, str) or not host:
        return False
    return bool(HOSTNAME_RE.match(host))


def require_http_scheme(url: str) -> str:
    """Return url if its scheme is http/https, else raise NetGuardError."""
    scheme = urlparse(url).scheme.lower()
    if scheme not in ALLOWED_SCHEMES:
        raise NetGuardError(f"unsupported URL scheme {scheme!r} (only http/https allowed)")
    return url


def _is_ip_address(text: str) -> bool:
    try:
        ipaddress.ip_address(text)
        return True
    except ValueError:
        return False


# A hostname made up of nothing but digits, dots, and an optional "0x" hex
# prefix is trying to *be* an IP address literal. If ipaddress.ip_address()
# (called just before this regex is consulted) already rejected it as not a
# canonical dotted-quad, it's an ambiguous numeric form: a leading-zero octet
# ("0177.0.0.1"), a bare decimal integer ("2130706433"), a hex literal
# ("0x7f000001"), or a short/partial dotted form ("127.1"). Python's
# ipaddress module deliberately refuses to guess what these mean (since
# Python 3.9.5, in response to CVE-2021-29921) — but a hostname like this
# would otherwise fall through to socket.gethostbyname(), whose octal/
# decimal/hex interpretation is glibc/platform-dependent (some resolvers
# treat "0177.0.0.1" as 127.0.0.1 via inet_aton-style parsing). That
# disagreement between our strict parser and the platform resolver is a
# classic SSRF filter bypass, so these forms are rejected outright rather
# than resolved. No legitimate DNS hostname looks like this.
_AMBIGUOUS_NUMERIC_HOST_RE = re.compile(r"^(0x[0-9a-fA-F]+|[0-9.]+)$", re.IGNORECASE)


def reject_private_target(url: str) -> None:
    """Resolve url's host and raise NetGuardError if it maps to a
    private/reserved/loopback/link-local/multicast/unspecified address.

    SSRF defense: a caller-supplied URL fetched over the network could point
    at loopback, RFC1918/link-local ranges, or a cloud metadata endpoint
    (169.254.169.254) unless resolution is checked first. Hostnames are
    resolved via DNS before the check; if resolution fails, the request is
    refused rather than allowed through.

    NOTE: there's a TOCTOU/DNS-rebinding window here — the hostname is
    resolved again (independently) when the actual connection is made, so a
    hostname could theoretically re-resolve to a private address between
    this check and the real request. Fully closing that gap would mean
    pinning the validated IP and connecting to it directly instead of
    letting the hostname re-resolve; out of scope for this pass.
    """
    hostname = urlparse(url).hostname
    if not hostname:
        raise NetGuardError(f"could not determine hostname from {url!r}")
    if _is_ip_address(hostname):
        ip_text = hostname
    elif _AMBIGUOUS_NUMERIC_HOST_RE.match(hostname):
        raise NetGuardError(f"ambiguous numeric host rejected: {hostname!r}")
    else:
        previous_timeout = socket.getdefaulttimeout()
        socket.setdefaulttimeout(DEFAULT_TIMEOUT_SECONDS)
        try:
            ip_text = socket.gethostbyname(hostname)
        except socket.gaierror as exc:
            raise NetGuardError(f"could not resolve host {hostname!r}: {exc}") from exc
        finally:
            socket.setdefaulttimeout(previous_timeout)
    addr = ipaddress.ip_address(ip_text)
    if (
        addr.is_private
        or addr.is_reserved
        or addr.is_loopback
        or addr.is_link_local
        or addr.is_multicast
        or addr.is_unspecified
    ):
        raise NetGuardError(
            f"refusing to fetch {url!r}: host {hostname!r} resolves to non-public address {ip_text}"
        )


def read_capped(response) -> bytes:
    """Read response's body, raising NetGuardError if it exceeds MAX_RESPONSE_BYTES."""
    raw = response.read(MAX_RESPONSE_BYTES + 1)
    if len(raw) > MAX_RESPONSE_BYTES:
        raise NetGuardError(f"response exceeds {MAX_RESPONSE_BYTES} byte limit")
    return raw


class SafeRedirectHandler(urllib.request.HTTPRedirectHandler):
    """Re-validates every redirect hop before following it.

    The default urllib redirect handling blindly follows 301/302/303/307/308
    Location headers, so a public URL that redirects to a private/loopback/
    link-local/metadata address would bypass a pre-request
    ``reject_private_target`` check. This handler re-runs that same
    validation on each hop's resolved target before it's allowed through.
    """

    max_redirections = MAX_REDIRECTS

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        require_http_scheme(newurl)
        reject_private_target(newurl)
        return super().redirect_request(req, fp, code, msg, headers, newurl)


def build_safe_opener() -> urllib.request.OpenerDirector:
    """Build a urllib opener whose redirect hops are re-validated via SafeRedirectHandler."""
    return urllib.request.build_opener(SafeRedirectHandler())
