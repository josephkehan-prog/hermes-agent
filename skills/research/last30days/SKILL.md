---
name: last30days
description: Research what people actually said about a topic in the last ~30 days across Reddit, Hacker News, Polymarket, and GitHub — using only keyless public endpoints and Hermes's own web/browser tools. No paid API keys. For recency checks, sentiment, "what are people saying about X", launch reactions, trend spotting.
version: 1.1.0
author: Hermes Agent (keyless port of mvanhorn/last30days-skill, MIT)
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [research, recency, reddit, hackernews, polymarket, github, sentiment, trends, keyless]
    category: research
    requires_toolsets: [web, terminal]
    related_skills: [deep-research, osint-reconnaissance, market-research]
---

# Last 30 Days (Keyless)

Pull recent public chatter on a topic from sources that need **no API key**.
Use Hermes's `web` tool (or `terminal` + `curl`) against the endpoints below,
then synthesize a short cited answer. X/Twitter, YouTube, TikTok require paid or
cookie backends — **skip them**; state the coverage limit in the answer.

## When to Use
- "What are people saying about X (lately / this month)?"
- Launch / earnings / release reaction, sentiment, emerging complaints.
- Sanity-check a claim's recency before deep research.

## Quickstart / scripts
A runnable CLI ships alongside this doc — `scripts/last30days.py` (stdlib
only, no API keys) actually fetches from the sources below instead of just
documenting them:
```bash
python3 scripts/last30days.py search "TOPIC" --sources all --limit 15
python3 scripts/last30days.py search "TOPIC" --sources reddit,hn --json
python3 scripts/last30days.py hn "TOPIC" --limit 10   # per-source: reddit|hn|polymarket|github
```
`search` prints a merged table (source/title/metric/date/link) with a
per-source count line; `--json` gives a structured `{entries, counts,
errors}` payload. Each source is fetched with error isolation — one failing
doesn't drop the others — and the process exits 2 only if every requested
source fails. See `scripts/README.md` for the full CLI shape.

**Model wiring**: run dedup/date-normalization over the merged results with
`agent1` (`:11434`, temp 0) — deterministic cleanup, not judgment. Run the
"what's the sentiment / what changed" synthesis step with `ornith`
(`:1235`, `enable_thinking: false`) over the deduped set.

## Sources (all keyless)

**Reddit** — public JSON, add `.json` to any listing, no auth:
```bash
curl -s -A "hermes/1.0" "https://www.reddit.com/search.json?q=TOPIC&sort=new&t=month&limit=25"
curl -s -A "hermes/1.0" "https://www.reddit.com/r/SUBREDDIT/search.json?q=TOPIC&restrict_sr=1&sort=top&t=month"
```
Read `data.children[].data`: `title`, `selftext`, `score`, `num_comments`, `permalink`, `created_utc`.

> **Reddit 403 fallback**: `curl` against `www.reddit.com/*.json` (and `old.reddit.com`) now usually returns **403** — Reddit blocks non-browser clients. Real fix: use the `browser` toolset (`browser_navigate` to the `.json` URL, read the response body as text, parse the JSON) — see the `browser-first` skill. Requires `bin/hermes-browser` running. Never fall back to `computer_use`. If the browser is unavailable, drop Reddit and disclose it in the coverage line.

**Hacker News** — Algolia API, no key, date-filtered:
```bash
# last 30 days = now-2592000 in unix seconds; compute NUM first
curl -s "https://hn.algolia.com/api/v1/search_by_date?query=TOPIC&tags=story&numericFilters=created_at_i>NUM"
```
Read `hits[]`: `title`, `url`, `points`, `num_comments`, `objectID` (→ `news.ycombinator.com/item?id=`).

**Polymarket** — public markets API, no key (real-money sentiment on events):
```bash
curl -s "https://gamma-api.polymarket.com/markets?closed=false&limit=20&order=volume&ascending=false"
# or filter by keyword client-side on the JSON `question` field
```

**GitHub** — public search, no key (or `gh` CLI if installed):
```bash
curl -s "https://api.github.com/search/issues?q=TOPIC+created:>YYYY-MM-DD&sort=created"
gh search issues "TOPIC" --created ">YYYY-MM-DD" --limit 20   # if gh present
```

**General web** — use Hermes's own `web_search` for anything else; it fills the gaps
Reddit/HN/Polymarket/GitHub miss.

## Procedure
1. Compute the 30-day cutoff (`date -v-30d +%s` on macOS, `date -d '30 days ago' +%s` on Linux; ISO date for GitHub).
2. Query Reddit + HN + Polymarket + GitHub for the topic (parallelize with the `web`/`terminal` tools).
3. Supplement with one `web_search` for general/news coverage.
4. Dedup, sort by engagement (score/points/comments/volume) and recency.
5. Synthesize: 1 short narrative paragraph on the dominant sentiment/themes, then a
   numbered `KEY PATTERNS:` list. Cite each claim with its source link.

## Rules (local-model friendly)
- Keyless only. Never require or invent an API key. If a source rate-limits, note it and move on.
- Always disclose coverage: e.g. "Covered Reddit/HN/Polymarket/GitHub + web; X/YouTube/TikTok skipped (need paid keys)."
- Don't fabricate counts or dates — every number comes from a fetched payload.
- Keep the answer tight; no filler sections.

## Optional: upstream engine
The full multi-source engine (adds X/YouTube/TikTok via paid/cookie backends) lives at
`~/.claude/plugins/marketplaces/last30days-skill/` — use only if the user has those keys
configured. Default Hermes path is the keyless flow above.
