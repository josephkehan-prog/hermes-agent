#!/usr/bin/env python3
"""pulse.py -- keyless CLI that synthesizes a combined crypto + prediction-market snapshot.

Subcommand: snapshot [--json]

Fetches three keyless sources in one run and prints a combined dashboard:
  - CoinGecko /coins/markets: top coins by market cap, price + 24h change
  - alternative.me: Crypto Fear & Greed Index
  - Polymarket Gamma /events: top prediction markets by volume

Stdlib only (json, urllib). See scripts/README.md for usage.

This is a SYNTHESIZER, not a new fetcher: it composes the same keyless
sources skills/research/crypto-market and skills/research/polymarket
already query, into one combined snapshot. Every host this script talks
to (COINGECKO_MARKETS, ALTERNATIVE_FNG, POLYMARKET_EVENTS) is a hardcoded
module-level constant, never built from user input -- so there's no
SSRF surface on the target host itself.

Each of the three sources is fetched and parsed in isolation: one source
failing (rate limit, timeout, malformed shape) never prevents the other
two from appearing in the dashboard. Every parsed field is isinstance-
guarded before use -- an unexpected response shape (list instead of
dict, missing key, wrong type) is reported as a per-source error, never
an uncaught crash (see skills/research/crypto-market/scripts/crypto.py's
docstring for the crash-class bug this pattern fixes).

Exit codes: 0 if at least one source succeeded, 2 if all three failed.
"""
import argparse
import json
import sys
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone

USER_AGENT = "market-pulse-skill/1.0 (hermes-agent)"
TIMEOUT_SECONDS = 15
MAX_RESPONSE_BYTES = 10_000_000

COINGECKO_MARKETS = "https://api.coingecko.com/api/v3/coins/markets"
ALTERNATIVE_FNG = "https://api.alternative.me/fng/"
POLYMARKET_EVENTS = "https://gamma-api.polymarket.com/events"

TOP_COINS_COUNT = 5
TOP_MARKETS_COUNT = 5


class PulseFetchError(Exception):
    """Raised for any network/HTTP/parse failure fetching a single source."""


def fetch_json(url):
    """GET url and return parsed JSON, or raise PulseFetchError."""
    headers = {"User-Agent": USER_AGENT, "Accept": "application/json"}
    request = urllib.request.Request(url, headers=headers, method="GET")
    try:
        with urllib.request.urlopen(request, timeout=TIMEOUT_SECONDS) as response:
            raw = response.read(MAX_RESPONSE_BYTES + 1)
            if len(raw) > MAX_RESPONSE_BYTES:
                raise PulseFetchError(f"response exceeds {MAX_RESPONSE_BYTES} bytes for {url}")
            return json.loads(raw.decode("utf-8"))
    except urllib.error.HTTPError as exc:
        raise PulseFetchError(f"HTTP {exc.code} for {url}") from exc
    except urllib.error.URLError as exc:
        raise PulseFetchError(f"request failed for {url}: {exc.reason}") from exc
    except (json.JSONDecodeError, UnicodeDecodeError) as exc:
        raise PulseFetchError(f"invalid response from {url}: {exc}") from exc


def gather_crypto():
    """Fetch the top coins by market cap with price + 24h change. Never raises."""
    params = {
        "vs_currency": "usd",
        "order": "market_cap_desc",
        "per_page": str(TOP_COINS_COUNT),
        "page": "1",
    }
    url = f"{COINGECKO_MARKETS}?{urllib.parse.urlencode(params)}"
    try:
        data = fetch_json(url)
        if not isinstance(data, list):
            raise PulseFetchError("unexpected CoinGecko response shape (expected list)")
        coins = []
        for entry in data:
            if not isinstance(entry, dict):
                continue
            coins.append({
                "symbol": str(entry.get("symbol", "?")).upper(),
                "name": entry.get("name", "?"),
                "price": entry.get("current_price"),
                "change_24h": entry.get("price_change_percentage_24h"),
            })
        return {"ok": True, "coins": coins}
    except PulseFetchError as exc:
        return {"ok": False, "error": str(exc)}


def gather_feargreed():
    """Fetch the current Crypto Fear & Greed Index. Never raises."""
    url = f"{ALTERNATIVE_FNG}?limit=1&format=json"
    try:
        data = fetch_json(url)
        entries = data.get("data") if isinstance(data, dict) else None
        if not isinstance(entries, list) or not entries or not isinstance(entries[0], dict):
            raise PulseFetchError("unexpected alternative.me response shape")
        entry = entries[0]
        return {
            "ok": True,
            "value": entry.get("value", "?"),
            "classification": entry.get("value_classification", "?"),
        }
    except PulseFetchError as exc:
        return {"ok": False, "error": str(exc)}


def gather_polymarket():
    """Fetch the top prediction-market events by volume. Never raises."""
    params = {
        "limit": str(TOP_MARKETS_COUNT),
        "active": "true",
        "closed": "false",
        "order": "volume",
        "ascending": "false",
    }
    url = f"{POLYMARKET_EVENTS}?{urllib.parse.urlencode(params)}"
    try:
        data = fetch_json(url)
        if not isinstance(data, list):
            raise PulseFetchError("unexpected Polymarket response shape (expected list)")
        events = []
        for entry in data:
            if not isinstance(entry, dict):
                continue
            events.append({
                "title": entry.get("title", "?"),
                "volume": entry.get("volume"),
                "slug": entry.get("slug", ""),
            })
        return {"ok": True, "events": events}
    except PulseFetchError as exc:
        return {"ok": False, "error": str(exc)}


def _fmt_price(value):
    return f"${value:,.2f}" if isinstance(value, (int, float)) else "?"


def _fmt_pct(value):
    return f"{value:+.2f}%" if isinstance(value, (int, float)) else "?"


def _fmt_volume(value):
    if not isinstance(value, (int, float)):
        return "?"
    if value >= 1_000_000:
        return f"${value / 1_000_000:.1f}M"
    if value >= 1_000:
        return f"${value / 1_000:.1f}K"
    return f"${value:.0f}"


def print_crypto_section(crypto):
    print(f"Crypto (top {TOP_COINS_COUNT} by market cap):")
    if not crypto["ok"]:
        print(f"  unavailable: {crypto['error']}")
        return
    for coin in crypto["coins"]:
        print(f"  {coin['symbol']:<6} {_fmt_price(coin['price']):>14}   24h: {_fmt_pct(coin['change_24h'])}")


def print_feargreed_section(feargreed):
    print("\nFear & Greed Index:")
    if not feargreed["ok"]:
        print(f"  unavailable: {feargreed['error']}")
        return
    print(f"  {feargreed['value']}/100 ({feargreed['classification']})")


def print_polymarket_section(polymarket):
    print(f"\nPolymarket (top {TOP_MARKETS_COUNT} trending by volume):")
    if not polymarket["ok"]:
        print(f"  unavailable: {polymarket['error']}")
        return
    if not polymarket["events"]:
        print("  (no trending markets returned)")
        return
    for i, event in enumerate(polymarket["events"], 1):
        print(f"  {i}. {event['title']}  |  Volume: {_fmt_volume(event['volume'])}")
        if event["slug"]:
            print(f"     slug: {event['slug']}")


def cmd_snapshot(args):
    """Gather all three sources and print a combined dashboard (or JSON)."""
    crypto = gather_crypto()
    feargreed = gather_feargreed()
    polymarket = gather_polymarket()
    any_ok = crypto["ok"] or feargreed["ok"] or polymarket["ok"]

    if args.json:
        payload = {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "crypto": crypto,
            "feargreed": feargreed,
            "polymarket": polymarket,
        }
        print(json.dumps(payload, indent=2))
    else:
        print(f"Market Pulse -- {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}\n")
        print_crypto_section(crypto)
        print_feargreed_section(feargreed)
        print_polymarket_section(polymarket)

    if not any_ok:
        print("error: all sources failed", file=sys.stderr)
        sys.exit(2)


def build_parser():
    parser = argparse.ArgumentParser(description="Keyless combined crypto + prediction-market snapshot.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    p_snapshot = subparsers.add_parser("snapshot", help="Print a combined market dashboard")
    p_snapshot.add_argument("--json", action="store_true", help="Emit machine-readable JSON instead of text")

    return parser


COMMAND_HANDLERS = {
    "snapshot": cmd_snapshot,
}


def main():
    parser = build_parser()
    args = parser.parse_args()
    handler = COMMAND_HANDLERS[args.command]
    handler(args)


if __name__ == "__main__":
    main()
