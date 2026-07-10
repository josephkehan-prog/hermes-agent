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

## Python: HTTP Scraping

### Single Request

```python
from scrapling.fetchers import Fetcher

page = Fetcher.get('https://quotes.toscrape.com/')
quotes = page.css('.quote .text::text').getall()
for q in quotes:
    print(q)
```

### Session (Persistent Cookies)

```python
from scrapling.fetchers import FetcherSession

with FetcherSession(impersonate='chrome') as session:
    page = session.get('https://example.com/', stealthy_headers=True)
    links = page.css('a::attr(href)').getall()
    for link in links[:5]:
        sub = session.get(link)
        print(sub.css('h1::text').get())
```

### POST / PUT / DELETE

```python
page = Fetcher.post('https://api.example.com/data', json={"key": "value"})
page = Fetcher.put('https://api.example.com/item/1', data={"name": "updated"})
page = Fetcher.delete('https://api.example.com/item/1')
```

### With Proxy

```python
page = Fetcher.get('https://example.com', proxy='http://user:pass@proxy:8080')
```

## Python: Dynamic Pages (JS-Rendered)

For pages that require JavaScript execution (SPAs, lazy-loaded content):

```python
from scrapling.fetchers import DynamicFetcher

page = DynamicFetcher.fetch('https://example.com', headless=True)
data = page.css('.js-loaded-content::text').getall()
```

### Wait for Specific Element

```python
page = DynamicFetcher.fetch(
    'https://example.com',
    wait_selector=('.results', 'visible'),
    network_idle=True,
)
```

### Disable Resources for Speed

Blocks fonts, images, media, stylesheets (~25% faster):

```python
from scrapling.fetchers import DynamicSession

with DynamicSession(headless=True, disable_resources=True, network_idle=True) as session:
    page = session.fetch('https://example.com')
    items = page.css('.item::text').getall()
```

### Custom Page Automation

```python
from playwright.sync_api import Page
from scrapling.fetchers import DynamicFetcher

def scroll_and_click(page: Page):
    page.mouse.wheel(0, 3000)
    page.wait_for_timeout(1000)
    page.click('button.load-more')
    page.wait_for_selector('.extra-results')

page = DynamicFetcher.fetch('https://example.com', page_action=scroll_and_click)
results = page.css('.extra-results .item::text').getall()
```

## Python: Stealth Mode (Anti-Bot Bypass)

For Cloudflare-protected or heavily fingerprinted sites:

```python
from scrapling.fetchers import StealthyFetcher

page = StealthyFetcher.fetch(
    'https://protected-site.com',
    headless=True,
    solve_cloudflare=True,
    block_webrtc=True,
    hide_canvas=True,
)
content = page.css('.protected-content::text').getall()
```

### Stealth Session

```python
from scrapling.fetchers import StealthySession

with StealthySession(headless=True, solve_cloudflare=True) as session:
    page1 = session.fetch('https://protected-site.com/page1')
    page2 = session.fetch('https://protected-site.com/page2')
```

## Element Selection

All fetchers return a `Selector` object with these methods:

### CSS Selectors

```python
page.css('h1::text').get()              # First h1 text
page.css('a::attr(href)').getall()      # All link hrefs
page.css('.quote .text::text').getall() # Nested selection
```

### XPath

```python
page.xpath('//div[@class="content"]/text()').getall()
page.xpath('//a/@href').getall()
```

### Find Methods

```python
page.find_all('div', class_='quote')       # By tag + attribute
page.find_by_text('Read more', tag='a')    # By text content
page.find_by_regex(r'\$\d+\.\d{2}')       # By regex pattern
```

### Similar Elements

Find elements with similar structure (useful for product listings, etc.):

```python
first_product = page.css('.product')[0]
all_similar = first_product.find_similar()
```

### Navigation

```python
el = page.css('.target')[0]
el.parent                # Parent element
el.children              # Child elements
el.next_sibling          # Next sibling
el.prev_sibling          # Previous sibling
```

## Python: Spider Framework

For multi-page crawling with link following:

```python
from scrapling.spiders import Spider, Request, Response

class QuotesSpider(Spider):
    name = "quotes"
    start_urls = ["https://quotes.toscrape.com/"]
    concurrent_requests = 10
    download_delay = 1

    async def parse(self, response: Response):
        for quote in response.css('.quote'):
            yield {
                "text": quote.css('.text::text').get(),
                "author": quote.css('.author::text').get(),
                "tags": quote.css('.tag::text').getall(),
            }

        next_page = response.css('.next a::attr(href)').get()
        if next_page:
            yield response.follow(next_page)

result = QuotesSpider().start()
print(f"Scraped {len(result.items)} quotes")
result.items.to_json("quotes.json")
```

### Multi-Session Spider

Route requests to different fetcher types:

```python
from scrapling.fetchers import FetcherSession, AsyncStealthySession

class SmartSpider(Spider):
    name = "smart"
    start_urls = ["https://example.com/"]

    def configure_sessions(self, manager):
        manager.add("fast", FetcherSession(impersonate="chrome"))
        manager.add("stealth", AsyncStealthySession(headless=True), lazy=True)

    async def parse(self, response: Response):
        for link in response.css('a::attr(href)').getall():
            if "protected" in link:
                yield Request(link, sid="stealth")
            else:
                yield Request(link, sid="fast", callback=self.parse)
```

### Pause/Resume Crawling

```python
spider = QuotesSpider(crawldir="./crawl_checkpoint")
spider.start()  # Ctrl+C to pause, re-run to resume from checkpoint
```

## Troubleshooting

| Symptom | Likely Cause | What To Do |
|---------|---------------|------------|
| Cloudflare challenge page in output | Turnstile/JS challenge not solved | Use `StealthyFetcher` with `solve_cloudflare=True`; expect +5-15s per fetch |
| Blank/near-empty content from a page that looks fine in a browser | Content is JS-rendered | Switch from `Fetcher` to `DynamicFetcher`, add `network_idle=True` or a `wait_selector` |
| Fetch succeeds but site immediately blocks/redirects on 2nd request | Fingerprinting (TLS/JA3, headers, canvas, WebRTC) flagged the client | Use `StealthyFetcher` with `block_webrtc=True`, `hide_canvas=True`; add `impersonate='chrome'` on `Fetcher`/`FetcherSession` |
| 403/429 responses after a burst of requests | Rate limiting | Add `download_delay` on `Spider`, lower `concurrent_requests`, reuse a `*Session` instead of one-off fetches, rotate `proxy` |
| `DynamicFetcher`/`StealthyFetcher` raises a browser-not-found error | Playwright browsers not installed | Run `scrapling install` after `pip install` |
| Selector returns nothing | Site markup differs from what you inspected (client-rendered, A/B test, geo-gated) | Re-inspect the actual fetched HTML/markdown (`scrapling extract get ... output.md`) rather than the browser DevTools view |
| Everything times out | Fetcher timeout units differ | `Fetcher` timeout is **seconds**; `DynamicFetcher`/`StealthyFetcher` timeout is **milliseconds** |

## Model-Assisted Extraction

For research/profiling workflows, pipe fetched text into a local model instead of hand-writing selectors for every field, or to summarize/analyze what you scraped. Two local endpoints are wired for this, split by task:

| Task | Model | Endpoint | Why |
|------|-------|----------|-----|
| Deterministic structured extraction (e.g. "pull name/title/date/price as JSON") | **agent1** (`hf.co/InternScience/Agents-A1-Q4_K_M-GGUF:latest`) | Ollama, `http://localhost:11434/api/chat` | Temperature 0 for repeatable output |
| Analytical/summarization passes (e.g. "what's the sentiment", "summarize this profile") | **ornith** (`ornith-uncensored`) | llama-swap, `http://localhost:1235/v1/chat/completions` | Reasoning model; disable thinking with `chat_template_kwargs: {"enable_thinking": false}` for fast, terse output |

Both are called by `scripts/extract.py` — see [scripts/README.md](scripts/README.md). To wire them up manually:

```python
import json
import urllib.request

# agent1: deterministic structured JSON, temperature 0
payload = {
    "model": "hf.co/InternScience/Agents-A1-Q4_K_M-GGUF:latest",
    "messages": [
        {"role": "system", "content": "Extract structured data as JSON only. No prose, no markdown fences."},
        {"role": "user", "content": f"Extract name, title, date as JSON.\n\n{page_text}"},
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
# ornith: analysis/summarization, thinking disabled
payload = {
    "model": "ornith-uncensored",
    "messages": [{"role": "user", "content": f"Summarize this page in 3 bullets.\n\n{page_text}"}],
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

If either curl returns nothing, the corresponding local server is down or the model isn't loaded — `extract.py` will fail fast with `connection refused` (exit 2) rather than hang.

## Pitfalls

- **Browser install required**: run `scrapling install` after pip install -- without it, `DynamicFetcher` and `StealthyFetcher` will fail
- **Timeouts**: DynamicFetcher/StealthyFetcher timeout is in **milliseconds** (default 30000), Fetcher timeout is in **seconds**
- **Cloudflare bypass**: `solve_cloudflare=True` adds 5-15 seconds to fetch time -- only enable when needed
- **Resource usage**: StealthyFetcher runs a real browser -- limit concurrent usage
- **Legal**: always check robots.txt and website ToS before scraping. This library is for educational and research purposes
- **Python version**: requires Python 3.10+
- **`scripts/extract.py` doesn't require scrapling**: it falls back to `urllib` + stdlib HTML stripping when scrapling isn't installed, but `--css` selection only works via scrapling — without it, the flag is ignored with a warning
