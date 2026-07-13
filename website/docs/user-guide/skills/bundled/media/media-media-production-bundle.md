---
title: "Media Production Bundle"
sidebar_label: "Media Production Bundle"
description: "Use when producing a multi-format media package from source content through transcript analysis, audio or music, visualization, animation, and publication-re..."
---

{/* This page is auto-generated from the skill's SKILL.md by website/scripts/generate-skill-docs.py. Edit the source SKILL.md, not this page. */}

# Media Production Bundle

Use when producing a multi-format media package from source content through transcript analysis, audio or music, visualization, animation, and publication-ready assets. Coordinates narrative and technical continuity across media outputs.

## Skill metadata

| | |
|---|---|
| Source | Bundled (installed by default) |
| Path | `skills/media/media-production-bundle` |
| Version | `1.0.0` |
| Author | Hermes Agent |
| License | MIT |
| Platforms | linux, macos, windows |
| Tags | `bundle`, `media`, `audio`, `video`, `music` |
| Related skills | [`youtube-content`](/docs/user-guide/skills/bundled/media/media-youtube-content), [`songsee`](/docs/user-guide/skills/bundled/media/media-songsee), [`heartmula`](/docs/user-guide/skills/bundled/media/media-heartmula), [`songwriting-and-ai-music`](/docs/user-guide/skills/bundled/creative/creative-songwriting-and-ai-music), [`manim-video`](/docs/user-guide/skills/bundled/creative/creative-manim-video), [`ascii-video`](/docs/user-guide/skills/bundled/creative/creative-ascii-video) |

## Reference: full SKILL.md

:::info
The following is the complete skill definition that Hermes loads when this skill is triggered. This is what the agent sees as instructions when the skill is active.
:::

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
