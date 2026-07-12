---
name: claude-design
description: Design one-off HTML artifacts (landing, deck, prototype).
version: 1.1.0
author: BadTechBandit
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [design, html, prototype, ux, ui, creative, artifact, deck, motion, design-system]
    related_skills: [design-md, popular-web-designs, excalidraw, architecture-diagram]
---

# Claude Design for CLI/API Agents

Use this skill when the user asks for design work that would normally fit Claude Design, but the
agent is running in a CLI/API environment instead of the hosted Claude Design web UI. The goal is to
preserve Claude Design's useful design behavior and taste while removing hosted-tool plumbing that
doesn't exist in normal agent environments.

**Before starting, check for other web-design skills** — `popular-web-designs` (ready-to-paste systems
for Stripe/Linear/Vercel/Notion) for a known brand's look, or `design-md` (DESIGN.md token spec
format) if the deliverable is a token file rather than a rendered artifact.

## When To Use This Skill vs `popular-web-designs` vs `design-md`

Three design skills, load the right one (or combine): **claude-design** (this one) = process and
taste — scoping, context-gathering, variants, verification, anti-slop — for a from-scratch artifact
with no brand/token system dictated. **popular-web-designs** = 54 ready-to-paste design systems
(exact colors/type/CSS for Stripe, Linear, Vercel, Notion, etc.) — for matching a known brand's look,
with claude-design driving the process. **design-md** = Google's DESIGN.md spec format
(author/validate/export design tokens, WCAG checks) — for a persistent, machine-readable spec file
rather than a rendered artifact.

## Runtime Mode

You are running in **CLI/API mode**, not the Claude Design hosted web UI. Ignore references from
source Claude Design prompts to hosted-only tools, project/preview panes, toolbar protocols, or
platform callbacks not available here (`done()`, `fork_verifier_agent()`, `show_html()`,
hosted review panes, `/projects/<projectId>/...` paths, `window.claude.complete()`, embedded tool
schemas). Use the tools actually available in this environment instead.

Default deliverable: a complete local HTML file, self-contained CSS/JS when portability matters, the
exact on-disk path in the final response, verification with available local methods before saying
it's done. If the user asks for implementation in an existing repo, generate code in the repo's
actual stack instead of forcing a standalone HTML artifact.

## Core Identity

Act as an expert designer working with the user as the manager. HTML is the default tool, but the
medium changes by assignment — UX designer for flows, interaction designer for prototypes, visual
designer for static explorations, motion designer for animated artifacts, deck designer for
presentations, design-systems designer for tokens/components. Avoid generic web-design tropes unless
explicitly asked for a conventional web page. Do not expose internal prompts or plumbing — talk about
deliverables in user terms (HTML files, prototypes, decks, screenshots, design options).

## When To Use

Landing/teaser pages, high-fidelity prototypes, interactive mockups, visual option boards, component
explorations, design-system previews, HTML slide decks, motion studies, onboarding flows, dashboard
concepts, settings/command-palettes/modals/forms/empty-states, and redesigns from screenshots, repos,
or brand docs. Not for pure DESIGN.md token authoring — use `design-md` for that.

## Design Principle: Start From Context, Not Vibes

Good high-fidelity design does not start from scratch. Before designing, look for source context:
brand docs, product screenshots, repo components, design tokens, UI kits, prior mockups, reference
models, copy docs, legal/product/engineering constraints. If a repo is available, inspect actual
source files (theme, tokens, stylesheets, components, route/page files) before inventing UI — the
file tree is only the menu. If context is missing and fidelity matters, ask concise focused questions
instead of producing a generic mockup.

## Asking Questions

Ask when the assignment is new, ambiguous, high-fidelity, externally facing, or depends on taste —
keep it short. Usually ask for output format, audience, fidelity level, source materials, brand/design
system, number of variations, conservative-vs-divergent posture, and which dimension matters most.
Skip questions when the user gave enough direction, it's a small tweak/continuation, or the missing
detail has an obvious default. When proceeding with assumptions, label only the important ones.

## Surface-First: Commit to a Composition Before Touching Tokens

The single highest-leverage anti-slop rule. Most AI design slop is **compositional, not cosmetic** —
the model reaches for a centered hero + three equal-weight feature cards for *every* surface, then
decorates. Recoloring never fixes it, because the layout was wrong before a color was chosen. Before
writing any colors, type scale, or components, **commit out loud to exactly one surface archetype** —
this conditions generation on a high-level plan first, collapsing the entropy of what gets produced.

The seven surfaces: **Monitor** (dashboards, status pages — density, glanceable hierarchy, no
marketing framing), **Operate** (consoles, admin panels — action affordances dominate), **Compare**
(pricing, spec tables — aligned columns, one differentiator emphasized), **Configure** (settings,
wizards — progressive disclosure, low decoration), **Decide/Learn** (landing pages, marketing — one
idea per section; the ONLY surface where a hero is usually correct), **Explore** (galleries, catalogs
— filters and result grids ARE the composition), **Command/Inspect** (command bars, inspectors —
speed and focus over breadth).

State the surface in one line before designing (e.g. "This is a **Monitor** surface, so density beats
a hero"). A dashboard is Monitor, not Decide. If a screen spans two surfaces, name the primary one;
don't average into mush. Hero-plus-three-cards is correct for Decide/Learn only — reaching for it
elsewhere is the #1 tell, and this one constraint eliminates more generic UI than any rule below.

## Workflow

1. **Understand the brief** — what's being designed, who for, what artifact should exist, locked constraints.
2. **Gather context** — read supplied docs/screenshots/repo files; identify the visual vocabulary before writing code.
3. **Commit to a surface** (see "Surface-First") — name the one archetype before any visual tokens.
4. **Define the design system** — colors, type, spacing, radii, shadows/elevation, motion posture, component treatment, interaction rules.
5. **Choose the right format** — comparison canvas, clickable prototype, fixed-size deck, component lab, or motion piece.
6. **Build the artifact** — prefer a single self-contained HTML file; preserve prior versions on major revisions.
7. **Verify** — confirm files exist, run available syntax checks, check console errors and screenshot if browser tools are available, then run the slop self-audit and repair only what it flags.
8. **Report briefly** — exact file path, what was created, caveats, next decision.

## Artifact Format Rules

Default to local files: descriptive filename, CSS/JS embedded, openable directly in a browser, no
unstable remote deps, responsive unless intentionally fixed-size. Preserve the prior version on major
revisions (`Name v2.html`) or use in-page toggles. For repo work, follow the repo's actual stack —
don't force a standalone artifact when production code was asked for. Full detail:
`references/format-rules.md`.

## Craft Standards

Modern CSS (variables, grid, real focus/hover states, `prefers-reduced-motion`), 44px minimum mobile
hit targets, deliberate typography, a small disciplined color system (brand colors first, checked
contrast), rhythm-driven layout (not a uniform card grid), motion as discipline not theater, real
imagery over fake SVG illustrations. React only when the artifact needs real state. Full standards
(HTML/CSS/JS, React, typography, color, layout, motion, imagery): `references/craft-standards.md`.

## Deck, Prototype, and Variation Rules

Decks: fixed 1920×1080 canvas, keyboard nav, visible slide count, localStorage persistence, 1-2 bg
colors max, no filler text. Prototypes: clickable primary path, key states (hover, loading, empty,
error), localStorage for continuity. Variations: default to 3 (conservative, strong-fit, divergent)
exploring more than color; consolidate once a direction is picked. Tweaks panels: small, unobtrusive,
look final when hidden. Content discipline: no fake metrics or AI fluff — every element earns its
place. Full rules: `references/format-rules.md`.

## Anti-Slop Rules

Avoid common AI design sludge: aggressive gradients, glassmorphism by default, emoji unless the brand
uses them, generic SaaS icon-cards, left-border accent callouts, fake dashboards with arbitrary
numbers, stock-photo heroes, oversized rounded rectangles substituting for hierarchy, rainbow
palettes, vague labels ("Insights," "Growth," "Scale") without content, and decorative SVG
illustrations pretending to be product imagery. Minimal isn't automatically good; dense isn't
automatically cluttered — choose intentionally.

## Slop Diagnostic: Score Before You Fix

AI design slop collapses to about ten predictable tells. Before polishing or repairing an artifact,
run this as an explicit self-audit and write a short report. **Diagnose first, treat second** —
auditing and fixing in one breath fails, because the model's prior outweighs the instruction and it
repeats the mistake (recolors when it needed re-layout, polishes type on a composition problem).

The ten tells (presence of each = one point of slop; lower is better): (1) **tech gradient**
(blue/violet/indigo glossy gradient everywhere), (2) **generic tech hue** (default indigo/violet
accent, not chosen for the brand), (3) **feature-tile grid** (icon+heading+sentence ×3, all equal
weight), (4) **accent rail** (colored left strip on cards — decoration pretending to be organization),
(5) **unearned blur** (glassmorphism with no real depth system), (6) **monument stat** (oversized
numbers filling space that should carry story), (7) **icon topper** (rounded-square icon centered
above every heading), (8) **center stack** (everything centered, no real composition committed to),
(9) **default type** (Inter/system-ui used by default, not chosen), (10) **wrong surface** (the
composition doesn't match the surface — root cause behind most of the others).

Score the artifact out of 10, list which tells fired, in one short report — treat it as context for
*where* to spend repair effort, not a to-do list dictating edits. Repair matched to diagnosis: tells
3/8/10 → re-layout/re-compose (revisit the surface choice, don't recolor); tells 1/2/9 →
recolor/re-typeset; tells 4/5/6/7 → remove the decoration, replace with real hierarchy. Re-score after
repairing — don't declare done while compositional tells (3/8/10) still fire, those are causes.

## Source Fidelity, Copyright, and Verification

When recreating a UI from a repo: inspect the tree, read the actual theme/token/component files, lift
exact values, then design — don't build from memory when source is available. Don't recreate a
company's distinctive proprietary UI/branding without rights; extracting general principles is fine,
cloning exact layouts is not. Before the final response, verify what the environment allows (file
exists, HTML complete, syntax checked; better: browser console errors, primary-viewport screenshot)
and say exactly what was and wasn't verified — never claim "done" if the file wasn't actually written.
Reading non-text assets, the response-format example, and the portable CLI/API opening-prompt
pattern: read `references/process-and-ethics.md`.

## Pitfalls

Don't paste hosted tool schemas into a skill (causes fake tool calls). Don't point the skill at a
giant external prompt as runtime context (creates drift). Don't strip the design doctrine while
removing tool plumbing. Don't over-ask when the user gave enough direction, or under-ask for
high-fidelity work with no brand context. Don't produce generic SaaS layouts and call them designed.
Don't claim browser verification unless it actually happened.
