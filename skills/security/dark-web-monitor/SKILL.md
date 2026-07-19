---
name: dark-web-monitor
description: Watch the dark web and export threat-intel feeds.
version: 1.0.0
platforms: [macos, linux]
metadata:
  hermes:
    tags: [tor, onion, dark-web, monitoring, threat-intel, stix, misp, watch, sicry]
    requires_toolsets: [terminal]
    related_skills: [dark-web-osint, tor-fetch]
---

# Dark Web Monitor

Persistent dark-web monitoring and threat-intel export. Register watch jobs that
re-run a query on a schedule and alert on new/changed results, then export hits
to STIX 2.1 or CSV for OpenCTI / MISP / Maltego. Backed by the **sicry** MCP
server (OnionClaw) behind agent-hub.

**Authorized security research / threat-intel only.**

## Prerequisites

Same as [[dark-web-osint]]: Tor on SOCKS `127.0.0.1:9050` (persistent brew
service), `sicry` trusted in agent-hub. Verify Tor before a run:

```
tool_call server="sicry" tool="sicry_check_tor" arguments={}
```

## Watch jobs

Register a recurring watch — re-runs every `interval_hours`, alerts on deltas:

```
tool_call server="sicry" tool="sicry_watch_add" arguments={
  "query": "BRAND OR LEAK KEYWORD",
  "mode": "threat_intel",
  "interval_hours": 12
}
```

List active watches:

```
tool_call server="sicry" tool="sicry_watch_list" arguments={}
```

Check all due watches now (returns alerts with new/changed results):

```
tool_call server="sicry" tool="sicry_watch_check" arguments={}
```

Scheduling: `sicry_watch_check` is pull-based — it only runs when called. Drive
it from a Hermes cron / heartbeat (e.g. every few hours) and surface any alerts.
The watch store persists in the sicry install's SQLite cache.

## Export threat intel

Run a search first (see [[dark-web-osint]] `sicry_search`), keep its `results`
array, then export:

```
# STIX 2.1 bundle (OpenCTI / MISP / Maltego import)
tool_call server="sicry" tool="sicry_to_stix" arguments={
  "results": [ ...search results... ],
  "query": "ORIGINAL QUERY",
  "report_text": "optional analyst summary"
}

# CSV (title, url, engine, confidence, timestamp)
tool_call server="sicry" tool="sicry_to_csv" arguments={ "results": [ ... ] }
```

Save STIX/CSV output to a file for downstream tooling; STIX is a JSON bundle,
CSV is a plain string.

## Notes

- Keep intervals modest — Tor searches are slow and many `.onion` engines are
  flaky. 6-24h is reasonable for most monitors.
- One watch per distinct query/brand; don't overload a single job.
- Investigation + ad-hoc fetch/analyze live in [[dark-web-osint]]; this skill is
  the standing-monitor + export half.
- Rotate identity between unrelated monitors if correlation matters:
  `tool_call server="sicry" tool="sicry_renew_identity" arguments={}`.
