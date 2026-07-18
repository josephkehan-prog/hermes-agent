---
name: sentinel-security-assurance
description: Audit a codebase or runtime for security risks.
version: 1.0.0
author: Hermes War Room
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    bundle: true
    domain: security-assurance
    tags: [bundle, security, audit, dependencies, exposure]
    related_skills: [env-audit, dependency-audit, dockerfile-lint, github-code-review, network-recon]
---

# Sentinel Security Assurance

## Boundary

Own one security assurance report for an authorized repository or local runtime:
scope, evidence, exploitability reasoning, severity, remediation, and retest.
Prefer passive inspection. Do not exploit, persist, exfiltrate, bypass access
controls, scan third-party targets, or expose secrets.

## Routing Table

| Surface | Skill | Mode |
|---|---|---|
| Environment and secret exposure | `env-audit` | Deterministic inspection |
| Vulnerable or stale packages | `dependency-audit` | Deterministic inventory, bounded severity |
| Container build risk | `dockerfile-lint` | Deterministic rules |
| Code and diff security review | `github-code-review` | Bounded analysis |
| Listening services and network surface | `network-recon` | Passive or explicitly authorized probes |

## Orchestration Workflow

1. Record asset owner, authorization, target boundary, prohibited actions, and data-handling rules.
2. Inventory first; never print secret values into logs or the report.
3. Correlate findings across code, configuration, dependencies, containers, and exposure.
4. Rank by evidence, reachability, impact, and confidence—not scanner label alone.
5. Propose the smallest remediation and define an exact retest. Hand implementation to Vanguard.

## Handoff Record

Record scope, authorization, affected component, evidence path, finding class,
severity rationale, confidence, remediation, retest, and accepted residual risk.

## Stop Conditions

- Authorization or target ownership is unclear.
- A step requires bypassing access controls or touching a third-party target.
- Evidence contains secrets that cannot be safely redacted.
- Containment or production mutation is required without authorization.

## Completion Gate

- [ ] Every finding has reproducible evidence
- [ ] Severity includes reachability and impact reasoning
- [ ] Secrets and sensitive data are redacted
- [ ] Remediation and retest are concrete
- [ ] Negative results and remaining blind spots are stated
