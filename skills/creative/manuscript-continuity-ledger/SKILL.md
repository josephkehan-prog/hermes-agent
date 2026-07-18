---
name: manuscript-continuity-ledger
description: Build and audit manuscript continuity artifacts.
version: 1.0.0
author: Hermes War Room
license: MIT
platforms: [macos]
metadata:
  hermes:
    tags: [manuscript, continuity, story-bible, chapters, canon]
    related_skills: [cydonia-creative-writing, humanizer]
---

# Maintain Manuscript Continuity

Keep long-form state in files instead of relying on model memory. Use stable
IDs and update canon only after a chapter or revision is accepted.

## Required artifacts

| File | Required state |
|---|---|
| `PREMISE.md` | Reader promise, audience, POV, tense, tone, boundaries |
| `OUTLINE.md` | Chapter ID, POV, obligation, turn, consequence, next dependency |
| `STORY-BIBLE.md` | Character, place, object, faction, rule, and terminology IDs |
| `CHAPTER-LEDGER.md` | Draft status, word count, accepted canon changes, open obligations |
| `THREAD-LEDGER.md` | Thread/clue ID, introduction, evidence, current state, planned payoff |
| `TIMELINE.md` | Absolute or relative event order, ages, travel, durations |
| `REVISION-LOG.md` | Date, scope, reason, affected IDs, retcon status, verifier |

## Workflow

1. Create the artifacts before chapter drafting. Use IDs such as `CHR-001`,
   `PLC-001`, `RULE-001`, `THR-001`, and `CH-001` rather than mutable names.
2. Before a chapter, extract a bounded continuity packet containing its outline
   obligation, active POV facts, setting/rule facts, timeline position, and
   threads that must advance or remain untouched.
3. After a draft, compare claims against the ledgers. Record contradictions,
   dropped obligations, unexplained knowledge, timing errors, rule exceptions,
   repeated beats, and premature thread payoffs.
4. Accept the chapter only after resolving those findings. Apply accepted facts
   to the bible, timeline, chapter ledger, and thread ledger as one transaction.
5. For a retcon, record old state, new state, reason, and every affected chapter
   before editing prose. Never silently overwrite accepted canon.
6. After each arc or ten chapters, audit all open threads and timeline spans.
   Before delivery, assemble chapters in ledger order and run a full audit.

## Continuity packet

Keep each prose-engine handoff compact:

```text
chapter_id:
obligation:
pov_and_voice:
time_and_place:
required_canon_ids:
threads_to_advance:
threads_to_preserve:
forbidden_changes:
ending_state:
```

## Completion gate

- [ ] Every chapter has one ledger row and satisfies its outline obligation
- [ ] All new facts map to stable canon IDs
- [ ] Timeline, travel, ages, knowledge, injuries, inventory, and rules agree
- [ ] Every thread is resolved, intentionally open, or explicitly deferred
- [ ] Retcons list all affected chapters and were propagated consistently
- [ ] Assembly order, chapter count, word count, and final path are recorded

