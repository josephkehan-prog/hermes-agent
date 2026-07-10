---
name: browser-first
description: For ANY web task (open a URL, read a page, search, dork, fetch a profile, click, fill a form), use the browser toolset — NOT computer_use. computer_use (screen/mouse control of the whole Mac) is a last resort for native desktop apps only. If the browser tool errors with no CDP endpoint, start one with bin/hermes-browser and connect. Local, no cloud, no API key.
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [macos]
metadata:
  hermes:
    tags: [browser, computer-use, cdp, chrome, web, routing, do-not-screen-control]
    category: computer-use
    requires_toolsets: [browser, terminal]
    related_skills: [osint-investigation, local-model-ops]
---

# Browser First — Never Screen-Control the Web

Hermes has two ways to touch a screen. Pick the right one:

- **`browser` toolset** (`browser_navigate`, `browser_snapshot`, `browser_vision`,
  `browser_click`, `browser_type`, `browser_cdp`) — drives a real Chrome over CDP.
  **This is the default for everything on the web.** Precise, scriptable, no mouse.
- **`computer_use`** — controls the whole Mac desktop by mouse/keyboard screenshots.
  Slow, imprecise, disruptive (moves the user's real cursor). **Only** for native
  desktop apps that have no web equivalent, and only when the user explicitly asks.

## Rule

For any request to open/read/search/click/fill/scrape a web page, URL, or profile:
use the `browser` toolset. Do **not** reach for `computer_use`. If you are tempted
to "take a screenshot and click," stop — that is the wrong tool for the web.

## If the browser tool fails with "no CDP endpoint" / "not connected"

The browser tool needs a Chrome DevTools endpoint. Bring one up, then connect:

```bash
bin/hermes-browser            # launches loopback Chrome w/ CDP on :9222 (idempotent)
bin/hermes-browser --status   # verify it's live
```

Then in Hermes: `/browser connect ws://127.0.0.1:9222`

Now `browser_navigate` etc. work. `bin/hermes-browser --stop` quits that instance.

Persistent fix (survives restarts) — set once in `~/.hermes/config.yaml`:

```yaml
browser:
  cloud_provider: local
  cdp_url: http://127.0.0.1:9222
```

(Config edits are the user's call — see `USER_ACTIONS.md`.)

## When computer_use IS correct

- A native macOS app (Preview, Finder, a menu-bar tool) with no web UI.
- The user explicitly says "control my screen" / "click on my desktop."
- Otherwise: browser toolset. Every time.

## Quick triage

| Symptom | Do this |
|---|---|
| "browser not connected" / CDP error | `bin/hermes-browser` then `/browser connect ws://127.0.0.1:9222` |
| about to use computer_use for a website | switch to `browser_navigate` |
| Chrome window won't attach ("already running") | dedicated debug profile in `chrome-debug/` avoids this — the launcher uses it |
| need raw DevTools control | `browser_cdp` (after connect), not screen clicks |
