---
title: "Creative Production Bundle"
sidebar_label: "Creative Production Bundle"
description: "Use when turning a creative brief into a coherent visual concept, design system, interface direction, diagram, or generative artifact across multiple media"
---

{/* This page is auto-generated from the skill's SKILL.md by website/scripts/generate-skill-docs.py. Edit the source SKILL.md, not this page. */}

# Creative Production Bundle

Use when turning a creative brief into a coherent visual concept, design system, interface direction, diagram, or generative artifact across multiple media. Routes concept, style, structure, and production without flattening them into one generic design pass.

## Skill metadata

| | |
|---|---|
| Source | Bundled (installed by default) |
| Path | `skills/creative/creative-production-bundle` |
| Version | `1.0.0` |
| Author | Hermes Agent |
| License | MIT |
| Platforms | linux, macos, windows |
| Tags | `bundle`, `creative`, `design`, `visual-production` |
| Related skills | [`design-md`](/docs/user-guide/skills/bundled/creative/creative-design-md), [`claude-design`](/docs/user-guide/skills/bundled/creative/creative-claude-design), [`popular-web-designs`](/docs/user-guide/skills/bundled/creative/creative-popular-web-designs), [`excalidraw`](/docs/user-guide/skills/bundled/creative/creative-excalidraw), [`architecture-diagram`](/docs/user-guide/skills/bundled/creative/creative-architecture-diagram), [`p5js`](/docs/user-guide/skills/bundled/creative/creative-p5js) |

## Reference: full SKILL.md

:::info
The following is the complete skill definition that Hermes loads when this skill is triggered. This is what the agent sees as instructions when the skill is active.
:::

# Creative Production Bundle

## Boundary

Coordinate creative work that needs concept direction plus one or more visual
production modes. Do not use for a tiny styling correction or a request already
bound to one exact artifact skill.

## Routing Table

| Need | Primary skill | Deliverable |
|---|---|---|
| Encode a reusable design language | `design-md` | Explicit tokens, rules, and visual grammar |
| Shape a distinctive interface direction | `claude-design` | Intentional UI composition and interaction |
| Adapt a recognizable web pattern | `popular-web-designs` | Pattern-grounded layout without imitation |
| Explore or communicate spatial ideas | `excalidraw` | Editable sketch or explanatory scene |
| Explain system structure | `architecture-diagram` | Semantically accurate technical diagram |
| Produce interactive generative art | `p5js` | Deterministic, parameterized visual artifact |

## Orchestration Workflow

1. Convert the brief into audience, message, medium, constraints, references,
   and one deliberate aesthetic thesis.
2. Select one direction-setting member and only the production members needed
   for requested artifacts.
3. Establish shared typography, color, spacing, imagery, and motion principles
   before producing multiple surfaces.
4. Build the smallest representative artifact first; review hierarchy,
   legibility, and coherence before expanding.
5. Render or run every final artifact in its actual medium and revise visible
   defects rather than judging source alone.

## Handoff Record

Carry the brief, aesthetic thesis, chosen member skills, design tokens,
artifact paths, render screenshots, accessibility observations, and deviations
from the brief. Record why each medium was selected.

## Stop Conditions

- The brief lacks a required brand asset or user-owned reference.
- The request asks to copy a protected work or living artist too closely.
- A technical diagram cannot be made accurate from available architecture.
- The output medium or dimensions remain materially ambiguous.

## Completion Gate

- [ ] Every artifact expresses the same intentional visual thesis
- [ ] Information hierarchy and medium-specific usability are verified
- [ ] Technical visuals are semantically accurate
- [ ] Interactive or generative outputs run deterministically where required
- [ ] Rendered output was inspected at target size
- [ ] Deliverable paths and known limitations are recorded

## Common Pitfalls

- Combining unrelated styles instead of choosing one thesis
- Using a website pattern as a pixel-for-pixel template
- Decorating a diagram before validating relationships
- Shipping unrendered source with hidden layout failures
