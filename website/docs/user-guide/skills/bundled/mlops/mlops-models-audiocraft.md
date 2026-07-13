---
title: "Audiocraft Audio Generation — AudioCraft: MusicGen text-to-music, AudioGen text-to-sound"
sidebar_label: "Audiocraft Audio Generation"
description: "AudioCraft: MusicGen text-to-music, AudioGen text-to-sound"
---

{/* This page is auto-generated from the skill's SKILL.md by website/scripts/generate-skill-docs.py. Edit the source SKILL.md, not this page. */}

# Audiocraft Audio Generation

AudioCraft: MusicGen text-to-music, AudioGen text-to-sound.

## Skill metadata

| | |
|---|---|
| Source | Bundled (installed by default) |
| Path | `skills/mlops/models/audiocraft` |
| Version | `1.0.0` |
| Author | Orchestra Research |
| License | MIT |
| Dependencies | `audiocraft`, `torch>=2.0.0`, `transformers>=4.30.0` |
| Platforms | linux, macos |
| Tags | `Multimodal`, `Audio Generation`, `Text-to-Music`, `Text-to-Audio`, `MusicGen` |

## Reference: full SKILL.md

:::info
The following is the complete skill definition that Hermes loads when this skill is triggered. This is what the agent sees as instructions when the skill is active.
:::

# AudioCraft: Audio Generation

Comprehensive guide to using Meta's AudioCraft for text-to-music and text-to-audio generation with MusicGen, AudioGen, and EnCodec.

## When to use AudioCraft

**Use AudioCraft when:**
- Need to generate music from text descriptions
- Creating sound effects and environmental audio
- Building music generation applications
- Need melody-conditioned music generation
- Want stereo audio output
- Require controllable music generation with style transfer

**Key features:**
- **MusicGen**: Text-to-music generation with melody conditioning
- **AudioGen**: Text-to-sound effects generation
- **EnCodec**: High-fidelity neural audio codec
- **Multiple model sizes**: Small (300M) to Large (3.3B)
- **Stereo support**: Full stereo audio generation
- **Style conditioning**: MusicGen-Style for reference-based generation

**Use alternatives instead:**
- **Stable Audio**: For longer commercial music generation
- **Bark**: For text-to-speech with music/sound effects
- **Riffusion**: For spectogram-based music generation
- **OpenAI Jukebox**: For raw audio generation with lyrics

## Quick start

### Installation

```bash
# From PyPI
pip install audiocraft

# From GitHub (latest)
pip install git+https://github.com/facebookresearch/audiocraft.git

# Or use HuggingFace Transformers
pip install transformers torch torchaudio
```

### Basic text-to-music (AudioCraft)

```python
import torchaudio
from audiocraft.models import MusicGen

# Load model
model = MusicGen.get_pretrained('facebook/musicgen-small')

# Set generation parameters
model.set_generation_params(
    duration=8,  # seconds
    top_k=250,
    temperature=1.0
)

# Generate from text
descriptions = ["happy upbeat electronic dance music with synths"]
wav = model.generate(descriptions)

# Save audio
torchaudio.save("output.wav", wav[0].cpu(), sample_rate=32000)
```

Alternative HuggingFace Transformers loading path, and the AudioGen sound-effect quickstart: read `references/usage-examples.md`.

## Core concepts

Architecture diagram (text encoder → transformer decoder → EnCodec decoder): read `references/usage-examples.md`.

### Model variants

| Model | Size | Description | Use Case |
|-------|------|-------------|----------|
| `musicgen-small` | 300M | Text-to-music | Quick generation |
| `musicgen-medium` | 1.5B | Text-to-music | Balanced |
| `musicgen-large` | 3.3B | Text-to-music | Best quality |
| `musicgen-melody` | 1.5B | Text + melody | Melody conditioning |
| `musicgen-melody-large` | 3.3B | Text + melody | Best melody |
| `musicgen-stereo-*` | Varies | Stereo output | Stereo generation |
| `musicgen-style` | 1.5B | Style transfer | Reference-based |
| `audiogen-medium` | 1.5B | Text-to-sound | Sound effects |

### Generation parameters

| Parameter | Default | Description |
|-----------|---------|-------------|
| `duration` | 8.0 | Length in seconds (1-120) |
| `top_k` | 250 | Top-k sampling |
| `top_p` | 0.0 | Nucleus sampling (0 = disabled) |
| `temperature` | 1.0 | Sampling temperature |
| `cfg_coef` | 3.0 | Classifier-free guidance |

## Model Usage & Workflows

Full generation code for MusicGen (text-to-music, melody conditioning, stereo, continuation), MusicGen-Style (style transfer), AudioGen (sound effects), EnCodec (compression), and three worked end-to-end workflows (generation pipeline class, batch sound design, Gradio demo): read `references/usage-examples.md`.

## Performance & Troubleshooting

Memory optimization, batch-processing efficiency, and a GPU VRAM-by-model-size table: read `references/advanced-usage.md` (Performance Optimization section) when tuning for available hardware.

Common issues (CUDA OOM, poor quality, short generations, artifacts, stereo not working) and detailed fixes: read `references/troubleshooting.md` when something breaks.

## References

- **[Advanced Usage](https://github.com/NousResearch/hermes-agent/blob/main/skills/mlops/models/audiocraft/references/advanced-usage.md)** - Training, fine-tuning, deployment, performance optimization
- **[Usage Examples](https://github.com/NousResearch/hermes-agent/blob/main/skills/mlops/models/audiocraft/references/usage-examples.md)** - Full MusicGen/AudioGen/EnCodec code and workflows
- **[Troubleshooting](https://github.com/NousResearch/hermes-agent/blob/main/skills/mlops/models/audiocraft/references/troubleshooting.md)** - Common issues and solutions

## Resources

- **GitHub**: https://github.com/facebookresearch/audiocraft
- **Paper (MusicGen)**: https://arxiv.org/abs/2306.05284
- **Paper (AudioGen)**: https://arxiv.org/abs/2209.15352
- **HuggingFace**: https://huggingface.co/facebook/musicgen-small
- **Demo**: https://huggingface.co/spaces/facebook/MusicGen
