---
title: "Changelog — Generate and maintain a Keep-a-Changelog CHANGELOG"
sidebar_label: "Changelog"
description: "Generate and maintain a Keep-a-Changelog CHANGELOG"
---

{/* This page is auto-generated from the skill's SKILL.md by website/scripts/generate-skill-docs.py. Edit the source SKILL.md, not this page. */}

# Changelog

Generate and maintain a Keep-a-Changelog CHANGELOG.md from git history using conventional-commit prefixes. Keyless, git-only, no cloud API.

## Skill metadata

| | |
|---|---|
| Source | Bundled (installed by default) |
| Path | `skills/devops/changelog` |
| Version | `1.0.0` |
| Author | Hermes Agent |
| License | MIT |
| Platforms | linux, macos, windows |
| Tags | `changelog`, `git`, `release-notes`, `conventional-commits`, `terminal` |
| Related skills | [`git-hygiene`](/docs/user-guide/skills/bundled/devops/devops-git-hygiene), [`dependency-audit`](/docs/user-guide/skills/bundled/devops/devops-dependency-audit) |

## Reference: full SKILL.md

:::info
The following is the complete skill definition that Hermes loads when this skill is triggered. This is what the agent sees as instructions when the skill is active.
:::

# Changelog

Derive `CHANGELOG.md` in [Keep a Changelog](https://keepachangelog.com) format
straight from `git log` — no cloud summarizer, no API key.

## When to Use

"Update the changelog" / "write release notes" / "summarize what changed
since X" / before tagging a release.

## Format

```markdown
# Changelog

## [Unreleased]
### Added
- ...
### Changed
- ...
### Fixed
- ...
### Removed
- ...

## [1.2.0] - 2026-07-10
### Added
- ...
```

Only non-empty sections appear. `[Unreleased]` sits on top and accumulates
until the next tagged release.

## Deriving entries from git log

```bash
LAST_TAG=$(git describe --tags --abbrev=0 2>/dev/null || echo "")
RANGE="${LAST_TAG:+$LAST_TAG..}HEAD"
git log $RANGE --pretty=format:'%s' --no-merges
```

Prefix → section mapping:

| commit prefix | section |
|---|---|
| `feat:` | Added |
| `fix:` | Fixed |
| `refactor:`, `perf:` | Changed |
| `docs:`, `test:`, `chore:`, `ci:` | omit (internal) |
| subject mentions remove/delete | Removed |

```bash
git log $RANGE --pretty=format:'%s' --no-merges | grep '^feat:'
git log $RANGE --pretty=format:'%s' --no-merges | grep '^fix:'
git log $RANGE --pretty=format:'%s' --no-merges | grep -E '^(refactor|perf):'
```

Strip the prefix and capitalize: `feat: add token router` becomes
`- Add token router`.

## Tagged release cutover

Rename `[Unreleased]` to `[X.Y.Z] - YYYY-MM-DD` (`date +%F`), add a fresh
empty `[Unreleased]` above it, then:

```bash
git tag -a v1.2.0 -m "release: v1.2.0"
```

## Pitfalls

- Filter merges and low-signal `chore:`/`docs:`/`ci:` prefixes with
  `--no-merges` unless the user wants everything.
- Non-conventional commits still matter — place by judgment, don't drop.
- Keep entries user-facing, not a raw commit-message dump.
