#!/usr/bin/env python3
"""Infrastructure drift snapshotting for authorized research and defensive use.

Subcommands:
    snapshot <domain> [--out FILE]
        Gather DNS A/MX/NS/TXT records (DNS-over-HTTPS, dns.google falling
        back to cloudflare-dns.com), Certificate Transparency subdomains
        (crt.sh), and the domain's primary resolved IP into one timestamped
        JSON snapshot. Written to FILE if given, else printed to stdout.
    diff <old.json> <new.json> [--json] [--fail-on-change]
        Structured diff between two snapshots: added/removed DNS records per
        type, added/removed subdomains, and IP change. Human-readable by
        default; --json prints the machine-readable diff instead.
        --fail-on-change exits 1 if any drift was found (0 otherwise) — for
        wiring into a cron/alerting workflow.

This is a snapshot-diff tool, not a live scanner: point-in-time state lives
in the JSON files you pass around. Re-run `snapshot` on a schedule and `diff`
consecutive snapshots to see drift over time.

stdlib only. Exits 2 on network/HTTP/parse/validation errors.
"""
import argparse
import json
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone

MAX_RESPONSE_BYTES = 10_000_000
DEFAULT_TIMEOUT_SECONDS = 15
USER_AGENT = "Mozilla/5.0 (compatible; hermes-infra-monitor/1.0)"

DOH_PROVIDERS = ["https://dns.google/resolve", "https://cloudflare-dns.com/dns-query"]
DOH_ACCEPT_HEADER = {"Accept": "application/dns-json"}
DNS_TYPES = ["A", "MX", "NS", "TXT"]

CRT_SH_URL = "https://crt.sh/"

# One or more dot-separated labels, 1-63 chars each, no leading/trailing
# hyphen, total length <= 253. Rejects shell metacharacters, spaces, and
# anything that isn't a plausible hostname. Same pattern as network-recon
# and cert_transparency_tool.
HOSTNAME_RE = re.compile(
    r"^(?=.{1,253}$)(?!-)[A-Za-z0-9-]{1,63}(?<!-)(\.(?!-)[A-Za-z0-9-]{1,63}(?<!-))+$"
)


def _fail(message):
    print(f"error: {message}", file=sys.stderr)
    sys.exit(2)


def validate_domain(domain):
    """Reject anything that isn't a plausible hostname before it touches a URL."""
    if not HOSTNAME_RE.match(domain):
        _fail(f"{domain!r} is not a valid hostname")
    return domain


def _read_capped(response):
    raw = response.read(MAX_RESPONSE_BYTES + 1)
    if len(raw) > MAX_RESPONSE_BYTES:
        _fail(f"response exceeds {MAX_RESPONSE_BYTES} byte limit")
    return raw


def _http_get_json(url, headers=None):
    """Raises urllib.error.URLError or TimeoutError on network failure — callers decide
    whether to retry (query_doh) or fail (main)."""
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT, **(headers or {})})
    with urllib.request.urlopen(request, timeout=DEFAULT_TIMEOUT_SECONDS) as response:
        body = _read_capped(response).decode("utf-8", errors="replace")
    return json.loads(body)


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
        payload = query_doh(domain, record_type)
        answers = payload.get("Answer", [])
        results[record_type] = sorted(a["data"] for a in answers) if answers else []
    return results


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


def build_snapshot(domain):
    """Assemble one point-in-time snapshot: DNS records, CT subdomains, primary IP."""
    dns_records = resolve_dns(domain, DNS_TYPES)
    subdomains = fetch_crtsh_subdomains(domain)
    resolved_ip = dns_records["A"][0] if dns_records.get("A") else None
    return {
        "domain": domain,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "dns": dns_records,
        "resolved_ip": resolved_ip,
        "subdomain_count": len(subdomains),
        "subdomains": subdomains,
    }


def cmd_snapshot(args):
    domain = validate_domain(args.domain)
    snapshot = build_snapshot(domain)
    text = json.dumps(snapshot, indent=2)
    if args.out:
        try:
            with open(args.out, "w", encoding="utf-8") as handle:
                handle.write(text)
        except OSError as exc:
            _fail(f"could not write {args.out!r}: {exc}")
        print(f"wrote snapshot for {domain} to {args.out}")
    else:
        print(text)


def load_snapshot(path):
    """Load and minimally validate a snapshot JSON file written by cmd_snapshot."""
    try:
        with open(path, "r", encoding="utf-8") as handle:
            raw = handle.read(MAX_RESPONSE_BYTES + 1)
    except OSError as exc:
        _fail(f"could not read {path!r}: {exc}")
    if len(raw) > MAX_RESPONSE_BYTES:
        _fail(f"{path!r} exceeds {MAX_RESPONSE_BYTES} byte limit")
    try:
        snapshot = json.loads(raw)
    except json.JSONDecodeError as exc:
        _fail(f"{path!r} is not valid JSON: {exc}")
    for key in ("domain", "dns", "subdomains"):
        if key not in snapshot:
            _fail(f"{path!r} is missing required snapshot field {key!r}")
    return snapshot


def _diff_list(old_list, new_list):
    old_set, new_set = set(old_list), set(new_list)
    return {"added": sorted(new_set - old_set), "removed": sorted(old_set - new_set)}


def diff_dns(old_dns, new_dns):
    """Per-record-type added/removed diff, only for types present on either side."""
    all_types = sorted(set(old_dns) | set(new_dns))
    changes = {}
    for record_type in all_types:
        record_diff = _diff_list(old_dns.get(record_type, []), new_dns.get(record_type, []))
        if record_diff["added"] or record_diff["removed"]:
            changes[record_type] = record_diff
    return changes


def diff_snapshots(old, new):
    """Combine DNS, subdomain, and IP diffs into one structure with a has_changes flag."""
    dns_changes = diff_dns(old.get("dns", {}), new.get("dns", {}))
    subdomain_changes = _diff_list(old.get("subdomains", []), new.get("subdomains", []))
    old_ip, new_ip = old.get("resolved_ip"), new.get("resolved_ip")
    ip_changed = old_ip != new_ip
    has_changes = bool(dns_changes) or bool(subdomain_changes["added"] or subdomain_changes["removed"]) or ip_changed
    return {
        "domain": new.get("domain", old.get("domain")),
        "old_timestamp": old.get("timestamp"),
        "new_timestamp": new.get("timestamp"),
        "dns_changes": dns_changes,
        "subdomain_changes": subdomain_changes,
        "ip_changed": ip_changed,
        "old_ip": old_ip,
        "new_ip": new_ip,
        "has_changes": has_changes,
    }


def format_diff_human(diff):
    """Render a diff dict as short human-readable text."""
    if not diff["has_changes"]:
        return f"No infrastructure changes detected for {diff['domain']}."

    lines = [f"Infrastructure drift detected for {diff['domain']}:"]
    for record_type, change in diff["dns_changes"].items():
        if change["added"]:
            lines.append(f"  {record_type} added: {', '.join(change['added'])}")
        if change["removed"]:
            lines.append(f"  {record_type} removed: {', '.join(change['removed'])}")
    if diff["ip_changed"]:
        lines.append(f"  resolved IP changed: {diff['old_ip']} -> {diff['new_ip']}")
    subdomain_changes = diff["subdomain_changes"]
    if subdomain_changes["added"]:
        lines.append(f"  subdomains added: {', '.join(subdomain_changes['added'])}")
    if subdomain_changes["removed"]:
        lines.append(f"  subdomains removed: {', '.join(subdomain_changes['removed'])}")
    return "\n".join(lines)


def cmd_diff(args):
    old = load_snapshot(args.old)
    new = load_snapshot(args.new)
    diff = diff_snapshots(old, new)
    if args.json:
        print(json.dumps(diff, indent=2))
    else:
        print(format_diff_human(diff))
    if args.fail_on_change and diff["has_changes"]:
        sys.exit(1)


def build_parser():
    parser = argparse.ArgumentParser(
        description="Infrastructure drift snapshotting for authorized/defensive monitoring."
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    snapshot_parser = subparsers.add_parser("snapshot", help="Capture a point-in-time infra snapshot")
    snapshot_parser.add_argument("domain", help="Domain name")
    snapshot_parser.add_argument("--out", help="Write snapshot JSON to this file instead of stdout")
    snapshot_parser.set_defaults(func=cmd_snapshot)

    diff_parser = subparsers.add_parser("diff", help="Diff two snapshots")
    diff_parser.add_argument("old", help="Path to the older snapshot JSON")
    diff_parser.add_argument("new", help="Path to the newer snapshot JSON")
    diff_parser.add_argument("--json", action="store_true", help="Print the machine-readable diff")
    diff_parser.add_argument(
        "--fail-on-change", action="store_true", help="Exit 1 if any drift was found (for cron/alerting)"
    )
    diff_parser.set_defaults(func=cmd_diff)

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
