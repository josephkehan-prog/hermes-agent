---
name: war-room-specialist-cascade
description: Route War Room requests to hidden niche profiles.
license: MIT
metadata:
  hermes:
    bundle: true
    domain: war-room-specialist-cascade
    tags: [bundle, routing, hidden-workers, local-models, specialization]
    related_skills: [screenplay-production, audiobook-narration-production, transcript-caption-production, structured-document-extraction, previsualization-production]
---

# War Room Specialist Cascade

## Boundary

Route narrow production work behind the visible domain leads. Keep Scriptroom,
Narrator, Caption, Extractor, and Previs inactive in the War Room. Invoke one
only after its niche is unambiguous. Do not use this cascade for ordinary prose,
general audio/video work, broad visual inspection, or generic implementation.

## Routing Table

```bash
python "$HERMES_HOME/hermes-agent/skills/autonomous-ai-agents/war-room-specialist-cascade/scripts/specialist_cascade.py" \
  --brief-file BRIEF.md --json
```

| Niche | Hidden profile | Visible lead | Skill |
|---|---|---|---|
| Screenplay, adaptation, scripted dialogue | `scriptroom` | Quill | `screenplay-production` |
| Audiobook, narration, local TTS | `narrator` | Composer | `audiobook-narration-production` |
| Transcript, subtitles, captions, ASR | `caption` | Director | `transcript-caption-production` |
| Invoice, form, table, schema-to-JSON extraction | `extractor` | Archivist | `structured-document-extraction` |
| Storyboard, animatic, concept trailer, shot proof | `previs` | Director | `previsualization-production` |

Read [references/route-map.md](references/route-map.md) only when a request
touches multiple niches. A tie must stop for one primary deliverable.

## Invoke one worker

```bash
python "$HERMES_HOME/hermes-agent/skills/autonomous-ai-agents/war-room-specialist-cascade/scripts/specialist_cascade.py" \
  --brief-file BRIEF.md --niche audiobook --invoke --workdir "$PWD" \
  --output SPECIALIST-HANDOFF.md
```

The helper uses an argv vector, an allowlisted profile map, one preloaded skill,
and only `code_execution,clarify`. The worker returns a bounded production
handoff. Its visible lead retains approvals, cross-domain decisions, final
files, and delivery.

## Orchestration Workflow

1. Confirm the request needs a niche worker rather than its visible lead.
2. Record primary deliverable, inputs, rights, acceptance target, and non-goals.
3. Route deterministically; clarify ties before invocation.
4. Invoke exactly one hidden profile and save the handoff.
5. Return control to the named visible lead for integration and delivery.
6. Leave the worker inactive; direct CLI invocation does not require activation.

## Handoff Record

Record request, primary niche, selected profile, visible lead, skill, source and
rights state, runtime/model preflight evidence, artifact paths, validation,
limitations, and next visible-lead action.

## Stop Conditions

- More than one primary deliverable is unresolved.
- Required source rights, voice consent, or model approval is missing.
- The selected runtime fails preflight.
- A requested profile is outside the five-entry allowlist.

## Completion Gate

- [ ] One niche, hidden profile, visible lead, and skill are named
- [ ] Exactly one hidden worker was invoked
- [ ] Runtime/model status and evidence paths are explicit
- [ ] Visible lead retains approval and final-delivery ownership
- [ ] Hidden profile remains inactive
