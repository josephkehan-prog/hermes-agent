---
name: previsualization-production
description: "Use when turning a script or visual brief into a shot grammar, storyboard, animatic plan, concept trailer, camera blocking study, or low-cost LTX motion proof before full video production."
license: MIT
metadata:
  hermes:
    bundle: true
    domain: previsualization-production
    tags: [bundle, previs, storyboard, animatic, ltx]
    related_skills: [director-video-production, canvas-local-visual-production, hawkeye-visual-evidence]
---

# Previsualization Production

## Boundary

Resolve shot intent and motion risk before full production. Use Canvas for
boards, the approved LTX helper for short motion proofs, and Hawkeye for visual
inspection. Director owns the final timeline, edit, audio, captions, and delivery.

## Routing Table

| Stage | Skill | Output |
|---|---|---|
| Shot/timeline ownership and LTX proof | `director-video-production` | Reproducible motion plan/proof |
| Still boards and visual variants | `canvas-local-visual-production` | Seeded boards/contact sheet |
| Pixel inspection and continuity evidence | `hawkeye-visual-evidence` | Accept/reject observations |

## Orchestration Workflow

1. Lock the scene objective, emotional beat, duration, aspect ratio, and production constraints.
2. Build stable shot IDs with subject, framing, lens feel, camera move, blocking, duration, transition, and audio intent.
3. Produce cheap still boards first; inspect continuity and screen direction.
4. Select only high-risk motion shots for 384x256, 9-frame fixed-seed LTX proofs.
5. Compare proof against shot intent; record artifacts, continuity breaks, and production recommendation.
6. Assemble an animatic only after board order and rough timing are accepted.
7. Return shot ledger, boards, proof settings, contact sheet, timing, and risks to Director.

Read [references/shot-contract.md](references/shot-contract.md) for the required
shot-ledger fields.

## Handoff Record

Record scene/shot IDs, boards, prompt/seed/settings, motion-proof paths,
inspection evidence, timing, accepted/rejected decisions, production risks,
and next Director action.

## Stop Conditions

- Script/brief lacks a stable scene objective.
- A full-resolution render is requested before a representative proof.
- Voice, likeness, source asset, or style authority is unclear.
- Memory pressure is unsafe for an exclusive LTX job.

## Completion Gate

- [ ] Every board/proof maps to a stable shot ID
- [ ] Screen direction, eyelines, geography, and visual continuity were inspected
- [ ] LTX prompts, seeds, dimensions, and frames are reproducible
- [ ] Director receives accepted/rejected shots and explicit production risks
