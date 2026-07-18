---
name: vanguard-engineering-ops
description: Own multi-step engineering and local-model ops.
version: 1.0.0
author: Hermes War Room
license: MIT
platforms: [macos]
metadata:
  hermes:
    bundle: true
    domain: vanguard-engineering-ops
    tags: [bundle, vanguard, engineering, operations, local-models]
    related_skills: [repo-location-discovery, codebase-inspection, systematic-debugging, test-driven-development, local-model-ops, log-triage]
---

# Vanguard Engineering Ops

## Boundary

Own implementation, debugging, and local-runtime changes that require tools and
verification. Route research-only work to Mythos, visual evidence to Hawkeye,
asset generation to Canvas, and prose to Quill.

## Routing Table

| Work | Skill | Inference mode |
|---|---|---|
| Find the authoritative repository or config owner | `repo-location-discovery` | Deterministic; no speculative planning |
| Inspect an unfamiliar codebase | `codebase-inspection` | Deterministic inventory before interpretation |
| Implement a scoped software change | `test-driven-development` | Bounded thinking only for design ambiguity |
| Diagnose a reproducible failure | `systematic-debugging` | Bounded thinking; verify every hypothesis |
| Triage logs or a failed service | `log-triage` | Deterministic filters and health probes |
| Select, serve, or evaluate a local model | `local-model-ops` | Bounded comparison, deterministic benchmark |

## Orchestration Workflow

1. Locate ownership and capture the current state before mutation.
2. Use deterministic execution for exact edits, commands, schemas, and tests.
3. Use the controller's bounded reasoning only when requirements, architecture,
   or root cause are genuinely ambiguous.
4. Make the smallest reversible change and run the narrowest proof first.
5. Record changed paths, checks, resource impact, rollback, and remaining risk.

## Handoff Record

Record outcome, owner path, assumptions, inference mode, files changed,
commands, test results, runtime probes, rollback, and unresolved risk.

## Stop Conditions

- The next action is destructive, publishes externally, or restarts a shared service without authority.
- Repository or configuration ownership is ambiguous.
- A model swap or new download is proposed but not approved.
- The failure cannot be reproduced and no stronger evidence is available.

## Completion Gate

- [ ] Ownership and baseline were verified
- [ ] Reasoning was reserved for ambiguity, not mechanical execution
- [ ] The smallest relevant tests and runtime probes pass
- [ ] Resource impact and rollback are documented
- [ ] Any model replacement is flagged for separate approval
