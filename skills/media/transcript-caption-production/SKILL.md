---
name: transcript-caption-production
description: Transcribe local audio to timestamped captions.
license: MIT
metadata:
  hermes:
    tags: [transcription, captions, subtitles, whisper, mlx]
    related_skills: [director-video-production, composer-audio-production, ocr-and-documents]
---

# Transcript and Caption Production

## Boundary

Produce local machine transcripts and caption files. Preserve uncertain words,
timestamps, speaker ambiguity, and source identity. Do not invent speakers or
silently rewrite meaning for readability.

## Runtime

```bash
python "$HERMES_HOME/hermes-agent/skills/media/transcript-caption-production/scripts/mlx_whisper_transcribe.py" preflight
python "$HERMES_HOME/hermes-agent/skills/media/transcript-caption-production/scripts/mlx_whisper_transcribe.py" transcribe \
  --input SOURCE.wav --output-json TRANSCRIPT.json --output-srt CAPTIONS.srt
```

The helper uses the isolated MLX Whisper runtime and cached
`mlx-community/whisper-large-v3-turbo` weights. No audio leaves the machine.

## Workflow

1. Record source path, hash, duration, language expectation, and caption format.
2. Normalize source audio only when required; preserve the original.
3. Run Whisper locally and keep segment timestamps plus raw text.
4. Correct names and technical terms against supplied evidence, never guesswork.
5. Split captions for readable line length and natural phrase boundaries without changing timestamps unsupported by audio.
6. Spot-check start, middle, end, overlaps, silence, and difficult proper nouns against playback.
7. Deliver raw JSON, corrected transcript, captions, correction ledger, and QA notes.

Read [references/caption-contract.md](references/caption-contract.md) before
editing timings or preparing publication captions.

## Stop Conditions

- Source audio is inaccessible or corrupt.
- Required speaker attribution lacks evidence.
- Requested verbatim accuracy exceeds what audio quality supports.

## Completion Gate

- [ ] Source hash, duration, model, language, and outputs are recorded
- [ ] Every caption has monotonic start/end timestamps
- [ ] Corrections are traceable to audio or supplied references
- [ ] Representative playback checks passed
