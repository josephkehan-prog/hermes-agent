---
name: quill-story-production
description: "Use when Quill must draft or revise fiction with Cydonia while preserving voice, continuity, requested boundaries, and a clean handoff to publication or manuscript workflows."
version: 1.0.0
author: Hermes War Room
license: MIT
platforms: [macos]
metadata:
  hermes:
    bundle: true
    domain: quill-story-production
    tags: [bundle, quill, fiction, prose, continuity]
    related_skills: [cydonia-creative-writing, humanizer, novel-generator]
---

# Quill Story Production

## Boundary

Own fiction, dialogue, roleplay, worldbuilding, and narrative revision. Do not
use Cydonia for research, citations, code, commands, or tool decisions.

## Routing Table

| Work | Skill | Inference mode |
|---|---|---|
| Scene, dialogue, voice, or worldbuilding | `cydonia-creative-writing` | Creative sampling; `think:false` |
| Publication-facing voice cleanup | `humanizer` | Deterministic revision; preserve meaning |
| Full manuscript workflow | `novel-generator` | Structured long-form sequence |

## Orchestration Workflow

1. Fix POV, tense, tone, canon, boundaries, and acceptance target.
2. Use Cydonia in `think:false` mode. Use creative temperature for a first
   draft; use a fixed seed and lower temperature for continuity-sensitive edits.
3. Keep Agents-A1 responsible for files, approvals, and continuity checks.
4. Update the story bible only after the user accepts a draft.
5. Use `humanizer` only after content is correct; use `novel-generator` only for
   manuscript-scale work.

## Handoff Record

Record brief, POV, tense, voice constraints, canon, content boundaries, sampling
mode and seed, draft path, revision notes, and story-bible status.

## Stop Conditions

- Required canon or content boundaries are missing and would change the story.
- The request is factual research or operational work.
- A revision would silently alter accepted canon.

## Completion Gate

- [ ] POV, tense, voice, and canon are consistent
- [ ] Cydonia remained a no-tool prose engine
- [ ] Sampling mode matches drafting versus revision
- [ ] Accepted content boundaries are preserved
- [ ] Draft and continuity artifacts are named in the handoff
