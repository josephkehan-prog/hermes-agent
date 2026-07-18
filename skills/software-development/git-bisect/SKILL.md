---
name: git-bisect
description: Find the commit that introduced a regression.
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    domain: software-development
    tags: [git, bisect, debugging, regression]
    related_skills: [systematic-debugging, git-hygiene]
---

# Git Bisect

## Boundary

Find the single commit that introduced a regression, using `git bisect` over a
known-good and known-bad commit range. Use only when the bug is reproducible by
a concrete check. Do not use for bugs you cannot reproduce on demand or that
depend on external state you cannot control.

## Preconditions

Confirm all three before starting; stop and ask if any is missing:

1. A **known-bad** commit (the bug is present) — usually `HEAD`.
2. A **known-good** commit (the bug is absent) — an older commit/tag.
3. A **deterministic test** that returns exit 0 when good, non-zero when bad.
   If the user only describes the symptom, first turn it into one command that
   exits non-zero on the bug.

Also confirm the working tree is clean (`git status`) — bisect checks out
commits and will refuse or lose uncommitted work.

## Automated Procedure (preferred)

1. `git bisect start`
2. `git bisect bad <known-bad>` (or just `git bisect bad` for HEAD)
3. `git bisect good <known-good>`
4. `git bisect run <test-command>` — the command must exit 0 on good, non-zero
   on bad. git checks out midpoints and converges automatically.
5. Read the `<sha> is the first bad commit` line from the output.
6. `git bisect reset` — ALWAYS run this to return to the original HEAD.
7. Report the culprit: `git show --stat <sha>` and the one-line subject.

## Manual Procedure (when no single command captures the test)

Repeat until git reports the first bad commit: run the reproduction, then tell
git the result with `git bisect good` or `git bisect bad`. git halves the range
each step (~log2(N) steps for N commits). End with `git bisect reset`.

## Special Cases

- **Exit code 125**: reserved — return it from the test to tell `git bisect
  run` to SKIP a commit that cannot be tested (e.g. won't build), rather than
  marking it good or bad.
- **Flaky test**: a non-deterministic check corrupts the search. Make the test
  deterministic first, or bisect manually and re-run suspect steps.
- **Merge commits in range**: bisect handles them; do not exclude them.

## Rules

1. Never skip the final `git bisect reset` — leaving a session mid-bisect
   confuses later git commands. If anything fails, run reset before stopping.
2. Do not commit, amend, or alter history during a bisect.
3. Report the culprit commit by SHA and subject; do not guess a cause beyond
   what its diff shows.

## Stop Conditions

- Working tree dirty and the user won't stash: stop before `git bisect start`.
- The "good" commit also exhibits the bug (test bad at both ends): stop — the
  range is wrong; report it instead of bisecting a meaningless range.
- Test cannot be made deterministic: stop and say bisect is unreliable here.

## Completion Gate

Done when the first-bad-commit SHA is reported with its subject and `git bisect
reset` has returned HEAD to its starting point (verify with `git status`).
