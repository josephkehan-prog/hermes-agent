---
name: audiobook-narration-production
description: "Use when producing local audiobook chapters, narrated essays, voiceover, spoken-word proofs, or accessible audio from approved text with Kokoro, ffmpeg assembly, reproducible voice settings, and listening QA."
license: MIT
metadata:
  hermes:
    tags: [audiobook, narration, tts, kokoro, local-audio]
    related_skills: [quill-story-production, composer-audio-production, transcript-caption-production]
---

# Audiobook Narration Production

## Boundary

Turn approved text into local spoken audio. Use installed Kokoro for the proven
route. Do not clone or imitate a real person's voice. Do not claim a chapter is
finished until its streams and complete playback are checked.

## Runtime

```bash
python "$HERMES_HOME/hermes-agent/skills/media/audiobook-narration-production/scripts/kokoro_narrate.py" preflight
python "$HERMES_HOME/hermes-agent/skills/media/audiobook-narration-production/scripts/kokoro_narrate.py" render \
  --text-file CHAPTER.txt --voice af_heart --speed 1.0 --output CHAPTER.wav
```

The helper uses the installed Kokoro CLI, local cached weights/voice, and
`ffprobe`. It accepts no shell fragments and emits a JSON artifact ledger.

## Workflow

1. Confirm text ownership, pronunciation notes, language, voice, pace, chapter boundaries, and output format.
2. Normalize only typography that changes speech; preserve authored wording.
3. Run preflight. Render a 20-60 second audition before a full chapter.
4. Record voice, language, speed, source hash, model identity, and output path.
5. Inspect waveform/loudness, listen end to end, and note mispronunciations or artifacts.
6. Re-render affected sections; preserve accepted takes and assemble explicitly with ffmpeg.
7. Generate captions through `transcript-caption-production` when requested.

Read [references/voice-ledger.md](references/voice-ledger.md) for multi-chapter
or multi-character projects.

## Stop Conditions

- Text rights or voice/likeness consent is unclear.
- Required Kokoro voice is not cached and a download lacks approval.
- The output cannot be opened, probed, or listened to.

## Completion Gate

- [ ] Source, voice, language, speed, model, and hashes are recorded
- [ ] WAV properties pass `ffprobe`
- [ ] Pronunciation and complete-playback QA are recorded
- [ ] AI-generated narration is disclosed where delivered to others
