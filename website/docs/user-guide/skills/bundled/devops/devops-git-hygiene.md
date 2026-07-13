---
title: "Git Hygiene — Keep a repo clean —"
sidebar_label: "Git Hygiene"
description: "Keep a repo clean —"
---

{/* This page is auto-generated from the skill's SKILL.md by website/scripts/generate-skill-docs.py. Edit the source SKILL.md, not this page. */}

# Git Hygiene

Keep a repo clean — .gitignore, no committed secrets, no large binaries, branch naming, atomic conventional commits. Plain git commands, no cloud API.

## Skill metadata

| | |
|---|---|
| Source | Bundled (installed by default) |
| Path | `skills/devops/git-hygiene` |
| Version | `1.0.0` |
| Author | Hermes Agent |
| License | MIT |
| Platforms | linux, macos, windows |
| Tags | `git`, `hygiene`, `secrets`, `commits`, `branching`, `terminal` |
| Related skills | [`changelog`](/docs/user-guide/skills/bundled/devops/devops-changelog), [`dependency-audit`](/docs/user-guide/skills/bundled/devops/devops-dependency-audit) |

## Reference: full SKILL.md

:::info
The following is the complete skill definition that Hermes loads when this skill is triggered. This is what the agent sees as instructions when the skill is active.
:::

# Git Hygiene

Local, keyless checklist for keeping a repo clean before commit/push. No API
keys, no cloud service — just `git`.

## When to Use

Before any commit (especially shared branches), when asked "is this repo
clean" / "did I leak a secret", or cleaning up a messy history.

## 1. .gitignore sanity

Minimum excludes: build output, local env files (`.env`), OS cruft
(`.DS_Store`), and any secrets drop-point. In this workspace that's
`secrets/` (see `bin/hermes-tokens`) — its own `.gitignore` already blocks
everything but `*.example`; never override it from outside.

```bash
git status --porcelain
git check-ignore -v secrets/tokens.inbox   # must print something
```

If `check-ignore` prints nothing, the file is NOT ignored — fix before staging.

## 2. No committed secrets

- Never `git add` inside `secrets/` except `*.example`.
- Grep staged content before commit:

```bash
git diff --cached | grep -Ei 'api[_-]?key|secret|token|password|BEGIN (RSA|OPENSSH) PRIVATE KEY'
```

- Unpushed leak: `git reset` + re-commit clean. Pushed leak: rotate via
  `bin/hermes-tokens` first; only rewrite history with explicit user approval.

## 3. No large binaries

```bash
find . -size +5M -not -path './.git/*'
```

Large binaries (models, media) go in a dedicated store or Git LFS.

## 4. Branch naming: `type/short-description`

Lowercase, hyphenated: `feat/git-hygiene-skill`, `fix/token-router-race`.

## 5. Atomic, conventional commits

One logical change per commit. Types: `feat fix refactor docs test chore perf ci`.

```
<type>: <imperative summary, ≤50 chars>

<optional body: why, not what>
```

```bash
git add path/to/file.py path/to/other.py   # never `git add -A` blindly
git diff --cached                          # review exactly what's staged
git commit -m "fix: dedupe watermark on restart"
```

## 6. Pre-commit sanity pass

`git status` then `git diff --cached` — read the actual diff, not just
filenames, before every commit.

## Pitfalls

- `git add -A` / `git add .` stages secrets and stray files silently.
- A `.gitignore` entry added AFTER a file was tracked does nothing —
  `git rm --cached <file>` first.
- Don't rewrite pushed history without explicit user approval.
