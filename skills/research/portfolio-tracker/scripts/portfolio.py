#!/usr/bin/env python3
"""portfolio.py -- keyless CLI to value a crypto portfolio from a local holdings file.

Subcommands: value, check.
Stdlib only (json, re, urllib). See scripts/README.md for usage.

Read-only. This script never trades, signs, or touches a private key or
seed phrase -- it only reads a user-maintained JSON file of {coin_id, amount}
pairs and looks up spot prices.

The only host this script talks to (COINGECKO_SIMPLE_PRICE) is a hardcoded
module-level constant, never built from user input -- so there's no
reject_private_target/SSRF guard here the way skills that fetch arbitrary
user-supplied URLs need one (see skills/research/network-recon/scripts/recon.py).
What IS user input -- the holdings file path and its contents -- is validated
defensively before use: the path must be a readable regular file, and every
field in the parsed JSON is isinstance-checked before being trusted.
"""
import argparse
import json
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

USER_AGENT = "portfolio-tracker-skill/1.0 (hermes-agent)"
TIMEOUT_SECONDS = 15
MAX_RESPONSE_BYTES = 10_000_000

COINGECKO_SIMPLE_PRICE = "https://api.coingecko.com/api/v3/simple/price"

COIN_ID_RE = re.compile(r"^[a-z0-9-]{1,64}$")


def fetch_json(url):
    """GET url and return parsed JSON. Exits 2 on any network/parse failure."""
    headers = {"User-Agent": USER_AGENT, "Accept": "application/json"}
    request = urllib.request.Request(url, headers=headers, method="GET")
    try:
        with urllib.request.urlopen(request, timeout=TIMEOUT_SECONDS) as response:
            raw = response.read(MAX_RESPONSE_BYTES + 1)
            if len(raw) > MAX_RESPONSE_BYTES:
                print(f"error: response exceeds {MAX_RESPONSE_BYTES} bytes for {url}", file=sys.stderr)
                sys.exit(2)
            return json.loads(raw.decode("utf-8"))
    except urllib.error.HTTPError as exc:
        print(f"error: HTTP {exc.code} for {url}", file=sys.stderr)
        sys.exit(2)
    except urllib.error.URLError as exc:
        print(f"error: request failed for {url}: {exc.reason}", file=sys.stderr)
        sys.exit(2)
    except (json.JSONDecodeError, UnicodeDecodeError) as exc:
        print(f"error: invalid response from {url}: {exc}", file=sys.stderr)
        sys.exit(2)


def read_holdings_file(path):
    """Validate path is a readable regular file and return its parsed JSON.

    Rejects directories, devices, missing files, and unparseable content
    with a clean exit(2) -- never a raw traceback.
    """
    holdings_path = Path(path)
    if not holdings_path.exists():
        print(f"error: holdings file not found: {path}", file=sys.stderr)
        sys.exit(2)
    if not holdings_path.is_file():
        print(f"error: holdings path is not a regular file: {path}", file=sys.stderr)
        sys.exit(2)
    try:
        raw = holdings_path.read_text(encoding="utf-8")
    except OSError as exc:
        print(f"error: could not read holdings file: {exc}", file=sys.stderr)
        sys.exit(2)
    try:
        return json.loads(raw)
    except json.JSONDecodeError as exc:
        print(f"error: holdings file is not valid JSON: {exc}", file=sys.stderr)
        sys.exit(2)


def validate_holdings(data):
    """Defensively validate the parsed holdings JSON and return a clean list.

    Every field is isinstance-checked -- a malformed shape (wrong type, missing
    key, negative amount) is rejected with a clear message and exit(2) rather
    than crashing further down the pipeline.
    """
    if not isinstance(data, list):
        print("error: holdings file must be a JSON array of {coin_id, amount}", file=sys.stderr)
        sys.exit(2)
    if not data:
        print("error: holdings file has no holdings", file=sys.stderr)
        sys.exit(2)

    holdings = []
    for i, entry in enumerate(data):
        if not isinstance(entry, dict):
            print(f"error: holding {i} is not an object", file=sys.stderr)
            sys.exit(2)
        coin_id = entry.get("coin_id")
        amount = entry.get("amount")
        if not isinstance(coin_id, str) or not COIN_ID_RE.match(coin_id):
            print(f"error: holding {i} has invalid coin_id {coin_id!r} (expected [a-z0-9-]{{1,64}})", file=sys.stderr)
            sys.exit(2)
        if isinstance(amount, bool) or not isinstance(amount, (int, float)) or amount < 0:
            print(f"error: holding {i} ({coin_id}) has invalid amount {amount!r} (expected a number >= 0)", file=sys.stderr)
            sys.exit(2)
        holdings.append({"coin_id": coin_id, "amount": amount})
    return holdings


def load_holdings(path):
    """Read, parse, and validate a holdings file in one step."""
    return validate_holdings(read_holdings_file(path))


def fetch_prices(coin_ids, vs):
    """Fetch spot prices for all coin_ids in one batched CoinGecko call."""
    params = {"ids": ",".join(coin_ids), "vs_currencies": vs}
    url = f"{COINGECKO_SIMPLE_PRICE}?{urllib.parse.urlencode(params, quote_via=urllib.parse.quote)}"
    data = fetch_json(url)
    if not isinstance(data, dict):
        print("error: unexpected CoinGecko response shape", file=sys.stderr)
        sys.exit(2)
    return data


def cmd_check(args):
    """Validate a holdings file's structure without fetching any prices."""
    holdings = load_holdings(args.holdings_file)
    coin_ids = ", ".join(h["coin_id"] for h in holdings)
    print(f"holdings file valid: {len(holdings)} holding(s) -- {coin_ids}")


def cmd_value(args):
    """Load holdings, fetch prices in one batched call, print a value table."""
    holdings = load_holdings(args.holdings_file)
    vs = args.vs.lower()
    unique_coin_ids = sorted({h["coin_id"] for h in holdings})
    prices = fetch_prices(unique_coin_ids, vs)

    rows = []
    for h in holdings:
        coin_id, amount = h["coin_id"], h["amount"]
        entry = prices.get(coin_id)
        if not isinstance(entry, dict):
            print(f"{coin_id}: price not found, skipping", file=sys.stderr)
            continue
        price = entry.get(vs)
        if not isinstance(price, (int, float)):
            print(f"{coin_id}: no {vs} price in response, skipping", file=sys.stderr)
            continue
        rows.append((coin_id, amount, price, amount * price))

    if not rows:
        print("error: no holdings could be priced", file=sys.stderr)
        sys.exit(2)

    rows.sort(key=lambda row: row[3], reverse=True)
    currency = vs.upper()
    print(f"{'coin':<20}{'amount':>18}{'price':>18}{'value':>20}")
    total = 0.0
    for coin_id, amount, price, value in rows:
        print(f"{coin_id:<20}{amount:>18,.8g}{price:>18,.2f}{value:>20,.2f}")
        total += value
    print(f"\ntotal: {total:,.2f} {currency}")


def build_parser():
    parser = argparse.ArgumentParser(description="Keyless crypto portfolio valuation from a local holdings file.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    p_value = subparsers.add_parser("value", help="Value a holdings file against a fiat currency")
    p_value.add_argument("holdings_file", help="Path to a holdings JSON file: [{coin_id, amount}, ...]")
    p_value.add_argument("--vs", default="usd", help="Fiat currency to value against (default: usd)")

    p_check = subparsers.add_parser("check", help="Validate a holdings file's structure, no network call")
    p_check.add_argument("holdings_file", help="Path to a holdings JSON file: [{coin_id, amount}, ...]")

    return parser


COMMAND_HANDLERS = {
    "value": cmd_value,
    "check": cmd_check,
}


def main():
    parser = build_parser()
    args = parser.parse_args()
    handler = COMMAND_HANDLERS[args.command]
    handler(args)


if __name__ == "__main__":
    main()
