---
name: director-video-production
description: "Use when planning, producing, rendering, or validating a local video deliverable from a brief, source video, script, storyboard, or audio track. Routes narrative structure, technical animation, real-time visuals, and ffmpeg assembly while exposing missing runtimes before production starts."
version: 1.0.0
author: Hermes War Room
license: MIT
platforms: [macos]
metadata:
  hermes:
    bundle: true
    domain: director-video-production
    tags: [bundle, video, storyboard, animation, local-production]
    related_skills: [youtube-content, manim-video, ascii-video, touchdesigner-mcp, canvas-local-visual-production, war-room-specialist-cascade]
---

# Director Video Production

## Boundary

Own the production path from brief to inspected video artifact. Cover research
cuts, storyboards, shot lists, programmatic animation, real-time visuals,
audio/caption synchronization, and ffmpeg assembly. Do not claim generative
video, Manim, or TouchDesigner output when its runtime is absent.

## Routing Table

| Need | Primary skill | Deliverable |
|---|---|---|
| Extract structure from a source video | `youtube-content` | Transcript, chapters, source ledger |
| Technical or explanatory animation | `manim-video` | Scene plan, render, captions |
| Terminal or audio-reactive motion | `ascii-video` | Reproducible MP4/GIF |
| Real-time, GLSL, VJ, or installation visuals | `touchdesigner-mcp` | Verified network and capture |
| Short generative video or image-to-video proof | bundled LTX helper | Seeded MPS render |
| Transcript, subtitles, or caption draft | `war-room-specialist-cascade` | Hidden `caption` profile |
| Storyboard, animatic, blocking, or motion-risk proof | `war-room-specialist-cascade` | Hidden `previs` profile |

Use `ffmpeg` directly for assembly, muxing, captions, probes, thumbnails, and
format conversion. Route still-image generation to Canvas and visual QA to
Hawkeye instead of silently substituting their work.

## Installed LTX route

Preflight the approved isolated runtime before promising a render:

```bash
python "$HERMES_HOME/hermes-agent/skills/media/director-video-production/scripts/ltx_render.py" --preflight
```

Start with 384x256, 9 frames, and a fixed seed. Increase duration or resolution
only after that representative render passes. LTX is a heavyweight exclusive
job on this 64GB Mac: do not overlap it with ACE-Step, Cydonia, Qwen-VL, or a
second video render, and re-check memory pressure before scaling.

The Hermes config intentionally disables LTX's optional prompt enhancer. It
would add roughly 9GB of Florence/Llama weights and load Hugging Face repository
code with `trust_remote_code`; Director supplies a production-ready prompt
instead.

## Orchestration Workflow

1. Fix audience, duration, aspect ratio, frame rate, delivery format, source
   rights, accessibility requirements, and acceptance target.
2. Preflight every selected runtime with a version or health command. Record
   missing commands as blocked stages, not as completed capabilities.
3. Create `BRIEF.md`, `STORYBOARD.md`, `SHOT-LIST.md`, and a timeline ledger
   whose stable scene IDs bind narration, visuals, captions, music, and sources.
4. Render a low-cost representative scene before producing the full timeline.
5. Assemble through explicit ffmpeg commands. Preserve seeds, project files,
   source URLs, licenses, render settings, and checksums.
6. Open the final output, inspect representative frames, probe streams and
   duration, and verify caption/audio synchronization before delivery.
7. Use the hidden Caption or Previs worker only for its bounded stage; Director
   owns the timeline, integration, approval, and final delivery.

## Handoff Record

Carry brief path, timeline and scene IDs, source/license ledger, runtime
preflight, storyboard, render commands, seeds/settings, intermediate paths,
final path, duration, resolution, codecs, captions, checksums, and QA findings.

## Stop Conditions

- A required runtime, model, source asset, or license is missing.
- A model download, install, or route swap lacks explicit approval.
- Requested voice, likeness, copyrighted footage, or protected style lacks
  sufficient authority or transformation boundaries.
- Timing changes invalidate downstream audio or caption alignment.

## Completion Gate

- [ ] Requested format, resolution, duration, frame rate, and aspect ratio match
- [ ] Every scene maps to the shared timeline and source ledger
- [ ] Required runtimes passed preflight or are explicitly marked blocked
- [ ] Final streams and duration pass `ffprobe`
- [ ] Representative frames and the complete playback were inspected
- [ ] Captions, audio, credits, project files, and final artifact paths are listed
