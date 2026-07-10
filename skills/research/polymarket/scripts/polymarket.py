#!/usr/bin/env python3
"""Polymarket CLI helper — query prediction market data.

Usage:
    python3 polymarket.py search "bitcoin"
    python3 polymarket.py trending [--limit 10]
    python3 polymarket.py closing-soon [--limit 10]
    python3 polymarket.py market <slug>
    python3 polymarket.py event <slug>
    python3 polymarket.py price <token_id>
    python3 polymarket.py book <token_id>
    python3 polymarket.py history <condition_id> [--interval all] [--fidelity 50]
    python3 polymarket.py trades [--limit 10] [--market CONDITION_ID]

All requests go to hardcoded Polymarket hosts (gamma-api.polymarket.com,
clob.polymarket.com, data-api.polymarket.com) — never a caller-supplied URL —
so this is a fixed-endpoint client, not an open fetcher. Caller-supplied
values (slug, token_id, condition_id, query, limit) are still validated
before being slotted into a URL, to keep malformed/oversized/control-char
input from reaching the query string.

Exit codes: 0 = ran, 1 = network/HTTP error, 2 = bad input.
"""

import json
import re
import sys
import urllib.request
import urllib.parse
import urllib.error
from datetime import datetime, timezone

GAMMA = "https://gamma-api.polymarket.com"
CLOB = "https://clob.polymarket.com"
DATA = "https://data-api.polymarket.com"

REQUEST_TIMEOUT_SECONDS = 15
MAX_RESPONSE_BYTES = 10_000_000
USER_AGENT = "Mozilla/5.0 (compatible; polymarket-skill/1.0; +research)"

DEFAULT_LIMIT = 10
MAX_LIMIT = 500
MAX_FIDELITY = 1000
MAX_QUERY_CHARS = 200
MAX_SLUG_CHARS = 200
MAX_ID_CHARS = 100

SLUG_RE = re.compile(r"^[a-z0-9-]+$")
ID_RE = re.compile(r"^(0x)?[0-9a-fA-F]+$")
INTERVALS = {"all", "1d", "1w", "1m", "3m", "6m", "1y"}


def _read_capped(resp) -> bytes:
    """Read an HTTP response body, capped to MAX_RESPONSE_BYTES."""
    raw = resp.read(MAX_RESPONSE_BYTES + 1)
    if len(raw) > MAX_RESPONSE_BYTES:
        raise ValueError(f"response exceeds {MAX_RESPONSE_BYTES} byte limit")
    return raw


def _get(url: str) -> dict | list:
    """GET request, return parsed JSON (capped to MAX_RESPONSE_BYTES)."""
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(req, timeout=REQUEST_TIMEOUT_SECONDS) as resp:
            raw = _read_capped(resp)
        return json.loads(raw.decode())
    except urllib.error.HTTPError as e:
        print(f"HTTP {e.code}: {e.reason}", file=sys.stderr)
        sys.exit(1)
    except urllib.error.URLError as e:
        print(f"Connection error: {e.reason}", file=sys.stderr)
        sys.exit(1)
    except ValueError as e:
        print(f"error: {e}", file=sys.stderr)
        sys.exit(1)


def validate_query(value: str) -> str:
    """Reject empty/oversized/control-char search queries."""
    stripped = value.strip()
    if not stripped:
        raise ValueError("query must not be empty")
    if len(stripped) > MAX_QUERY_CHARS:
        raise ValueError(f"query too long (max {MAX_QUERY_CHARS} chars)")
    if any(ord(ch) < 0x20 for ch in stripped):
        raise ValueError("query must not contain control characters")
    return stripped


def validate_slug(value: str) -> str:
    """Allowlist market/event slugs to lowercase alphanumeric + hyphens."""
    if not value or len(value) > MAX_SLUG_CHARS or not SLUG_RE.match(value):
        raise ValueError(f"invalid slug: {value!r} (expected lowercase letters, digits, hyphens)")
    return value


def validate_id(value: str, label: str = "id") -> str:
    """Allowlist token_id/condition_id to an optional 0x prefix + hex digits.

    CLOB token IDs are decimal strings and Gamma condition IDs are 0x-prefixed
    hex strings; decimal digits are a subset of hex digits so this one
    allowlist covers both without accepting anything else.
    """
    if not value or len(value) > MAX_ID_CHARS or not ID_RE.match(value):
        raise ValueError(f"invalid {label}: {value!r} (expected hex/decimal identifier)")
    return value


def validate_interval(value: str) -> str:
    if value not in INTERVALS:
        raise ValueError(f"invalid interval: {value!r} (expected one of {sorted(INTERVALS)})")
    return value


def validate_limit(value: int, default: int = DEFAULT_LIMIT, max_limit: int = MAX_LIMIT) -> int:
    """Clamp a caller-supplied limit/fidelity into [1, max_limit]."""
    if value is None or value < 1:
        return default
    return min(value, max_limit)


def _parse_json_field(val):
    """Parse double-encoded JSON fields (outcomePrices, outcomes, clobTokenIds)."""
    if isinstance(val, str):
        try:
            return json.loads(val)
        except (json.JSONDecodeError, TypeError):
            return val
    return val


def _fmt_pct(price_str: str) -> str:
    """Format price string as percentage."""
    try:
        return f"{float(price_str) * 100:.1f}%"
    except (ValueError, TypeError):
        return price_str


def _fmt_volume(vol) -> str:
    """Format volume as human-readable."""
    try:
        v = float(vol)
        if v >= 1_000_000:
            return f"${v / 1_000_000:.1f}M"
        if v >= 1_000:
            return f"${v / 1_000:.1f}K"
        return f"${v:.0f}"
    except (ValueError, TypeError):
        return str(vol)


def _fmt_time_to_close(end_date: str) -> str:
    """Format an ISO8601 endDate as a human-readable time-to-close."""
    if not end_date:
        return "?"
    try:
        end = datetime.fromisoformat(end_date.replace("Z", "+00:00"))
        delta = end - datetime.now(timezone.utc)
        total_seconds = delta.total_seconds()
        if total_seconds <= 0:
            return "closed"
        days, rem = divmod(int(total_seconds), 86400)
        hours, _ = divmod(rem, 3600)
        if days > 0:
            return f"{days}d {hours}h"
        hours, rem = divmod(int(total_seconds), 3600)
        minutes = rem // 60
        return f"{hours}h {minutes}m"
    except (ValueError, TypeError):
        return end_date


def _print_market(m: dict, indent: str = ""):
    """Print a market summary."""
    question = m.get("question", "?")
    prices = _parse_json_field(m.get("outcomePrices", "[]"))
    outcomes = _parse_json_field(m.get("outcomes", "[]"))
    vol = _fmt_volume(m.get("volume", 0))
    closed = m.get("closed", False)
    status = " [CLOSED]" if closed else ""

    if isinstance(prices, list) and len(prices) >= 2:
        outcome_labels = outcomes if isinstance(outcomes, list) else ["Yes", "No"]
        price_str = " / ".join(
            f"{outcome_labels[i]}: {_fmt_pct(prices[i])}"
            for i in range(min(len(prices), len(outcome_labels)))
        )
        print(f"{indent}{question}{status}")
        print(f"{indent}  {price_str}  |  Volume: {vol}")
    else:
        print(f"{indent}{question}{status}  |  Volume: {vol}")

    slug = m.get("slug", "")
    if slug:
        print(f"{indent}  slug: {slug}")


def cmd_search(query: str):
    """Search for markets."""
    query = validate_query(query)
    q = urllib.parse.quote(query)
    data = _get(f"{GAMMA}/public-search?q={q}")
    events = data.get("events", [])
    total = data.get("pagination", {}).get("totalResults", len(events))
    print(f"Found {total} results for \"{query}\":\n")
    for evt in events[:10]:
        print(f"=== {evt['title']} ===")
        print(f"  Volume: {_fmt_volume(evt.get('volume', 0))}  |  slug: {evt.get('slug', '')}")
        markets = evt.get("markets", [])
        for m in markets[:5]:
            _print_market(m, indent="  ")
        if len(markets) > 5:
            print(f"  ... and {len(markets) - 5} more markets")
        print()


def cmd_trending(limit: int = DEFAULT_LIMIT):
    """Show trending events by volume."""
    limit = validate_limit(limit)
    events = _get(f"{GAMMA}/events?limit={limit}&active=true&closed=false&order=volume&ascending=false")
    print(f"Top {len(events)} trending events:\n")
    for i, evt in enumerate(events, 1):
        print(f"{i}. {evt['title']}")
        print(f"   Volume: {_fmt_volume(evt.get('volume', 0))}  |  Markets: {len(evt.get('markets', []))}")
        print(f"   slug: {evt.get('slug', '')}")
        markets = evt.get("markets", [])
        for m in markets[:3]:
            _print_market(m, indent="   ")
        if len(markets) > 3:
            print(f"   ... and {len(markets) - 3} more markets")
        print()


def cmd_closing_soon(limit: int = DEFAULT_LIMIT):
    """Show open markets with the soonest end date."""
    limit = validate_limit(limit)
    events = _get(f"{GAMMA}/events?limit={limit}&active=true&closed=false&order=endDate&ascending=true")
    print(f"Top {len(events)} events closing soonest:\n")
    for i, evt in enumerate(events, 1):
        print(f"{i}. {evt['title']}")
        print(
            f"   Closes: {_fmt_time_to_close(evt.get('endDate', ''))}  |  "
            f"Volume: {_fmt_volume(evt.get('volume', 0))}  |  Markets: {len(evt.get('markets', []))}"
        )
        print(f"   slug: {evt.get('slug', '')}")
        markets = evt.get("markets", [])
        for m in markets[:3]:
            _print_market(m, indent="   ")
        if len(markets) > 3:
            print(f"   ... and {len(markets) - 3} more markets")
        print()


def cmd_market(slug: str):
    """Get market details by slug."""
    slug = validate_slug(slug)
    markets = _get(f"{GAMMA}/markets?slug={urllib.parse.quote(slug)}")
    if not markets:
        print(f"No market found with slug: {slug}")
        return
    m = markets[0]
    print(f"Market: {m.get('question', '?')}")
    print(f"Status: {'CLOSED' if m.get('closed') else 'ACTIVE'}")
    _print_market(m)
    print(f"\n  conditionId: {m.get('conditionId', 'N/A')}")
    tokens = _parse_json_field(m.get("clobTokenIds", "[]"))
    if isinstance(tokens, list):
        outcomes = _parse_json_field(m.get("outcomes", "[]"))
        for i, t in enumerate(tokens):
            label = outcomes[i] if isinstance(outcomes, list) and i < len(outcomes) else f"Outcome {i}"
            print(f"  token ({label}): {t}")
    desc = m.get("description", "")
    if desc:
        print(f"\n  Description: {desc[:500]}")


def cmd_event(slug: str):
    """Get event details by slug."""
    slug = validate_slug(slug)
    events = _get(f"{GAMMA}/events?slug={urllib.parse.quote(slug)}")
    if not events:
        print(f"No event found with slug: {slug}")
        return
    evt = events[0]
    print(f"Event: {evt['title']}")
    print(f"Volume: {_fmt_volume(evt.get('volume', 0))}")
    print(f"Status: {'CLOSED' if evt.get('closed') else 'ACTIVE'}")
    print(f"Markets: {len(evt.get('markets', []))}\n")
    for m in evt.get("markets", []):
        _print_market(m, indent="  ")
        print()


def cmd_price(token_id: str):
    """Get current price for a token."""
    token_id = validate_id(token_id, "token_id")
    buy = _get(f"{CLOB}/price?token_id={token_id}&side=buy")
    mid = _get(f"{CLOB}/midpoint?token_id={token_id}")
    spread = _get(f"{CLOB}/spread?token_id={token_id}")
    print(f"Token: {token_id[:30]}...")
    print(f"  Buy price: {_fmt_pct(buy.get('price', '?'))}")
    print(f"  Midpoint:  {_fmt_pct(mid.get('mid', '?'))}")
    print(f"  Spread:    {spread.get('spread', '?')}")


def cmd_book(token_id: str):
    """Get orderbook for a token."""
    token_id = validate_id(token_id, "token_id")
    book = _get(f"{CLOB}/book?token_id={token_id}")
    bids = book.get("bids", [])
    asks = book.get("asks", [])
    last = book.get("last_trade_price", "?")
    print(f"Orderbook for {token_id[:30]}...")
    print(f"Last trade: {_fmt_pct(last)}  |  Tick size: {book.get('tick_size', '?')}")
    print(f"\n  Top bids ({len(bids)} total):")
    # Show bids sorted by price descending (best bids first)
    sorted_bids = sorted(bids, key=lambda x: float(x.get("price", 0)), reverse=True)
    for b in sorted_bids[:10]:
        print(f"    {_fmt_pct(b['price']):>7}  |  Size: {float(b['size']):>10.2f}")
    print(f"\n  Top asks ({len(asks)} total):")
    sorted_asks = sorted(asks, key=lambda x: float(x.get("price", 0)))
    for a in sorted_asks[:10]:
        print(f"    {_fmt_pct(a['price']):>7}  |  Size: {float(a['size']):>10.2f}")


def cmd_history(condition_id: str, interval: str = "all", fidelity: int = 50):
    """Get price history for a market."""
    condition_id = validate_id(condition_id, "condition_id")
    interval = validate_interval(interval)
    fidelity = validate_limit(fidelity, default=50, max_limit=MAX_FIDELITY)
    data = _get(f"{CLOB}/prices-history?market={condition_id}&interval={interval}&fidelity={fidelity}")
    history = data.get("history", [])
    if not history:
        print("No price history available for this market.")
        return
    print(f"Price history ({len(history)} points, interval={interval}):\n")
    for pt in history:
        ts = datetime.fromtimestamp(pt["t"], tz=timezone.utc).strftime("%Y-%m-%d %H:%M")
        price = _fmt_pct(pt["p"])
        bar = "█" * int(float(pt["p"]) * 40)
        print(f"  {ts}  {price:>7}  {bar}")


def cmd_trades(limit: int = DEFAULT_LIMIT, market: str = None):
    """Get recent trades."""
    limit = validate_limit(limit)
    url = f"{DATA}/trades?limit={limit}"
    if market:
        market = validate_id(market, "market")
        url += f"&market={market}"
    trades = _get(url)
    if not isinstance(trades, list):
        print(f"Unexpected response: {trades}")
        return
    print(f"Recent trades ({len(trades)}):\n")
    for t in trades:
        side = t.get("side", "?")
        price = _fmt_pct(t.get("price", "?"))
        size = t.get("size", "?")
        outcome = t.get("outcome", "?")
        title = t.get("title", "?")[:50]
        print(f"  {side:4}  {price:>7}  x{float(size):>8.2f}  [{outcome}]  {title}")


def main():
    args = sys.argv[1:]
    if not args or args[0] in {"-h", "--help", "help"}:
        print(__doc__)
        return

    cmd = args[0]

    try:
        if cmd == "search" and len(args) >= 2:
            cmd_search(" ".join(args[1:]))
        elif cmd == "trending":
            limit = DEFAULT_LIMIT
            if "--limit" in args:
                idx = args.index("--limit")
                limit = int(args[idx + 1]) if idx + 1 < len(args) else DEFAULT_LIMIT
            cmd_trending(limit)
        elif cmd == "closing-soon":
            limit = DEFAULT_LIMIT
            if "--limit" in args:
                idx = args.index("--limit")
                limit = int(args[idx + 1]) if idx + 1 < len(args) else DEFAULT_LIMIT
            cmd_closing_soon(limit)
        elif cmd == "market" and len(args) >= 2:
            cmd_market(args[1])
        elif cmd == "event" and len(args) >= 2:
            cmd_event(args[1])
        elif cmd == "price" and len(args) >= 2:
            cmd_price(args[1])
        elif cmd == "book" and len(args) >= 2:
            cmd_book(args[1])
        elif cmd == "history" and len(args) >= 2:
            interval = "all"
            fidelity = 50
            if "--interval" in args:
                idx = args.index("--interval")
                interval = args[idx + 1] if idx + 1 < len(args) else "all"
            if "--fidelity" in args:
                idx = args.index("--fidelity")
                fidelity = int(args[idx + 1]) if idx + 1 < len(args) else 50
            cmd_history(args[1], interval, fidelity)
        elif cmd == "trades":
            limit = DEFAULT_LIMIT
            market = None
            if "--limit" in args:
                idx = args.index("--limit")
                limit = int(args[idx + 1]) if idx + 1 < len(args) else DEFAULT_LIMIT
            if "--market" in args:
                idx = args.index("--market")
                market = args[idx + 1] if idx + 1 < len(args) else None
            cmd_trades(limit, market)
        else:
            print(f"Unknown command: {cmd}")
            print(__doc__)
    except ValueError as e:
        print(f"error: {e}", file=sys.stderr)
        sys.exit(2)


if __name__ == "__main__":
    main()
