---
title: "Concept Diagrams"
sidebar_label: "Concept Diagrams"
description: "Generate flat, minimal light/dark-aware SVG diagrams as standalone HTML files, using a unified educational visual language with 9 semantic color ramps, sente..."
---

{/* This page is auto-generated from the skill's SKILL.md by website/scripts/generate-skill-docs.py. Edit the source SKILL.md, not this page. */}

# Concept Diagrams

Generate flat, minimal light/dark-aware SVG diagrams as standalone HTML files, using a unified educational visual language with 9 semantic color ramps, sentence-case typography, and automatic dark mode. Best suited for educational and non-software visuals — physics setups, chemistry mechanisms, math curves, physical objects (aircraft, turbines, smartphones, mechanical watches), anatomy, floor plans, cross-sections, narrative journeys (lifecycle of X, process of Y), hub-spoke system integrations (smart city, IoT), and exploded layer views. If a more specialized skill exists for the subject (dedicated software/cloud architecture, hand-drawn sketches, animated explainers, etc.), prefer that — otherwise this skill can also serve as a general-purpose SVG diagram fallback with a clean educational look. Ships with 15 example diagrams.

## Skill metadata

| | |
|---|---|
| Source | Optional — install with `hermes skills install official/creative/concept-diagrams` |
| Path | `optional-skills/creative/concept-diagrams` |
| Version | `0.1.0` |
| Author | v1k22 (original PR), ported into hermes-agent |
| License | MIT |
| Platforms | linux, macos, windows |
| Tags | `diagrams`, `svg`, `visualization`, `education`, `physics`, `chemistry`, `engineering` |
| Related skills | [`architecture-diagram`](/docs/user-guide/skills/bundled/creative/creative-architecture-diagram), [`excalidraw`](/docs/user-guide/skills/bundled/creative/creative-excalidraw), `generative-widgets` |

## Reference: full SKILL.md

:::info
The following is the complete skill definition that Hermes loads when this skill is triggered. This is what the agent sees as instructions when the skill is active.
:::

# Concept Diagrams

Generate production-quality SVG diagrams with a unified flat, minimal design system. Output is a single self-contained HTML file that renders identically in any modern browser, with automatic light/dark mode.

## Scope

**Best suited for:**
- Physics setups, chemistry mechanisms, math curves, biology
- Physical objects (aircraft, turbines, smartphones, mechanical watches, cells)
- Anatomy, cross-sections, exploded layer views
- Floor plans, architectural conversions
- Narrative journeys (lifecycle of X, process of Y)
- Hub-spoke system integrations (smart city, IoT networks, electricity grids)
- Educational / textbook-style visuals in any domain
- Quantitative charts (grouped bars, energy profiles)

**Look elsewhere first for:**
- Dedicated software / cloud infrastructure architecture with a dark tech aesthetic (consider `architecture-diagram` if available)
- Hand-drawn whiteboard sketches (consider `excalidraw` if available)
- Animated explainers or video output (consider an animation skill)

If a more specialized skill is available for the subject, prefer that. If none fits, this skill can serve as a general-purpose SVG diagram fallback — the output will carry the clean educational aesthetic described below, which is a reasonable default for almost any subject.

## Workflow

1. Decide on the diagram type (see Diagram Types below).
2. Lay out components using the Design System rules.
3. Write the full HTML page using `templates/template.html` as the wrapper — paste your SVG where the template says `<!-- PASTE SVG HERE -->`.
4. Save as a standalone `.html` file (for example `~/my-diagram.html` or `./my-diagram.html`).
5. User opens it directly in a browser — no server, no dependencies.

Optional: if the user wants a browsable gallery of multiple diagrams, see "Local Preview Server" at the bottom.

Load the HTML template:
```
skill_view(name="concept-diagrams", file_path="templates/template.html")
```

The template embeds the full CSS design system (`c-*` color classes, text classes, light/dark variables, arrow marker styles). The SVG you generate relies on these classes being present on the hosting page.

---

## Design System

### Philosophy

- **Flat**: no gradients, drop shadows, blur, glow, or neon effects.
- **Minimal**: show the essential. No decorative icons inside boxes.
- **Consistent**: same colors, spacing, typography, and stroke widths across every diagram.
- **Dark-mode ready**: all colors auto-adapt via CSS classes — no per-mode SVG.

### Color Palette

9 color ramps, 2-3 per diagram, chosen by **meaning** not sequence: `c-gray`
for neutral/structural nodes; `c-purple`/`c-teal`/`c-coral`/`c-pink` for
general categories; `c-blue`/`c-green`/`c-amber`/`c-red` reserved for
semantic meaning (info/success/warning/error). Exact hex values per stop and
the light/dark stop mapping: read `references/design-system.md`.

### Typography

Only two font sizes — `th` (14px/500, titles/labels) and `ts` (12px/400,
subtitles/descriptions), plus `t` (14px/400, general text). **Sentence case
always**, never Title Case or ALL CAPS. Every `<text>` MUST carry one of
these classes, with `dominant-baseline="central"` and `text-anchor="middle"`
inside boxes. Width estimation formula and full spacing/stroke/rounding
numbers (viewbox, gaps, padding, `rx` values): read `references/design-system.md`.

### Arrow Marker & CSS Classes

Every SVG needs the same `<defs>` arrow-marker block and relies on template-
provided classes (`.t`/`.ts`/`.th`, `.box`/`.arr`/`.leader`/`.node`, `.c-*`
ramps) — you never redefine them, just apply them. Exact `<defs>` markup,
SVG boilerplate, and copy-paste node/connector/container patterns: read
`references/design-system.md`.

---

## Diagram Types

Choose the layout that fits the subject:

1. **Flowchart** — CI/CD pipelines, request lifecycles, approval workflows, data processing. Single-direction flow (top-down or left-right). Max 4-5 nodes per row.
2. **Structural / Containment** — Cloud infrastructure nesting, system architecture with layers. Large outer containers with inner regions. Dashed rects for logical groupings.
3. **API / Endpoint Map** — REST routes, GraphQL schemas. Tree from root, branching to resource groups, each containing endpoint nodes.
4. **Microservice Topology** — Service mesh, event-driven systems. Services as nodes, arrows for communication patterns, message queues between.
5. **Data Flow** — ETL pipelines, streaming architectures. Left-to-right flow from sources through processing to sinks.
6. **Physical / Structural** — Vehicles, buildings, hardware, anatomy. Use shapes that match the physical form — `<path>` for curved bodies, `<polygon>` for tapered shapes, `<ellipse>`/`<circle>` for cylindrical parts, nested `<rect>` for compartments. See `references/physical-shape-cookbook.md`.
7. **Infrastructure / Systems Integration** — Smart cities, IoT networks, multi-domain systems. Hub-spoke layout with central platform connecting subsystems. Semantic line styles (`.data-line`, `.power-line`, `.water-pipe`, `.road`). See `references/infrastructure-patterns.md`.
8. **UI / Dashboard Mockups** — Admin panels, monitoring dashboards. Screen frame with nested chart/gauge/indicator elements. See `references/dashboard-patterns.md`.

For physical, infrastructure, and dashboard diagrams, load the matching reference file before generating — each one provides ready-made CSS classes and shape primitives.

---

## Validation Checklist

Before finalizing any SVG, verify: every `<text>` is classed and correctly
anchored, every connector has `fill="none"`, no arrow crosses an unrelated
box, box widths fit their label text, viewBox height matches content, colors
carry meaning not sequence, and no gradients/shadows/glow effects exist. Full
12-point checklist with exact formulas: read `references/design-system.md`.

---

## Output & Preview

### Default: standalone HTML file

Write a single `.html` file the user can open directly. No server, no dependencies, works offline. Pattern:

```python
# 1. Load the template
template = skill_view("concept-diagrams", "templates/template.html")

# 2. Fill in title, subtitle, and paste your SVG
html = template.replace(
    "<!-- DIAGRAM TITLE HERE -->", "SN2 reaction mechanism"
).replace(
    "<!-- OPTIONAL SUBTITLE HERE -->", "Bimolecular nucleophilic substitution"
).replace(
    "<!-- PASTE SVG HERE -->", svg_content
)

# 3. Write to a user-chosen path (or ./ by default)
write_file("./sn2-mechanism.html", html)
```

Tell the user how to open it:

```
# macOS
open ./sn2-mechanism.html
# Linux
xdg-open ./sn2-mechanism.html
```

### Optional: local preview server (multi-diagram gallery)

Only use this when the user explicitly wants a browsable gallery of multiple diagrams.

**Rules:**
- Bind to `127.0.0.1` only. Never `0.0.0.0`. Exposing diagrams on all network interfaces is a security hazard on shared networks.
- Pick a free port (do NOT hard-code one) and tell the user the chosen URL.
- The server is optional and opt-in — prefer the standalone HTML file first.

Recommended pattern (lets the OS pick a free ephemeral port):

```bash
# Put each diagram in its own folder under .diagrams/
mkdir -p .diagrams/sn2-mechanism
# ...write .diagrams/sn2-mechanism/index.html...

# Serve on loopback only, free port
cd .diagrams && python3 -c "
import http.server, socketserver
with socketserver.TCPServer(('127.0.0.1', 0), http.server.SimpleHTTPRequestHandler) as s:
    print(f'Serving at http://127.0.0.1:{s.server_address[1]}/')
    s.serve_forever()
" &
```

If the user insists on a fixed port, use `127.0.0.1:<port>` — still never `0.0.0.0`. Document how to stop the server (`kill %1` or `pkill -f "http.server"`).

---

## Examples & Quick Reference

The `examples/` directory ships 15 complete, tested diagrams — browse them
for working patterns before writing a new diagram of a similar type. Load
one with `skill_view(name="concept-diagrams", file_path="examples/<filename>")`.

The full per-file index (which example demonstrates what) and a "user says →
diagram type → suggested colors" lookup table for quickly picking a layout:
read `references/examples-index.md`.
