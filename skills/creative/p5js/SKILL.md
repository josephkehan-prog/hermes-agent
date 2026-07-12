---
name: p5js
description: "p5.js sketches: gen art, shaders, interactive, 3D."
version: 1.0.0
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [creative-coding, generative-art, p5js, canvas, interactive, visualization, webgl, shaders, animation]
    related_skills: [ascii-video, manim-video, excalidraw]
---

# p5.js Production Pipeline

## When to use

Use when users request p5.js sketches, creative coding, generative art, interactive visualizations, canvas animations, browser-based visual art, data viz, or shader effects.

## What's inside

Production pipeline for interactive and generative visual art using p5.js:
sketches, generative art, data viz, interactive experiences, 3D scenes,
audio-reactive visuals, motion graphics — exported as HTML, PNG, GIF, MP4,
or SVG. Covers 2D/3D rendering, noise/particle systems, GLSL shaders, pixel
manipulation, kinetic typography, audio analysis, interaction, headless export.

## Creative Standard

This is visual art rendered in the browser — the canvas is the medium, the
algorithm is the brush. **Before writing a single line of code**, articulate
the creative concept: what does this piece communicate, what makes the
viewer stop scrolling, what separates it from a tutorial example. Treat the
user's prompt as a starting point, not a spec.

**First-render excellence is non-negotiable** — the output must be visually
striking on first load. If it looks like a tutorial exercise, a default
configuration, or "AI-generated creative coding," rethink before shipping.
**Go beyond the reference vocabulary**: the noise functions, particle
systems, palettes, and shader effects in the references are a starting
vocabulary to combine, layer, and invent from, not a menu to pick one item
from. **Be proactively creative** — a requested "particle system" should
ship with emergent flocking, trailing ghost echoes, palette-shifted depth
fog, and a breathing background noise field: at least one detail the user
didn't ask for but will appreciate. **Dense, layered, considered**: every
frame should reward viewing — no flat backgrounds, always compositional
hierarchy, intentional color, micro-detail on close inspection.
**Cohesive aesthetic over feature count**: all elements share a unified
visual language (color temperature, stroke weight vocabulary, motion
speeds) — three effects that belong together beat ten that don't.

## Modes

| Mode | Output | Reference |
|------|--------|-----------|
| **Generative art** | Procedural composition (still/animated) from seed/parameters | `references/visual-effects.md` |
| **Data visualization** | Interactive charts/graphs from dataset/API | `references/interaction.md` |
| **Interactive experience** | Mouse/keyboard/touch-driven sketch | `references/interaction.md` |
| **Animation / motion graphics** | Timed sequences, kinetic typography | `references/animation.md` |
| **3D scene** | WebGL geometry, lighting, camera, materials | `references/webgl-and-3d.md` |
| **Image processing** | Pixel manipulation, filters, mosaic, pointillism | `references/visual-effects.md` § Pixel Manipulation |
| **Audio-reactive** | Sound-driven generative visuals | `references/interaction.md` § Audio Input |

## Stack

Single self-contained HTML file per project. No build step required.

| Layer | Tool | Purpose |
|-------|------|---------|
| Core | p5.js 1.11.3 (CDN) | Canvas rendering, math, transforms, event handling |
| 3D | p5.js WebGL mode | 3D geometry, camera, lighting, GLSL shaders |
| Audio | p5.sound.js (CDN) | FFT analysis, amplitude, mic input, oscillators |
| Export | Built-in `saveCanvas()`/`saveGif()`/`saveFrames()` | PNG, GIF, frame sequence output |
| Capture | CCapture.js (optional) | Deterministic framerate video capture (WebM, GIF) |
| Headless | Puppeteer + Node.js (optional) | Automated high-res rendering, MP4 via ffmpeg |
| SVG | p5.js-svg 1.6.0 (optional) | Vector output for print — requires p5.js 1.x |
| Natural media | p5.brush (optional) | Watercolor, charcoal, pen — requires p5.js 2.x + WEBGL |
| Texture | p5.grain (optional) | Film grain, texture overlays |
| Fonts | Google Fonts / `loadFont()` | Custom typography via OTF/TTF/WOFF2 |

### Version Note

**p5.js 1.x** (1.11.3) is the default — stable, well-documented, broadest
compatibility; use unless a project needs 2.x features. **p5.js 2.x** (2.2+)
adds `async setup()`, OKLCH/OKLAB color, `splineVertex()`, shader `.modify()`,
variable fonts, `textToContours()`, pointer events, and is required for
p5.brush. See `references/core-api.md` § p5.js 2.0.

## Pipeline

`CONCEPT → DESIGN → CODE → PREVIEW → EXPORT → VERIFY` (Workflow Steps 1-6 below).

## Creative Direction

### Aesthetic Dimensions

Vary deliberately across color system, noise vocabulary, particle systems,
shape language, motion style, typography, shader effects, composition,
interaction model, blend modes, layering, and texture — never settle for
just one. See the References table below for which file covers each
dimension.

### Per-Project Variation Rules & Parameter Design

Never use default configurations — every project needs a designed color
palette, a stroke weight vocabulary, a non-flat background treatment, motion
speed variety across elements, and at least one invented element. Tunable
parameters should expose the algorithm's character (quantities, scales,
rates, thresholds, ratios), not generic cosmetic sliders. Full rules and the
good-vs-bad parameter examples: read `references/creative-direction.md`.

## Workflow

### Step 1: Creative Vision

Before any code, articulate mood/atmosphere, visual story (build/decay/
transform/oscillate), color world, shape language, motion vocabulary, and
what makes THIS sketch different. Map the prompt to aesthetic choices — "a
relaxing generative background" demands different everything from "glitch
data visualization."

### Step 2: Technical Design

Decide mode (from the 7 above), canvas size (1920x1080 landscape, 1080x1920
portrait, 1080x1080 square, or responsive), renderer (`P2D` default or
`WEBGL` for 3D/shaders), frame rate (60fps interactive, 30fps ambient, or
`noLoop()` static), export target, and interaction model. For viewer UI,
start from `templates/viewer.html` for interactive generative art (seed nav,
sliders, download), or bare HTML for simple sketches/video export.

### Step 3: Code the Sketch

For **interactive generative art** (seed exploration, parameter tuning):
start from `templates/viewer.html`. Read it first, keep the fixed sections
(seed nav, actions), replace the algorithm and parameter controls — this
gives seed prev/next/random/jump, live parameter sliders, and PNG download,
all wired up.

For **animations, video export, or simple sketches**: use bare HTML — a
single self-contained file with the standard structure (globals → CONFIG/PALETTE
→ `preload()` → `setup()` → `draw()` → helpers → classes → event handlers).
The full boilerplate template with CDN script tags, seeded randomness,
HSB color mode, and state separation: read `references/core-api.md` §
Standard Single-File Sketch Boilerplate.

### Step 4: Preview & Iterate

Open the HTML file in the browser (local assets need `scripts/serve.sh` or
`python3 -m http.server`). Verify 60fps in DevTools, test at target export
resolution, adjust parameters until it matches the Step 1 concept.

### Step 5: Export

PNG: `saveCanvas('output', 'png')` in `keyPressed()` (press 's'). High-res
PNG: `node scripts/export-frames.js sketch.html --width 3840 --height 2160
--frames 1`. GIF: `saveGif('output', 5)` (press 'g'). Frame sequence:
`saveFrames('frame', 'png', 10, 30)` then `ffmpeg -i frame-%04d.png -c:v
libx264 output.mp4`. MP4: `bash scripts/render.sh sketch.html output.mp4
--duration 30 --fps 30`. SVG: `createCanvas(w, h, SVG)` with p5.js-svg,
`save('output.svg')`.

### Step 6: Quality Verification

Compare output to the concept (generic → back to Step 1); check resolution
sharpness, no aliasing; check 60fps holds (30fps min for animations); check
colors on both light and dark monitors; check edge cases (canvas edges,
resize, after 10 minutes running).

## Critical Implementation Notes

Every production sketch needs these from the first line, not bolted on
after: disable FES (`p5.disableFriendlyErrors = true`, 10x overhead
otherwise), always seed with `randomSeed()`/`noiseSeed()`, use
`colorMode(HSB, 360, 100, 100, 100)` not raw RGB, layer noise octaves
(`fbm()`) not raw `noise()`, use `createGraphics()` offscreen buffers for
layered composition, vectorize particle rendering for thousands of
elements, use instance mode for multi-sketch pages, mind WebGL's
center-origin/inverted-Y system, wire up `keyPressed()` export shortcuts,
and use `noLoop()` + `_p5Ready` for headless capture.

Full code for every pattern above: read `references/implementation-notes.md`
before writing sketch code, not just when something breaks.

### Agent Workflow

Write the single self-contained HTML file → open in browser (`open
sketch.html` macOS / `xdg-open` Linux; local assets need `python3 -m
http.server 8080`) → add `keyPressed()` export shortcuts, tell the user
which key to press → headless export via `node scripts/export-frames.js
sketch.html --frames 300` (needs `noLoop()` + `_p5Ready`) → MP4 via `bash
scripts/render.sh sketch.html output.mp4 --duration 30` → iterate by
editing and refreshing → load references on demand via
`skill_view(name="p5js", file_path="references/...")`.

## Performance Targets

Frame rate: 60fps sustained (interactive), 30fps minimum (animated export).
Particle count at 60fps: 5,000-10,000 (P2D shapes), 50,000-100,000 (pixel
buffer). Canvas resolution: up to 3840x2160 export, 1920x1080 interactive.
File size: <100KB HTML (excluding CDN libs). Load time: <2s to first frame.

## References

| File | Contents |
|------|----------|
| `references/core-api.md` | Canvas setup, coordinate system, draw loop, offscreen buffers, composition, `pixelDensity()`, responsive design, sketch boilerplate |
| `references/shapes-and-geometry.md` | 2D primitives, `beginShape()`/`endShape()`, Bezier/Catmull-Rom curves, `p5.Vector`, signed distance fields, SVG path conversion |
| `references/visual-effects.md` | Noise (Perlin, fractal, domain warp, curl), flow fields, particle systems, pixel manipulation, texture generation, feedback loops |
| `references/animation.md` | Frame-based animation, easing, `lerp()`/`map()`, spring physics, state machines, timeline sequencing, transitions |
| `references/typography.md` | `text()`, `loadFont()`, `textToPoints()`, kinetic typography, text masks, font metrics |
| `references/color-systems.md` | `colorMode()`, HSB/HSL/RGB, `lerpColor()`, procedural palettes, color harmony, `blendMode()`, curated palette library |
| `references/webgl-and-3d.md` | WEBGL renderer, 3D primitives, camera, lighting, materials, GLSL shaders, framebuffers, post-processing |
| `references/interaction.md` | Mouse/keyboard/touch events, DOM elements, audio input (FFT/amplitude), scroll-driven animation |
| `references/export-pipeline.md` | `saveCanvas()`/`saveGif()`/`saveFrames()`, deterministic headless capture, ffmpeg, SVG export, platform export (fxhash) |
| `references/troubleshooting.md` | Performance profiling, common mistakes, browser compatibility, WebGL debugging, memory leaks, CORS |
| `references/implementation-notes.md` | Full code for every "Critical Implementation Notes" pattern above |
| `references/creative-divergence.md` | Full step-by-step for Creative Divergence strategies |
| `references/creative-direction.md` | Full per-project variation rules and parameter design examples |
| `templates/viewer.html` | Interactive viewer template: seed navigation, parameter sliders, download PNG. Start from this for explorable generative art |

---

## Creative Divergence (use only when user requests experimental/creative/unique output)

When the user asks for creative, experimental, surprising, or unconventional
output, select a strategy and reason through its steps BEFORE generating
code: **Conceptual Blending** (user names two things to combine), **SCAMPER**
(twist on a known generative art pattern), or **Distance Association** (user
gives one concept and wants exploration, e.g. "make something about time").
Full step-by-step for each strategy: read `references/creative-divergence.md`.
