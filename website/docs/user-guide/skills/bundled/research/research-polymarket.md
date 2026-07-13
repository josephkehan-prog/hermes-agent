---
title: "Polymarket — Query Polymarket: markets, prices, orderbooks, history"
sidebar_label: "Polymarket"
description: "Query Polymarket: markets, prices, orderbooks, history"
---

{/* This page is auto-generated from the skill's SKILL.md by website/scripts/generate-skill-docs.py. Edit the source SKILL.md, not this page. */}

# Polymarket

Query Polymarket: markets, prices, orderbooks, history.

## Skill metadata

| | |
|---|---|
| Source | Bundled (installed by default) |
| Path | `skills/research/polymarket` |
| Version | `1.1.0` |
| Author | Hermes Agent + Teknium |
| Platforms | linux, macos, windows |

## Reference: full SKILL.md

:::info
The following is the complete skill definition that Hermes loads when this skill is triggered. This is what the agent sees as instructions when the skill is active.
:::

# Polymarket — Prediction Market Data

Query prediction market data from Polymarket using their public REST APIs.
All endpoints are read-only and require zero authentication.

See `references/api-endpoints.md` for the full endpoint reference with curl examples.

## When to Use

- User asks about prediction markets, betting odds, or event probabilities
- User wants to know "what are the odds of X happening?"
- User asks about Polymarket specifically
- User wants market prices, orderbook data, or price history
- User asks to monitor or track prediction market movements

## Key Concepts

- **Events** contain one or more **Markets** (1:many relationship)
- **Markets** are binary outcomes with Yes/No prices between 0.00 and 1.00
- Prices ARE probabilities: price 0.65 means the market thinks 65% likely
- `outcomePrices` field: JSON-encoded array like `["0.80", "0.20"]`
- `clobTokenIds` field: JSON-encoded array of two token IDs [Yes, No] for price/book queries
- `conditionId` field: hex string used for price history queries
- Volume is in USDC (US dollars)

## Three Public APIs

1. **Gamma API** at `gamma-api.polymarket.com` — Discovery, search, browsing
2. **CLOB API** at `clob.polymarket.com` — Real-time prices, orderbooks, history
3. **Data API** at `data-api.polymarket.com` — Trades, open interest

## Commands

```bash
python3 scripts/polymarket.py search "bitcoin"
python3 scripts/polymarket.py trending [--limit 10]
python3 scripts/polymarket.py closing-soon [--limit 10]   # open markets, soonest end date first
python3 scripts/polymarket.py market <slug>
python3 scripts/polymarket.py event <slug>
python3 scripts/polymarket.py price <token_id>
python3 scripts/polymarket.py book <token_id>
python3 scripts/polymarket.py history <condition_id> [--interval all] [--fidelity 50]
python3 scripts/polymarket.py trades [--limit 10] [--market CONDITION_ID]
```

## Typical Workflow

When a user asks about prediction market odds:

1. **Search** using the Gamma API public-search endpoint with their query
2. **Parse** the response — extract events and their nested markets
3. **Present** market question, current prices as percentages, and volume
4. **Deep dive** if asked — use clobTokenIds for orderbook, conditionId for history

## Presenting Results

Format prices as percentages for readability:
- outcomePrices `["0.652", "0.348"]` becomes "Yes: 65.2%, No: 34.8%"
- Always show the market question and probability
- Include volume when available

Example: `"Will X happen?" — 65.2% Yes ($1.2M volume)`

## Parsing Double-Encoded Fields

The Gamma API returns `outcomePrices`, `outcomes`, and `clobTokenIds` as JSON strings
inside JSON responses (double-encoded). When processing with Python, parse them with
`json.loads(market['outcomePrices'])` to get the actual array.

## Model Wiring

| Task | Model | Endpoint | Why |
|------|-------|----------|-----|
| Deterministic market/odds extraction + dedup (e.g. "collapse these search/trending results into one JSON list of &#123;question, yes_pct, no_pct, volume, slug&#125;, drop duplicate markets") | **agent1** (`hf.co/InternScience/Agents-A1-Q4_K_M-GGUF:latest`) | Ollama, `http://localhost:11434/api/chat` | Temperature 0 for repeatable structured output |
| Market-sentiment / fair-pricing triage (e.g. "is this priced fairly, what's the implied-probability narrative, what would move this market") | **ornith** (`ornith-uncensored`) | llama-swap, `http://localhost:1235/v1/chat/completions` | Reasoning model; disable thinking with `chat_template_kwargs: {"enable_thinking": false}` for fast, terse output |

```python
import json
import urllib.request

# agent1: extract/dedup market fields, temperature 0
payload = {
    "model": "hf.co/InternScience/Agents-A1-Q4_K_M-GGUF:latest",
    "messages": [
        {"role": "system", "content": "Extract {question, yes_pct, no_pct, volume, slug} per market and dedup near-identical questions. JSON only, no prose, no markdown fences."},
        {"role": "user", "content": f"Extract and dedup markets:\n\n{markets_json}"},
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
# ornith: fair-pricing / sentiment triage, thinking disabled
payload = {
    "model": "ornith-uncensored",
    "messages": [{"role": "user", "content": f"Is this market priced fairly? What's the implied-probability narrative and what would move it?\n\n{market_json}"}],
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

- **Double-encoded odds fields**: `outcomePrices`, `outcomes`, and `clobTokenIds` come back as JSON strings inside JSON — always `json.loads()` them (see "Parsing Double-Encoded Fields" above); treating them as arrays directly silently breaks formatting.
- **Volume/liquidity aren't interchangeable**: `volume` is cumulative traded USDC over the market's life, `liquidity` is resting order-book depth right now. A high-volume market can still have thin live liquidity (wide spreads, low `book` depth) — check `book` before treating a price as executable.
- **Markets resolve and close**: a market's odds go stale the moment it's `closed`; don't quote a cached price as current without checking `closed`/`active` first.
- **`closing-soon` can include markets whose `endDate` already passed**: Polymarket sometimes leaves a market `closed=false` past its scheduled `endDate` while resolution is pending, so `closing-soon` may show "Closes: closed" for markets still technically open. Treat `closing-soon` as "at or past its scheduled window," not a guarantee of imminent resolution.

## Rate Limits

Generous — unlikely to hit for normal usage:
- Gamma: 4,000 requests per 10 seconds (general)
- CLOB: 9,000 requests per 10 seconds (general)
- Data: 1,000 requests per 10 seconds (general)

## Limitations

- This skill is read-only — it does not support placing trades
- Trading requires wallet-based crypto authentication (EIP-712 signatures)
- Some new markets may have empty price history
- Geographic restrictions apply to trading but read-only data is globally accessible
