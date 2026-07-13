---
title: "Dependency Audit"
sidebar_label: "Dependency Audit"
description: "Audit dependencies for staleness and vulnerabilities using free, local, keyless tools only — npm audit, pip-audit, cargo audit, OSV-Scanner"
---

{/* This page is auto-generated from the skill's SKILL.md by website/scripts/generate-skill-docs.py. Edit the source SKILL.md, not this page. */}

# Dependency Audit

Audit dependencies for staleness and vulnerabilities using free, local, keyless tools only — npm audit, pip-audit, cargo audit, OSV-Scanner. No paid services.

## Skill metadata

| | |
|---|---|
| Source | Bundled (installed by default) |
| Path | `skills/devops/dependency-audit` |
| Version | `1.0.0` |
| Author | Hermes Agent |
| License | MIT |
| Platforms | linux, macos, windows |
| Tags | `dependencies`, `security`, `audit`, `npm`, `pip`, `cargo`, `osv`, `terminal` |
| Related skills | [`git-hygiene`](/docs/user-guide/skills/bundled/devops/devops-git-hygiene), [`changelog`](/docs/user-guide/skills/bundled/devops/devops-changelog) |

## Reference: full SKILL.md

:::info
The following is the complete skill definition that Hermes loads when this skill is triggered. This is what the agent sees as instructions when the skill is active.
:::

# Dependency Audit

Check dependencies for known vulnerabilities and staleness using only free,
open-source, keyless scanners. No paid service — everything below runs local
or against free public advisory databases, no account needed.

## When to Use

"Check dependencies" / "any known vulnerabilities" / "what's outdated" /
pre-release, alongside `git-hygiene`.

## Node / npm

```bash
npm audit          # built into npm, free, keyless
npm outdated        # staleness only
```

## Python

```bash
pip list --outdated
pip install pip-audit   # one-time local install
pip-audit                # OSS, keyless, uses free PyPI Advisory DB
```

## Rust

```bash
cargo install cargo-audit   # one-time local install
cargo audit                  # OSS, keyless, uses RustSec advisory DB
```

## Cross-ecosystem: OSV-Scanner

[OSV-Scanner](https://github.com/google/osv-scanner) is Google's OSS, keyless
scanner covering npm, PyPI, crates.io, Go, Maven via the free OSV.dev DB.

```bash
go install github.com/google/osv-scanner/cmd/osv-scanner@latest
osv-scanner -r .                       # recursive repo scan
osv-scanner --lockfile=package-lock.json
osv-scanner --lockfile=requirements.txt
```

## Reading results

- Prioritize critical/high severity with a known fix version.
- Staleness without an advisory is lower priority than an outdated-but-safe
  package — staleness alone isn't a vulnerability.
- Note per finding: package, current version, fixed version, advisory ID
  (CVE/GHSA/OSV), and whether the fix is a simple bump or breaking major.

## Explicitly out of scope

No paid/subscription scanners (Snyk paid tier or similar) — free/local
tooling only. Never wire in an API key for a vuln service; every tool above
ships locally or hits a free, keyless public database.

## Pitfalls

- `npm audit fix --force` can bump majors and break things — review the diff.
- These scanners need periodic manual re-runs; pair with the `watchers`
  skill for scheduled reminders.
- Installing scanners is a one-time local install, not a cloud service.
