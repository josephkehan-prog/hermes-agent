---
name: platform-scrape-research
description: Lightweight research pipeline for scraping a single platform (Substack, GitHub, Twitter/X, blog) on a specific topic. Uses web_search with site operator plus web_extract to compile a markdown report. No MCPs required.
version: 1.0.0
---

# Platform Scrape Research

Lightweight research when the user wants content from ONE platform on ONE or TWO topics. Heavier than a quick search, lighter than deep-research. Fills the gap between web_search and multi-source synthesis.

## When to Activate

- "Scrape Substack for X" / "Find posts about Y on [platform]"
- Platform is named explicitly (Substack, Medium, HackerNoon, GitHub repos, Reddit subs)
- Single-topic or paired topics, not a broad cross-domain investigation
- User wants synthesized findings, not just links

When the task requires 3+ platforms or cross-source synthesis, escalate to deep-research with MCPs.

## Workflow

### 1. Search Phase (parallel queries)

Run multiple web_search calls with site operator in parallel -- never one at a time. Vary keyword angles:

```
site:<platform> "topic" primary_kws
site:<platform> "topic" alternative_kws
site:<platform> topic synonyms long_tail
```

3-5 queries, limit per query 5, ALL batched in ONE function-call turn.

### 2. Extract Phase (parallel reads)

Pick 3-8 most relevant URLs from search results. Run web_extract with char_limit=12000 on ALL of them in a SINGLE parallel call. Do not read them sequentially.

If any extract is truncated, page through with read_file on the cached path (footer tells you where).

### 3. Compile

Write a structured markdown report to a file under the Hermes output directory. Format:

```markdown
# Report Title

## Theme 1 -- source_count sources
### Source Name -- Author/Handle -- URL
- Key finding 1
- Key finding 2

## Theme 2 ...

## Summary / TL;DR
- Actionable insight 1
- Actionable insight 2
```

Include: date scraped, number of sources, platform name.

### 4. Deliver

Save file, share path with user inline. No need to print the whole report in chat unless it is under ~30 lines.

## Pitfalls

- Never read extracts sequentially. Batch them all. A round-trip for each URL adds minutes of wait time.
- Truncated pages contain a footer with the cache path and read_file command to continue reading. Follow it if the middle content matters.
- Substack free vs paid posts: Some articles are paywalled -- search results may show snippets only. Note which sources were partial.
- Do not confuse site scope. site:substack.com catches Substack; site:reddit.com/r/llama catches a specific subreddit. Adjust the site value precisely.

## Delivery Options

User may want the report sent somewhere after compilation:

- Signal: Signal Desktop often not installed on Macs. No CLI/MCP sender exists in the gateway. If user asks to send to Signal, save file and tell them to copy-paste.
- iMessage: Use imsg CLI with skill apple/imessage. Get phone number from user if not known.
- Email: Use himalaya or google-workspace skills.
- Leave as file: Default -- save to Hermes output directory, report path in chat.