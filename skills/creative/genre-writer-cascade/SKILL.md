---
name: genre-writer-cascade
description: Select the matching standby genre profile for Quill.
license: MIT
metadata:
  hermes:
    domain: genre-writer-cascade
    tags: [routing, fiction, manuscript, hidden-workers, local-model]
    related_skills: [genre-novel-production, cydonia-creative-writing, manuscript-continuity-ledger]
---

# Genre Writer Cascade

## Boundary

Quill is the visible book desk. Heartline, Spellbound, Orbit, Nocturne, and
Casefile are standby workers: keep them off the active roster and invoke one
only when a manuscript-scale request matches its primary reader promise.
Short fiction, isolated scenes, dialogue, roleplay, and general prose revision
remain with Quill.

## Deterministic routing

Run the router before invoking a worker:

```bash
python "$HERMES_HOME/hermes-agent/skills/creative/genre-writer-cascade/scripts/genre_writer_cascade.py" \
  --brief-file MANUSCRIPT-BRIEF.md --json
```

| Primary promise | Standby profile |
|---|---|
| Romance and relationship arc | `heartline` |
| Fantasy, magic, myth, or secondary worlds | `spellbound` |
| Science fiction and speculative technology | `orbit` |
| Horror, dread, or supernatural fear | `nocturne` |
| Mystery, crime, suspense, or thriller | `casefile` |

When genres tie, ask for the one primary reader promise. Do not silently pick
from a tie. Secondary genres belong in the handoff, not in a second worker
invocation.

## Invoke a standby worker

After the route is unambiguous, invoke exactly one worker:

```bash
python "$HERMES_HOME/hermes-agent/skills/creative/genre-writer-cascade/scripts/genre_writer_cascade.py" \
  --brief-file MANUSCRIPT-BRIEF.md --genre fantasy --invoke \
  --workdir "$PWD" --output STANDBY-HANDOFF.md
```

The helper uses an argv list rather than a shell, limits the child to the
profile's approved `code_execution,clarify` toolsets, preloads
`genre-novel-production`, and returns the worker's bounded handoff to Quill.
Quill remains responsible for approvals, cross-genre decisions, the final
manuscript, and user delivery.

## Cascade workflow

1. Decide whether the request is manuscript-scale. If not, keep it in Quill.
2. Write a compact brief with primary promise, audience, POV, tense, tone,
   length, canon, boundaries, and requested deliverable.
3. Route deterministically. Resolve a tie with the user before invocation.
4. Invoke one standby profile and save its result as a handoff artifact.
5. Use the returned genre contract and chapter packet with
   `genre-novel-production`, `cydonia-creative-writing`, and
   `manuscript-continuity-ledger`.
6. Keep the standby profile inactive after the call; direct CLI invocation does
   not require it to be present in the active delegation roster.

## Stop conditions

- Primary genre or material content boundaries are missing.
- More than one primary reader promise is required but precedence is unclear.
- The request is short-form prose that Quill already owns.
- The proposed call would use a profile outside the five allowlisted slugs.

## Completion gate

- [ ] The route is deterministic and names one primary genre
- [ ] Exactly one allowlisted standby profile was invoked
- [ ] The worker handoff records genre contract, canon, boundaries, and output
- [ ] Quill retained control of files, approvals, and final delivery
- [ ] Standby profiles remain absent from the active roster
