---
name: watch-notify
description: Watch a URL for changes and push an alert.
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [Monitoring, Alerting, Change-Detection, Watch, Automation]
    category: research
    related_skills: [blogwatcher, deal-hunting, network-recon]
prerequisites:
  commands: [python3]
---

# Watch & Notify

A general-purpose change-detector: fetch a source, compare it against the
last-known state, and alert when it changed. Works on anything reachable
over plain HTTP(S) — no external CLI, no API keys, no paid service.

This is deliberately generic. `blogwatcher` already owns RSS/Atom-specific
polling (feed discovery, read/unread state, OPML) — reach for that when the
source *is* a blog feed. `network-recon` already owns DNS/Certificate
Transparency lookups — reach for that to pull the DNS record set or crt.sh
subdomain list you want to watch. `watch-notify` is the piece none of those
have: a stdlib diff-and-alert loop you can point at *any* URL (a page, a
JSON API, a DNS/cert snapshot produced by `network-recon`, an RSS item list
produced by `blogwatcher`) and get "changed / unchanged" plus a push
notification, without hand-rolling state persistence each time.

## When to Use

- "Tell me when this page changes" (docs page, pricing page, status page,
  changelog with no feed)
- "Tell me when this API field changes" (a JSON status/version/price field)
- "Alert me if this DNS record or TLS cert changes" — pair with
  `network-recon`'s `dns`/`fingerprint`/`subdomains` output: pipe its JSON
  through `watch.py`'s content-hash check the same way you would a page
- "New items in this RSS feed" — pair with `blogwatcher scan`; `watch-notify`
  adds a push-notification step blogwatcher doesn't have on its own
- Not for: high-frequency (sub-minute) polling, or sources that require
  authentication/session cookies (no auth support here — use a
  purpose-built integration instead)

## Sources

| Source type | How to watch it | Tool |
|---|---|---|
| URL content hash | Fetch, SHA-256 the body, compare to stored hash | `watch.py check <url> --state FILE` |
| JSON field value | Fetch JSON, extract a dotted-path field, compare to stored value | `watch.py watch-json <url> --field a.b.c --state FILE` |
| RSS/Atom new items | Feed polling, dedup, read/unread state | `blogwatcher-cli scan` (external CLI, see [blogwatcher](../blogwatcher/SKILL.md)) — feed its "new" article list into `watch.py notify` for push alerts |
| DNS record change | Resolve record set, hash/compare the sorted result | `network-recon recon.py dns <domain>` output piped through your own hash-and-store loop, or save its JSON and `watch.py check` a `file://`-style local snapshot workflow (see Workflow) |
| Cert/subdomain change | crt.sh subdomain list, hashed and compared per run | `network-recon recon.py subdomains <domain>` output, same pattern as DNS above |

`watch.py` only implements the first two rows directly (content hash, JSON
field) because those are the two truly generic, keyless, no-CLI-dependency
cases. The DNS/cert/RSS rows lean on the sibling skills for *fetching* and
use `watch.py`'s state-diff-notify plumbing as the generic glue — don't
duplicate DNS/CT/RSS logic here.

## Workflow

1. **Baseline**: first run of `check` or `watch-json` against a fresh
   `--state FILE` has nothing to compare to — it records the current
   hash/value and reports `new` (not `changed`, not `unchanged`).
2. **Poll**: re-run the same command on a schedule (via the `cron`/`schedule`
   skill — this script does not loop or sleep internally, it's a single
   check per invocation, by design, so the caller controls cadence).
3. **Diff**: each run compares the freshly-fetched hash/value against what's
   stored in `--state FILE` and reports one of `new` / `changed` /
   `unchanged`, updating the state file only when the value actually moved.
4. **Notify**: on `changed`, pipe a summary into `watch.py notify "<message>"
   --topic <topic>` to push a keyless alert, or just log/print — see
   [Notification backends](#notification-backends).

For noisy sources (a page whose body includes a timestamp or ad slot that
changes every load), don't watch the raw page — extract the meaningful
substring/field first (JSON field via `watch-json`, or pre-filter the HTML
yourself before hashing) so the hash only reflects content that matters.

## Notification backends

All three are free and keyless:

| Backend | How | Good for |
|---|---|---|
| **ntfy.sh push** | `watch.py notify "<message>" --topic <topic>` — POSTs to `https://ntfy.sh/<topic>`. Subscribe to the same topic in the ntfy mobile/desktop app or via `curl -s https://ntfy.sh/<topic>/json` to receive it. | Real push notification to a phone/desktop, no account needed |
| **Local file/log** | Redirect `check`/`watch-json` output (`>> watch.log`) or write your own line when `changed` is reported | Silent audit trail, cron job output |
| **stdout** | Default — `check`/`watch-json` always print a JSON result to stdout regardless of notify backend | Piping into another tool, or manual runs |

ntfy.sh is a shared public relay: anyone who knows (or guesses) your topic
name can subscribe and read your notifications, or publish to it themselves.
Treat the topic name like a weak secret — use a long, random, unguessable
string (e.g. `watch-<uuid4>`), not `my-watch` or a project name.

## Model Wiring

For workflows watching many sources at once (a watchlist, not a single URL),
pipe raw diff output into a local model instead of hand-reading every
change. Same two-endpoint split used by `deal-hunting` and `open-databases`:

| Task | Model | Endpoint | Why |
|---|---|---|---|
| Deterministic diff summarization / dedup (e.g. "collapse this batch of `changed` results into one JSON list, one line per source") | **agent1** (`hf.co/InternScience/Agents-A1-Q4_K_M-GGUF:latest`) | Ollama, `http://localhost:11434/api/chat` | Temperature 0 for repeatable structured output |
| "Is this change important?" triage (e.g. "which of these page changes are substantive vs. cosmetic/noise") | **ornith** (`ornith-uncensored`) | llama-swap, `http://localhost:1235/v1/chat/completions` | Reasoning model; disable thinking with `chat_template_kwargs: {"enable_thinking": false}` for fast, terse output |

```python
import json
import urllib.request

# agent1: dedupe/summarize a batch of watch results, temperature 0
payload = {
    "model": "hf.co/InternScience/Agents-A1-Q4_K_M-GGUF:latest",
    "messages": [
        {"role": "system", "content": "Summarize which watched sources changed as JSON only. No prose, no markdown fences."},
        {"role": "user", "content": f"Summarize:\n\n{results_json}"},
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
# ornith: triage which changes are worth a human's attention, thinking disabled
payload = {
    "model": "ornith-uncensored",
    "messages": [{"role": "user", "content": f"Which of these changes are substantive vs. noise? Explain briefly.\n\n{results_json}"}],
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

- **Poll interval etiquette**: this script does one check per invocation and
  never loops or sleeps — the calling schedule sets the cadence. Don't poll
  a single source faster than once a minute, and prefer once every 5-15
  minutes for anything you're not actively debugging; hammering a site on a
  tight cron loop is the kind of thing that gets an IP rate-limited or
  blocked. Respect `robots.txt` and any documented rate limit for the target.
- **Flapping**: a source whose content includes a rotating ad, a "generated
  at HH:MM:SS" timestamp, a CSRF token, or a per-request nonce will hash-diff
  as `changed` on every single poll. Extract just the field you care about
  (`watch-json --field ...`) instead of hashing the whole body whenever the
  source has that kind of noise.
- **ntfy topic privacy**: ntfy.sh topics are public by default — no auth, no
  ACL, unless you self-host or use ntfy's paid tiers. Never put secrets in
  the notification message, and pick an unguessable topic name (see
  [Notification backends](#notification-backends)).
- **State file is local, not shared**: `--state FILE` is a plain JSON file on
  disk. Two concurrent runs against the same state file can race; don't
  schedule overlapping polls of the same source/state pair.
- **No auth support**: sources behind a login wall or requiring cookies/API
  keys aren't in scope — this is a keyless tool for public sources only.
