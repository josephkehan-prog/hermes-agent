---
name: ethical-investigation-bundle
description: Authorized OSINT investigations with evidence control.
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    bundle: true
    domain: ethical-investigation
    tags: [bundle, osint, investigation, entity-resolution, ethics]
    related_skills: [osint-investigation, social-footprint, network-recon, scrapling, open-databases]
---

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
