#!/usr/bin/env python3
"""Pull recent (~30 day) public chatter on a topic from keyless sources.

Sources: Reddit search JSON, Hacker News Algolia API, Polymarket Gamma API,
GitHub repo search. No API keys, no paid endpoints.

Usage:
    python3 last30days.py search <query> [--sources reddit,hn,polymarket,github|all] [--limit N]
    python3 last30days.py reddit <query> [--limit N]
    python3 last30days.py hn <query> [--limit N]
    python3 last30days.py polymarket <query> [--limit N]
    python3 last30days.py github <query> [--limit N]

Add --json to any subcommand for machine-readable output.

stdlib only.
"""
import argparse
import json
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone

DEFAULT_TIMEOUT_SECONDS = 15
DEFAULT_LIMIT = 15
MAX_QUERY_CHARS = 200
MAX_RESPONSE_BYTES = 10_000_000
THIRTY_DAYS_SECONDS = 30 * 24 * 60 * 60
POLYMARKET_FETCH_LIMIT = 200  # over-fetch, then filter by query client-side

USER_AGENT = "Mozilla/5.0 (compatible; last30days-skill/1.1; +research)"
REDDIT_USER_AGENT = "last30days-skill/1.1 (by /u/research)"
GITHUB_HEADERS = {"Accept": "application/vnd.github+json"}

REDDIT_SEARCH_URL = "https://www.reddit.com/search.json"
REDDIT_OLD_SEARCH_URL = "https://old.reddit.com/search.json"
HN_SEARCH_URL = "https://hn.algolia.com/api/v1/search_by_date"
POLYMARKET_MARKETS_URL = "https://gamma-api.polymarket.com/markets"
GITHUB_SEARCH_URL = "https://api.github.com/search/repositories"

SOURCES = ["reddit", "hn", "polymarket", "github"]


class SourceFetchError(Exception):
    """Raised when a source cannot be fetched or parsed."""


def fetch_url(url, user_agent=USER_AGENT, extra_headers=None):
    headers = {"User-Agent": user_agent, **(extra_headers or {})}
    request = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(request, timeout=DEFAULT_TIMEOUT_SECONDS) as response:
            raw = response.read(MAX_RESPONSE_BYTES + 1)
    except urllib.error.URLError as exc:
        raise SourceFetchError(f"failed to fetch {url}: {exc}") from exc
    if len(raw) > MAX_RESPONSE_BYTES:
        raise SourceFetchError(f"response from {url} exceeds {MAX_RESPONSE_BYTES} byte limit")
    return raw.decode("utf-8", errors="replace")


def fetch_json(url, user_agent=USER_AGENT, extra_headers=None):
    text = fetch_url(url, user_agent=user_agent, extra_headers=extra_headers)
    try:
        return json.loads(text)
    except json.JSONDecodeError as exc:
        raise SourceFetchError(f"response from {url} is not valid JSON: {exc}") from exc


def compute_cutoff(now=None):
    """Return (epoch_seconds, iso_date) for 30 days before `now` (defaults to time.time())."""
    reference = now if now is not None else time.time()
    cutoff_epoch = int(reference) - THIRTY_DAYS_SECONDS
    cutoff_date = datetime.fromtimestamp(cutoff_epoch, tz=timezone.utc).strftime("%Y-%m-%d")
    return cutoff_epoch, cutoff_date


def parse_reddit_json(payload, limit):
    children = payload.get("data", {}).get("children", [])
    entries = []
    for child in children[:limit]:
        post = child.get("data", {})
        permalink = post.get("permalink", "")
        entries.append({
            "source": "reddit",
            "title": post.get("title", ""),
            "date": _epoch_to_iso(post.get("created_utc")),
            "link": f"https://www.reddit.com{permalink}" if permalink else "",
            "metric": f"score {post.get('score', 0)} · r/{post.get('subreddit', '?')}",
        })
    return entries


def fetch_reddit(query, limit):
    params = urllib.parse.urlencode({"q": query, "sort": "new", "t": "month", "limit": limit})
    try:
        payload = fetch_json(f"{REDDIT_SEARCH_URL}?{params}", user_agent=REDDIT_USER_AGENT)
    except SourceFetchError:
        # www.reddit.com/*.json frequently 403s non-browser clients; old.reddit.com
        # sometimes still answers. See SKILL.md's "Reddit 403 fallback" note.
        payload = fetch_json(f"{REDDIT_OLD_SEARCH_URL}?{params}", user_agent=REDDIT_USER_AGENT)
    return parse_reddit_json(payload, limit)


def parse_hn_json(payload, limit):
    hits = payload.get("hits", [])
    entries = []
    for hit in hits[:limit]:
        object_id = hit.get("objectID", "")
        link = hit.get("url") or (f"https://news.ycombinator.com/item?id={object_id}" if object_id else "")
        entries.append({
            "source": "hn",
            "title": hit.get("title", ""),
            "date": hit.get("created_at", ""),
            "link": link,
            "metric": f"{hit.get('points', 0)} pts · {hit.get('num_comments', 0)} comments",
        })
    return entries


def fetch_hn(query, limit, cutoff_epoch):
    params = urllib.parse.urlencode({
        "query": query,
        "tags": "story",
        "numericFilters": f"created_at_i>={cutoff_epoch}",
    })
    payload = fetch_json(f"{HN_SEARCH_URL}?{params}")
    return parse_hn_json(payload, limit)


def parse_polymarket_json(payload, query, limit):
    needle = query.lower()
    entries = []
    for market in payload:
        question = market.get("question", "")
        if needle not in question.lower():
            continue
        slug = market.get("slug", "")
        entries.append({
            "source": "polymarket",
            "title": question,
            "date": market.get("startDate", "") or market.get("endDate", ""),
            "link": f"https://polymarket.com/event/{slug}" if slug else "",
            "metric": f"volume ${market.get('volume', '0')}",
        })
        if len(entries) >= limit:
            break
    return entries


def fetch_polymarket(query, limit):
    params = urllib.parse.urlencode({
        "closed": "false",
        "limit": POLYMARKET_FETCH_LIMIT,
        "order": "volume",
        "ascending": "false",
    })
    payload = fetch_json(f"{POLYMARKET_MARKETS_URL}?{params}")
    if not isinstance(payload, list):
        raise SourceFetchError("unexpected polymarket response shape (expected a list of markets)")
    return parse_polymarket_json(payload, query, limit)


def parse_github_json(payload, limit):
    items = payload.get("items", [])
    entries = []
    for repo in items[:limit]:
        entries.append({
            "source": "github",
            "title": repo.get("full_name", ""),
            "date": repo.get("pushed_at", ""),
            "link": repo.get("html_url", ""),
            "metric": f"★ {repo.get('stargazers_count', 0)}",
        })
    return entries


def fetch_github(query, limit, cutoff_date):
    params = urllib.parse.urlencode({
        "q": f"{query} pushed:>={cutoff_date}",
        "sort": "updated",
        "per_page": min(limit, 100),
    })
    payload = fetch_json(f"{GITHUB_SEARCH_URL}?{params}", extra_headers=GITHUB_HEADERS)
    return parse_github_json(payload, limit)


def _epoch_to_iso(epoch_seconds):
    if not epoch_seconds:
        return ""
    return datetime.fromtimestamp(epoch_seconds, tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def search_all(query, sources, limit):
    """Fetch each requested source with per-source error isolation.

    Returns (entries, errors) where errors is {source: message} for every
    source that failed. A source failing never drops the others.
    """
    cutoff_epoch, cutoff_date = compute_cutoff()
    fetchers = {
        "reddit": lambda: fetch_reddit(query, limit),
        "hn": lambda: fetch_hn(query, limit, cutoff_epoch),
        "polymarket": lambda: fetch_polymarket(query, limit),
        "github": lambda: fetch_github(query, limit, cutoff_date),
    }
    entries = []
    errors = {}
    for source in sources:
        try:
            entries.extend(fetchers[source]())
        except SourceFetchError as exc:
            errors[source] = str(exc)
    return entries, errors


def print_table(entries, errors, sources):
    if not entries:
        print("No results found.")
    for entry in entries:
        print(f"[{entry['source']}] {entry['title']}")
        print(f"    {entry['metric']}  date: {entry['date'] or '-'}")
        print(f"    {entry['link']}")
    counts = {source: sum(1 for e in entries if e["source"] == source) for source in sources}
    print("---")
    print("counts: " + ", ".join(f"{source}={count}" for source, count in counts.items()))
    for source, message in errors.items():
        print(f"warning: {source} failed: {message}", file=sys.stderr)


def print_json(entries, errors, sources):
    counts = {source: sum(1 for e in entries if e["source"] == source) for source in sources}
    print(json.dumps({"entries": entries, "counts": counts, "errors": errors}, indent=2))


def validate_query(query):
    """Reject empty/oversized/control-character queries.

    Values are only ever passed through urllib.parse.urlencode (never
    shell-interpolated or string-concatenated into a URL), so this guard is
    about rejecting garbage input, not URL injection.
    """
    stripped = query.strip()
    if not stripped:
        raise ValueError("query must not be empty")
    if len(stripped) > MAX_QUERY_CHARS:
        raise ValueError(f"query too long (max {MAX_QUERY_CHARS} chars)")
    if any(ord(ch) < 0x20 or ord(ch) == 0x7F for ch in stripped):
        raise ValueError("query must not contain control characters")
    return stripped


def parse_sources(raw):
    if raw == "all":
        return SOURCES
    requested = [s.strip() for s in raw.split(",") if s.strip()]
    invalid = [s for s in requested if s not in SOURCES]
    if invalid:
        raise ValueError(f"unknown source(s): {', '.join(invalid)} (choose from {', '.join(SOURCES)}, or 'all')")
    return requested


def build_parser():
    parser = argparse.ArgumentParser(description="Pull recent (~30 day) chatter from keyless sources.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    search_parser = subparsers.add_parser("search", help="query one or more sources and print a merged table")
    search_parser.add_argument("query")
    search_parser.add_argument("--sources", default="all", help="comma-separated: reddit,hn,polymarket,github or 'all'")
    search_parser.add_argument("--limit", type=int, default=DEFAULT_LIMIT)
    search_parser.add_argument("--json", action="store_true", dest="as_json")

    for source in SOURCES:
        source_parser = subparsers.add_parser(source, help=f"query {source} only")
        source_parser.add_argument("query")
        source_parser.add_argument("--limit", type=int, default=DEFAULT_LIMIT)
        source_parser.add_argument("--json", action="store_true", dest="as_json")

    return parser


def main():
    args = build_parser().parse_args()
    try:
        query = validate_query(args.query)
        sources = parse_sources(args.sources) if args.command == "search" else [args.command]
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        sys.exit(2)

    entries, errors = search_all(query, sources, args.limit)

    if errors and len(errors) == len(sources):
        for source, message in errors.items():
            print(f"error: {source} failed: {message}", file=sys.stderr)
        sys.exit(2)

    if args.as_json:
        print_json(entries, errors, sources)
    else:
        print_table(entries, errors, sources)


if __name__ == "__main__":
    main()
