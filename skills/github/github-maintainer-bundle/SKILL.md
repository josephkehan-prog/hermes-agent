---
name: github-maintainer-bundle
description: "Use when maintaining a GitHub repository across authentication, issue triage, code inspection, pull-request creation, review, CI follow-up, and merge readiness. Orchestrates the complete repository-maintenance lifecycle."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    bundle: true
    domain: github-maintenance
    tags: [bundle, github, maintenance, pull-requests]
    related_skills: [github-auth, codebase-inspection, github-issues, github-pr-workflow, github-code-review, github-repo-management]
---

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
