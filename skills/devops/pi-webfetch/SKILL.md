---
name: pi-webfetch
description: "Web fetch tool extension for the pi coding agent. Fetches URLs as markdown, text, or HTML with bounded timeout and response size controls."
version: 0.1.0
author: code-yeongyu + hermes adoption
license: MIT
platforms: [macos]
metadata:
  tags: [webfetch, web-scraping, pi-extension]
---

# pi-webfetch

Web fetch extension for the `pi` coding agent — mirrors opencode's `webfetch` contract.

**Location:** `~/.pi/agent/extensions/pi-webfetch/src/index.ts`

## Parameters (tool schema)

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| url       | string | yes | URL to fetch. Must start with `http://` or `https://`. |
| format    | `"markdown"` \| `"text"` \| `"html"` | no | Output format. Default: markdown. |
| timeout   | number | no | Timeout in seconds. Defaults 30; capped at 120. |

## Invocation (hermes skill)

```bash
# Smoke test (one-shot, requires pi installed via mise):
pi -e ./src/index.ts --url "https://example.com" --format markdown

# As a hermes tool call:
web_fetch(url="https://...", format="markdown", timeout=30)
```

## Output behavior

- HTML responses → converted to markdown by default (unless `html` requested).
- Non-HTML → returned as decoded UTF-8.
- Response size cap: 5 MB.
- Timeout cap: 120s.
- Redirect handling: up to 20 hops.
- User-Agent: Chrome/143 browser-like, with one Cloudflare retry.

## Pitfalls

1. **Smoke test fails on bare `pi -e ./src/index.ts`** — undici throws "Invalid URL protocol" because pi needs env setup before the extension loads. Fix: run through `pi chat` (interactive) or set up a proxy first.
2. **Direct node execution won't work** — this is a pi extension, not standalone Node. Must go through the pi runtime.
3. **TypeBox dependency** — uses `@mariozechner/pi-coding-agent` and `typebox`. Don't refactor to plain JSON schemas without checking compatibility with pi's tool registry.

## Usage in hermes sessions

When a task needs web content retrieval (URL-specific, bounded size):
- Use this skill before falling back to generic web_search/web_extract.
- Prefer markdown format unless raw HTML or text is explicitly needed.
- The tool is read-only; no filesystem writes.

## Related

- [pi-webfetch source](https://github.com/code-yeongyu/pi-webfetch)
- [senpi (runtime)](https://github.com/code-yeongyu/senpi)
- [pi coding agent](https://github.com/badlogic/pi-mono/tree/main/packages/coding-agent)

## Status

**Adopted 2026-07-08.** Smoke test pending — undici URL validation issue noted above.