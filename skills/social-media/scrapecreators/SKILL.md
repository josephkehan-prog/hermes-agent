---
name: scrapecreators
description: ScrapeCreators API for social profiles (paid key).
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [Social Media, Scraping, TikTok, Instagram, YouTube, Twitter, Profiling, API]
    category: social-media
    related_skills: [scrapling, social-footprint, duckduckgo-search]
---

# ScrapeCreators

[ScrapeCreators](https://scrapecreators.com) is a paid API for scraping public
social-media profiles and posts across TikTok, Instagram, YouTube, X/Twitter,
Reddit, LinkedIn, Facebook, and Threads — no cookies, no login automation, no
browser needed on your side. `scripts/scrapecreators.py` is a stdlib-only CLI
wrapper around it.

## Requires a Paid API Key

This is **not** a free/keyless skill. Every subcommand requires
`SCRAPECREATORS_API_KEY` in the environment:

- Set it in `~/.hermes/.env` as `SCRAPECREATORS_API_KEY=<your key>`
- Get a key at [scrapecreators.com](https://scrapecreators.com) (paid plans;
  pricing is per-request/credit-based — check the current plan before
  running bulk jobs)
- With the key **unset**, every command prints a `[NEEDS-KEY]` message and
  exits 2 **without making a network call** — this script never guesses,
  stubs a fake response, or silently no-ops
- Never hardcode the key in code, logs, or committed files; never print it

## Ethics / ToS Note

- Public data only — this wrapper fetches public profile/post data as
  ScrapeCreators exposes it. It does not bypass authentication, solve
  CAPTCHAs, or access private/gated content.
- Respect both the target platform's Terms of Service and
  [ScrapeCreators' own ToS](https://scrapecreators.com) — a paid API sitting
  in front of a scrape does not exempt you from the underlying platform's
  rules on automated data collection.
- Don't use this for harassment, stalking, or unauthorized profiling of a
  private individual. Treat results the same way as the `social-footprint`
  skill's ethics note: a hit is a lead, not proof, and bulk collection at
  scale carries more legal/ToS risk than a one-off lookup.

## When to Use

- Pulling a public profile (bio, follower count, avatar, etc.) for a named
  handle on a supported platform
- Pulling recent posts from a public profile for content/engagement analysis
- Searching a platform for accounts or content matching a query (where the
  platform's ScrapeCreators endpoint supports search)
- Any research/profiling task where `agent-reach`, `scrapling`, or
  `social-footprint` don't cover the platform, or you specifically need
  ScrapeCreators' normalized JSON instead of raw HTML

Do NOT use this skill for:

- Free/keyless platform-presence checks — use `social-footprint` instead
- General web scraping of non-social-media sites — use `scrapling`
- Posting, commenting, or any write action — this is read-only by design;
  ScrapeCreators is a scraping API, not a posting API

## Platform + Endpoint Catalog

Endpoint paths follow ScrapeCreators' commonly-documented v1 shape. **These
are documented patterns, not independently verified against live API docs in
this environment — confirm each against your ScrapeCreators dashboard/docs
before relying on it.** Each path is its own constant in
`PLATFORM_ENDPOINTS` in `scripts/scrapecreators.py`, so a drifted path is a
one-line fix.

| Platform | Profile endpoint (documented pattern) | Posts endpoint | Returns |
|---|---|---|---|
| TikTok | `GET /v1/tiktok/profile?handle=` | `GET /v1/tiktok/posts?handle=` | bio, followers, avatar / recent videos, captions, engagement |
| Instagram | `GET /v1/instagram/profile?handle=` | `GET /v1/instagram/posts?handle=` | bio, followers, avatar / recent posts, captions, engagement |
| YouTube | `GET /v1/youtube/profile?handle=` | `GET /v1/youtube/posts?handle=` | channel info, subscriber count / recent videos, view counts |
| X/Twitter | `GET /v1/twitter/profile?handle=` | `GET /v1/twitter/posts?handle=` | bio, follower count / recent tweets, engagement |
| Reddit | `GET /v1/reddit/profile?handle=` | `GET /v1/reddit/posts?handle=` | user karma, account age / recent posts/comments |
| LinkedIn | `GET /v1/linkedin/profile?handle=` | `GET /v1/linkedin/posts?handle=` | headline, position, company / recent posts |
| Facebook | `GET /v1/facebook/profile?handle=` | `GET /v1/facebook/posts?handle=` | page/profile info / recent posts |
| Threads | `GET /v1/threads/profile?handle=` | `GET /v1/threads/posts?handle=` | bio, follower count / recent threads |

Search (`GET /v1/<platform>/search?query=`) follows the same pattern where
the platform's API supports it — verify support per platform before
depending on it in a script.

## Quickstart

```bash
export SCRAPECREATORS_API_KEY=your-key-here   # or set it in ~/.hermes/.env

python3 scripts/scrapecreators.py profile tiktok someuser
python3 scripts/scrapecreators.py posts instagram someuser --limit 10
python3 scripts/scrapecreators.py search youtube "some query"
```

With the key unset:

```bash
$ python3 scripts/scrapecreators.py profile tiktok someuser
[NEEDS-KEY] ScrapeCreators requires a paid API key. Set SCRAPECREATORS_API_KEY in ~/.hermes/.env — get one at https://scrapecreators.com
$ echo $?
2
```

## Model Wiring

| Task | Model | Endpoint | Why |
|------|-------|----------|-----|
| Deterministic field extraction from the JSON response (e.g. "pull follower_count/bio/handle as JSON") | **qwen3-coder** | llama-swap `http://localhost:1235/v1/chat/completions`, `"temperature": 0` | Temperature 0 for repeatable structured output |
| Profile/content summarization + audience analysis (e.g. "what's this account's niche and audience") | **ornith** | llama-swap `http://localhost:1235/v1/chat/completions`, `"chat_template_kwargs": {"enable_thinking": false}` | Reasoning model with thinking disabled for fast, terse synthesis |

```python
import json
import urllib.request

# qwen3-coder: deterministic field extraction, temperature 0
payload = {
    "model": "qwen3-coder",
    "messages": [
        {"role": "system", "content": "Extract structured data as JSON only. No prose, no markdown fences."},
        {"role": "user", "content": f"Extract handle, bio, follower_count, post_count as JSON.\n\n{response_json}"},
    ],
    "temperature": 0,
    "stream": False,
}
req = urllib.request.Request(
    "http://localhost:1235/v1/chat/completions",
    data=json.dumps(payload).encode(),
    headers={"Content-Type": "application/json"},
)
result = json.loads(urllib.request.urlopen(req, timeout=120).read())["choices"][0]["message"]["content"]
```

```python
# ornith: profile/content summarization and audience analysis, thinking disabled
payload = {
    "model": "ornith-uncensored",
    "messages": [{"role": "user", "content": f"Summarize this profile's niche, content style, and likely audience.\n\n{profile_and_posts_json}"}],
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
curl -s http://localhost:1235/v1/models | grep -o '"qwen3-coder"'
curl -s http://localhost:1235/v1/models | grep -o '"ornith-uncensored"'
```

## Pitfalls

- **Rate limits are plan-dependent**: ScrapeCreators' rate limit and monthly
  credit allotment depend on your subscription tier — check your dashboard
  before scripting a loop over many handles; a 429 means you've hit either
  the rate limit or your credit ceiling, not necessarily the same thing.
- **Key security**: `SCRAPECREATORS_API_KEY` is sent as the `x-api-key`
  header on every request. Never log, print, or commit it — `scrapecreators.py`
  never writes the key value to stdout/stderr, and no traceback path in it
  includes the key.
- **Cost per call**: this is a paid, metered API — every `profile`/`posts`/
  `search` call spends a credit even on a successful response. Don't run it
  in a retry loop without backoff, and don't call it speculatively.
- **Endpoint drift**: the endpoint paths in `PLATFORM_ENDPOINTS` are
  documented patterns, not independently verified in this environment.
  ScrapeCreators can add/rename endpoints; if a call 404s where you'd expect
  200, check your dashboard's current docs and fix the one-line constant
  rather than assuming the platform itself is unsupported.
- **`search` isn't guaranteed for every platform**: some platforms' APIs
  don't expose a search endpoint upstream even if ScrapeCreators documents
  one generically — a 404/501-style response on `search` for a given
  platform likely means "not supported," not "you did something wrong."
- **Handles vs. usernames**: some platforms (Instagram, TikTok) key profiles
  by handle/username directly; others (Facebook pages, LinkedIn) may expect
  a numeric ID or slug instead of a display handle — check the platform's
  ScrapeCreators docs if a `profile` call 404s on what looks like a valid
  handle.
