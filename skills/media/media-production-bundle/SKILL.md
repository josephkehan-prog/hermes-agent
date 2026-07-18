---
name: media-production-bundle
description: Produce a coordinated multi-format media package.
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    bundle: true
    domain: media-production
    tags: [bundle, media, audio, video, music]
    related_skills: [youtube-content, songsee, heartmula, songwriting-and-ai-music, manim-video, ascii-video]
---

# Media Production Bundle

## Boundary

Create a coordinated package spanning two or more media modes. Do not use for
a transcript-only request, a single audio analysis, or one isolated animation.

## Routing Table

| Production need | Primary skill | Output |
|---|---|---|
| Source or analyze YouTube material | `youtube-content` | Transcript and source structure |
| Analyze audio features | `songsee` | Time-based audio observations |
| Generate or manipulate musical material | `heartmula` | Reproducible music artifact |
| Develop lyrics, song concept, or AI-music brief | `songwriting-and-ai-music` | Structured creative direction |
| Explain ideas with precise animation | `manim-video` | Rendered educational animation |
| Produce terminal-native motion | `ascii-video` | Verified ASCII animation |

## Orchestration Workflow

1. Define audience, message, source rights, target platforms, durations,
   aspect ratios, accessibility needs, and final artifact list.
2. Build a source transcript or beat sheet before generating derivative media.
3. Establish one timeline with scene/section IDs. Map narration, visuals,
   music, captions, and citations to those IDs.
4. Route each artifact to its specialist member and preserve shared naming,
   timing, loudness, typography, and attribution conventions.
5. Render representative intermediates early, then render every final artifact
   and inspect synchronization, clipping, legibility, and file integrity.

## Handoff Record

Carry source licenses/URLs, transcript, beat sheet, timeline IDs, scripts,
audio settings, render commands, artifact paths, checksums, captions, and QA
findings. Record which outputs are source-derived versus generated.

## Stop Conditions

- Rights to transform or redistribute source media are unclear.
- Required voice, likeness, music, or brand assets are missing.
- Timing changes invalidate downstream scene or caption alignment.
- A requested imitation crosses protected-style or impersonation boundaries.

## Completion Gate

- [ ] Every requested artifact maps to the shared beat sheet or timeline
- [ ] Source rights and attribution are recorded
- [ ] Audio, visuals, captions, and narration remain synchronized
- [ ] Final renders were opened and inspected, not merely generated
- [ ] Accessibility requirements such as captions or readable contrast are met
- [ ] Artifact paths, formats, durations, and known limitations are listed

## Common Pitfalls

- Starting animation before narrative timing is stable
- Letting each artifact invent its own terminology or style
- Checking render exit codes without watching or listening to outputs
- Omitting captions and source attribution from the final package
