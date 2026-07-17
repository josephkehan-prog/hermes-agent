---
name: wildcard-triage-routing
description: "Use when Wildcard must turn an ambiguous request into an evidence-backed scope and route it to the correct War Room specialist without duplicating specialist work."
version: 1.0.0
author: Hermes War Room
license: MIT
platforms: [macos]
metadata:
  hermes:
    bundle: true
    domain: wildcard-triage-routing
    tags: [bundle, wildcard, triage, routing, evidence]
    related_skills: [duckduckgo-search, quick-summary, workspace-rag, repo-location-discovery, codebase-inspection, war-room-specialist-cascade]
---

# Wildcard Triage Routing

## Boundary

Clarify intent, gather the minimum evidence needed for routing, and create a
compact handoff. Do not perform specialist implementation, deep synthesis,
visual judgment, image production, or narrative drafting.

## Routing Table

| Need | Skill | Inference mode |
|---|---|---|
| Current external facts | `duckduckgo-search` | Deterministic source collection |
| Compress supplied material | `quick-summary` | Deterministic, preserve caveats |
| Recover local decisions | `workspace-rag` | Deterministic retrieval before inference |
| Find code or config ownership | `repo-location-discovery` | Deterministic path evidence |
| Identify relevant components | `codebase-inspection` | Deterministic architecture inventory |
| Screenplay, audiobook, caption, document-extraction, or previs niche | `war-room-specialist-cascade` | Deterministic hidden profile |

## Specialist Precedence

Apply the narrowest matching owner before the broad original roles:

- GitHub issue, branch, PR, review, CI, or merge readiness: **Forge**, not Vanguard.
- Running service, gateway, automation, recovery, or recurrence monitoring: **Sentry**, not Vanguard.
- Authorized dependency, configuration, container, code-security, or exposed-service audit: **Sentinel**, not Vanguard or Mythos.
- Document or note extraction into one canonical artifact and derivatives: **Archivist**, not Mythos or Hawkeye.
- Video brief, storyboard, shot list, animation, edit, render, caption, or delivery: **Director**, not Canvas or Vanguard.
- Music, song, lyrics, sound effects, soundtrack, stems, mix, master, or audio analysis: **Composer**, not Quill or Vanguard.
- Screenplay/adaptation, audiobook narration, transcript/captions, schema-first document extraction, or previsualization: load `war-room-specialist-cascade` and invoke one hidden niche worker behind its visible lead.
- Any novel or manuscript-scale genre project: **Quill**, which cascades to the matching standby genre writer.
- Short fiction, scenes, dialogue, roleplay, and general prose revision remain with **Quill**.
- Use Vanguard for general implementation only after these precedence rules do not match.

For mixed incidents, route unexpected windows, browser launches, screenshots,
or other visible UI symptoms to Hawkeye first. Route the resulting confirmed
test-harness, teardown, or code repair to Vanguard as a second handoff.

## Orchestration Workflow

1. State the requested outcome and the one ambiguity that affects routing.
2. Retrieve local evidence first; use web discovery only for current facts.
3. Use deterministic Agents-A1 routing. When evidence remains materially
   ambiguous, hand the reasoning problem to Vanguard or Mythos instead of
   widening this profile.
4. Route engineering to Vanguard, visual inspection to Hawkeye, evidence
   synthesis to Mythos, images to Canvas, video to Director, audio to Composer,
   short prose and manuscript intake to Quill; Quill alone selects a standby genre writer.
   For a supported production niche, use `war-room-specialist-cascade` and
   preserve the returned visible-lead ownership.
5. Apply Specialist Precedence before selecting a broad role.
6. Stop after a specialist-ready handoff; do not shadow the assigned role.

## Handoff Record

Record request, scope, evidence paths or URLs, key uncertainty, selected
specialist, reason for routing, and explicit non-goals.

## Stop Conditions

- Evidence is insufficient to choose between materially different scopes.
- The next action belongs to a specialist or requires external authorization.
- Unsupported model inference is the only support for a claim.

## Completion Gate

- [ ] Intent and non-goals are explicit
- [ ] Routing is supported by local or current evidence
- [ ] No specialist workflow was duplicated
- [ ] The handoff is short, testable, and names its owner
- [ ] Tool and source evidence, not unsupported inference, supports the route
