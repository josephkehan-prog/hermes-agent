---
name: market-pulse
description: One-shot market-snapshot dashboard combining keyless crypto and prediction-market signals — top coin prices, the Fear & Greed Index, and Polymarket's trending markets — into a single "how's the market doing" read. Includes scripts/pulse.py.
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [Crypto, Markets, Sentiment, Dashboard, Finance, Prediction-Markets]
    category: research
    related_skills: [crypto-market, polymarket, deal-hunting]
prerequisites:
  commands: [python3]
---

# Market Pulse — Combined Crypto + Prediction-Market Snapshot

Query CoinGecko, alternative.me, and Polymarket in one run and get back a
single combined dashboard: top coin prices with 24h change, the Crypto
Fear & Greed Index, and the prediction markets currently pulling the most
volume. Keyless, read-only, and free.

This skill is a **synthesizer, not a new fetcher**. It composes the same
keyless sources [[crypto-market]] and [[polymarket]] already query — it
does not add a new data source or duplicate their per-source CLIs. Reach
for `crypto-market` or `polymarket` when the user wants to drill into one
coin or one market; reach for `market-pulse` when they want the overall
picture in one shot.

## When to Use

- "Give me a market snapshot"
- "What's the mood out there?"
- "How's the market doing today?" (open-ended, not about one specific coin or market)
- User wants crypto sentiment AND prediction-market activity together, not one or the other
- **Not** for a single coin's price (use [[crypto-market]]) or a specific prediction market's details (use [[polymarket]]) — this skill is for the wide-angle view

## Sources Combined

| Source | Endpoint | What it contributes |
|---|---|---|
| CoinGecko | `GET /api/v3/coins/markets` | Top coins by market cap: price, 24h change |
| alternative.me | `GET /fng/` | Crypto Fear & Greed Index (0 = Extreme Fear, 100 = Extreme Greed) |
| Polymarket Gamma | `GET /events` (sorted by volume) | Top prediction markets currently trending by volume |

All three are keyless, public, read-only endpoints — no signup, no
account, no auth headers.

## Quickstart

```bash
python3 scripts/pulse.py snapshot
python3 scripts/pulse.py snapshot --json
```

## Workflow

1. **Gather** — `snapshot` fetches all three sources in one run. Each
   source is wrapped in its own try/except: if CoinGecko is rate-limited
   or Polymarket times out, the other sources still print. A source that
   fails is shown as "unavailable: `<reason>`" in its section rather than
   aborting the whole snapshot.
2. **Synthesize** — once the three sections are gathered, read them
   together rather than in isolation: a low Fear & Greed reading alongside
   Polymarket markets betting on further downside, or a high Fear & Greed
   reading alongside broad-based crypto gains, is a more useful read than
   any one section alone. See Model Wiring below for how to hand this off
   to a model rather than eyeballing it.

Exit codes: 0 if at least one source succeeded, 2 if all three failed.

## Model Wiring

| Task | Model | Endpoint | Why |
|------|-------|----------|-----|
| Deterministic number extraction / table assembly (e.g. "pull symbol, price, 24h change into a clean table from this snapshot JSON") | **agent1** | Ollama `http://localhost:11434/api/chat`, `"options": {"temperature": 0}` | Temperature 0 for repeatable structured output |
| Overall market-mood / notable-signals narrative (e.g. "given this Fear & Greed reading, these coin moves, and these trending prediction markets, what's the read?") | **ornith** | llama-swap `http://localhost:1235/v1/chat/completions`, `"chat_template_kwargs": {"enable_thinking": false}` | Fast, terse takes without a slow reasoning trace |

```python
import json
import urllib.request

# agent1: deterministic table assembly, temperature 0
payload = {
    "model": "hf.co/InternScience/Agents-A1-Q4_K_M-GGUF:latest",
    "messages": [
        {"role": "system", "content": "Extract structured data as JSON only. No prose, no markdown fences."},
        {"role": "user", "content": f"Assemble a {{symbol, price, change_24h}} table from this pulse snapshot.\n\n{snapshot_json}"},
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
# ornith: market-mood synthesis, thinking disabled
payload = {
    "model": "ornith-uncensored",
    "messages": [{"role": "user", "content": f"Given this combined crypto + Fear & Greed + Polymarket snapshot, give a one-paragraph read on overall market mood and any notable signals.\n\n{snapshot_json}"}],
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

- **This is a snapshot, not advice**: a point-in-time read of price,
  sentiment, and prediction-market odds is not a trading or investment
  recommendation. Always relay it as "here's the current state," never
  as a signal to act on.
- **Rate limits**: CoinGecko's keyless tier and Polymarket's Gamma API
  are both generous but undocumented and can throttle bursty usage.
  `snapshot` makes one call per source per run — don't poll it in a tight
  loop.
- **Correlation is not causation**: Fear & Greed dropping and a
  particular Polymarket market moving on the same day doesn't mean one
  caused the other. Present the sections side by side as independent
  signals, not as a causal chain, unless a real link is evident.
- **Fixed endpoints, no user-controlled URLs**: every host this skill
  talks to (`api.coingecko.com`, `api.alternative.me`,
  `gamma-api.polymarket.com`) is a hardcoded constant in `scripts/pulse.py`
  — there's no SSRF surface here since the skill takes no free-text
  target URL from the user.
- **Per-source failure is expected, not exceptional**: if one source is
  down, `snapshot` still prints the other two and exits 0. Only treat a
  full failure (exit 2, all three sources unavailable) as something worth
  surfacing to the user as "market data is temporarily unavailable."
