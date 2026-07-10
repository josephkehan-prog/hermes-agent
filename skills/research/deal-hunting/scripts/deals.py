#!/usr/bin/env python3
"""Hunt software/hardware deals across free, keyless RSS/JSON sources.

Sources: Slickdeals (RSS), OzBargain (RSS), r/buildapcsales and r/GameDeals
(Reddit RSS via old.reddit.com). No API keys, no paid endpoints.

Usage:
    python3 deals.py search <query> [--source SOURCE] [--limit N]
    python3 deals.py watch <query> --out FILE [--source SOURCE] [--limit N]

SOURCE is one of: slickdeals, ozbargain, reddit-bapcs, reddit-gamedeals, all
(default: all)

stdlib only.
"""
import argparse
import hashlib
import json
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET

DEFAULT_TIMEOUT_SECONDS = 15
DEFAULT_LIMIT = 15
MAX_QUERY_CHARS = 200
MAX_RESPONSE_BYTES = 10_000_000
USER_AGENT = "Mozilla/5.0 (compatible; deal-hunting-skill/1.0; +research)"
REDDIT_USER_AGENT = "deal-hunting-skill/1.0 (by /u/research)"
DANGEROUS_XML_MARKERS = (b"<!doctype", b"<!entity")

ATOM_NS = {"a": "http://www.w3.org/2005/Atom"}
PRICE_PATTERN = re.compile(r"\$[\d,]+(?:\.\d{1,2})?")

SLICKDEALS_SEARCH_URL = "https://slickdeals.net/newsearch.php?q={query}&rss=1"
OZBARGAIN_FEED_URL = "https://www.ozbargain.com.au/deals/feed"
REDDIT_SEARCH_URL = "https://old.reddit.com/r/{sub}/search.rss?q={query}&restrict_sr=on&sort=new"
REDDIT_SUBREDDITS = {"reddit-bapcs": "buildapcsales", "reddit-gamedeals": "GameDeals"}

SOURCES = ["slickdeals", "ozbargain", "reddit-bapcs", "reddit-gamedeals"]


class DealFetchError(Exception):
    """Raised when a source cannot be fetched."""


def fetch_url(url, user_agent=USER_AGENT):
    request = urllib.request.Request(url, headers={"User-Agent": user_agent})
    try:
        with urllib.request.urlopen(request, timeout=DEFAULT_TIMEOUT_SECONDS) as response:
            raw = response.read(MAX_RESPONSE_BYTES + 1)
    except urllib.error.URLError as exc:
        raise DealFetchError(f"failed to fetch {url}: {exc}") from exc
    if len(raw) > MAX_RESPONSE_BYTES:
        raise DealFetchError(f"response from {url} exceeds {MAX_RESPONSE_BYTES} byte limit")
    return raw.decode("utf-8", errors="replace")


def extract_price(text):
    match = PRICE_PATTERN.search(text)
    return match.group(0) if match else ""


def reject_dangerous_xml(xml_text):
    """Raise DealFetchError if xml_text carries a DTD or entity declaration.

    ElementTree.fromstring doesn't resolve external entities by default, but
    we refuse to hand it anything DOCTYPE/ENTITY-bearing at all. The check
    runs on encoded, NUL-stripped bytes rather than the decoded string: a
    UTF-16 feed decoded permissively as UTF-8 comes out as interleaved
    "<\x00!\x00D\x00O\x00C..." bytes, which would dodge a plain substring
    match on the string but reassembles into a matchable marker once the
    NULs are dropped.
    """
    raw = xml_text.encode("utf-8", errors="replace").replace(b"\x00", b"").lower()
    for marker in DANGEROUS_XML_MARKERS:
        if marker in raw:
            raise DealFetchError(f"rejected feed: contains disallowed XML construct ({marker.decode()})")


def parse_rss(xml_text, source_name, query_filter=None):
    """Parse a standard RSS 2.0 <item> feed (Slickdeals, OzBargain)."""
    reject_dangerous_xml(xml_text)
    root = ET.fromstring(xml_text)
    deals = []
    for item in root.findall(".//item"):
        title = (item.findtext("title") or "").strip()
        if query_filter and query_filter.lower() not in title.lower():
            continue
        deals.append({
            "source": source_name,
            "title": title,
            "price": extract_price(title),
            "link": (item.findtext("link") or "").strip(),
            "date": (item.findtext("pubDate") or "").strip(),
        })
    return deals


def parse_atom(xml_text, source_name):
    """Parse an Atom <entry> feed (Reddit's old.reddit.com RSS)."""
    reject_dangerous_xml(xml_text)
    root = ET.fromstring(xml_text)
    deals = []
    for entry in root.findall("a:entry", ATOM_NS):
        title = (entry.findtext("a:title", namespaces=ATOM_NS) or "").strip()
        link_el = entry.find("a:link", ATOM_NS)
        link = link_el.attrib.get("href", "") if link_el is not None else ""
        deals.append({
            "source": source_name,
            "title": title,
            "price": extract_price(title),
            "link": link,
            "date": (entry.findtext("a:updated", namespaces=ATOM_NS) or "").strip(),
        })
    return deals


def fetch_slickdeals(query):
    url = SLICKDEALS_SEARCH_URL.format(query=urllib.parse.quote(query))
    return parse_rss(fetch_url(url), "slickdeals")


def fetch_ozbargain(query):
    # OzBargain's search endpoint sits behind a Cloudflare challenge and has
    # no keyless RSS variant; fetch the main deals feed and filter locally.
    return parse_rss(fetch_url(OZBARGAIN_FEED_URL), "ozbargain", query_filter=query)


def fetch_reddit(source_key, query):
    subreddit = REDDIT_SUBREDDITS[source_key]
    url = REDDIT_SEARCH_URL.format(sub=subreddit, query=urllib.parse.quote(query))
    return parse_atom(fetch_url(url, user_agent=REDDIT_USER_AGENT), source_key)


FETCHERS = {
    "slickdeals": fetch_slickdeals,
    "ozbargain": fetch_ozbargain,
    "reddit-bapcs": lambda query: fetch_reddit("reddit-bapcs", query),
    "reddit-gamedeals": lambda query: fetch_reddit("reddit-gamedeals", query),
}


def search_deals(query, source, limit):
    sources = SOURCES if source == "all" else [source]
    all_deals = []
    for src in sources:
        try:
            all_deals.extend(FETCHERS[src](query))
        except DealFetchError as exc:
            print(f"warning: {exc}", file=sys.stderr)
        except ET.ParseError as exc:
            print(f"warning: {src} returned unparseable feed ({exc})", file=sys.stderr)
    return all_deals[:limit]


def print_table(deals):
    if not deals:
        print("No deals found.")
        return
    for deal in deals:
        print(f"[{deal['source']}] {deal['title']}")
        print(f"    price: {deal['price'] or '-'}  date: {deal['date']}")
        print(f"    {deal['link']}")


def link_hash(link):
    return hashlib.sha256(link.encode("utf-8")).hexdigest()


def load_watchlist(path):
    try:
        with open(path, "r", encoding="utf-8") as handle:
            return json.load(handle)
    except FileNotFoundError:
        return []
    except json.JSONDecodeError as exc:
        raise DealFetchError(f"watchlist {path} is not valid JSON: {exc}") from exc


def save_watchlist(path, entries):
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(entries, handle, indent=2)


def watch_deals(query, source, out_path, limit):
    deals = search_deals(query, source, limit)
    existing = load_watchlist(out_path)
    seen_hashes = {entry["hash"] for entry in existing}
    added = 0
    for deal in deals:
        deal_hash = link_hash(deal["link"])
        if deal_hash in seen_hashes:
            continue
        existing.append({**deal, "hash": deal_hash})
        seen_hashes.add(deal_hash)
        added += 1
    save_watchlist(out_path, existing)
    print(f"added {added} new deal(s) to {out_path} ({len(existing)} total)")


def validate_query(query):
    """Reject empty/oversized queries. Values are only ever used as URL
    parameters (via urllib.parse.quote) or dict lookups — never passed to a
    shell."""
    stripped = query.strip()
    if not stripped:
        raise ValueError("query must not be empty")
    if len(stripped) > MAX_QUERY_CHARS:
        raise ValueError(f"query too long (max {MAX_QUERY_CHARS} chars)")
    return stripped


def build_parser():
    parser = argparse.ArgumentParser(description="Hunt software/hardware deals from free RSS/JSON sources.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    search_parser = subparsers.add_parser("search", help="search for deals and print a table")
    search_parser.add_argument("query", help="search term, e.g. 'ssd' or 'gpu'")
    search_parser.add_argument("--source", choices=SOURCES + ["all"], default="all")
    search_parser.add_argument("--limit", type=int, default=DEFAULT_LIMIT)

    watch_parser = subparsers.add_parser("watch", help="append new matches to a JSON watchlist")
    watch_parser.add_argument("query", help="search term to watch")
    watch_parser.add_argument("--out", required=True, help="path to watchlist JSON file")
    watch_parser.add_argument("--source", choices=SOURCES + ["all"], default="all")
    watch_parser.add_argument("--limit", type=int, default=DEFAULT_LIMIT)

    return parser


def main():
    args = build_parser().parse_args()
    try:
        query = validate_query(args.query)
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        sys.exit(2)

    if args.command == "search":
        print_table(search_deals(query, args.source, args.limit))
        return

    try:
        watch_deals(query, args.source, args.out, args.limit)
    except DealFetchError as exc:
        print(f"error: {exc}", file=sys.stderr)
        sys.exit(2)


if __name__ == "__main__":
    main()
