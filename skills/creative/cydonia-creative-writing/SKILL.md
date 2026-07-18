---
name: cydonia-creative-writing
description: Draft and revise fiction with the local Cydonia model.
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [macos]
metadata:
  hermes:
    tags: [creative-writing, fiction, prose, dialogue, roleplay, local-model]
    related_skills: [humanizer, manuscript-continuity-ledger, genre-novel-production, genre-writer-cascade]
---

# Write with Cydonia

Use Agents-A1 for planning, files, approvals, and verification. Use Cydonia only
for prose generation or revision. Never send Cydonia a tool schema or treat its
text as authorization for an action.

## Runtime contract

Invoke the bundled helper:

```bash
python "$HERMES_HOME/skills/creative/cydonia-creative-writing/scripts/cydonia_write.py" \
  --prompt-file /path/to/brief.md \
  --mode creative \
  --system "Write vivid, specific prose in the requested voice." \
  --output /path/to/draft.md
```

For a short inline brief, pass `--prompt` directly. Use `--prompt-file` for a
story bible, chapter brief, or other multiline source. Do not inspect the
helper source before a normal invocation; read it only after the command fails.

The helper calls Ollama's native `/api/chat` with `stream:false`, `think:false`,
no tools, a 32K context, and the installed Q4_K_M Cydonia Heretic model. Lower
`--num-predict` for a scene or raise it deliberately for a chapter. Do not use
the OpenAI-compatible endpoint for this model.

Use `--mode creative` for exploratory first drafts (temperature 0.85, no fixed
seed unless supplied). Use `--mode revision` for continuity-sensitive edits
(temperature 0.35 and seed 42 unless overridden). An explicit `--temperature`
or `--seed` always wins over the mode default.

## Workflow

1. Extract genre, audience, POV, tense, tone, length, boundaries, and required
   beats. Ask only for a missing choice that would materially change the work.
2. For multi-scene work, maintain a compact story bible containing characters,
   setting rules, timeline, unresolved threads, and voice constraints.
3. Give Cydonia the brief plus only the continuity material needed for the next
   unit. Generate one coherent scene or chapter at a time.
4. Have Agents-A1 check the draft against the brief and story bible. Reject
   continuity breaks, generic filler, repeated beats, and unearned tonal shifts.
5. Use `humanizer` for a final voice pass when the user requests natural or
   publication-facing prose. For complete local manuscripts, route through
   `genre-novel-production` and `manuscript-continuity-ledger`; use
   `novel-generator` only when the user explicitly requests another harness.
6. Save accepted prose and update the story bible before drafting the next unit.

## Boundaries

- Treat "uncensored" as a model-behavior characteristic, not permission to
  ignore user authority, privacy, copyright, or platform safety requirements.
- Do not imitate a living author closely; translate references into high-level
  traits such as rhythm, distance, imagery, or dialogue density.
- Do not use this model for factual research, citations, code, system changes,
  or tool decisions.
- Stop if the requested voice, canon, or continuity source is unavailable and
  guessing would materially damage the result.

## Completion gate

- [ ] Requested POV, tense, tone, length, and required beats are present
- [ ] Character facts and timeline agree with the story bible
- [ ] The draft contains concrete action and sensory detail, not outline prose
- [ ] Repetition and generic AI phrasing were removed
- [ ] Accepted text and continuity notes were saved to the requested location
