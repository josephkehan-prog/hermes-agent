#!/usr/bin/env python3
"""Generic watch-a-source-and-alert engine. stdlib only, no API keys.

Subcommands:
    check <url> --state FILE
        Fetch a URL, SHA-256 the body, compare against the hash stored in
        --state FILE. Reports new / changed / unchanged and updates state.
    watch-json <url> --field a.b.c --state FILE
        Fetch a JSON URL, extract a dotted-path field, compare against the
        value stored in --state FILE. Reports new / changed / unchanged.
    notify <message> --topic TOPIC
        POST message to https://ntfy.sh/<topic> — keyless push notification.

Every network read is capped at 10 MB, only http/https URLs are accepted,
redirects are re-validated against the SSRF guard on every hop, and the
outbound request uses an honest User-Agent with a 15s timeout. No shell is
invoked. Exits 2 on network/HTTP/parse/validation errors.
"""
import argparse
import hashlib
import ipaddress
import json
import re
import socket
import sys
import urllib.error
import urllib.parse
import urllib.request

MAX_RESPONSE_BYTES = 10_000_000
DEFAULT_TIMEOUT_SECONDS = 15
MAX_REDIRECTS = 3
ALLOWED_SCHEMES = {"http", "https"}
USER_AGENT = "Mozilla/5.0 (compatible; hermes-watch-notify/1.0; +research)"

NTFY_BASE_URL = "https://ntfy.sh"
MAX_TOPIC_LENGTH = 64
MAX_MESSAGE_BYTES = 4096
TOPIC_RE = re.compile(r"^[A-Za-z0-9_-]{1,64}$")


def _fail(message):
    print(f"error: {message}", file=sys.stderr)
    sys.exit(2)


def require_http_scheme(url):
    scheme = urllib.parse.urlparse(url).scheme.lower()
    if scheme not in ALLOWED_SCHEMES:
        _fail(f"unsupported URL scheme {scheme!r} (only http/https allowed)")


def reject_private_target(url):
    """Resolve the URL's host and refuse to proceed if it maps to a
    private/reserved/loopback/link-local/multicast/unspecified address.

    SSRF defense: every subcommand here issues an outbound GET to a
    caller-supplied URL, so without this check a caller could point it at
    loopback, RFC1918/link-local ranges, or a cloud metadata endpoint
    (169.254.169.254) and read back the response.

    NOTE: there's a TOCTOU/DNS-rebinding window — the hostname is resolved
    again (independently) when the actual connection is made, so it could
    theoretically re-resolve to a private address between this check and
    the real request. Closing that gap fully means pinning the validated IP
    and connecting to it directly; out of scope for this pass.
    """
    hostname = urllib.parse.urlparse(url).hostname
    if not hostname:
        _fail(f"could not determine hostname from {url!r}")
    if _is_ip_address(hostname):
        ip_text = hostname
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


def _is_ip_address(text):
    try:
        ipaddress.ip_address(text)
        return True
    except ValueError:
        return False


def read_capped(response):
    raw = response.read(MAX_RESPONSE_BYTES + 1)
    if len(raw) > MAX_RESPONSE_BYTES:
        _fail(f"response exceeds {MAX_RESPONSE_BYTES} byte limit")
    return raw


class _SafeRedirectHandler(urllib.request.HTTPRedirectHandler):
    """Re-validates every redirect hop before following it.

    The default urllib redirect handling blindly follows 301/302/303/307/308
    Location headers, so a public URL that redirects to a private/loopback/
    metadata address would bypass the pre-request reject_private_target
    check below. This handler re-runs that same validation on each hop.
    """

    max_redirections = MAX_REDIRECTS

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        require_http_scheme(newurl)
        reject_private_target(newurl)
        return super().redirect_request(req, fp, code, msg, headers, newurl)


def build_safe_opener():
    return urllib.request.build_opener(_SafeRedirectHandler())


def fetch_url(url, method="GET", data=None, extra_headers=None):
    """Fetch url with the SSRF guard applied and a capped, decoded body returned."""
    require_http_scheme(url)
    reject_private_target(url)
    headers = {"User-Agent": USER_AGENT, **(extra_headers or {})}
    request = urllib.request.Request(url, data=data, headers=headers, method=method)
    opener = build_safe_opener()
    try:
        with opener.open(request, timeout=DEFAULT_TIMEOUT_SECONDS) as response:
            raw = read_capped(response)
            status = response.status
    except urllib.error.URLError as exc:
        _fail(f"failed to fetch {url}: {exc}")
    return raw, status


def compute_hash(data):
    return hashlib.sha256(data).hexdigest()


def load_state(path):
    try:
        with open(path, "r", encoding="utf-8") as handle:
            return json.load(handle)
    except FileNotFoundError:
        return {}
    except json.JSONDecodeError as exc:
        _fail(f"state file {path!r} is not valid JSON: {exc}")


def save_state(path, state):
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(state, handle, indent=2, sort_keys=True)


def extract_json_field(payload, field):
    """Walk a dotted path (a.b.c, list indices as digits) through payload."""
    current = payload
    for segment in field.split("."):
        if isinstance(current, list) and segment.isdigit():
            index = int(segment)
            if index >= len(current):
                _fail(f"field {field!r}: index {index} out of range")
            current = current[index]
        elif isinstance(current, dict):
            if segment not in current:
                _fail(f"field {field!r}: key {segment!r} not found")
            current = current[segment]
        else:
            _fail(f"field {field!r}: cannot descend into {type(current).__name__} at {segment!r}")
    return current


def cmd_check(args):
    raw, _status = fetch_url(args.url)
    new_hash = compute_hash(raw)
    state = load_state(args.state)
    previous = state.get(args.url, {})
    old_hash = previous.get("hash")

    if old_hash is None:
        result = "new"
    elif old_hash == new_hash:
        result = "unchanged"
    else:
        result = "changed"

    state[args.url] = {"hash": new_hash}
    save_state(args.state, state)
    print(json.dumps({"url": args.url, "result": result, "hash": new_hash}, indent=2))


def cmd_watch_json(args):
    raw, _status = fetch_url(args.url)
    try:
        payload = json.loads(raw.decode("utf-8", errors="replace"))
    except json.JSONDecodeError as exc:
        _fail(f"response from {args.url} is not valid JSON: {exc}")

    value = extract_json_field(payload, args.field)
    state = load_state(args.state)
    key = f"{args.url}::{args.field}"
    previous = state.get(key, {})
    old_value = previous.get("value", previous.get("_missing", object()))
    had_previous = "value" in previous

    if not had_previous:
        result = "new"
    elif old_value == value:
        result = "unchanged"
    else:
        result = "changed"

    state[key] = {"value": value}
    save_state(args.state, state)
    print(json.dumps({"url": args.url, "field": args.field, "result": result, "value": value}, indent=2))


def validate_topic(topic):
    if not TOPIC_RE.match(topic):
        _fail(f"topic {topic!r} must match {TOPIC_RE.pattern} (max {MAX_TOPIC_LENGTH} chars)")
    return topic


def cmd_notify(args):
    topic = validate_topic(args.topic)
    message = args.message.encode("utf-8")
    if len(message) > MAX_MESSAGE_BYTES:
        _fail(f"message exceeds {MAX_MESSAGE_BYTES} byte limit")

    url = f"{NTFY_BASE_URL}/{topic}"
    _raw, status = fetch_url(url, method="POST", data=message, extra_headers={"Content-Type": "text/plain"})
    print(json.dumps({"topic": topic, "status": status, "sent": True}, indent=2))


def build_parser():
    parser = argparse.ArgumentParser(description="Watch a source, detect a change, alert.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    check_parser = subparsers.add_parser("check", help="hash a URL's body and diff against stored state")
    check_parser.add_argument("url")
    check_parser.add_argument("--state", required=True, help="path to JSON state file")
    check_parser.set_defaults(func=cmd_check)

    json_parser = subparsers.add_parser("watch-json", help="extract a JSON field and diff against stored state")
    json_parser.add_argument("url")
    json_parser.add_argument("--field", required=True, help="dotted path, e.g. data.status")
    json_parser.add_argument("--state", required=True, help="path to JSON state file")
    json_parser.set_defaults(func=cmd_watch_json)

    notify_parser = subparsers.add_parser("notify", help="push a message to ntfy.sh/<topic>")
    notify_parser.add_argument("message")
    notify_parser.add_argument("--topic", required=True, help="ntfy.sh topic (unguessable, no auth)")
    notify_parser.set_defaults(func=cmd_notify)

    return parser


def main():
    parser = build_parser()
    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
