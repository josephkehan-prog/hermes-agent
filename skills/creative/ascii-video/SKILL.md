---
name: ascii-video
description: "ASCII video: convert video/audio to colored ASCII MP4/GIF."
platforms: [linux, macos, windows]
---

# ASCII Video Production Pipeline

## When to use

Use when users request: ASCII video, text art video, terminal-style video, character art animation, retro text visualization, audio visualizer in ASCII, converting video to ASCII art, matrix-style effects, or any animated ASCII output.

## What's inside

Production pipeline for ASCII art video — any format. Converts video/audio/images/generative input into colored ASCII character video output (MP4, GIF, image sequence). Covers: video-to-ASCII conversion, audio-reactive music visualizers, generative ASCII art animations, hybrid video+audio reactive, text/lyrics overlays, real-time terminal rendering.

## Creative Standard

This is visual art. ASCII characters are the medium; cinema is the standard.

**Before writing a single line of code**, articulate the creative concept. What is the mood? What visual story does this tell? What makes THIS project different from every other ASCII video? The user's prompt is a starting point — interpret it with creative ambition, not literal transcription.

**First-render excellence is non-negotiable.** The output must be visually striking without requiring revision rounds. If something looks generic, flat, or like "AI-generated ASCII art," it is wrong — rethink the creative concept before shipping.

**Go beyond the reference vocabulary.** The effect catalogs, shader presets, and palette libraries in the references are a starting vocabulary. For every project, combine, modify, and invent new patterns. The catalog is a palette of paints — you write the painting.

**Be proactively creative.** Extend the skill's vocabulary when the project calls for it. If the references don't have what the vision demands, build it. Include at least one visual moment the user didn't ask for but will appreciate — a transition, an effect, a color choice that elevates the whole piece.

**Cohesive aesthetic over technical correctness.** All scenes in a video must feel connected by a unifying visual language — shared color temperature, related character palettes, consistent motion vocabulary. A technically correct video where every scene uses a random different effect is an aesthetic failure.

**Dense, layered, considered.** Every frame should reward viewing. Never flat black backgrounds. Always multi-grid composition. Always per-scene variation. Always intentional color.

## Modes

| Mode | Input | Output | Reference |
|------|-------|--------|-----------|
| **Video-to-ASCII** | Video file | ASCII recreation of source footage | `references/inputs.md` § Video Sampling |
| **Audio-reactive** | Audio file | Generative visuals driven by audio features | `references/inputs.md` § Audio Analysis |
| **Generative** | None (or seed params) | Procedural ASCII animation | `references/effects.md` |
| **Hybrid** | Video + audio | ASCII video with audio-reactive overlays | Both input refs |
| **Lyrics/text** | Audio + text/SRT | Timed text with visual effects | `references/inputs.md` § Text/Lyrics |
| **TTS narration** | Text quotes + TTS API | Narrated testimonial/quote video with typed text | `references/inputs.md` § TTS Integration |

## Stack

Single self-contained Python script per project. No GPU required.

| Layer | Tool | Purpose |
|-------|------|---------|
| Core | Python 3.10+, NumPy | Math, array ops, vectorized effects |
| Signal | SciPy | FFT, peak detection (audio modes) |
| Imaging | Pillow (PIL) | Font rasterization, frame decoding, image I/O |
| Video I/O | ffmpeg (CLI) | Decode input, encode output, mux audio |
| Parallel | concurrent.futures | N workers for batch/clip rendering |
| TTS | ElevenLabs API (optional) | Generate narration clips |
| Optional | OpenCV | Video frame sampling, edge detection |

## Pipeline Architecture

Every mode follows the same 6-stage pipeline:

```
INPUT → ANALYZE → SCENE_FN → TONEMAP → SHADE → ENCODE
```

1. **INPUT** — Load/decode source material (video frames, audio samples, images, or nothing)
2. **ANALYZE** — Extract per-frame features (audio bands, video luminance/edges, motion vectors)
3. **SCENE_FN** — Scene function renders to pixel canvas (`uint8 H,W,3`). Composes multiple character grids via `_render_vf()` + pixel blend modes. See `references/composition.md`
4. **TONEMAP** — Percentile-based adaptive brightness normalization. See `references/composition.md` § Adaptive Tonemap
5. **SHADE** — Post-processing via `ShaderChain` + `FeedbackBuffer`. See `references/shaders.md`
6. **ENCODE** — Pipe raw RGB frames to ffmpeg for H.264/GIF encoding

## Creative Direction

### Aesthetic Dimensions

The full matrix of creative choices (character palette, color strategy, background texture, primary effects, particles, shader mood, grid density, coordinate space, feedback, masking, transitions) with per-dimension reference pointers: read `references/architecture.md` § Aesthetic Dimensions Matrix when making Step 2 technical/creative decisions.

### Per-Section Variation

Never use the same config for the entire video. For each section/scene:
- **Different background effect** (or compose 2-3)
- **Different character palette** (match the mood)
- **Different color strategy** (or at minimum a different hue)
- **Vary shader intensity** (more bloom during peaks, more grain during quiet)
- **Different particle types** if particles are active

### Project-Specific Invention

For every project, invent at least one of:
- A custom character palette matching the theme
- A custom background effect (combine/modify existing building blocks)
- A custom color palette (discrete RGB set matching the brand/mood)
- A custom particle character set
- A novel scene transition or visual moment

Don't just pick from the catalog. The catalog is vocabulary — you write the poem.

## Workflow

### Step 1: Creative Vision

Before any code, articulate the creative concept:

- **Mood/atmosphere**: What should the viewer feel? Energetic, meditative, chaotic, elegant, ominous?
- **Visual story**: What happens over the duration? Build tension? Transform? Dissolve?
- **Color world**: Warm/cool? Monochrome? Neon? Earth tones? What's the dominant hue?
- **Character texture**: Dense data? Sparse stars? Organic dots? Geometric blocks?
- **What makes THIS different**: What's the one thing that makes this project unique?
- **Emotional arc**: How do scenes progress? Open with energy, build to climax, resolve?

Map the user's prompt to aesthetic choices. A "chill lo-fi visualizer" demands different everything from a "glitch cyberpunk data stream."

### Step 2: Technical Design

- **Mode** — which of the 6 modes above
- **Resolution** — landscape 1920x1080 (default), portrait 1080x1920, square 1080x1080 @ 24fps
- **Hardware detection** — auto-detect cores/RAM, set quality profile. See `references/optimization.md`
- **Sections** — map timestamps to scene functions, each with its own effect/palette/color/shader config
- **Output format** — MP4 (default), GIF (640x360 @ 15fps), PNG sequence

### Step 3: Build the Script

Single Python file, built in this order: hardware detection + quality profile (`references/optimization.md`) → input loader, mode-dependent (`references/inputs.md`) → feature analyzer (audio FFT / video luminance / synthetic) → grid + renderer with bitmap cache (`references/architecture.md`) → character palettes + color system, HSV/RGB/harmony (`references/architecture.md` § Palettes, § Color) → scene functions each returning `canvas (uint8 H,W,3)` (`references/scenes.md`) → tonemap (`references/composition.md`) → shader pipeline, `ShaderChain` + `FeedbackBuffer` (`references/shaders.md`) → scene table + dispatcher (`references/scenes.md`) → parallel encoder, N-worker clip rendering with ffmpeg pipes → main orchestration.

### Step 4: Quality Verification

- **Test frames first**: render single frames at key timestamps before full render
- **Brightness check**: `canvas.mean() > 8` for all ASCII content. If dark, lower gamma
- **Visual coherence**: do all scenes feel like they belong to the same video?
- **Creative vision check**: does the output match the concept from Step 1? If it looks generic, go back

## Critical Implementation Notes

Five recurring failure modes, each with full explanation/code in the linked reference:

- **Brightness — use `tonemap()`, not linear multipliers.** This is the #1 visual issue: ASCII on black is inherently dark, and `canvas * N` clips highlights. Pipeline is `scene_fn() → tonemap() → FeedbackBuffer → ShaderChain → ffmpeg`; per-scene gamma defaults to 0.75 (solarize 0.55, posterize 0.50, bright scenes 0.85), `screen` blend for dark layers. Full `tonemap()` implementation: `references/composition.md` § The `tonemap()` Function.
- **Font cell height** — macOS Pillow's `textbbox()` returns the wrong height; use `font.getmetrics()` (`ascent + descent`). See `references/troubleshooting.md` § Font Issues.
- **ffmpeg pipe deadlock** — never `stderr=subprocess.PIPE` with long-running ffmpeg (buffer fills at 64KB and deadlocks); redirect to file. See `references/troubleshooting.md` § ffmpeg Issues.
- **Font compatibility** — not all Unicode chars render in all fonts; validate palettes at init by rendering each char and checking for blank output. See `references/troubleshooting.md` § Font Issues.
- **Per-clip architecture** — for segmented videos (quotes, scenes, chapters), render each as a separate clip file for parallel rendering and selective re-rendering. See `references/scenes.md`.

## Performance Targets

Total budget ~100-200ms/frame (character render is the bottleneck at 80-150ms). Full per-component budget table and optimization techniques: `references/optimization.md` § Performance Budget.

## References

| File | Contents |
|------|----------|
| `references/architecture.md` | Grid system, resolution presets, font selection, character palettes (20+), color system (HSV + OKLAB + discrete RGB + harmony generation), `_render_vf()` helper, GridLayer class |
| `references/composition.md` | Pixel blend modes (20 modes), `blend_canvas()`, multi-grid composition, adaptive `tonemap()`, `FeedbackBuffer`, `PixelBlendStack`, masking/stencil system |
| `references/effects.md` | Effect building blocks: value field generators, hue fields, noise/fBM/domain warp, voronoi, reaction-diffusion, cellular automata, SDFs, strange attractors, particle systems, coordinate transforms, temporal coherence |
| `references/shaders.md` | `ShaderChain`, `_apply_shader_step()` dispatch, 38 shader catalog, audio-reactive scaling, transitions, tint presets, output format encoding, terminal rendering |
| `references/scenes.md` | Scene protocol, `Renderer` class, `SCENES` table, `render_clip()`, beat-synced cutting, parallel rendering, design patterns (layer hierarchy, directional arcs, visual metaphors, compositional techniques), complete scene examples at every complexity level, scene design checklist |
| `references/inputs.md` | Audio analysis (FFT, bands, beats), video sampling, image conversion, text/lyrics, TTS integration (ElevenLabs, voice assignment, audio mixing) |
| `references/optimization.md` | Hardware detection, quality profiles, vectorized patterns, parallel rendering, memory management, performance budgets |
| `references/troubleshooting.md` | NumPy broadcasting traps, blend mode pitfalls, multiprocessing/pickling, brightness diagnostics, ffmpeg issues, font problems, common mistakes |
| `references/creative-divergence.md` | Forced Connections, Conceptual Blending, Oblique Strategies — lateral-thinking strategies for experimental/creative requests |

---

## Creative Divergence

If the user asks for creative, experimental, surprising, or unconventional output, run one of three lateral-thinking strategies (Forced Connections, Conceptual Blending, Oblique Strategies) before generating code: read `references/creative-divergence.md`.
