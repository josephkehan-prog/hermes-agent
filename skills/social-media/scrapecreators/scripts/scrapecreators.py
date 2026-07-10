#!/usr/bin/env python3
"""scrapecreators.py — CLI wrapper for the ScrapeCreators API (stdlib only).

ScrapeCreators (scrapecreators.com) is a PAID social-media scraping API
covering TikTok, Instagram, YouTube, X/Twitter, Reddit, LinkedIn, Facebook,
and Threads. This wrapper requires a paid key — see the skill's SKILL.md.

Subcommands:
  profile <platform> <handle>              fetch a public profile
  posts <platform> <handle> [--limit N]    fetch recent posts for a profile
  search <platform> <query>                search a platform (where supported)

Auth: reads SCRAPECREATORS_API_KEY from the environment and sends it as the
`x-api-key` header. If unset, every subcommand prints a [NEEDS-KEY] message
and exits 2 WITHOUT making a network call — this script never hardcodes or
prompts for a key, and never prints the key value.

Endpoint paths below follow the commonly-documented ScrapeCreators v1 shape
(GET /v1/<platform>/profile?handle=..., /v1/<platform>/posts, /v1/<platform>/
search) but are NOT verified against live docs in this environment — verify
each against your ScrapeCreators dashboard/docs before relying on it, and
correct the PLATFORM_ENDPOINTS entry for that platform if it drifts.

Exit codes: 0 = ran, 2 = bad input / missing key / network or HTTP error.
Never shells out.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import urllib.error
import urllib.parse
import urllib.request

API_BASE = "https://api.scrapecreators.com"
ENV_VAR = "SCRAPECREATORS_API_KEY"
REQUEST_TIMEOUT = 20.0
MAX_RESPONSE_BYTES = 10_000_000
USER_AGENT = "hermes-scrapecreators-skill/1.0"

ALLOWED_PLATFORMS = frozenset(
    {"tiktok", "instagram", "youtube", "twitter", "reddit", "linkedin", "facebook", "threads"}
)

# Handles: letters/digits/dot/underscore/hyphen, optional leading '@'. This
# whitelist inherently excludes control characters, CR/LF, and path/query
# injection — nothing outside it is accepted.
_HANDLE_RE = re.compile(r"^@?[A-Za-z0-9](?:[A-Za-z0-9_.\-]{0,63})$")

# Documented v1 endpoint patterns — verify each against your ScrapeCreators
# dashboard/docs before relying on it; per-platform paths can drift from
# these, so each is its own constant, easy to correct in isolation.
PLATFORM_ENDPOINTS = {
    "tiktok": {"profile": "/v1/tiktok/profile", "posts": "/v1/tiktok/posts", "search": "/v1/tiktok/search"},
    "instagram": {"profile": "/v1/instagram/profile", "posts": "/v1/instagram/posts", "search": "/v1/instagram/search"},
    "youtube": {"profile": "/v1/youtube/profile", "posts": "/v1/youtube/posts", "search": "/v1/youtube/search"},
    "twitter": {"profile": "/v1/twitter/profile", "posts": "/v1/twitter/posts", "search": "/v1/twitter/search"},
    "reddit": {"profile": "/v1/reddit/profile", "posts": "/v1/reddit/posts", "search": "/v1/reddit/search"},
    "linkedin": {"profile": "/v1/linkedin/profile", "posts": "/v1/linkedin/posts", "search": "/v1/linkedin/search"},
    "facebook": {"profile": "/v1/facebook/profile", "posts": "/v1/facebook/posts", "search": "/v1/facebook/search"},
    "threads": {"profile": "/v1/threads/profile", "posts": "/v1/threads/posts", "search": "/v1/threads/search"},
}

_NEEDS_KEY_MESSAGE = (
    "[NEEDS-KEY] ScrapeCreators requires a paid API key. Set "
    f"{ENV_VAR} in ~/.hermes/.env — get one at https://scrapecreators.com"
)


class ScrapeCreatorsError(ValueError):
    """Raised on invalid user input or a request failure."""


def validate_platform(value: str) -> str:
    platform = value.strip().lower()
    if platform not in ALLOWED_PLATFORMS:
        raise ScrapeCreatorsError(
            f"invalid platform {value!r}: must be one of {sorted(ALLOWED_PLATFORMS)}"
        )
    return platform


def validate_handle(value: str) -> str:
    if not _HANDLE_RE.match(value):
        raise ScrapeCreatorsError(
            f"invalid handle {value!r}: only letters, digits, '.', '_', '-', optional "
            "leading '@' allowed, 1-64 chars"
        )
    return value


def validate_query(value: str) -> str:
    if not value or any(ord(ch) < 32 for ch in value):
        raise ScrapeCreatorsError(f"invalid query {value!r}: empty or contains control characters")
    return value


def _endpoint_path(platform: str, endpoint_key: str) -> str:
    try:
        return PLATFORM_ENDPOINTS[platform][endpoint_key]
    except KeyError as exc:
        raise ScrapeCreatorsError(
            f"no documented {endpoint_key!r} endpoint for platform {platform!r}"
        ) from exc


def _build_request(platform: str, endpoint_key: str, params: dict, api_key: str) -> urllib.request.Request:
    path = _endpoint_path(platform, endpoint_key)
    query = urllib.parse.urlencode(params, quote_via=urllib.parse.quote)
    url = f"{API_BASE}{path}?{query}"
    return urllib.request.Request(
        url,
        headers={"x-api-key": api_key, "User-Agent": USER_AGENT, "Accept": "application/json"},
    )


def _request(platform: str, endpoint_key: str, params: dict, api_key: str) -> bytes:
    """Send the request and return the raw response body. Never logs api_key."""
    req = _build_request(platform, endpoint_key, params, api_key)
    try:
        with urllib.request.urlopen(req, timeout=REQUEST_TIMEOUT) as resp:
            raw = resp.read(MAX_RESPONSE_BYTES + 1)
    except urllib.error.HTTPError as exc:
        if exc.code == 401:
            raise ScrapeCreatorsError("HTTP 401 unauthorized — check your SCRAPECREATORS_API_KEY") from exc
        if exc.code == 429:
            raise ScrapeCreatorsError("HTTP 429 rate limited — slow down or check your plan quota") from exc
        body = exc.read(200) if exc.fp else b""
        raise ScrapeCreatorsError(f"HTTP {exc.code}: {body[:200]!r}") from exc
    except urllib.error.URLError as exc:
        raise ScrapeCreatorsError(f"network error: {exc.reason}") from exc
    if len(raw) > MAX_RESPONSE_BYTES:
        raise ScrapeCreatorsError(f"response exceeds {MAX_RESPONSE_BYTES} bytes")
    return raw


def _require_api_key() -> str | None:
    api_key = os.getenv(ENV_VAR)
    return api_key if api_key else None


def _print_body(raw: bytes) -> None:
    try:
        print(json.dumps(json.loads(raw.decode("utf-8")), indent=2))
    except (json.JSONDecodeError, UnicodeDecodeError):
        print(raw.decode("utf-8", errors="replace"))


def cmd_profile(args: argparse.Namespace) -> int:
    platform = validate_platform(args.platform)
    handle = validate_handle(args.handle)
    api_key = _require_api_key()
    if not api_key:
        print(_NEEDS_KEY_MESSAGE, file=sys.stderr)
        return 2
    raw = _request(platform, "profile", {"handle": handle}, api_key)
    _print_body(raw)
    return 0


def cmd_posts(args: argparse.Namespace) -> int:
    platform = validate_platform(args.platform)
    handle = validate_handle(args.handle)
    api_key = _require_api_key()
    if not api_key:
        print(_NEEDS_KEY_MESSAGE, file=sys.stderr)
        return 2
    raw = _request(platform, "posts", {"handle": handle, "limit": args.limit}, api_key)
    _print_body(raw)
    return 0


def cmd_search(args: argparse.Namespace) -> int:
    platform = validate_platform(args.platform)
    query = validate_query(args.query)
    api_key = _require_api_key()
    if not api_key:
        print(_NEEDS_KEY_MESSAGE, file=sys.stderr)
        return 2
    raw = _request(platform, "search", {"query": query}, api_key)
    _print_body(raw)
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="scrapecreators.py",
        description="ScrapeCreators API wrapper — paid social-media scraping (requires SCRAPECREATORS_API_KEY).",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    p_profile = sub.add_parser("profile", help="fetch a public profile")
    p_profile.add_argument("platform", help=f"one of {sorted(ALLOWED_PLATFORMS)}")
    p_profile.add_argument("handle")
    p_profile.set_defaults(func=cmd_profile)

    p_posts = sub.add_parser("posts", help="fetch recent posts for a profile")
    p_posts.add_argument("platform", help=f"one of {sorted(ALLOWED_PLATFORMS)}")
    p_posts.add_argument("handle")
    p_posts.add_argument("--limit", type=int, default=20)
    p_posts.set_defaults(func=cmd_posts)

    p_search = sub.add_parser("search", help="search a platform (where supported)")
    p_search.add_argument("platform", help=f"one of {sorted(ALLOWED_PLATFORMS)}")
    p_search.add_argument("query")
    p_search.set_defaults(func=cmd_search)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return args.func(args)
    except ScrapeCreatorsError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
