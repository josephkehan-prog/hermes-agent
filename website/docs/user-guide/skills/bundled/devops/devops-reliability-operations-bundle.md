---
title: "Reliability Operations Bundle"
sidebar_label: "Reliability Operations Bundle"
description: "Use when diagnosing, repairing, and preventing service or automation failures across logs, infrastructure checks, dependency health, monitoring, and self-hea..."
---

{/* This page is auto-generated from the skill's SKILL.md by website/scripts/generate-skill-docs.py. Edit the source SKILL.md, not this page. */}

# Reliability Operations Bundle

Use when diagnosing, repairing, and preventing service or automation failures across logs, infrastructure checks, dependency health, monitoring, and self-healing. Coordinates a conservative reliability response from signal to verified recovery.

## Skill metadata

| | |
|---|---|
| Source | Bundled (installed by default) |
| Path | `skills/devops/reliability-operations-bundle` |
| Version | `1.0.0` |
| Author | Hermes Agent |
| License | MIT |
| Platforms | linux, macos, windows |
| Tags | `bundle`, `reliability`, `devops`, `monitoring`, `recovery` |
| Related skills | [`log-triage`](/docs/user-guide/skills/bundled/devops/devops-log-triage), [`self-healing`](/docs/user-guide/skills/bundled/devops/devops-self-healing), [`infra-monitor`](/docs/user-guide/skills/bundled/research/research-infra-monitor), [`watch-notify`](/docs/user-guide/skills/bundled/research/research-watch-notify), [`dependency-audit`](/docs/user-guide/skills/bundled/devops/devops-dependency-audit), [`git-hygiene`](/docs/user-guide/skills/bundled/devops/devops-git-hygiene) |

## Reference: full SKILL.md

:::info
The following is the complete skill definition that Hermes loads when this skill is triggered. This is what the agent sees as instructions when the skill is active.
:::

# Reliability Operations Bundle

## Boundary

Handle reliability work spanning detection, diagnosis, recovery, and
prevention. Prefer the focused member skill for a one-off log query,
dependency report, or git cleanup.

## Routing Table

| Signal | Primary skill | Exit evidence |
|---|---|---|
| Error logs or noisy incidents | `log-triage` | Correlated timeline and likely failure class |
| Service health or host drift | `infra-monitor` | Current health snapshot with thresholds |
| Safe automated remediation | `self-healing` | Bounded repair and post-repair verification |
| Recurring or external signal | `watch-notify` | Stateful watch with deduplicated notification |
| Vulnerable or stale dependencies | `dependency-audit` | Prioritized dependency findings |
| Repository state impedes recovery | `git-hygiene` | Clean, preserved, explainable worktree state |

## Orchestration Workflow

1. Capture the symptom, impact, start time, environment, and last known good
   state before mutating anything.
2. Use `log-triage` and `infra-monitor` to separate signal from consequence.
3. Apply `self-healing` only when the repair is reversible, scoped, and guarded
   by a health check. Otherwise propose a manual repair.
4. Route dependency-caused failures to `dependency-audit`; preserve worktree
   ownership with `git-hygiene` before patching.
5. Add `watch-notify` only for a recurring condition with a defined threshold,
   recovery condition, and deduplication state.

## Handoff Record

Maintain incident ID or timestamp, observed symptoms, evidence sources,
hypotheses, mutations, before/after health, rollback command, and monitoring
state. Separate confirmed cause from plausible contributor.

## Stop Conditions

- Recovery would delete data, rotate credentials, or restart production
  without authorization.
- No reliable health check exists to judge the repair.
- Evidence points to an active security incident requiring containment.
- User-owned worktree or configuration changes overlap the proposed repair.

## Completion Gate

- [ ] Impact and root cause are distinguished
- [ ] Recovery is verified with the same signal that detected failure
- [ ] Rollback is available for every state-changing repair
- [ ] Dependency or repository changes have focused validation
- [ ] Recurrence monitoring has threshold, recovery, and deduplication rules
- [ ] Remaining uncertainty and follow-up ownership are explicit

## Common Pitfalls

- Restarting first and destroying diagnostic evidence
- Calling correlation a root cause
- Adding an infinite repair loop without a retry budget
- Alerting on every poll instead of state transitions
