#!/usr/bin/env python3
"""Keyless DNS / infrastructure reconnaissance for authorized research and defensive use.

Subcommands:
    dns <domain> [--types A,AAAA,MX,NS,TXT,CNAME,SOA,CAA]
        Resolve records via DNS-over-HTTPS (dns.google, falls back to
        cloudflare-dns.com). Also resolves PTR when --types includes PTR and
        <domain> is an IP address.
    subdomains <domain>
        Certificate Transparency subdomain discovery via crt.sh JSON.
    fingerprint <url>
        HTTP header + security-header audit for a single URL.
    whois <domain>
        Wraps the system `whois` command, if present.

stdlib only. Exits 2 on network/HTTP/parse/validation errors.
"""
import argparse
import ipaddress
import json
import re
import shutil
import socket
import subprocess
import sys
import urllib.error
import urllib.parse
import urllib.request

MAX_RESPONSE_BYTES = 10_000_000
MAX_WHOIS_BYTES = 1_000_000
DEFAULT_TIMEOUT_SECONDS = 15
MAX_REDIRECTS = 3
ALLOWED_SCHEMES = {"http", "https"}
USER_AGENT = "Mozilla/5.0 (compatible; hermes-network-recon/1.0)"

DOH_PROVIDERS = ["https://dns.google/resolve", "https://cloudflare-dns.com/dns-query"]
DOH_ACCEPT_HEADER = {"Accept": "application/dns-json"}

DEFAULT_DNS_TYPES = ["A", "AAAA", "MX", "NS", "TXT", "CNAME", "SOA", "CAA"]

CRT_SH_URL = "https://crt.sh/"

SECURITY_HEADERS = [
    "Strict-Transport-Security",
    "Content-Security-Policy",
    "X-Content-Type-Options",
    "X-Frame-Options",
    "Referrer-Policy",
    "Permissions-Policy",
]

# One or more dot-separated labels, 1-63 chars each, no leading/trailing
# hyphen, total length <= 253. Rejects shell metacharacters, spaces, and
# anything that isn't a plausible hostname.
HOSTNAME_RE = re.compile(
    r"^(?=.{1,253}$)(?!-)[A-Za-z0-9-]{1,63}(?<!-)(\.(?!-)[A-Za-z0-9-]{1,63}(?<!-))+$"
)


def _fail(message):
    print(f"error: {message}", file=sys.stderr)
    sys.exit(2)


def validate_domain(domain):
    """Reject anything that isn't a plausible hostname before it touches a URL or subprocess."""
    if not HOSTNAME_RE.match(domain):
        _fail(f"{domain!r} is not a valid hostname")
    return domain


def _require_http_scheme(url):
    scheme = urllib.parse.urlparse(url).scheme.lower()
    if scheme not in ALLOWED_SCHEMES:
        _fail(f"unsupported URL scheme {scheme!r} (only http/https allowed)")


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
#
# Kept in sync with tools/_net_guard.py's reject_private_target and
# skills/research/watch-notify/scripts/watch.py's reject_private_target —
# tests/tools/test_net_guard_drift.py asserts all three agree.
_AMBIGUOUS_NUMERIC_HOST_RE = re.compile(r"^(0x[0-9a-fA-F]+|[0-9.]+)$", re.IGNORECASE)


def _reject_private_target(url):
    """Resolve the URL's host and refuse to proceed if it maps to a
    private/reserved/loopback/link-local/multicast/unspecified address.

    SSRF defense: fetch_fingerprint issues an outbound GET to a caller-supplied
    URL, so without this check a caller could point it at loopback, RFC1918/
    link-local ranges, or a cloud metadata endpoint (169.254.169.254) and read
    back the response. Hostnames are resolved via DNS before the check; if
    resolution fails, the request is refused rather than allowed through.

    NOTE: there's a TOCTOU/DNS-rebinding window here — the hostname is
    resolved again (independently) when the actual connection is made, so a
    hostname could theoretically re-resolve to a private address between
    this check and the real request. Fully closing that gap would mean
    pinning the validated IP and connecting to it directly instead of
    letting the hostname re-resolve; out of scope for this pass.
    """
    hostname = urllib.parse.urlparse(url).hostname
    if not hostname:
        _fail(f"could not determine hostname from {url!r}")
    if is_ip_address(hostname):
        ip_text = hostname
    elif _AMBIGUOUS_NUMERIC_HOST_RE.match(hostname):
        _fail(f"ambiguous numeric host rejected: {hostname!r}")
    else:
        previous_timeout = socket.getdefaulttimeout()
        socket.setdefaulttimeout(DEFAULT_TIMEOUT_SECONDS)
        try:
            ip_text = socket.gethostbyname(hostname)
        except socket.gaierror as exc:
            _fail(f"could not resolve host {hostname!r}: {exc}")
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
        _fail(f"refusing to fetch {url!r}: host {hostname!r} resolves to non-public address {ip_text}")


def _read_capped(response):
    raw = response.read(MAX_RESPONSE_BYTES + 1)
    if len(raw) > MAX_RESPONSE_BYTES:
        _fail(f"response exceeds {MAX_RESPONSE_BYTES} byte limit")
    return raw


def _http_get_json(url, headers=None):
    """Raises urllib.error.URLError or TimeoutError on network failure — callers decide
    whether to retry (query_doh) or fail (main)."""
    _require_http_scheme(url)
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT, **(headers or {})})
    with urllib.request.urlopen(request, timeout=DEFAULT_TIMEOUT_SECONDS) as response:
        body = _read_capped(response).decode("utf-8", errors="replace")
    return json.loads(body)


def _build_ptr_name(ip_text):
    """Build the reverse-DNS query name (in-addr.arpa / ip6.arpa) for an IP."""
    try:
        addr = ipaddress.ip_address(ip_text)
    except ValueError:
        _fail(f"PTR requires an IP address, got: {ip_text}")
    if addr.version == 4:
        return ".".join(reversed(addr.exploded.split("."))) + ".in-addr.arpa"
    nibbles = addr.exploded.replace(":", "")
    return ".".join(reversed(nibbles)) + ".ip6.arpa"


def query_doh(name, record_type):
    """Query DNS-over-HTTPS, trying dns.google first and falling back to Cloudflare."""
    params = urllib.parse.urlencode({"name": name, "type": record_type})
    last_error = None
    for base_url in DOH_PROVIDERS:
        try:
            return _http_get_json(f"{base_url}?{params}", headers=DOH_ACCEPT_HEADER)
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
            last_error = exc
    _fail(f"all DoH providers failed for {name} {record_type}: {last_error}")


def resolve_dns(domain, record_types):
    """Query each requested record type, returning {type: [answer values]}."""
    results = {}
    for record_type in record_types:
        record_type = record_type.strip().upper()
        query_name = _build_ptr_name(domain) if record_type == "PTR" else domain
        payload = query_doh(query_name, record_type)
        answers = payload.get("Answer", [])
        results[record_type] = [a["data"] for a in answers] if answers else []
    return results


def is_ip_address(text):
    try:
        ipaddress.ip_address(text)
        return True
    except ValueError:
        return False


def cmd_dns(args):
    domain = args.domain if is_ip_address(args.domain) else validate_domain(args.domain)
    record_types = [t.strip().upper() for t in args.types.split(",") if t.strip()]
    results = resolve_dns(domain, record_types)
    print(json.dumps({"domain": domain, "records": results}, indent=2))


def fetch_crtsh_subdomains(domain):
    """Query crt.sh's JSON endpoint and return a deduped, sorted list of hostnames."""
    query = urllib.parse.quote(f"%.{domain}")
    url = f"{CRT_SH_URL}?q={query}&output=json"
    entries = _http_get_json(url)
    names = set()
    for entry in entries:
        for name in entry.get("name_value", "").split("\n"):
            name = name.strip().lower().lstrip("*.")
            if name and HOSTNAME_RE.match(name):
                names.add(name)
    return sorted(names)


def cmd_subdomains(args):
    domain = validate_domain(args.domain)
    subdomains = fetch_crtsh_subdomains(domain)
    print(json.dumps({"domain": domain, "count": len(subdomains), "subdomains": subdomains}, indent=2))


def audit_security_headers(headers):
    """Return {present: [...], missing: [...]} for the standard security-header set."""
    header_keys = {k.lower(): k for k in headers.keys()}
    present = [h for h in SECURITY_HEADERS if h.lower() in header_keys]
    missing = [h for h in SECURITY_HEADERS if h.lower() not in header_keys]
    return {"present": present, "missing": missing}


class _SafeRedirectHandler(urllib.request.HTTPRedirectHandler):
    """Re-validates every redirect hop before following it.

    The default urllib redirect handling blindly follows 301/302/303/307/308
    Location headers, so a public URL that redirects to a private/loopback/
    link-local/metadata address would bypass the pre-request
    _reject_private_target check below. This handler re-runs that same
    validation on each hop's resolved target before it's allowed through.
    """

    max_redirections = MAX_REDIRECTS

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        _require_http_scheme(newurl)
        _reject_private_target(newurl)
        return super().redirect_request(req, fp, code, msg, headers, newurl)


def fetch_fingerprint(url):
    _require_http_scheme(url)
    _reject_private_target(url)
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT}, method="GET")
    opener = urllib.request.build_opener(_SafeRedirectHandler())
    with opener.open(request, timeout=DEFAULT_TIMEOUT_SECONDS) as response:
        _read_capped(response)
        headers = dict(response.headers.items())
        status = response.status
    return {
        "url": url,
        "status": status,
        "server": headers.get("Server", ""),
        "x_powered_by": headers.get("X-Powered-By", ""),
        "headers": headers,
        "security_headers": audit_security_headers(headers),
    }


def cmd_fingerprint(args):
    result = fetch_fingerprint(args.url)
    print(json.dumps(result, indent=2))


def run_whois(domain):
    """Wrap the system `whois` binary. List-args only, never shell=True."""
    whois_path = shutil.which("whois")
    if not whois_path:
        _fail("`whois` command not found on this system")
    try:
        completed = subprocess.run(
            [whois_path, domain],
            capture_output=True,
            text=True,
            timeout=DEFAULT_TIMEOUT_SECONDS,
            check=False,
        )
    except subprocess.TimeoutExpired:
        _fail(f"whois lookup for {domain} timed out")
    if completed.returncode != 0 and not completed.stdout:
        _fail(f"whois lookup failed: {completed.stderr.strip()}")
    # Cap output size to match the "cap everywhere" contract applied to HTTP responses.
    return completed.stdout[:MAX_WHOIS_BYTES]


def cmd_whois(args):
    domain = validate_domain(args.domain)
    print(run_whois(domain))


def build_parser():
    parser = argparse.ArgumentParser(description="Keyless DNS / infrastructure recon (authorized use only).")
    subparsers = parser.add_subparsers(dest="command", required=True)

    dns_parser = subparsers.add_parser("dns", help="Resolve DNS records via DoH")
    dns_parser.add_argument("domain", help="Domain name (or IP, for --types PTR)")
    dns_parser.add_argument("--types", default=",".join(DEFAULT_DNS_TYPES), help="Comma-separated record types")
    dns_parser.set_defaults(func=cmd_dns)

    subdomains_parser = subparsers.add_parser("subdomains", help="Discover subdomains via crt.sh")
    subdomains_parser.add_argument("domain", help="Domain name")
    subdomains_parser.set_defaults(func=cmd_subdomains)

    fingerprint_parser = subparsers.add_parser("fingerprint", help="HTTP header + security-header audit")
    fingerprint_parser.add_argument("url", help="Full URL, e.g. https://example.com")
    fingerprint_parser.set_defaults(func=cmd_fingerprint)

    whois_parser = subparsers.add_parser("whois", help="System whois lookup")
    whois_parser.add_argument("domain", help="Domain name")
    whois_parser.set_defaults(func=cmd_whois)

    return parser


def main():
    args = build_parser().parse_args()
    try:
        args.func(args)
    except urllib.error.URLError as exc:
        _fail(f"network request failed: {exc.reason}")
    except TimeoutError:
        _fail(f"network request timed out after {DEFAULT_TIMEOUT_SECONDS}s")


if __name__ == "__main__":
    main()
