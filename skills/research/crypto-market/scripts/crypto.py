#!/usr/bin/env python3
"""crypto.py -- keyless CLI for crypto market data and public wallet lookups.

Subcommands: price, trending, feargreed, eth-balance.
Stdlib only (json, re, urllib). See scripts/README.md for usage.

Read-only, public-chain data only. Never requests, stores, or transmits a
private key or seed phrase; cannot move funds.

Every host this script talks to (COINGECKO_*, ALTERNATIVE_FNG,
CLOUDFLARE_ETH_RPC) is a hardcoded module-level constant, never built from
user input -- so there's no reject_private_target/SSRF guard here the way
skills that fetch arbitrary user-supplied URLs need one (see
skills/research/network-recon/scripts/recon.py). What IS user input --
coin ids and ETH addresses -- is validated against a strict regex before
it's ever placed in a URL or RPC body.
"""
import argparse
import json
import re
import sys
import urllib.error
import urllib.parse
import urllib.request

USER_AGENT = "crypto-market-skill/1.0 (hermes-agent)"
TIMEOUT_SECONDS = 15
MAX_RESPONSE_BYTES = 10_000_000

COINGECKO_SIMPLE_PRICE = "https://api.coingecko.com/api/v3/simple/price"
COINGECKO_TRENDING = "https://api.coingecko.com/api/v3/search/trending"
ALTERNATIVE_FNG = "https://api.alternative.me/fng/"
CLOUDFLARE_ETH_RPC = "https://cloudflare-eth.com"

COIN_ID_RE = re.compile(r"^[a-z0-9-]+$")
ETH_ADDRESS_RE = re.compile(r"^0x[0-9a-fA-F]{40}$")


def fetch_json(url, *, method="GET", data=None):
    """GET/POST url and return parsed JSON. Exits 2 on any network/parse failure."""
    headers = {"User-Agent": USER_AGENT, "Accept": "application/json"}
    body = None
    if data is not None:
        body = json.dumps(data).encode("utf-8")
        headers["Content-Type"] = "application/json"
    request = urllib.request.Request(url, data=body, headers=headers, method=method)
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


def validate_coin_ids(coins):
    """Return coins unchanged if every id matches the CoinGecko id charset, else exit 2."""
    for coin_id in coins:
        if not COIN_ID_RE.match(coin_id):
            print(f"error: invalid coin id {coin_id!r} (expected [a-z0-9-]+)", file=sys.stderr)
            sys.exit(2)
    return coins


def cmd_price(args):
    """Fetch USD price, 24h change, and market cap for one or more coin ids.

    Missing coins (e.g. a typo'd id CoinGecko doesn't recognize) are reported
    per-coin on stderr rather than aborting the whole batch.
    """
    coin_ids = validate_coin_ids(args.coins)
    params = {
        "ids": ",".join(coin_ids),
        "vs_currencies": "usd",
        "include_24hr_change": "true",
        "include_market_cap": "true",
    }
    url = f"{COINGECKO_SIMPLE_PRICE}?{urllib.parse.urlencode(params, quote_via=urllib.parse.quote)}"
    data = fetch_json(url)

    for coin_id in coin_ids:
        entry = data.get(coin_id)
        if entry is None:
            print(f"{coin_id}: not found", file=sys.stderr)
            continue
        price = entry.get("usd")
        change = entry.get("usd_24h_change")
        cap = entry.get("usd_market_cap")
        price_str = f"${price:,.2f}" if isinstance(price, (int, float)) else "?"
        change_str = f"{change:+.2f}%" if isinstance(change, (int, float)) else "?"
        cap_str = f"${cap:,.0f}" if isinstance(cap, (int, float)) else "?"
        print(f"{coin_id}: {price_str}  24h: {change_str}  mcap: {cap_str}")


def cmd_trending(_args):
    """Show CoinGecko's currently trending coins."""
    data = fetch_json(COINGECKO_TRENDING)
    coins = data.get("coins", [])
    if not coins:
        print("(no trending data)")
        return
    print(f"Trending ({len(coins)}):\n")
    for i, item in enumerate(coins, 1):
        c = item.get("item", {})
        name = c.get("name", "?")
        symbol = c.get("symbol", "?")
        rank = c.get("market_cap_rank", "?")
        print(f"{i}. {name} ({symbol})  market cap rank: {rank}")


def cmd_feargreed(_args):
    """Show the current Crypto Fear & Greed Index and its classification."""
    url = f"{ALTERNATIVE_FNG}?limit=1&format=json"
    data = fetch_json(url)
    entries = data.get("data", [])
    if not entries:
        print("error: no fear & greed data returned", file=sys.stderr)
        sys.exit(2)
    entry = entries[0]
    value = entry.get("value", "?")
    classification = entry.get("value_classification", "?")
    print(f"Fear & Greed Index: {value}/100 ({classification})")


def cmd_eth_balance(args):
    """Look up an ETH address's balance via Cloudflare's public JSON-RPC gateway.

    The address regex is validated BEFORE any network call, so malformed
    input never reaches the RPC endpoint.
    """
    address = args.address
    if not ETH_ADDRESS_RE.match(address):
        print(f"error: invalid ETH address {address!r} (expected 0x + 40 hex chars)", file=sys.stderr)
        sys.exit(2)

    payload = {"jsonrpc": "2.0", "method": "eth_getBalance", "params": [address, "latest"], "id": 1}
    data = fetch_json(CLOUDFLARE_ETH_RPC, method="POST", data=payload)
    if "error" in data:
        print(f"error: RPC error: {data['error']}", file=sys.stderr)
        sys.exit(2)
    result = data.get("result")
    if result is None:
        print("error: no result in RPC response", file=sys.stderr)
        sys.exit(2)
    wei = int(result, 16)
    eth = wei / 1e18
    print(f"{address}: {eth:.6f} ETH ({wei} wei)")


def build_parser():
    parser = argparse.ArgumentParser(description="Keyless crypto market data and public wallet lookups.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    p_price = subparsers.add_parser("price", help="USD price, 24h change, market cap for one or more coins")
    p_price.add_argument("coins", nargs="+", help="CoinGecko coin ids, e.g. bitcoin ethereum monero")

    subparsers.add_parser("trending", help="Show CoinGecko trending coins")
    subparsers.add_parser("feargreed", help="Show the Crypto Fear & Greed Index")

    p_eth = subparsers.add_parser("eth-balance", help="Look up an ETH address balance (MetaMask-style)")
    p_eth.add_argument("address", help="0x-prefixed 40-hex-char ETH address")

    return parser


COMMAND_HANDLERS = {
    "price": cmd_price,
    "trending": cmd_trending,
    "feargreed": cmd_feargreed,
    "eth-balance": cmd_eth_balance,
}


def main():
    parser = build_parser()
    args = parser.parse_args()
    handler = COMMAND_HANDLERS[args.command]
    handler(args)


if __name__ == "__main__":
    main()
