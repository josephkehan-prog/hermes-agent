---
title: "Crypto Market"
sidebar_label: "Crypto Market"
description: "Keyless crypto market data (prices, trends, sentiment) and public wallet lookups (Bitcoin, Ethereum/MetaMask, Monero, any coin) via CoinGecko, alternative"
---

{/* This page is auto-generated from the skill's SKILL.md by website/scripts/generate-skill-docs.py. Edit the source SKILL.md, not this page. */}

# Crypto Market

Keyless crypto market data (prices, trends, sentiment) and public wallet lookups (Bitcoin, Ethereum/MetaMask, Monero, any coin) via CoinGecko, alternative.me, Cloudflare's ETH gateway, and Blockchair. Includes scripts/crypto.py.

## Skill metadata

| | |
|---|---|
| Source | Bundled (installed by default) |
| Path | `skills/research/crypto-market` |
| Version | `1.0.0` |
| Author | Hermes Agent |
| License | MIT |
| Platforms | linux, macos, windows |
| Tags | `Crypto`, `Bitcoin`, `Ethereum`, `Monero`, `MetaMask`, `Market-Data`, `Prices`, `Wallets` |
| Related skills | [`polymarket`](/docs/user-guide/skills/bundled/research/research-polymarket), [`deal-hunting`](/docs/user-guide/skills/bundled/research/research-deal-hunting), [`open-databases`](/docs/user-guide/skills/bundled/research/research-open-databases) |

## Reference: full SKILL.md

:::info
The following is the complete skill definition that Hermes loads when this skill is triggered. This is what the agent sees as instructions when the skill is active.
:::

# Crypto Market — Prices, Sentiment & Wallet Lookups

Query cryptocurrency market data and public wallet balances using free,
keyless APIs. No exchange accounts, no signup, no API keys — and this
skill never touches private keys or seed phrases. Everything it does is
read-only, public data: prices, sentiment, and on-chain balances that
anyone can already see on a block explorer.

## When to Use

- User asks for a coin's price, market cap, or 24h change (BTC, ETH, XMR, or any CoinGecko-listed coin)
- User wants to know what's trending in crypto right now
- User asks "is the market fear or greedy?" or wants a sentiment read
- User wants to check the balance of an Ethereum/MetaMask address
- User asks about a Bitcoin or Monero address and wants public-chain info
- **Not** for placing trades, connecting a wallet, or anything requiring a private key — this skill is read-only by design

## Source Catalog

| Source | Base URL | Auth-free limits | Example query URL |
|---|---|---|---|
| CoinGecko simple price | `api.coingecko.com/api/v3` | ~10-30 req/min keyless (public tier, no key) | `https://api.coingecko.com/api/v3/simple/price?ids=bitcoin,ethereum&vs_currencies=usd&include_24hr_change=true&include_market_cap=true` |
| CoinGecko trending | `api.coingecko.com/api/v3` | same pool as above | `https://api.coingecko.com/api/v3/search/trending` |
| alternative.me Fear & Greed Index | `api.alternative.me/fng` | generous, no documented cap | `https://api.alternative.me/fng/?limit=1&format=json` |
| Cloudflare Ethereum Gateway | `cloudflare-eth.com` | keyless JSON-RPC, no signup | POST `eth_getBalance` for any address |
| Blockchair | `api.blockchair.com` | keyless, shared pool (~30 req/min) | `https://api.blockchair.com/bitcoin/dashboards/address/<addr>`, `https://api.blockchair.com/monero/dashboards/address/<addr>` |

## Quickstart

```bash
python3 scripts/crypto.py price bitcoin ethereum monero
python3 scripts/crypto.py trending
python3 scripts/crypto.py feargreed
python3 scripts/crypto.py eth-balance 0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045
```

## Workflow

For a typical "how's the market doing" ask, chain the three read-only
calls in order:

1. **Price** — `price <coins...>` for the specific coins the user cares about (USD price, 24h change, market cap).
2. **Trend** — `trending` to see what's moving right now, for broader context.
3. **Sentiment** — `feargreed` for the aggregate market mood (0 = Extreme Fear, 100 = Extreme Greed).

Present all three together when the user's question is open-ended
("how's crypto doing") rather than about one specific coin.

## Wallet Lookups

### Ethereum / MetaMask addresses

`eth-balance <address>` validates the address against
`^0x[0-9a-fA-F]{40}$` **before** making any network call, then queries
Cloudflare's public Ethereum JSON-RPC gateway with `eth_getBalance` and
converts the wei result to ETH. This is exactly the balance MetaMask (or
any wallet) shows for that address — it's public on-chain state, not
account-specific data, so no login or signature is required to read it.

```bash
python3 scripts/crypto.py eth-balance 0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045
```

### Bitcoin addresses

Blockchair exposes address balance, transaction count, and totals sent/received
for any BTC address, keyless:

```bash
curl -s "https://api.blockchair.com/bitcoin/dashboards/address/bc1qxy2kgdygjrsqtzq2n0yrf2493p83kkfjhx0wlh" | python3 -m json.tool
```

### Monero (XMR) — privacy note

Monero is a privacy-focused chain by design: transaction amounts, senders,
and receivers are cryptographically obscured (ring signatures, stealth
addresses, RingCT). **Individual Monero addresses are not publicly
queryable for balance or transaction history** — that's the point of the
chain, not a gap in tooling. For Monero, this skill only supports:

- **Price** via `price monero` (CoinGecko has public XMR market data — the
  market data is public even though the chain itself isn't transparent)
- **Aggregate/public explorer data** (network hashrate, block height,
  mempool size) via `https://api.blockchair.com/monero/stats` — never
  per-address balances

If a user asks to "look up" a specific XMR address's balance, explain that
this isn't possible by design and isn't a missing feature.

## Model Wiring

| Task | Model | Endpoint | Why |
|------|-------|----------|-----|
| Deterministic price/field extraction (e.g. "pull price, 24h change, market cap as JSON from this CoinGecko response") | **agent1** | Ollama `http://localhost:11434/api/chat`, `"options": {"temperature": 0}` | Temperature 0 for repeatable structured output |
| Market-sentiment / "risk read" triage (e.g. "given this Fear & Greed value and these trending coins, what's the read?") | **ornith** | llama-swap `http://localhost:1235/v1/chat/completions`, `"chat_template_kwargs": {"enable_thinking": false}` | Fast, terse takes without a slow reasoning trace |

```python
import json
import urllib.request

# agent1: deterministic normalization, temperature 0
payload = {
    "model": "hf.co/InternScience/Agents-A1-Q4_K_M-GGUF:latest",
    "messages": [
        {"role": "system", "content": "Extract structured data as JSON only. No prose, no markdown fences."},
        {"role": "user", "content": f"Extract {{price, change_24h, market_cap}} from this CoinGecko record.\n\n{record_text}"},
    ],
    "options": {"temperature": 0},
    "stream": False,
}
req = urllib.request.Request(
    "http://localhost:11434/api/chat",
    data=json.dumps(payload).encode(),
    headers={"Content-Type": "application/json"},
)
result = json.loads(urllib.request.urlopen(req, timeout=120).read())["message"]["content"]
```

```python
# ornith: sentiment/risk triage, thinking disabled
payload = {
    "model": "ornith-uncensored",
    "messages": [{"role": "user", "content": f"Given this Fear & Greed reading and trending coins, give a one-paragraph market risk read.\n\n{market_snapshot}"}],
    "chat_template_kwargs": {"enable_thinking": False},
    "stream": False,
}
req = urllib.request.Request(
    "http://localhost:1235/v1/chat/completions",
    data=json.dumps(payload).encode(),
    headers={"Content-Type": "application/json"},
)
result = json.loads(urllib.request.urlopen(req, timeout=120).read())["choices"][0]["message"]["content"]
```

Verify wiring before relying on it:

```bash
curl -s http://localhost:11434/api/tags | grep -o '"hf.co/InternScience/Agents-A1[^"]*"'
curl -s http://localhost:1235/v1/models | grep -o '"ornith-uncensored"'
```

## Pitfalls

- **CoinGecko rate limits**: the public (keyless) tier is generous but
  undocumented and can throttle bursty usage — space out repeated `price`
  calls rather than polling tightly in a loop.
- **Price volatility**: crypto prices move fast; a price fetched a few
  minutes ago may already be stale. Always note that a price is a
  point-in-time snapshot when relaying it to the user.
- **Wallet lookups are READ-ONLY public-chain data**: `eth-balance` reads
  what's already publicly visible on the Ethereum blockchain. It never
  requests, stores, or transmits a private key or seed phrase, and it
  cannot move funds. If a user asks this skill to "send" or "sign"
  anything, that's out of scope — refuse and explain why.
- **XMR privacy is by design, not a limitation of this skill**: see the
  Monero section above. Don't attempt to work around it with third-party
  "Monero tracing" services — that defeats the purpose of the chain and
  isn't what keyless, public data means here.
- **Fixed endpoints, validated params**: every host this skill talks to
  (`api.coingecko.com`, `api.alternative.me`, `cloudflare-eth.com`,
  `api.blockchair.com`) is a hardcoded constant in `scripts/crypto.py` —
  never built from user input — so there's no SSRF surface on the target
  host itself. What *is* user input (coin ids, ETH addresses) is validated
  against a strict charset/regex before it's ever placed in a URL or RPC
  body; see `scripts/crypto.py` for details.
- **ETH address checksums aren't verified**: the regex only checks shape
  (`0x` + 40 hex chars), not EIP-55 checksum casing. That's fine for a
  balance lookup (the RPC accepts either case), but don't assume a
  regex-valid address is necessarily a real, funded account.
