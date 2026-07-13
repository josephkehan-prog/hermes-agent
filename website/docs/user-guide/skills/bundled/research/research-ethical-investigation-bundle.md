---
title: "Ethical Investigation Bundle"
sidebar_label: "Ethical Investigation Bundle"
description: "Use when conducting authorized open-source investigations across people, organizations, domains, infrastructure, public records, and social footprints"
---

{/* This page is auto-generated from the skill's SKILL.md by website/scripts/generate-skill-docs.py. Edit the source SKILL.md, not this page. */}

# Ethical Investigation Bundle

Use when conducting authorized open-source investigations across people, organizations, domains, infrastructure, public records, and social footprints. Coordinates evidence collection and entity resolution with privacy and confidence controls.

## Skill metadata

| | |
|---|---|
| Source | Bundled (installed by default) |
| Path | `skills/research/ethical-investigation-bundle` |
| Version | `1.0.0` |
| Author | Hermes Agent |
| License | MIT |
| Platforms | linux, macos, windows |
| Tags | `bundle`, `osint`, `investigation`, `entity-resolution`, `ethics` |
| Related skills | [`osint-investigation`](/docs/user-guide/skills/bundled/osint-investigation/osint-investigation-osint-investigation), [`social-footprint`](/docs/user-guide/skills/bundled/research/research-social-footprint), [`network-recon`](/docs/user-guide/skills/bundled/research/research-network-recon), [`scrapling`](/docs/user-guide/skills/bundled/scrapling/scrapling-scrapling), [`open-databases`](/docs/user-guide/skills/bundled/research/research-open-databases) |

## Reference: full SKILL.md

:::info
The following is the complete skill definition that Hermes loads when this skill is triggered. This is what the agent sees as instructions when the skill is active.
:::

# Ethical Investigation Bundle

## Boundary

Investigate public evidence for a legitimate, authorized purpose. Restrict work
to lawfully accessible sources. Do not facilitate stalking, credential theft,
deanonymization for harm, unauthorized intrusion, or publication of sensitive
personal data.

## Routing Table

| Lead type | Primary skill | Expected evidence |
|---|---|---|
| Multi-entity case | `osint-investigation` | Case structure, entities, sources, confidence |
| Username or public social presence | `social-footprint` | Platform candidates and verified profiles |
| Domain, host, certificate, or service | `network-recon` | Passive/authorized technical observations |
| Public webpage extraction | `scrapling` | Reproducible structured page evidence |
| Corporate, court, or government record | `open-databases` | Source-backed public records |

## Orchestration Workflow

1. Record purpose, authorization, target boundary, prohibited actions, and
   retention needs before collecting data.
2. Create separate entity and identifier ledgers. Never merge two identities
   from a single shared attribute.
3. Route each lead by evidence type and prefer passive collection. Escalate to
   active network checks only when explicitly authorized.
4. Preserve source URL, access time, raw observation, and collection method.
5. Resolve entities using multiple independent attributes; carry confidence
   and contradictions into the report.
6. Minimize the final report to information necessary for the stated purpose.

## Handoff Record

Track authorization, scope, entity IDs, identifiers, source provenance,
collection timestamps, confidence, contradictions, sensitive-data flags, and
next lawful leads. Keep observations separate from conclusions.

## Stop Conditions

- Purpose, authority, or target scope is unclear.
- A step requires bypassing access controls, authentication, or rate limits.
- Evidence could expose a vulnerable person's precise location or secrets.
- Entity resolution rests on one weak or common identifier.
- Requested publication exceeds the original collection purpose.

## Completion Gate

- [ ] Purpose and authorization remained within scope
- [ ] Every conclusion traces to preserved public evidence
- [ ] Entity matches use multiple attributes and explicit confidence
- [ ] Contradictions and negative results are retained
- [ ] Sensitive data is minimized or redacted
- [ ] No active technique exceeded documented authorization

## Common Pitfalls

- Equating a username match with identity confirmation
- Treating HTTP 200 as proof the correct account was found
- Following lead drift beyond the authorized target boundary
- Publishing raw personal data when a summarized finding is sufficient
