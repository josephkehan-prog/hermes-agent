#!/usr/bin/env python3
"""footprint.py — username + email footprint reconnaissance (stdlib only).

Authorized/defensive/research use only — see the skill's ethics note before
running this against anyone who has not consented to the check.

Subcommands:
  username <name>                 curated platform presence check (HTTP status)
  email-permute <first> <last> <domain>   print candidate email addresses
  gravatar <email>                 MD5 -> Gravatar existence check (keyless)
  hibp <email>                     STUB — Have I Been Pwned requires a paid
                                    API key; this subcommand does NOT call it.

Exit codes: 0 = ran, 2 = bad input / network error. Never shells out.
"""
from __future__ import annotations

import argparse
import concurrent.futures
import hashlib
import json
import re
import ssl
import sys
import urllib.error
import urllib.parse
import urllib.request

_MAX_RESPONSE_BYTES = 65536
_REQUEST_TIMEOUT = 10.0
_ALLOWED_SCHEMES = ("http", "https")
_USER_AGENT = (
    "hermes-social-footprint/1.0 "
    "(+https://github.com/NousResearch/hermes-agent; research/OSINT tool, "
    "authorized use only)"
)

# GitHub/GitLab allow dots/hyphens/underscores; keep the allowlist generous
# but bounded so it can never be used to smuggle a path segment or query.
_USERNAME_RE = re.compile(r"^[A-Za-z0-9_.-]{1,39}$")
_NAME_PART_RE = re.compile(r"^[A-Za-z][A-Za-z'-]{0,49}$")
_DOMAIN_RE = re.compile(r"^[A-Za-z0-9]([A-Za-z0-9-]*[A-Za-z0-9])?(\.[A-Za-z0-9]([A-Za-z0-9-]*[A-Za-z0-9])?)+$")

# Control username used to empirically classify soft-404 sites at runtime —
# any real registration of this string would be a remarkable coincidence.
_CONTROL_USERNAME = "hermes-osint-control-zzz9f3k2x"

# (name, url_template) — curated keyless subset. Inspired by the far larger
# sherlock-project/sherlock (MIT, github.com/sherlock-project/sherlock);
# no code vendored from it, just the general status-code-presence technique.
PLATFORMS = [
    ("GitHub", "https://github.com/{u}"),
    ("GitLab", "https://gitlab.com/{u}"),
    ("Reddit", "https://www.reddit.com/user/{u}/about.json"),
    ("Keybase", "https://keybase.io/{u}"),
    ("Dev.to", "https://dev.to/{u}"),
    ("HackerNews", "https://news.ycombinator.com/user?id={u}"),
    ("Docker Hub", "https://hub.docker.com/u/{u}"),
    ("SoundCloud", "https://soundcloud.com/{u}"),
]


class FootprintError(ValueError):
    """Raised on invalid user-supplied input."""


def validate_username(value: str) -> str:
    if not _USERNAME_RE.match(value):
        raise FootprintError(
            f"invalid username {value!r}: only letters, digits, '.', '_', '-' "
            "allowed, 1-39 chars"
        )
    return value


def validate_name_part(value: str, label: str) -> str:
    if not _NAME_PART_RE.match(value):
        raise FootprintError(f"invalid {label} {value!r}: letters/hyphen/apostrophe only")
    return value


def validate_domain(value: str) -> str:
    if "@" in value or " " in value or not _DOMAIN_RE.match(value):
        raise FootprintError(f"invalid domain {value!r}: expected a bare domain like example.com")
    return value


def validate_email(value: str) -> str:
    if "@" not in value or value.startswith("@") or value.endswith("@") or " " in value:
        raise FootprintError(f"invalid email {value!r}: expected local@domain, no spaces")
    local, _, domain = value.partition("@")
    if not local or not _DOMAIN_RE.match(domain):
        raise FootprintError(f"invalid email {value!r}: bad local part or domain")
    return value


def _require_http_scheme(url: str) -> None:
    scheme = urllib.parse.urlsplit(url).scheme
    if scheme not in _ALLOWED_SCHEMES:
        raise FootprintError(f"refusing non-http(s) scheme in URL: {url!r}")


def fetch_status(url: str, timeout: float = _REQUEST_TIMEOUT) -> tuple[int | None, bytes, str | None]:
    """GET url. Returns (status_code, body_bytes, error) — error is None on success."""
    _require_http_scheme(url)
    req = urllib.request.Request(url, headers={"User-Agent": _USER_AGENT})
    ctx = ssl.create_default_context()
    try:
        with urllib.request.urlopen(req, timeout=timeout, context=ctx) as resp:
            return resp.getcode(), resp.read(_MAX_RESPONSE_BYTES), None
    except urllib.error.HTTPError as e:
        body = e.read(_MAX_RESPONSE_BYTES) if e.fp else b""
        return e.code, body, None
    except (urllib.error.URLError, ssl.SSLError, TimeoutError, OSError) as e:
        return None, b"", str(e)[:120]


def _classify(control_status: int | None, target_status: int | None,
              control_body: bytes, target_body: bytes) -> str:
    """Decide present/absent/manual/unknown from a control + target pair.

    control_status is the response for a username that (almost certainly)
    does not exist. If the site 404s the control cleanly, status codes are
    trustworthy. If the site soft-404s (200 for everything), we fall back to
    comparing body length against the control — never claim "present" when
    we can't tell the two apart.
    """
    if target_status is None:
        return "error"
    if control_status in (404, 410):
        if target_status in (404, 410):
            return "absent"
        if target_status == 200:
            return "present"
        return "unknown"
    if control_status == 200:
        # Soft-404 site: compare against the control body as a fingerprint.
        if target_status != 200:
            return "unknown"
        if abs(len(target_body) - len(control_body)) < 32:
            return "absent"  # looks like the same "not found" page
        return "manual"  # differs from control but status alone can't confirm
    return "unknown"


def check_platform(name: str, template: str, username: str, timeout: float) -> dict:
    control_url = template.format(u=_CONTROL_USERNAME)
    target_url = template.format(u=username)
    control_status, control_body, control_err = fetch_status(control_url, timeout)
    target_status, target_body, target_err = fetch_status(target_url, timeout)
    if target_err is not None:
        return {"site": name, "url": target_url, "status": "error", "detail": target_err}
    status = _classify(control_status, target_status, control_body, target_body)
    return {"site": name, "url": target_url, "status": status, "code": target_status}


def cmd_username(args: argparse.Namespace) -> int:
    username = validate_username(args.username)
    results = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=max(1, args.workers)) as ex:
        futs = {
            ex.submit(check_platform, name, template, username, args.timeout): name
            for name, template in PLATFORMS
        }
        for fut in concurrent.futures.as_completed(futs):
            results.append(fut.result())

    order = {"present": 0, "manual": 1, "unknown": 2, "error": 3, "absent": 4}
    results.sort(key=lambda r: (order.get(r["status"], 9), r["site"]))

    if args.json:
        print(json.dumps({"username": username, "results": results}, indent=2))
        return 0

    present = [r for r in results if r["status"] == "present"]
    print(f"USERNAME: {username}  ({len(present)}/{len(PLATFORMS)} confirmed present)")
    print("-" * 62)
    tags = {"present": "[ + ]", "absent": "[ - ]", "manual": "[man]", "unknown": "[ ? ]", "error": "[err]"}
    for r in results:
        print(f"{tags[r['status']]} {r['site']:<12} {r['url']}")
    print("-" * 62)
    print("[ + ] present  [ - ] absent  [man] needs manual confirmation")
    print("[ ? ] ambiguous/bot-blocked  [err] network error")
    print(f"For 500+ site coverage run: sherlock {username}")
    return 0


def email_permutations(first: str, last: str, domain: str) -> list[str]:
    f, l = first.lower(), last.lower()
    fi, li = f[0], l[0]
    patterns = [
        f"{f}.{l}", f"{f}{l}", f, l, f"{fi}.{l}", f"{fi}{l}",
        f"{f}{li}", f"{f}_{l}", f"{l}.{f}", f"{li}{f}", f"{f}-{l}",
    ]
    # dedupe, preserve order
    seen: set[str] = set()
    out = []
    for p in patterns:
        if p not in seen:
            seen.add(p)
            out.append(f"{p}@{domain}")
    return out


def cmd_email_permute(args: argparse.Namespace) -> int:
    first = validate_name_part(args.first, "first name")
    last = validate_name_part(args.last, "last name")
    domain = validate_domain(args.domain)
    candidates = email_permutations(first, last, domain)
    if args.json:
        print(json.dumps({"candidates": candidates}, indent=2))
    else:
        for addr in candidates:
            print(addr)
    return 0


def gravatar_hash(email: str) -> str:
    normalized = email.strip().lower()
    return hashlib.md5(normalized.encode("utf-8")).hexdigest()  # noqa: S324 — Gravatar's protocol mandates MD5, not a security use


def cmd_gravatar(args: argparse.Namespace) -> int:
    email = validate_email(args.email)
    digest = gravatar_hash(email)
    url = f"https://www.gravatar.com/avatar/{digest}?d=404"
    status, _body, err = fetch_status(url)
    if err is not None:
        print(f"error: {err}", file=sys.stderr)
        result = {"email": email, "md5": digest, "url": url, "exists": None, "error": err}
        if args.json:
            print(json.dumps(result, indent=2))
        return 2
    exists = status == 200
    result = {"email": email, "md5": digest, "url": url, "exists": exists, "code": status}
    if args.json:
        print(json.dumps(result, indent=2))
    else:
        print(f"EMAIL: {email}")
        print(f"MD5:   {digest}")
        print(f"URL:   {url}")
        print(f"EXISTS: {exists} (HTTP {status})")
    return 0


_HIBP_STUB_MESSAGE = (
    "[NEEDS-REVIEW] Have I Been Pwned breach-check requires a PAID API key "
    "(haveibeenpwned.com/API/Key) — this subcommand is a STUB and does NOT "
    "call HIBP. No key is wired here by design (see skill's ethics/legal "
    "note). TODO: if the user provides their own key, wire it via an env "
    "var (e.g. HIBP_API_KEY) and honor its rate limit (1 req/1.5-6s "
    "depending on tier) — never hardcode a key in this repo."
)


def cmd_hibp(args: argparse.Namespace) -> int:
    validate_email(args.email)
    print(_HIBP_STUB_MESSAGE)
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="footprint.py",
        description="Username + email footprint reconnaissance (stdlib only, keyless).",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    p_user = sub.add_parser("username", help="check username presence across curated platforms")
    p_user.add_argument("username")
    p_user.add_argument("--json", action="store_true")
    p_user.add_argument("--timeout", type=float, default=_REQUEST_TIMEOUT)
    p_user.add_argument("--workers", type=int, default=8)
    p_user.set_defaults(func=cmd_username)

    p_email = sub.add_parser("email-permute", help="generate candidate email addresses")
    p_email.add_argument("first")
    p_email.add_argument("last")
    p_email.add_argument("domain")
    p_email.add_argument("--json", action="store_true")
    p_email.set_defaults(func=cmd_email_permute)

    p_grav = sub.add_parser("gravatar", help="check Gravatar existence for an email (MD5, keyless)")
    p_grav.add_argument("email")
    p_grav.add_argument("--json", action="store_true")
    p_grav.set_defaults(func=cmd_gravatar)

    p_hibp = sub.add_parser("hibp", help="STUB — Have I Been Pwned requires a paid key, not wired")
    p_hibp.add_argument("email")
    p_hibp.set_defaults(func=cmd_hibp)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return args.func(args)
    except FootprintError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
