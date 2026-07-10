---
name: portfolio-tracker
description: Keyless crypto portfolio valuation from a local holdings file (JSON list of {coin_id, amount}). Fetches spot prices from CoinGecko in one batched call, computes per-holding and total value, and reports risk/concentration reads. Includes scripts/portfolio.py.
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [Crypto, Portfolio, Finance, Tracking, Valuation]
    category: research
    related_skills: [crypto-market, polymarket]
prerequisites:
  commands: [python3]
---

# Portfolio Tracker — Crypto Holdings Valuation

Value a crypto portfolio from a local holdings file using free, keyless
CoinGecko price data. No exchange accounts, no signup, no API keys — and
this skill never touches private keys or seed phrases. It composes the
same keyless CoinGecko pricing this workspace already uses in
[[crypto-market]] into a portfolio-level view; it does not replace or
duplicate that skill's per-coin lookups.

## When to Use

- User wants to know what their crypto portfolio is worth right now
- User maintains a list of coins and amounts and wants a total valuation
- User asks "how concentrated / risky is my portfolio?" or wants a
  rebalance read
- **Not** for placing trades, connecting a wallet, or anything requiring a
  private key — this skill is read-only by design. It also does not track
  cost basis, realized gains, or taxes (see Pitfalls).

## Holdings File Format

A holdings file is a local, user-maintained plaintext JSON file — a
list of `{coin_id, amount}` objects. `coin_id` is a CoinGecko coin id
(same ids used by [[crypto-market]]'s `price` command, e.g. `bitcoin`,
`ethereum`, `usd-coin`); `amount` is the quantity held.

```json
[
  {"coin_id": "bitcoin", "amount": 0.05},
  {"coin_id": "ethereum", "amount": 1.2},
  {"coin_id": "usd-coin", "amount": 500}
]
```

See `scripts/sample-holdings.json` for a working example. **Never put
private keys, seed phrases, exchange API keys, or any other secret in a
holdings file** — it's a plaintext list of coin ids and quantities, and
this skill treats it that way. It has no field for anything else.

## Quickstart

```bash
python3 scripts/portfolio.py check scripts/sample-holdings.json
python3 scripts/portfolio.py value scripts/sample-holdings.json
python3 scripts/portfolio.py value scripts/sample-holdings.json --vs eur
```

## Workflow

1. **Load** — `check <holdings.json>` validates the file's structure
   (every `coin_id`/`amount` shape-checked) without making a network call.
   Run this first if you're unsure the file is well-formed.
2. **Fetch prices** — `value <holdings.json>` loads the holdings, then
   fetches spot prices for every unique `coin_id` in **one** batched
   CoinGecko `/simple/price` call (not one call per coin).
3. **Value** — computes `amount * price` per holding and a portfolio total,
   printed as a table sorted by value descending.
4. **Report** — for an open-ended "how's my portfolio doing" ask, present
   the table plus a one-paragraph risk/concentration read (see Model
   Wiring below) rather than just the raw numbers.

## Model Wiring

| Task | Model | Endpoint | Why |
|------|-------|----------|-----|
| Deterministic valuation math + table formatting (e.g. "given these holdings and this CoinGecko price payload, compute per-holding and total value as a JSON table") | **agent1** (`hf.co/InternScience/Agents-A1-Q4_K_M-GGUF:latest`) | Ollama, `http://localhost:11434/api/chat`, `"options": {"temperature": 0}` | Temperature 0 for repeatable arithmetic and formatting — this is math, not creative synthesis |
| Portfolio risk/concentration/rebalance read (e.g. "given this valuation table, how concentrated is this portfolio and what would you flag for rebalancing?") | **ornith** (`ornith-uncensored`) | llama-swap, `http://localhost:1235/v1/chat/completions`, `"chat_template_kwargs": {"enable_thinking": false}` | Fast, terse takes without a slow reasoning trace |

```python
import json
import urllib.request

# agent1: deterministic valuation math, temperature 0
payload = {
    "model": "hf.co/InternScience/Agents-A1-Q4_K_M-GGUF:latest",
    "messages": [
        {"role": "system", "content": "Compute per-holding value (amount * price) and a total. JSON only, no prose, no markdown fences."},
        {"role": "user", "content": f"Value these holdings against this price payload:\n\n{holdings_and_prices_json}"},
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
# ornith: risk/concentration/rebalance triage, thinking disabled
payload = {
    "model": "ornith-uncensored",
    "messages": [{"role": "user", "content": f"Given this portfolio valuation table, how concentrated is it and what would you flag for rebalancing?\n\n{valuation_table}"}],
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

If either curl returns nothing, that local server is down or the model isn't loaded.

## Pitfalls

- **Prices are spot, not realized**: `value` reports what the portfolio is
  worth *right now* at CoinGecko's current spot price — it is not a
  realized-gain or exit price, and it moves the moment the market does.
  Always note that a valuation is a point-in-time snapshot when relaying
  it to the user.
- **No tax or cost-basis tracking**: this skill has no concept of when or
  at what price a holding was acquired. It cannot compute unrealized
  gain/loss, realized gain/loss, or anything tax-relevant. If the user
  asks for that, say so explicitly rather than approximating it from spot
  price alone.
- **Holdings file is user-maintained plaintext — no secrets**: it holds
  `coin_id`/`amount` pairs only. Never write a private key, seed phrase,
  or exchange API key into it, and never suggest a user do so.
- **Volatility**: crypto prices move fast; a valuation computed a few
  minutes ago may already be stale, especially for a portfolio concentrated
  in a single volatile coin.
- **CoinGecko rate limits**: the public (keyless) tier is generous but
  undocumented and can throttle bursty usage — this skill already batches
  all coin ids into one `/simple/price` call per `value` run rather than
  querying per-coin, but avoid tight polling loops on top of that.
- **Fixed endpoint, validated input**: the only host this skill talks to
  (`api.coingecko.com`) is a hardcoded constant in `scripts/portfolio.py`,
  never built from user input. What *is* user input — the holdings file
  path and its contents — is validated defensively: the path must be a
  readable regular file (directories and devices are rejected), and every
  `coin_id`/`amount` field is isinstance-checked before use, so a
  malformed or hand-edited holdings file fails cleanly with exit 2 instead
  of crashing.
- **Unpriced coins are skipped, not fatal**: if CoinGecko doesn't recognize
  a `coin_id` (typo, delisted, wrong id), that holding is reported on
  stderr and excluded from the total rather than aborting the whole
  valuation — check stderr if the total looks lower than expected.

## Ethics

Read-only. This skill never places trades, connects to a wallet, or
requests, stores, or transmits a private key or seed phrase. If a user
asks it to "buy", "sell", "send", or "sign" anything, that's out of scope
— refuse and explain why.
