---
title: "Rest Graphql Debug — Debug REST/GraphQL APIs: status codes, auth, schemas, repro"
sidebar_label: "Rest Graphql Debug"
description: "Debug REST/GraphQL APIs: status codes, auth, schemas, repro"
---

{/* This page is auto-generated from the skill's SKILL.md by website/scripts/generate-skill-docs.py. Edit the source SKILL.md, not this page. */}

# Rest Graphql Debug

Debug REST/GraphQL APIs: status codes, auth, schemas, repro.

## Skill metadata

| | |
|---|---|
| Source | Optional — install with `hermes skills install official/software-development/rest-graphql-debug` |
| Path | `optional-skills/software-development/rest-graphql-debug` |
| Version | `1.2.0` |
| Author | eren-karakus0 |
| License | MIT |
| Tags | `api`, `rest`, `graphql`, `http`, `debugging`, `testing`, `curl`, `integration` |
| Related skills | [`systematic-debugging`](/docs/user-guide/skills/bundled/software-development/software-development-systematic-debugging), [`test-driven-development`](/docs/user-guide/skills/bundled/software-development/software-development-test-driven-development) |

## Reference: full SKILL.md

:::info
The following is the complete skill definition that Hermes loads when this skill is triggered. This is what the agent sees as instructions when the skill is active.
:::

# API Testing & Debugging

Drive REST and GraphQL diagnosis through Hermes tools — `terminal` for `curl`, `execute_code` for Python `requests`, `web_extract` for vendor docs. Isolate the failing layer before guessing at the fix.

## When to Use

- API returns unexpected status or body
- Auth fails (401/403 after token refresh, OAuth, API key)
- Works in Postman but fails in code
- Webhook / callback integration debugging
- Building or reviewing API integration tests
- Rate limiting or pagination issues

Skip for UI rendering, DB query tuning, or DNS/firewall infra (escalate).

## Core Principle

**Isolate the layer, then fix.** A 200 OK can hide broken data. A 500 can mask a one-character auth typo. Walk the chain in order; never skip a step.

```
1. Connectivity   → can we reach the host at all?
1.5 Timeouts      → connect-slow vs read-slow?
2. TLS/SSL        → cert valid and trusted?
3. Auth           → credentials correct and unexpired?
4. Request format → payload shape match server expectations?
5. Response parse → does our code accept what came back?
6. Semantics      → does the data mean what we assume?
```

## 5-Minute Quickstart

### REST via terminal

```python
# Verbose request/response exchange
terminal('curl -v https://api.example.com/users/1')

# POST with JSON
terminal("""curl -X POST https://api.example.com/users \\
  -H 'Content-Type: application/json' \\
  -H "Authorization: Bearer $TOKEN" \\
  -d '{"name":"test","email":"test@example.com"}'""")

# Headers only
terminal('curl -sI https://api.example.com/health')

# Pretty-print JSON
terminal('curl -s https://api.example.com/users | python3 -m json.tool')
```

### GraphQL via terminal

```python
terminal("""curl -X POST https://api.example.com/graphql \\
  -H 'Content-Type: application/json' \\
  -H "Authorization: Bearer $TOKEN" \\
  -d '{"query":"{ user(id: 1) { name email } }"}'""")
```

**GraphQL gotcha:** servers often return HTTP 200 even when the query failed. Always inspect the `errors` field regardless of status code:

```python
execute_code('''
import os, requests
resp = requests.post(
    "https://api.example.com/graphql",
    json={"query": "{ user(id: 1) { name email } }"},
    headers={"Authorization": f"Bearer {os.environ['TOKEN']}"},
    timeout=10,
)
data = resp.json()
if data.get("errors"):
    for err in data["errors"]:
        print(f"GraphQL error: {err['message']} (path: {err.get('path')})")
print(data.get("data"))
''')
```

### Python (requests) via execute_code

```python
execute_code('''
import requests
resp = requests.get(
    "https://api.example.com/users/1",
    headers={"Authorization": "Bearer <TOKEN>"},
    timeout=(3.05, 30),  # (connect, read)
)
print(resp.status_code, dict(resp.headers))
print(resp.text[:500])
''')
```

## Layered Debug Flow

Walk these six layers in order — never skip one. Commands, checklists, and diagnosis criteria for each step: read `references/layered-debug.md`.

1. Connectivity — can we reach the host at all?
2. Timeouts — connect-slow vs read-slow?
3. TLS/SSL — cert valid and trusted?
4. Auth — credentials correct and unexpired?
5. Request format — payload shape match server expectations?
6. Response parse / semantics — does our code accept and correctly interpret what came back?

## HTTP Status Playbook

Per-status-code checklists (401, 403, 404, 409, 422, 429, 5xx) with diagnosis steps and a backoff snippet: read `references/status-codes.md` when triaging a specific status code.

## Pagination & Idempotency

**Pagination.** Verify you're getting *all* results. Look for `next_cursor`, `next_page`, `total_count`. Two patterns:
- Offset (`?limit=100&offset=200`) — simple, can skip items if data shifts.
- Cursor (`?cursor=abc123`) — preferred for live or large datasets.

**Idempotency.** For non-idempotent operations (POST), send `Idempotency-Key: <uuid>` so retries don't double-charge / double-create. Mandatory for payments and orders.

## Contract Validation, Correlation IDs & Regression Tests

Schema-drift validators, vendor request-ID capture + bug-report template, and a drop-in pytest smoke-test suite: read `references/examples.md` when hardening an integration or filing a vendor bug report.

## Security

Token handling, safe-logging redaction helper, and a leak checklist (credentials in URLs, PII in errors, stack traces, internal hostnames, echoed tokens, verbose headers): read `references/security.md` before shipping any API integration code.

## Hermes Tool Patterns

`terminal` for curl/dig/openssl one-liners; `execute_code` for multi-step auth→fetch→paginate→validate flows; `web_extract` for vendor docs; `delegate_task` for full CRUD test sweeps. Full snippets and an example findings write-up: read `references/examples.md`.

## Related

- `systematic-debugging` — once the failing API layer is isolated, root-cause your code
- `test-driven-development` — write the regression test before shipping the fix
