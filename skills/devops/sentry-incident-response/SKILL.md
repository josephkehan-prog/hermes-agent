---
name: sentry-incident-response
description: Diagnose and recover from a runtime incident.
version: 1.0.0
author: Hermes War Room
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    bundle: true
    domain: incident-response
    tags: [bundle, incident, reliability, recovery, monitoring]
    related_skills: [log-triage, infra-monitor, stacktrace-triage, self-healing, watch-notify, dependency-audit]
---

# Sentry Incident Response

## Boundary

Own one incident packet: impact, timeline, observed signal, cause confidence,
reversible recovery, verification, and recurrence guard. Do not restart first,
erase evidence, rotate credentials, or mutate production without authorization.

## Routing Table

| Signal | Skill | Mode |
|---|---|---|
| Logs and event timeline | `log-triage` | Deterministic filtering |
| Host or service health | `infra-monitor` | Deterministic probes |
| Exception or crash evidence | `stacktrace-triage` | Bounded diagnosis |
| Reversible automated repair | `self-healing` | Deterministic with retry budget |
| Stateful recurrence watch | `watch-notify` | Deterministic transitions |
| Dependency-caused failure | `dependency-audit` | Deterministic inventory, bounded prioritization |

## Orchestration Workflow

1. Capture impact, start time, environment, last known good state, and detection signal.
2. Build a timeline before mutation; separate symptom, contributor, and confirmed cause.
3. Choose the smallest reversible repair with a health check and rollback.
4. Verify recovery using the same signal that detected the failure.
5. Add monitoring only with threshold, recovery condition, deduplication, and retry budget.

## Handoff Record

Record incident timestamp, impact, evidence paths, hypotheses, cause confidence,
mutations, before/after health, rollback command, and monitoring state.

## Stop Conditions

- No reliable health check exists.
- Recovery risks data loss, credential changes, or unauthorized service control.
- Evidence suggests an active security incident requiring Sentinel.
- The repair overlaps user-owned configuration or repository changes.

## Completion Gate

- [ ] Impact and cause are distinguished
- [ ] Recovery is verified with the original detection signal
- [ ] Every mutation has a rollback
- [ ] Retry and monitoring behavior are bounded
- [ ] Remaining uncertainty and owner are explicit
