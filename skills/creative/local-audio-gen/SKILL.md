---
name: local-audio-gen
description: Generate music and convert voice locally on Apple Silicon.
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [macos]
compatibility: "Apple Silicon (MPS/MLX). Uses the workspace-local ACE-Step and Chatterbox lanes in ~/mac/Hermes/bin; those bins carry their own venvs."
prerequisites:
  commands: ["python3"]
metadata:
  hermes:
    tags: [audio, music-generation, voice-conversion, local-model, creative]
    related_skills: [flux-local, songwriting-and-ai-music]
---

# Local Audio Generation

On-device audio generation via the workspace's local media lanes — no cloud
key, no upload. Two lanes:

- **Music** — ACE-Step XL (diffusers, MPS): tags/lyrics to a full WAV.
- **Voice conversion** — Chatterbox VC (MLX): re-render existing speech in a
  target speaker's voice, preserving prosody/timing.

Both binaries live in the workspace bin dir and ship their own virtualenvs, so
call them by absolute path. Set once:

```bash
HB=~/mac/Hermes/bin
```

## When to Use

- User wants a song, jingle, background track, or instrumental → **music**.
- User has a voice clip and wants it re-voiced as another speaker → **voice
  conversion**.
- Text-to-speech (plain narration) is **not** covered here — no local TTS bin is
  wired yet; use the configured `tts` provider for that.

## Lane A: Music (ACE-Step)

```bash
"$HB/acestep-compose" \
  --tags "lo-fi hip hop, mellow, rainy, vinyl crackle" \
  --duration 30 \
  -o ./song.wav
```

With lyrics (structure tags like `[verse]` / `[chorus]` are honored):

```bash
"$HB/acestep-compose" \
  --tags "synthwave, driving, 120bpm" \
  --lyrics-file ./lyrics.txt \
  --duration 60 \
  -o ./track.wav
```

Flags: `--tags` (required — genre/mood/instrument prompt), `--lyrics` /
`--lyrics-file` (omit for instrumental), `--duration` seconds (default 30),
`--steps` (default 27; turbo is few-step), `--guidance` (default 7.5), `--seed`,
`-o/--output` (required WAV path), `--device` (default `mps`).

## Lane B: Voice Conversion (Chatterbox VC)

```bash
"$HB/chatterbox-vc" \
  --input ./source_speech.wav \
  --target ./target_voice.wav \
  --output ./converted.wav
```

- `--input` — audio whose content/prosody/timing is kept.
- `--target` — 3–10s clean reference clip of the voice to convert into.
- `--output` — result WAV.

## Runtime note (RAM)

These lanes load multi-GB models on MPS/MLX. Per the workspace rule, ONE big
model is resident at a time — a heavy generation may contend with the resident
llama-swap model. For long jobs, generate when the big chat model is idle, and
prefer shorter `--duration` / fewer `--steps` for quick drafts.
