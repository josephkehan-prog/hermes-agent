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

> **Engine upgraded (2026-07-18):** ACE-Step 1.5 2B (server/API path) was
> replaced by **ACE-Step XL turbo 4B, diffusers format** (~11GB, self-contained),
> driven by the `acestep-compose` CLI. Higher audio quality, simpler runner (no
> API server, no separate LM). See "Installed ACE-Step route" below.


## Boundary

Own the path from sonic brief to inspected audio package: composition brief,
lyrics, generation settings, edits, analysis, stems, mix notes, metadata, and
master. Do not treat a prompt or lyric sheet as generated audio, and do not use
CUDA-only HeartMuLa on this Apple-Silicon workstation.

## Routing Table

| Need | Primary skill | Deliverable |
|---|---|---|
| Song concept, structure, lyrics, prosody | `songwriting-and-ai-music` | Lyric sheet and production prompt |
| Local music generation | `acestep-compose` CLI (ACE-Step XL 4B, diffusers) | Seeded XL-turbo render, direct diffusers |
| Local sound-effect synthesis | `audiocraft-audio-generation` | Seeded audio render when runtime exists |
| Spectral, loudness, tempo, or feature QA | `songsee` | Analysis images and findings |
| Audiobook chapter, narrated essay, or local voiceover | `war-room-specialist-cascade` | Hidden `narrator` profile |

Use `ffmpeg` and `ffprobe` directly for trimming, fades, normalization,
conversion, muxing, and stream verification.

## Installed ACE-Step route (XL 4B, diffusers)

Model: `~/models/acestep-xl-turbo-diffusers` (ACE-Step 1.5 XL turbo, ~11GB,
self-contained diffusers pipeline — transformer + text/condition encoders + vae).
Driver: `acestep-compose` (on PATH via `~/.local/bin`). Loads `AceStepPipeline`
on MPS, runs, exits. Uncensored by design (no content filter).

```bash
# Instrumental
acestep-compose --tags "lo-fi hip hop, mellow piano, rainy day" \
  --duration 30 --steps 27 --seed 7 -o TAKE.wav

# With vocals — pass lyrics ([verse]/[chorus] tags supported)
acestep-compose --tags "synthwave, driving, female vocal" \
  --lyrics-file lyrics.txt --duration 60 -o TAKE.wav
```

Flags: `--tags` (genre/mood/instrument prompt) · `--lyrics`/`--lyrics-file`
(omit for instrumental) · `--duration` sec · `--steps` (default 27, turbo is
few-step) · `--seed`. Output is stereo 44.1kHz WAV. `--guidance` is ignored on
the turbo (guidance-distilled) checkpoint.

Treat as a heavyweight exclusive job: batch size one, audition first, and do not
overlap it with LTX video or another large media model. ~11GB resident at gen;
check `memory_pressure -Q` first (needs >20% free alongside the warm base LLM).

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
