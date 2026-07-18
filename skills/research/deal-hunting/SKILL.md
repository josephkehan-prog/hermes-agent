---
name: deal-hunting
description: Hunt software and hardware deals from free RSS feeds.
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [Deals, Price Tracking, Shopping, Research, RSS]
    category: research
    related_skills: [scrapling, duckduckgo-search]
prerequisites:
  commands: [python3]
---

# Deal Hunting

Find software and hardware deals using only free, keyless sources: Slickdeals
and OzBargain RSS feeds, plus Reddit's `r/buildapcsales` and `r/GameDeals`
via `old.reddit.com` RSS. No API keys, no paid deal-tracking services
(ITAD/IsThereAnyDeal, CamelCamelCamel's own API, PCPartPicker's data feed —
none expose a keyless endpoint that survived verification; see
[Pitfalls](#pitfalls)).

## When to Use

- User wants current deals on a specific product/category ("find me a cheap SSD deal", "any GPU deals right now?")
- User wants to track a product over time and get notified of new matches
- User wants a price-history *sanity check* before buying (manual browser lookup — see [Sources](#sources))
- Not for: real-time price-drop alerts (requires polling on a schedule, e.g. via `cron` skill), or historical price charts (no keyless API — see Pitfalls)

## Quickstart

```bash
# One-off search across all sources
python3 scripts/deals.py search "ssd" --source all --limit 10

# Search a single source
python3 scripts/deals.py search "rtx 4070" --source slickdeals

# Track a query over time, deduped by link
python3 scripts/deals.py watch "steam deck" --out watchlist.json --source reddit-gamedeals
```

## Sources

| Source | URL pattern | Good for | Rate-limit courtesy |
|--------|-------------|----------|----------------------|
| Slickdeals search RSS | `https://slickdeals.net/newsearch.php?q={query}&rss=1` | US retail, electronics, software keys, broad frontpage deals | No documented limit observed; keep to a few requests per minute |
| OzBargain deals RSS | `https://www.ozbargain.com.au/deals/feed` | AU retail/software; **no keyless search RSS** — the `/search/node/...` endpoint is behind a Cloudflare challenge, so `deals.py` fetches the main feed and filters locally | Feed refreshes every few minutes; don't poll faster than ~1/min |
| Reddit r/buildapcsales | `https://old.reddit.com/r/buildapcsales/search.rss?q={query}&restrict_sr=on&sort=new` | PC hardware (GPU, SSD, RAM, prebuilts) | Reddit rate-limits aggressively (429s observed after a handful of requests); space requests out, use one source at a time when iterating |
| Reddit r/GameDeals | `https://old.reddit.com/r/GameDeals/search.rss?q={query}&restrict_sr=on&sort=new` | Game keys, launchers (Steam, GOG, Epic) | Same as above |
| PCPartPicker price trends | *no scrape endpoint documented here* | Sanity-checking whether a component's current price is actually low | Manual lookup via browser tools (`claude-in-chrome` or `scrapling`) — PCPartPicker pages are JS-rendered and ToS discourages scraping; do a one-off visual check, don't automate |
| CamelCamelCamel | *no scrape endpoint documented here* | Amazon price history charts | Manual browser lookup only — CCC has no public keyless API and explicitly disallows scraping in its ToS; treat as a human-in-the-loop verification step, not an automatable source |

`www.reddit.com/.../new.json` (the public JSON endpoint) returned an HTML
consent/challenge page during verification, not JSON — it is **not** a
reliable keyless source from this environment. `old.reddit.com/.../*.rss`
(Atom format) worked reliably and is what `deals.py` uses.

## Workflow

1. **Search**: run `deals.py search <query> --source all` to pull matches from every source in one pass. Each source is fetched independently and a failure in one (network error, malformed feed) only warns to stderr — the others still return results.
2. **Filter**: `deals.py` extracts a `$price` substring from the title via regex where present; titles without a parseable price still show up with `price: -`. Skim titles for category noise (accessories, extended warranties, affiliate bait — see Pitfalls).
3. **Track**: switch to `deals.py watch <query> --out watchlist.json` on a recurring cadence (e.g. via the `cron`/`schedule` skill) to accumulate new matches over time, deduped by SHA-256 of the link so re-running never double-adds a deal.
4. **Verify a standout deal**: for anything you're about to act on, open the link and, if price history matters, do a manual PCPartPicker/CamelCamelCamel check rather than trusting the listed price alone — deal titles are user-submitted and can be stale or wrong.

## Model Wiring

For larger result sets, pipe the raw `search` output into a local model
instead of hand-scanning every title. Two local endpoints, split by task
(same wiring as the [scrapling](../../scrapling/SKILL.md) skill):

| Task | Model | Endpoint | Why |
|------|-------|----------|-----|
| Deterministic dedupe/parse (e.g. "collapse near-duplicate titles across sources into one JSON list with canonical price") | **agent1** (`hf.co/InternScience/Agents-A1-Q4_K_M-GGUF:latest`) | Ollama, `http://localhost:11434/api/chat` | Temperature 0 for repeatable structured output |
| Deal-quality reasoning (e.g. "which of these are actually good deals vs. inflated MSRP or accessory noise") | **ornith** (`ornith-uncensored`) | llama-swap, `http://localhost:1235/v1/chat/completions` | Reasoning model; disable thinking with `chat_template_kwargs: {"enable_thinking": false}` for fast, terse output |

```python
import json
import urllib.request

# agent1: dedupe/normalize a batch of deal titles, temperature 0
payload = {
    "model": "hf.co/InternScience/Agents-A1-Q4_K_M-GGUF:latest",
    "messages": [
        {"role": "system", "content": "Dedupe near-identical deals and extract canonical price as JSON only. No prose, no markdown fences."},
        {"role": "user", "content": f"Dedupe and normalize:\n\n{deals_json}"},
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
# ornith: rank/reason about deal quality, thinking disabled
payload = {
    "model": "ornith-uncensored",
    "messages": [{"role": "user", "content": f"Which of these are genuinely good deals vs. noise? Explain briefly.\n\n{deals_json}"}],
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

If either curl returns nothing, that local server is down or the model isn't
loaded.

## Pitfalls

- **Stale RSS**: feeds cache for a few minutes server-side; a deal shown as "new" may have already expired or sold out. Always click through before acting.
- **Affiliate/noise listings**: Slickdeals and OzBargain both carry sponsored or low-value posts (extended warranties, "deal" reposts, accessory bundles). Titles alone aren't a quality signal — use the [ornith triage](#model-assisted-triage) pass or read the top comments for community sentiment before trusting a listing.
- **Regional pricing**: OzBargain and `.com.au` links are AUD and Australia-only; Slickdeals/Reddit skew US. Don't assume a price quoted on one feed is available in your region or currency.
- **No keyless price-history API**: ITAD/IsThereAnyDeal's free tier and CamelCamelCamel both require either an API key or browser-rendered pages — neither exposes a documented keyless JSON/RSS endpoint that survived verification. Treat price-history checks as a manual, human-in-the-loop step via browser tools, not something `deals.py` automates.
- **Reddit rate limiting**: `www.reddit.com/.../*.json` returned an HTML challenge page in testing; `old.reddit.com/.../*.rss` worked but returned HTTP 429 after repeated rapid requests in the same session. Space out `--source reddit-bapcs`/`reddit-gamedeals` calls, or use `--source all` sparingly rather than looping per-query.
- **OzBargain has no keyless search**: `deals.py fetch_ozbargain` pulls the full `/deals/feed` (30 most recent items) and filters by substring locally — a niche query may return zero OzBargain matches even if an older, now-scrolled-off deal exists. Widen the query or check the OzBargain website directly for deeper history.
