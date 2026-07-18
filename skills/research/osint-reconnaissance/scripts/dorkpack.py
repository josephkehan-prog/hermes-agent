#!/usr/bin/env python3
"""dorkpack.py - emit ready-to-paste search "dork" queries for an OSINT target.

Pure string generator. STDLIB ONLY: no pip packages, no network calls.
It never fetches anything -- it only prints query strings meant to be
pasted into a browser (Hermes drives the browser toolset separately).

Usage:
    dorkpack.py --name "First Last"
    dorkpack.py --username handle
    dorkpack.py --email user@example.com
    dorkpack.py --domain example.com
    (any combination of the above; at least one is required)
    dorkpack.py --name "Ada Lovelace" --engine google
    dorkpack.py --domain example.com --json
"""

import argparse
import json
import re
import sys

DOMAIN_RE = re.compile(r"^[A-Za-z0-9]([A-Za-z0-9-]*[A-Za-z0-9])?(\.[A-Za-z0-9]([A-Za-z0-9-]*[A-Za-z0-9])?)+$")


class DorkError(ValueError):
    """Raised when a target value fails validation."""


def validate_email(value):
    if "@" not in value or value.startswith("@") or value.endswith("@"):
        raise DorkError('invalid --email %r: must contain "@" with text on both sides' % value)
    if " " in value:
        raise DorkError("invalid --email %r: must not contain spaces" % value)
    return value


def validate_domain(value):
    if "@" in value:
        raise DorkError("invalid --domain %r: must not contain '@' (that looks like an email)" % value)
    if " " in value:
        raise DorkError("invalid --domain %r: must not contain spaces" % value)
    if "." not in value or not DOMAIN_RE.match(value):
        raise DorkError('invalid --domain %r: expected a bare domain like "example.com"' % value)
    return value


def validate_name(value):
    if not value.strip():
        raise DorkError("invalid --name: must not be blank")
    return value


def validate_username(value):
    if not value.strip() or " " in value:
        raise DorkError("invalid --username %r: must be non-blank with no spaces" % value)
    return value


# Each builder returns a list of (label, google_query_or_None, bing_query_or_None).
# A None means "no equivalent operator on that engine" -> skipped for that engine.

def name_dorks(name):
    q = '"%s"' % name
    return [
        ("LinkedIn profile", '%s site:linkedin.com/in' % q, '%s site:linkedin.com/in' % q),
        ("Resume / CV files", '%s (resume OR cv) filetype:pdf' % q, '%s (resume OR cv) filetype:pdf' % q),
        ("Contact info mentions", 'intext:%s (email OR phone OR contact)' % q, '%s (email OR phone OR contact)' % q),
        ("GitHub presence", '%s site:github.com' % q, '%s site:github.com' % q),
    ]


def username_dorks(username):
    return [
        ("Reddit mentions", 'intext:%s site:reddit.com' % username, '%s site:reddit.com' % username),
        ("Code hosting profiles", '"%s" (site:github.com OR site:gitlab.com)' % username,
         '"%s" (site:github.com OR site:gitlab.com)' % username),
        ("URL slug matches", 'inurl:%s' % username, 'inurl:%s' % username),
    ]


def email_dorks(email):
    domain = email.split("@", 1)[1]
    return [
        ("Exact mentions", '"%s"' % email, '"%s"' % email),
        ("Off-site mentions", 'intext:"%s" -site:%s' % (email, domain), '"%s" -site:%s' % (email, domain)),
        ("Leaked in spreadsheets/docs", '"%s" (filetype:xls OR filetype:csv OR filetype:txt)' % email,
         '"%s" (filetype:xls OR filetype:csv OR filetype:txt)' % email),
    ]


def domain_dorks(domain):
    return [
        ("All indexed pages", 'site:%s' % domain, 'site:%s' % domain),
        ("Public documents", 'site:%s (filetype:pdf OR filetype:xls OR filetype:doc)' % domain,
         'site:%s (filetype:pdf OR filetype:xls OR filetype:doc)' % domain),
        ("Login / admin surfaces", 'site:%s inurl:(login OR admin OR dashboard)' % domain,
         'site:%s (inurl:login OR inurl:admin OR inurl:dashboard)' % domain),
        ("Off-site brand mentions", '"%s" -site:%s' % (domain, domain), '"%s" -site:%s' % (domain, domain)),
        ("Pastebin leaks", 'site:pastebin.com "%s"' % domain, 'site:pastebin.com "%s"' % domain),
    ]


CATEGORY_BUILDERS = (
    ("name", "Name", validate_name, name_dorks),
    ("username", "Username", validate_username, username_dorks),
    ("email", "Email", validate_email, email_dorks),
    ("domain", "Domain", validate_domain, domain_dorks),
)


def build_records(args):
    """Return a flat list of {category, label, query, engine} dicts."""
    records = []
    for attr, category_label, validate, builder in CATEGORY_BUILDERS:
        raw = getattr(args, attr)
        if raw is None:
            continue
        value = validate(raw)
        for label, google_q, bing_q in builder(value):
            if args.engine in ("google", "both") and google_q is not None:
                records.append({"category": category_label, "label": label, "query": google_q, "engine": "google"})
            if args.engine in ("bing", "both") and bing_q is not None:
                records.append({"category": category_label, "label": label, "query": bing_q, "engine": "bing"})
    return records


def print_text(records):
    current_category = None
    for rec in records:
        if rec["category"] != current_category:
            current_category = rec["category"]
            print()
            print("== %s ==" % current_category)
        print("[%s/%s] %s" % (rec["engine"], rec["label"], rec["query"]))


def build_parser():
    parser = argparse.ArgumentParser(
        prog="dorkpack.py",
        description="Generate ready-to-paste Google/Bing OSINT dork queries. "
                     "String generator only -- no network calls, no fetching.",
    )
    parser.add_argument("--name", metavar="NAME", help='person full name, e.g. "First Last"')
    parser.add_argument("--username", metavar="HANDLE", help="username / handle")
    parser.add_argument("--email", metavar="ADDR", help="email address")
    parser.add_argument("--domain", metavar="DOMAIN", help="domain or company site, e.g. example.com")
    parser.add_argument("--engine", choices=["google", "bing", "both"], default="both",
                         help="which engine syntax to emit (default: both)")
    parser.add_argument("--json", action="store_true", dest="as_json",
                         help="emit structured JSON instead of grouped plain text")
    return parser


def main(argv=None):
    parser = build_parser()
    args = parser.parse_args(argv)

    if not any((args.name, args.username, args.email, args.domain)):
        parser.error("at least one of --name, --username, --email, --domain is required")

    try:
        records = build_records(args)
    except DorkError as exc:
        parser.error(str(exc))
        return 2  # unreachable; parser.error exits, but keeps linters happy

    if args.as_json:
        print(json.dumps(records, indent=2))
    else:
        print_text(records)
    return 0


if __name__ == "__main__":
    sys.exit(main())
