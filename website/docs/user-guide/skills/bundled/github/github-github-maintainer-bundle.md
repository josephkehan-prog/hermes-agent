---
title: "Github Maintainer Bundle"
sidebar_label: "Github Maintainer Bundle"
description: "Use when maintaining a GitHub repository across authentication, issue triage, code inspection, pull-request creation, review, CI follow-up, and merge readiness"
---

{/* This page is auto-generated from the skill's SKILL.md by website/scripts/generate-skill-docs.py. Edit the source SKILL.md, not this page. */}

# Github Maintainer Bundle

Use when maintaining a GitHub repository across authentication, issue triage, code inspection, pull-request creation, review, CI follow-up, and merge readiness. Orchestrates the complete repository-maintenance lifecycle.

## Skill metadata

| | |
|---|---|
| Source | Bundled (installed by default) |
| Path | `skills/github/github-maintainer-bundle` |
| Version | `1.0.0` |
| Author | Hermes Agent |
| License | MIT |
| Platforms | linux, macos, windows |
| Tags | `bundle`, `github`, `maintenance`, `pull-requests` |
| Related skills | [`github-auth`](/docs/user-guide/skills/bundled/github/github-github-auth), [`codebase-inspection`](/docs/user-guide/skills/bundled/github/github-codebase-inspection), [`github-issues`](/docs/user-guide/skills/bundled/github/github-github-issues), [`github-pr-workflow`](/docs/user-guide/skills/bundled/github/github-github-pr-workflow), [`github-code-review`](/docs/user-guide/skills/bundled/github/github-github-code-review), [`github-repo-management`](/docs/user-guide/skills/bundled/github/github-github-repo-management) |

## Reference: full SKILL.md

:::info
The following is the complete skill definition that Hermes loads when this skill is triggered. This is what the agent sees as instructions when the skill is active.
:::

# GitHub Maintainer Bundle

## Boundary

Coordinate repository work that crosses two or more GitHub surfaces. Do not
use for a local-only git operation or when one focused GitHub skill fully covers
the request.

## Routing Table

| Need | Primary skill | Required output |
|---|---|---|
| Establish or repair credentials | `github-auth` | Authenticated identity and access scope |
| Understand unfamiliar code | `codebase-inspection` | Relevant architecture and change surface |
| Create, update, or triage issues | `github-issues` | Issue state and rationale |
| Branch, commit, open, monitor, or merge PR | `github-pr-workflow` | PR lifecycle state |
| Review a diff or PR | `github-code-review` | Prioritized actionable findings |
| Manage repository settings or metadata | `github-repo-management` | Confirmed repository state |

## Orchestration Workflow

1. Identify repository, remote, current branch, worktree state, and requested
   external mutations. Authenticate before any API-dependent stage.
2. Inspect the code and linked issue before changing issue or PR state.
3. Keep issue, branch, commit, and PR scope aligned; split unrelated work.
4. Run review after the diff stabilizes. Apply fixes locally and re-check CI.
5. Merge or change repository settings only when the user authorized that
   external state change and protections allow it.

## Handoff Record

Record repository and branch, issue/PR identifiers, authorization boundaries,
files changed, commit SHAs, check results, review threads, and unresolved
maintainer decisions. Link evidence to the exact GitHub object.

## Stop Conditions

- Authentication identity or repository target is ambiguous.
- The worktree contains overlapping user changes that cannot be preserved.
- Review feedback requires a product decision rather than a code correction.
- Required checks or branch protections are still pending or failing.
- The next action merges, closes, publishes, or changes settings without clear
  authorization.

## Completion Gate

- [ ] Repository, branch, issue, and PR identities are consistent
- [ ] Requested local changes and GitHub state changes are both verified
- [ ] Review findings and unresolved threads are accounted for
- [ ] Required checks pass or their failures are accurately reported
- [ ] No external mutation exceeded the user's authority
- [ ] Final handoff includes durable links or identifiers

## Common Pitfalls

- Editing before reading the linked issue and current diff
- Treating a green unit test as proof that GitHub checks are green
- Losing contributor authorship when salvaging external work
- Resolving review threads without implementing or explaining the resolution
