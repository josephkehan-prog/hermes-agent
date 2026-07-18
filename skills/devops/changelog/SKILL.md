---
name: changelog
description: Build a Keep-a-Changelog CHANGELOG.md from git history.
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [changelog, git, release-notes, conventional-commits, terminal]
    category: devops
    requires_toolsets: [terminal]
    related_skills: [git-hygiene, dependency-audit]
---

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
