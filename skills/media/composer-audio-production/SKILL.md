---
name: composer-audio-production
description: "Use when planning, writing, generating, editing, analyzing, or packaging local music, sound effects, soundscapes, lyrics, stems, or soundtrack assets. Routes composition, local generation, audio analysis, and ffmpeg mastering while refusing to invent output from an unavailable engine."
version: 1.0.0
author: Hermes War Room
license: MIT
platforms: [macos]
metadata:
  hermes:
    bundle: true
    domain: composer-audio-production
    tags: [bundle, audio, music, songwriting, local-production]
    related_skills: [songwriting-and-ai-music, audiocraft-audio-generation, songsee, war-room-specialist-cascade]
---

# Composer Audio Production

## Boundary

Own the path from sonic brief to inspected audio package: composition brief,
lyrics, generation settings, edits, analysis, stems, mix notes, metadata, and
master. Do not treat a prompt or lyric sheet as generated audio, and do not use
CUDA-only HeartMuLa on this Apple-Silicon workstation.

## Routing Table

| Need | Primary skill | Deliverable |
|---|---|---|
| Song concept, structure, lyrics, prosody | `songwriting-and-ai-music` | Lyric sheet and production prompt |
| Local music generation | bundled ACE-Step helper | Seeded 2B-turbo render through local API |
| Local sound-effect synthesis | `audiocraft-audio-generation` | Seeded audio render when runtime exists |
| Spectral, loudness, tempo, or feature QA | `songsee` | Analysis images and findings |
| Audiobook chapter, narrated essay, or local voiceover | `war-room-specialist-cascade` | Hidden `narrator` profile |

Use `ffmpeg` and `ffprobe` directly for trimming, fades, normalization,
conversion, muxing, and stream verification.

## Installed ACE-Step route

The approved runtime is isolated at `~/mac/Hermes/runtimes/ace-step-1.5` with
the 2B turbo DiT and the 0.6B MLX language model. Preflight or render through:

```bash
python "$HERMES_HOME/hermes-agent/skills/media/composer-audio-production/scripts/ace_step_render.py" preflight
python "$HERMES_HOME/hermes-agent/skills/media/composer-audio-production/scripts/ace_step_render.py" generate \
  --prompt "instrumental production brief" --duration 10 --bpm 96 --output TAKE.wav
```

Default `thinking:false` uses deterministic text-to-music and the lowest memory
path. Add `--thinking` only when the 0.6B LM's query rewrite or audio codes are
materially useful. The helper starts ACE lazily and stops it after the take.
Treat ACE as a heavyweight exclusive job: batch size one, audition first, and
do not overlap it with LTX or another large media model.

## Orchestration Workflow

1. Fix purpose, audience, duration, structure, tempo/key if relevant, vocals,
   instrumentation, deliverable formats, rights, and originality constraints.
2. Preflight the chosen generator, `ffmpeg`, `ffprobe`, and analysis tool.
   Record missing runtimes before drafting an execution plan.
3. Write `AUDIO-BRIEF.md`, a section/beat map, lyric sheet when needed, and a
   generation ledger containing model, version, prompt, seed, and settings.
4. Produce short audition renders first. Select by documented criteria before
   extending, editing, or mastering.
5. Preserve sources and intermediates; never overwrite the only accepted take.
6. Probe the final streams, listen end to end, inspect clipping and loudness,
   and record limitations plus provenance.
7. For speech-first delivery, invoke Narrator through the specialist cascade;
   Composer retains mix, mastering, approvals, and final package ownership.

## Handoff Record

Carry brief, tempo/key, structure, lyric version, generator/runtime status,
model and license, prompts, seeds, take decisions, source and stem paths,
editing/mastering commands, final codecs, duration, loudness, checksums, and QA.

## Stop Conditions

- The requested generator or analyzer is not installed.
- A model download, install, API account, or routing change lacks approval.
- Rights for reference audio, voice, lyrics, samples, or adaptation are unclear.
- A requested living-artist imitation cannot be converted to high-level traits.

## Completion Gate

- [ ] The package includes the requested audio artifact, not only a prompt
- [ ] Model/runtime, prompt, seed, and take selection are reproducible
- [ ] Rights, source provenance, and generated status are recorded
- [ ] Final codec, sample rate, channels, and duration pass `ffprobe`
- [ ] The final was listened to end to end and checked for clipping/artifacts
- [ ] Lyrics, stems, project files, master, and known limitations are listed
