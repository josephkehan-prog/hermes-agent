---
name: chatterbox-tts
description: Local TTS with voice cloning via Chatterbox MLX.
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [macos]
prerequisites:
  commands: [espeak-ng]
metadata:
  hermes:
    tags: [tts, speech, voice-cloning, mlx, chatterbox, offline, audio]
    category: media
    requires_toolsets: [terminal]
    related_skills: [audiobook-narration-production]
---

# Chatterbox TTS (local, MLX)

Local text-to-speech quality lane. Resemble AI's Chatterbox, 4-bit MLX build.
Runs on Apple Silicon MPS, ~0.56x realtime, offline. Voice cloning + emotion.

## When to use which TTS

- **Chatterbox** (this) — quality lane: natural voice, cloning from a reference
  clip, emotion/exaggeration control. Slower (~RTF 0.56).
- **Kokoro-82M** — fast/tiny lane (`audiobook-narration-production`): lowest RAM,
  fastest, "good enough" for long narration.
- **edge-tts** — cloud fallback (hermes `tts.provider: edge`); avoid when offline
  quality matters — Chatterbox replaces it for local use.

## Commands

```bash
CB=~/models/chatterbox-tts-4bit/.venv/bin/chatterbox

# Basic English TTS
$CB "Your text here." -l en --backend mlx -o out.wav

# Voice cloning from a reference clip (3-10s of target speaker)
$CB "Text in the cloned voice." -v reference.wav --backend mlx -o out.wav

# Emotion / expressiveness (0.0 flat … 1.0+ dramatic; default ~0.5)
$CB "So excited to see you!" --exaggeration 0.8 --backend mlx -o out.wav

# Other languages (multilingual model): es fr de ja zh …
$CB "Hola, ¿qué tal?" -l es --backend mlx -o out.wav
```

Flags: `--cfg` (guidance), `--seed` (reproducibility), `--backend {mlx,pytorch,hybrid-mlx}` (use `mlx` on Apple Silicon).

## Install notes (already done 2026-07-18)

- Model: `mlx-community/Chatterbox-TTS-4bit` (976MB) → `~/models/chatterbox-tts-4bit/`
- Runner: `chatterbox-mlx` in a project-local venv there.
- Dependency gotchas fixed at install:
  - needs `resemble-perth` (NOT the unrelated `perth` PyPI package) for the
    watermarker, and `setuptools<81` so `pkg_resources` exists — without either,
    `ChatterboxTTS.__init__` dies with `'NoneType' object is not callable`.
  - needs `espeak-ng` on PATH (Homebrew) for phonemization.

## Voice conversion (VC)

Convert EXISTING audio into a target voice (keeps original prosody/timing —
different from TTS cloning which synthesizes from text):

```bash
chatterbox-vc --input source.wav --target target_voice.wav --output out.wav
```

`--input` = audio whose content/prosody is kept · `--target` = 3-10s clip of the
voice to convert into. Runs the `ChatterboxVC` model in the same venv.

## Rules

- Exclusive-ish job: loads the model each run; not a persistent server.
  Chatterbox is now the primary local TTS (Kokoro was removed 2026-07-18).
- Voice-clone reference clips: keep 3-10s, clean, single speaker.
- Do not clone a real person's voice without their consent.
