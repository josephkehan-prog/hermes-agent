---
name: screenplay-production
description: Write and revise screenplays with local Cydonia.
license: MIT
metadata:
  hermes:
    bundle: true
    domain: screenplay-production
    tags: [bundle, screenplay, adaptation, dialogue, scenes]
    related_skills: [cydonia-creative-writing, manuscript-continuity-ledger, humanizer]
---

# Screenplay Production

## Boundary

Produce dramatic scripts and adaptation packets. Use Cydonia only for bounded
creative drafting; keep qwen3-coder responsible for files, format checks,
continuity, approvals, and delivery. Route prose manuscripts to Quill's genre
cascade and final video production to Director.

## Routing Table

| Stage | Skill | Output |
|---|---|---|
| Dramatic scene/dialogue draft | `cydonia-creative-writing` | Bounded no-tool prose |
| Character, prop, location, and information state | `manuscript-continuity-ledger` | Stable scene ledger |
| Final voice cleanup | `humanizer` | Meaning-preserving polish |

## Orchestration Workflow

1. Fix medium, audience, target runtime/page count, rating, format, tone, and adaptation rights.
2. Create premise, dramatic question, character wants, act/sequence beats, and scene purpose ledger.
3. Draft one scene packet at a time with `cydonia-creative-writing` in `think:false` mode.
4. Track entrances, props, locations, time, knowledge, injuries, promises, and unresolved turns in `manuscript-continuity-ledger`.
5. Revise in passes: structure, scene objective/conflict/turn, dialogue voice, economy, then format.
6. Apply `humanizer` only after dramatic content is stable.
7. Deliver script, beat sheet, scene ledger, continuity risks, and adaptation/source notes.

Use Fountain or Markdown text artifacts. Do not create a Python/JavaScript
"screenplay converter" unless software automation is explicitly requested.
When source material is absent, return `blocked-input` and list the exact source
and format decisions needed; do not fabricate a sample adaptation.

Read [references/format-contract.md](references/format-contract.md) before a
formatted screenplay or stage-script delivery.

## Handoff Record

Record source and rights, medium, runtime/page target, rating, beat sheet,
scene ledger, script path, Cydonia mode/seed, continuity risks, format check,
and next Quill action.

## Stop Conditions

- Adaptation or likeness rights are unclear.
- Requested runtime, medium, or content boundary would materially change structure.
- Source canon is missing for a continuity-sensitive adaptation.
- The request is prose-first rather than performance-first.
- Required source material is absent for an adaptation request.

## Completion Gate

- [ ] Every scene has objective, conflict, turn, and exit state
- [ ] Sluglines, action, dialogue, and transitions follow the selected medium
- [ ] Character voice and information state remain consistent
- [ ] Page/runtime estimate and unresolved production risks are recorded
- [ ] Cydonia remained a no-tool prose engine
