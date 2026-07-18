#!/usr/bin/env python3
"""footprint.py — keyless username presence checker (stdlib only, no installs).

A zero-dependency fallback for OSINT username recon when sherlock/maigret are
not installed. Checks a curated set of high-signal platforms by fetching each
profile URL and classifying the response. Runs concurrently, respects a global
timeout, prints a compact report (text or JSON).

Usage:
  python3 footprint.py <username> [--json] [--timeout SECONDS] [--workers N]

Exit codes: 0 = ran, 2 = bad args. Never raises on per-site network errors.

Not a replacement for sherlock/maigret (500+ sites); this is the always-works
local baseline. Escalate to sherlock (`sherlock <user>`) for full coverage.
"""
import argparse
import concurrent.futures
import json
import ssl
import sys
import urllib.error
import urllib.request

# (name, url_template, absence_marker, reliable)
# reliable=True  -> HTTP 404/marker cleanly distinguishes present/absent.
# reliable=False -> site soft-404s (returns 200 for any name, JS-rendered); we
#   never claim "present" for these — reported as "manual" for human check.
# absence_marker: substring appearing ONLY on a not-found page (server-rendered).
SITES = [
    # Reliable — clean 404 or stable server-side "not found" marker.
    ("GitHub", "https://github.com/{u}", None, True),
    ("GitLab", "https://gitlab.com/{u}", None, True),
    ("DevTo", "https://dev.to/{u}", None, True),
    ("YouTube", "https://www.youtube.com/@{u}", None, True),
    ("Keybase", "https://keybase.io/{u}", None, True),
    ("Docker", "https://hub.docker.com/u/{u}", None, True),
    ("SoundCloud", "https://soundcloud.com/{u}", None, True),
    ("HackerNews", "https://news.ycombinator.com/user?id={u}", "No such user.", True),
    ("Steam", "https://steamcommunity.com/id/{u}", "could not be found", True),
    ("Reddit", "https://www.reddit.com/user/{u}/about.json", None, True),
    # Weak — soft-404 / JS-rendered; presence NOT decidable by HTTP alone.
    ("Instagram", "https://www.instagram.com/{u}/", None, False),
    ("X/Twitter", "https://x.com/{u}", None, False),
    ("Twitch", "https://www.twitch.tv/{u}", None, False),
    ("Medium", "https://medium.com/@{u}", None, False),
    ("Telegram", "https://t.me/{u}", None, False),
    ("Pinterest", "https://www.pinterest.com/{u}/", None, False),
    ("Replit", "https://replit.com/@{u}", None, False),
    ("PyPI", "https://pypi.org/user/{u}/", None, False),
]

UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 hermes-footprint"


def check(site, username, timeout):
    name, template, absence_marker, reliable = site
    url = template.format(u=username)
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    ctx = ssl.create_default_context()
    try:
        with urllib.request.urlopen(req, timeout=timeout, context=ctx) as resp:
            code = resp.getcode()
            body = resp.read(65536).decode("utf-8", "ignore") if absence_marker else ""
    except urllib.error.HTTPError as e:
        status = "absent" if e.code in (404, 410) else "unknown"
        return {"site": name, "url": url, "status": status, "code": e.code, "reliable": reliable}
    except (urllib.error.URLError, ssl.SSLError, TimeoutError, OSError) as e:
        return {"site": name, "url": url, "status": "error", "detail": str(e)[:80], "reliable": reliable}
    if absence_marker and absence_marker.lower() in body.lower():
        return {"site": name, "url": url, "status": "absent", "code": code, "reliable": reliable}
    if code == 200:
        # Weak sites soft-404 as 200 — never claim present, flag for manual check.
        status = "present" if reliable else "manual"
        return {"site": name, "url": url, "status": status, "code": code, "reliable": reliable}
    return {"site": name, "url": url, "status": "unknown", "code": code, "reliable": reliable}


def main():
    p = argparse.ArgumentParser(description="Keyless username presence checker (stdlib).")
    p.add_argument("username")
    p.add_argument("--json", action="store_true", help="emit JSON instead of text")
    p.add_argument("--timeout", type=float, default=8.0, help="per-site timeout seconds")
    p.add_argument("--workers", type=int, default=8, help="concurrent requests")
    args = p.parse_args()

    if not args.username.strip():
        print("error: empty username", file=sys.stderr)
        return 2

    results = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=max(1, args.workers)) as ex:
        futs = {ex.submit(check, s, args.username, args.timeout): s for s in SITES}
        for fut in concurrent.futures.as_completed(futs):
            results.append(fut.result())

    order = {"present": 0, "manual": 1, "unknown": 2, "error": 3, "absent": 4}
    results.sort(key=lambda r: (order.get(r["status"], 9), r["site"]))

    if args.json:
        print(json.dumps({"username": args.username, "results": results}, indent=2))
        return 0

    present = [r for r in results if r["status"] == "present"]
    reliable_n = sum(1 for s in SITES if s[3])
    print(f"USERNAME: {args.username}  ({len(present)}/{reliable_n} confirmed on reliable sites)")
    print("-" * 62)
    tags = {"present": "[ + ]", "absent": "[ - ]", "manual": "[man]", "unknown": "[ ? ]", "error": "[err]"}
    for r in results:
        print(f"{tags[r['status']]} {r['site']:<12} {r['url']}")
    print("-" * 62)
    print("[ + ] confirmed (reliable 404 semantics)  [ - ] absent  [man] soft-404")
    print("site — open the URL to confirm  [ ? ] bot-blocked/ambiguous  [err] network.")
    print("For 500+ site coverage run:  sherlock " + args.username)
    return 0


if __name__ == "__main__":
    sys.exit(main())
