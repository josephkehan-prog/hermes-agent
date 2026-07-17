---
name: genre-novel-production
description: "Use when planning, drafting, revising, or continuity-checking a romance, fantasy, science-fiction, horror, mystery, or thriller novel with the local Cydonia prose engine. Enforces genre-specific promises, chapter ledgers, story-bible updates, and manuscript-scale verification."
version: 1.0.0
author: Hermes War Room
license: MIT
platforms: [macos]
metadata:
  hermes:
    bundle: true
    domain: genre-novel-production
    tags: [bundle, novel, genre-fiction, continuity, local-model]
    related_skills: [cydonia-creative-writing, manuscript-continuity-ledger, humanizer]
---

# Genre Novel Production

## Boundary

Own one genre manuscript from premise through continuity-checked chapters and
assembled delivery. Use Agents-A1 for planning, files, approvals, and review;
use Cydonia only as a no-tool prose engine. Quill retains short fiction, scenes,
dialogue, and general revision outside a manuscript-scale genre workflow.

Read [references/genre-contracts.md](references/genre-contracts.md) only for
the selected genre. If a project intentionally blends genres, name one primary
reader promise and use at most two secondary contract sections.

## Routing Table

| Work | Primary skill | Output |
|---|---|---|
| Chapter prose, dialogue, voice, scene revision | `cydonia-creative-writing` | Bounded no-tool draft |
| Story bible, chapter loop, threads, assembly audit | `manuscript-continuity-ledger` | Canon and manuscript ledgers |
| Final publication-facing voice cleanup | `humanizer` | Revised accepted prose |

## Orchestration Workflow

1. Fix primary genre, audience, premise, POV, tense, tone, length target,
   content boundaries, and the selected genre contract.
2. Create `PREMISE.md`, `OUTLINE.md`, `STORY-BIBLE.md`, `CHAPTER-LEDGER.md`,
   and `REVISION-LOG.md`. Define stable character, place, rule, clue, and thread
   IDs before drafting.
3. Draft one chapter at a time through Cydonia `think:false`. Give it only the
   chapter brief and continuity facts needed for that unit.
4. Have Agents-A1 check genre promises, causality, voice, timeline, unresolved
   threads, and chapter obligations. Accept or revise before updating canon.
5. Run continuity checks after each arc or ten chapters, whichever comes first.
6. Assemble the manuscript, run a full consistency and repetition pass, then
   apply `humanizer` only after story content is stable.

## Handoff Record

Carry genre contract, premise, audience, POV/tense, boundaries, outline and
bible paths, chapter ledger, accepted canon changes, unresolved thread IDs,
Cydonia mode/seed, chapter paths and word counts, revision log, manuscript
path, and final consistency findings.

## Stop Conditions

- Primary genre, audience, canon, or material content boundaries are missing.
- A chapter would contradict accepted canon without an explicit retcon record.
- Factual or sensitivity research is required but has not been handed to Mythos.
- The request asks for close imitation of a living author rather than traits.

## Completion Gate

- [ ] Every chapter satisfies its outline entry and primary genre promise
- [ ] Character, place, rule, clue, timeline, and thread IDs remain consistent
- [ ] Cydonia remained no-tool and Agents-A1 controlled files and approvals
- [ ] All unresolved threads are intentionally resolved, deferred, or logged
- [ ] Repetition, pacing, and voice passes were completed after assembly
- [ ] Chapter count, word count, manuscript path, and limitations are reported
