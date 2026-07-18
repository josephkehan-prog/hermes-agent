---
name: career-campaign-bundle
description: Run an end-to-end job application campaign.
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    bundle: true
    domain: career-campaign
    tags: [bundle, career, job-search, applications]
    related_skills: [job-search-tracking, resume-tailor, cover-letter, interview-prep, google-workspace]
---

# Career Campaign Bundle

## Boundary

Coordinate a multi-stage job search or a complete application package. Do not
use for generic career advice or a single document edit with no campaign state.

## Routing Table

| Campaign need | Primary skill | Durable output |
|---|---|---|
| Track opportunity and next action | `job-search-tracking` | Application record and status |
| Align experience to a role | `resume-tailor` | Truthful role-specific resume |
| Explain motivation and fit | `cover-letter` | Evidence-based tailored letter |
| Prepare for evaluation | `interview-prep` | Question bank, stories, and practice plan |
| Manage source or delivery documents | `google-workspace` | Located, created, or updated workspace file |

## Orchestration Workflow

1. Capture the canonical job posting, deadline, company, role, and application
   state in `job-search-tracking`.
2. Build a fact bank from the user's verified experience. Reuse it across
   resume, letter, and interview stories; never invent credentials or metrics.
3. Tailor the resume before the cover letter so both share the same positioning
   and evidence.
4. Derive interview stories from the submitted artifacts and job criteria.
5. Update the tracker after every external milestone and set a dated next
   action. Use `google-workspace` only when the user wants those files managed.

## Handoff Record

Maintain job ID/URL, posting snapshot, requirements matrix, verified fact bank,
artifact versions, submission status, contacts, interview evidence, and next
action date. Mark any claim that still needs user verification.

## Stop Conditions

- A requested credential, date, title, or metric is unverified.
- The original job posting is missing or materially incomplete.
- The next step sends an application, email, or message without authorization.
- Multiple document versions conflict and no canonical source is identified.

## Completion Gate

- [ ] Tracker reflects the current stage and a dated next action
- [ ] Resume and letter map to the posting's material requirements
- [ ] Every candidate claim comes from the verified fact bank
- [ ] Interview preparation matches the submitted positioning
- [ ] Final artifacts are readable in their delivery format
- [ ] No application or communication was sent without approval

## Common Pitfalls

- Optimizing for keywords by fabricating experience
- Tailoring each document from a different fact base
- Losing the exact posting after it is removed
- Treating artifact creation as permission to submit it
