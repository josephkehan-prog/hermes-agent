---
name: dark-web-osint
description: Search, fetch, and analyze .onion sites for OSINT.
version: 1.0.0
platforms: [macos, linux]
metadata:
  hermes:
    tags: [tor, onion, dark-web, osint, threat-intel, investigation, sicry, hidden-service]
    requires_toolsets: [terminal]
    related_skills: [tor-fetch, dark-web-monitor]
---

# Dark Web OSINT

Search the Tor dark web, fetch `.onion` pages, and produce structured OSINT
reports. Backed by the **sicry** MCP server (OnionClaw) behind agent-hub — call
its tools through the hub, no local setup per call.

**Authorized security research / threat-intel only.** Do not use to target
private individuals or facilitate wrongdoing.

## Prerequisites

- Tor daemon on SOCKS `127.0.0.1:9050` (persistent brew service
  `homebrew.mxcl.tor`; `hermes-tor status` to check, `brew services start tor`
  if down).
- `sicry` registered + trusted in agent-hub (`gatewayOnly`). Reach it via the
  agent-hub `tool_call` tool — a fresh session if the hub was connected before
  sicry was added.

Every step is an agent-hub `tool_call` with `server: "sicry"`. Always verify Tor
first:

```
tool_call server="sicry" tool="sicry_check_tor" arguments={}
# -> {tor_active: true, exit_ip: "...", error: null}
```

## Workflow

### 1. Search the dark web

```
tool_call server="sicry" tool="sicry_search" arguments={
  "query": "SEARCH TERM",
  "max_results": 20,        # optional
  "mode": "threat_intel"    # optional focus
}
```

Returns ranked results (title, url, engine, confidence). Searches up to 12
`.onion` engines at once. Keep the returned `results` array — `sicry_ask`,
`sicry_to_stix`, and `sicry_to_csv` (see [[dark-web-monitor]]) consume it.

### 2. Fetch a specific page over Tor

```
tool_call server="sicry" tool="sicry_fetch" arguments={ "url": "http://SOME.onion/path" }
```

Works for `.onion` and clearnet-via-Tor. Returns title, status, links, body
text. (For a one-off fetch with no OSINT layer, [[tor-fetch]] is lighter.)

### 3. Analyze fetched content

LLM report — routes to the local **RESEARCH specialist** role, no cloud:

```
tool_call server="sicry" tool="sicry_ask" arguments={
  "content": "RAW PAGE TEXT",
  "query": "What is this and who runs it?",
  "mode": "threat_intel"     # threat_intel | ransomware | personal_identity | corporate
}
```

No-LLM pass (fast, deterministic — keywords + entities + regex, free):

```
tool_call server="sicry" tool="sicry_analyze_nollm" arguments={ "content": "TEXT", "query": "FOCUS" }
tool_call server="sicry" tool="sicry_extract_keywords" arguments={ "text": "TEXT", "top_n": 15 }
```

### 4. Crawl a site (map structure, follow links)

```
tool_call server="sicry" tool="sicry_crawl" arguments={
  "seed_url": "http://SOME.onion/",
  "max_depth": 2,
  "max_pages": 25
}
# then, with the returned job id:
tool_call server="sicry" tool="sicry_crawl_export" arguments={ "job_id": "JOB_ID" }
```

Keep `max_depth`/`max_pages` small — Tor is slow and many engines/sites time
out. Bump only when a shallow crawl is clearly incomplete.

## Operational notes

- **Rotate identity** between sensitive targets to avoid correlation:
  `tool_call server="sicry" tool="sicry_renew_identity" arguments={}`.
- **Dead engines / timeouts** are normal on Tor. Check engine health:
  `tool_call server="sicry" tool="sicry_check_engines" arguments={"cached": true}`.
- **Stop chasing generic results.** After 3-4 rounds of the same directory
  pages, pivot to clearnet OSINT ([[maigret]], [[sherlock]], person lookups)
  instead of re-searching the same term.
- Analysis stays **fully local** (RESEARCH role, local inference) — content
  never leaves the machine to a cloud LLM.
- For persistent monitoring / alerts / STIX export, see [[dark-web-monitor]].
