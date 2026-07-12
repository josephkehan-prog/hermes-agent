---
name: scrapling
description: Web scraping with Scrapling - HTTP fetching, stealth browser automation, Cloudflare bypass, and spider crawling via CLI and Python. Includes local-model-assisted extraction (agent1/ornith) and scripts/extract.py.
version: 1.1.0
author: FEUAZUR
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [Web Scraping, Browser, Cloudflare, Stealth, Crawling, Spider, Research, Profiling]
    related_skills: [duckduckgo-search, domain-intel]
    homepage: https://github.com/D4Vinci/Scrapling
prerequisites:
  commands: [scrapling, python]
---

# Scrapling

[Scrapling](https://github.com/D4Vinci/Scrapling) is a web scraping framework with anti-bot bypass, stealth browser automation, and a spider framework. It provides three fetching strategies (HTTP, dynamic JS, stealth/Cloudflare) and a full CLI. Use it for research, scraping, and profiling tasks where `web_extract` or browser tools fall short.

**This skill is for educational and research purposes only.** Users must comply with local/international data scraping laws and respect website Terms of Service.

**API verification note:** the Python examples below reflect the documented Scrapling API (`Fetcher` / `DynamicFetcher` / `StealthyFetcher` / `Spider`). This environment does not have `scrapling` pip-installed, so they are documented as reference — verify against your installed version with `python3 -c "from scrapling.fetchers import Fetcher; help(Fetcher.get)"` before relying on exact signatures, especially across major versions.

## When to Use

- Scraping static HTML pages (faster than browser tools)
- Scraping JS-rendered pages that need a real browser
- Bypassing Cloudflare Turnstile or bot detection
- Crawling multiple pages with a spider
- Researching/profiling a site or set of pages, optionally with local-model extraction (see [Model-Assisted Extraction](#model-assisted-extraction))
- When the built-in `web_extract` tool does not return the data you need

## Quickstart

```bash
# Install (not run automatically by this skill)
pip install "scrapling[all]" && scrapling install

# Static page -> markdown
scrapling extract get 'https://example.com' output.md

# JS-rendered page -> markdown, wait for network idle
scrapling extract fetch 'https://example.com' output.md --network-idle

# Cloudflare-protected page -> html
scrapling extract stealthy-fetch 'https://protected-site.com' output.html --solve-cloudflare

# This skill's helper: fetch + optional local-model extraction, no install required
python3 scripts/extract.py 'https://example.com'
python3 scripts/extract.py 'https://example.com' --css '.article' --model agent1
```

## Installation

```bash
pip install "scrapling[all]"
scrapling install
```

Minimal install (HTTP only, no browser):
```bash
pip install scrapling
```

With browser automation only:
```bash
pip install "scrapling[fetchers]"
scrapling install
```

## Three Fetcher Strategies

Scrapling gives you three fetchers, cheapest-first. Try `Fetcher` before reaching for `DynamicFetcher` or `StealthyFetcher` — each step up costs more time and resources.

| Approach | Class | Use When | Python Examples |
|----------|-------|----------|------------------|
| HTTP | `Fetcher` / `FetcherSession` | Static pages, APIs, fast bulk requests | [Python: HTTP Scraping](#python-http-scraping) |
| Dynamic | `DynamicFetcher` / `DynamicSession` | JS-rendered content, SPAs | [Python: Dynamic Pages](#python-dynamic-pages-js-rendered) |
| Stealth | `StealthyFetcher` / `StealthySession` | Cloudflare, anti-bot protected sites | [Python: Stealth Mode](#python-stealth-mode-anti-bot-bypass) |
| Spider | `Spider` | Multi-page crawling with link following | [Python: Spider Framework](#python-spider-framework) |

## CLI Usage

### Extract Static Page

```bash
scrapling extract get 'https://example.com' output.md
```

With CSS selector and browser impersonation:

```bash
scrapling extract get 'https://example.com' output.md \
  --css-selector '.content' \
  --impersonate 'chrome'
```

### Extract JS-Rendered Page

```bash
scrapling extract fetch 'https://example.com' output.md \
  --css-selector '.dynamic-content' \
  --disable-resources \
  --network-idle
```

### Extract Cloudflare-Protected Page

```bash
scrapling extract stealthy-fetch 'https://protected-site.com' output.html \
  --solve-cloudflare \
  --block-webrtc \
  --hide-canvas
```

### POST Request

```bash
scrapling extract post 'https://example.com/api' output.json \
  --json '{"query": "search term"}'
```

### Output Formats

The output format is determined by the file extension:
- `.html` -- raw HTML
- `.md` -- converted to Markdown
- `.txt` -- plain text
- `.json` / `.jsonl` -- JSON

## Python API

Full Python code for each strategy — direct requests, sessions, dynamic/stealth fetch, element selection (CSS/XPath/find methods), and the spider framework (including multi-session routing and pause/resume): read `references/python-api.md` when writing Python against Scrapling directly rather than the CLI.

## Troubleshooting

Common failure symptoms (Cloudflare challenge pages, blank JS-rendered content, blocked after first request, rate limiting, missing browser binaries, selector mismatches, timeout unit confusion) and fixes: read `references/troubleshooting.md` when a fetch misbehaves.

## Model-Assisted Extraction

For research/profiling workflows, pipe fetched text into a local model (agent1 for deterministic structured JSON, ornith for analysis/summarization) instead of hand-writing selectors. Both are called by `scripts/extract.py` (see [scripts/README.md](scripts/README.md)). Wiring details, endpoints, and manual-call examples: read `references/model-assisted-extraction.md` when hooking these up yourself.

## Pitfalls

- **Browser install required**: run `scrapling install` after pip install -- without it, `DynamicFetcher` and `StealthyFetcher` will fail
- **Timeouts**: DynamicFetcher/StealthyFetcher timeout is in **milliseconds** (default 30000), Fetcher timeout is in **seconds**
- **Cloudflare bypass**: `solve_cloudflare=True` adds 5-15 seconds to fetch time -- only enable when needed
- **Resource usage**: StealthyFetcher runs a real browser -- limit concurrent usage
- **Legal**: always check robots.txt and website ToS before scraping. This library is for educational and research purposes
- **Python version**: requires Python 3.10+
- **`scripts/extract.py` doesn't require scrapling**: it falls back to `urllib` + stdlib HTML stripping when scrapling isn't installed, but `--css` selection only works via scrapling — without it, the flag is ignored with a warning
