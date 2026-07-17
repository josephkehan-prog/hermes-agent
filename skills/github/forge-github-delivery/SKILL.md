---
name: forge-github-delivery
description: "Use when Forge must carry one scoped GitHub change from issue and repository orientation through branch, review, CI, and a merge-ready handoff without silently publishing or merging."
version: 1.0.0
author: Hermes War Room
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    bundle: true
    domain: github-delivery
    tags: [bundle, github, delivery, review, ci]
    related_skills: [github-auth, codebase-inspection, github-issues, github-pr-workflow, github-code-review, github-repo-management, git-hygiene, changelog]
---

# Forge GitHub Delivery

## Boundary

Own one GitHub delivery packet: linked scope, preserved worktree, reviewed diff,
validation evidence, CI state, and merge-ready handoff. Do not merge, publish,
close, or change repository settings without explicit authorization.

## Routing Table

| Need | Skill | Mode |
|---|---|---|
| Confirm identity and access | `github-auth` | Deterministic |
| Locate the change surface | `codebase-inspection` | Deterministic inventory |
| Align or update issue scope | `github-issues` | Bounded judgment |
| Preserve dirty repository state | `git-hygiene` | Deterministic |
| Manage branch, PR, and checks | `github-pr-workflow` | Deterministic state transitions |
| Review the stable diff | `github-code-review` | Bounded analysis |
| Change repository metadata | `github-repo-management` | Deterministic, authorization-gated |
| Produce release-facing notes | `changelog` | Deterministic from accepted diff |

## Orchestration Workflow

1. Identify repository, remote, issue, branch, dirty state, and authorized external mutations.
2. Inspect before editing; keep issue, diff, tests, and PR scope aligned.
3. Review only after the diff stabilizes. Resolve findings with evidence.
4. Check CI and unresolved review threads; distinguish local green from remote green.
5. Stop at merge readiness unless the user explicitly authorized the next mutation.

## Handoff Record

Record repository, branch, issue and PR IDs, files changed, commit SHAs, local
checks, remote checks, review threads, authorization boundary, and next action.

## Stop Conditions

- Repository, issue, or target branch is ambiguous.
- User changes overlap the proposed edit and cannot be preserved.
- Credentials or required checks are unavailable.
- The next step merges, publishes, closes, or changes settings without authorization.

## Completion Gate

- [ ] Scope, branch, diff, issue, and PR agree
- [ ] User work is preserved
- [ ] Local validation and remote checks are reported separately
- [ ] Review findings and unresolved threads are accounted for
- [ ] Handoff states the exact authorized next action
