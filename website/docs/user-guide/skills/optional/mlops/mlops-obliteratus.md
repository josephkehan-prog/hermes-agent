---
title: "Obliteratus — OBLITERATUS: abliterate LLM refusals (diff-in-means)"
sidebar_label: "Obliteratus"
description: "OBLITERATUS: abliterate LLM refusals (diff-in-means)"
---

{/* This page is auto-generated from the skill's SKILL.md by website/scripts/generate-skill-docs.py. Edit the source SKILL.md, not this page. */}

# Obliteratus

OBLITERATUS: abliterate LLM refusals (diff-in-means).

## Skill metadata

| | |
|---|---|
| Source | Optional — install with `hermes skills install official/mlops/obliteratus` |
| Path | `optional-skills/mlops/obliteratus` |
| Version | `2.0.0` |
| Author | Hermes Agent |
| License | MIT |
| Dependencies | `obliteratus`, `torch`, `transformers`, `bitsandbytes`, `accelerate`, `safetensors` |
| Platforms | linux, macos |
| Tags | `Abliteration`, `Uncensoring`, `Refusal-Removal`, `LLM`, `Weight-Projection`, `SVD`, `Mechanistic-Interpretability`, `HuggingFace`, `Model-Surgery` |
| Related skills | `vllm`, `gguf`, [`huggingface-tokenizers`](/docs/user-guide/skills/optional/mlops/mlops-huggingface-tokenizers) |

## Reference: full SKILL.md

:::info
The following is the complete skill definition that Hermes loads when this skill is triggered. This is what the agent sees as instructions when the skill is active.
:::

# OBLITERATUS Skill

## What's inside

9 CLI methods, 28 analysis modules, 116 model presets across 5 compute tiers, tournament evaluation, and telemetry-driven recommendations.

Remove refusal behaviors (guardrails) from open-weight LLMs without retraining or fine-tuning. Uses mechanistic interpretability techniques — including diff-in-means, SVD, whitened SVD, LEACE concept erasure, SAE decomposition, Bayesian kernel projection, and more — to identify and surgically excise refusal directions from model weights while preserving reasoning capabilities.

**License warning:** OBLITERATUS is AGPL-3.0. NEVER import it as a Python library. Always invoke via CLI (`obliteratus` command) or subprocess. This keeps Hermes Agent's MIT license clean.

## Video Guide

Walkthrough of OBLITERATUS used by a Hermes agent to abliterate Gemma:
https://www.youtube.com/watch?v=8fG9BrNTeHs ("OBLITERATUS: An AI Agent Removed Gemma 4's Safety Guardrails")

Useful when the user wants a visual overview of the end-to-end workflow before running it themselves.

## When to Use This Skill

Trigger when the user:
- Wants to "uncensor" or "abliterate" an LLM
- Asks about removing refusal/guardrails from a model
- Wants to create an uncensored version of Llama, Qwen, Mistral, etc.
- Mentions "refusal removal", "abliteration", "weight projection"
- Wants to analyze how a model's refusal mechanism works
- References OBLITERATUS, abliterator, or refusal directions

## Step 1: Installation

Check if already installed:
```bash
obliteratus --version 2>/dev/null && echo "INSTALLED" || echo "NOT INSTALLED"
```

If not installed, clone and install from GitHub:
```bash
git clone https://github.com/elder-plinius/OBLITERATUS.git
cd OBLITERATUS
pip install -e .
# For Gradio web UI support:
# pip install -e ".[spaces]"
```

**IMPORTANT:** Confirm with user before installing. This pulls in ~5-10GB of dependencies (PyTorch, Transformers, bitsandbytes, etc.).

## Step 2: Check Hardware

Before anything, check what GPU is available:
```bash
python3 -c "
import torch
if torch.cuda.is_available():
    gpu = torch.cuda.get_device_name(0)
    vram = torch.cuda.get_device_properties(0).total_memory / 1024**3
    print(f'GPU: {gpu}')
    print(f'VRAM: {vram:.1f} GB')
    if vram < 4: print('TIER: tiny (models under 1B)')
    elif vram < 8: print('TIER: small (models 1-4B)')
    elif vram < 16: print('TIER: medium (models 4-9B with 4bit quant)')
    elif vram < 32: print('TIER: large (models 8-32B with 4bit quant)')
    else: print('TIER: frontier (models 32B+)')
else:
    print('NO GPU - only tiny models (under 1B) on CPU')
"
```

### VRAM Requirements (with 4-bit quantization)

| VRAM     | Max Model Size  | Example Models                              |
|:---------|:----------------|:--------------------------------------------|
| CPU only | ~1B params      | GPT-2, TinyLlama, SmolLM                    |
| 4-8 GB   | ~4B params      | Qwen2.5-1.5B, Phi-3.5 mini, Llama 3.2 3B   |
| 8-16 GB  | ~9B params      | Llama 3.1 8B, Mistral 7B, Gemma 2 9B       |
| 24 GB    | ~32B params     | Qwen3-32B, Llama 3.1 70B (tight), Command-R |
| 48 GB+   | ~72B+ params    | Qwen2.5-72B, DeepSeek-R1                    |
| Multi-GPU| 200B+ params    | Llama 3.1 405B, DeepSeek-V3 (685B MoE)      |

## Step 3: Browse Available Models & Get Recommendations

```bash
# Browse models by compute tier
obliteratus models --tier medium

# Get architecture info for a specific model
obliteratus info <model_name>

# Get telemetry-driven recommendation for best method & params
obliteratus recommend <model_name>
obliteratus recommend <model_name> --insights  # global cross-architecture rankings
```

## Step 4: Choose a Method

### Method Selection Guide
**Default / recommended for most cases: `advanced`.** It uses multi-direction SVD with norm-preserving projection and is well-tested.

| Situation                         | Recommended Method | Why                                      |
|:----------------------------------|:-------------------|:-----------------------------------------|
| Default / most models             | `advanced`         | Multi-direction SVD, norm-preserving, reliable |
| Quick test / prototyping          | `basic`            | Fast, simple, good enough to evaluate    |
| Dense model (Llama, Mistral)      | `advanced`         | Multi-direction, norm-preserving         |
| MoE model (DeepSeek, Mixtral)     | `nuclear`          | Expert-granular, handles MoE complexity  |
| Reasoning model (R1 distills)     | `surgical`         | CoT-aware, preserves chain-of-thought    |
| Stubborn refusals persist         | `aggressive`       | Whitened SVD + head surgery + jailbreak   |
| Want reversible changes           | Use steering vectors (see Analysis section) |
| Maximum quality, time no object   | `optimized`        | Bayesian search for best parameters      |
| Experimental auto-detection       | `informed`         | Auto-detects alignment type — experimental, may not always outperform advanced |

Per-method details (speed, risk, directions, how it works), the 3 `--direction-method` extraction strategies, a selection flowchart, and key-parameter tuning ranges: read `references/methods-guide.md` before picking a non-default method.

### 4 Python-API-Only Methods
(NOT available via CLI — require Python import, which violates AGPL boundary. Mention to user only if they explicitly want to use OBLITERATUS as a library in their own AGPL project.)
- failspy, gabliteration, heretic, rdo

## Step 5: Run Abliteration

### Standard usage
```bash
# Default method (advanced) — recommended for most models
obliteratus obliterate <model_name> --method advanced --output-dir ./abliterated-models

# With 4-bit quantization (saves VRAM)
obliteratus obliterate <model_name> --method advanced --quantization 4bit --output-dir ./abliterated-models

# Large models (70B+) — conservative defaults
obliteratus obliterate <model_name> --method advanced --quantization 4bit --large-model --output-dir ./abliterated-models
```

A full fine-tuning invocation with every tunable flag set explicitly: read `references/methods-guide.md` (Key Parameters table) for a worked example alongside the ranges.

### Key flags
| Flag | Description | Default |
|:-----|:------------|:--------|
| `--method` | Abliteration method | advanced |
| `--direction-method` | Direction extraction | diff_means |
| `--quantization` | Load in 4bit or 8bit | none (full precision) |
| `--large-model` | Conservative defaults for 120B+ | false |
| `--output-dir` | Where to save the abliterated model | ./obliterated_model |

Tuning flags (`--n-directions`, `--refinement-passes`, `--regularization`, `--verify-sample-size`, `--dtype`) with ranges and effects: read `references/methods-guide.md` (Key Parameters table).

### Other execution modes
```bash
# Interactive guided mode (hardware → model → preset)
obliteratus interactive

# Web UI (Gradio)
obliteratus ui --port 7860

# Run a full ablation study from YAML config
obliteratus run config.yaml --preset quick

# Tournament: pit all methods against each other
obliteratus tourney <model_name>
```

## Step 6: Verify Results

After abliteration, check the output metrics:

| Metric | Good Value | Warning |
|:-------|:-----------|:--------|
| Refusal rate | &lt; 5% (ideally ~0%) | > 10% means refusals persist |
| Perplexity change | &lt; 10% increase | > 15% means coherence damage |
| KL divergence | &lt; 0.1 | > 0.5 means significant distribution shift |
| Coherence | High / passes qualitative check | Degraded responses, repetition |

If refusals persist or coherence is damaged, don't guess at parameters — the fix depends on which failure mode: read `references/methods-guide.md` (Troubleshooting table) for the mapped remediation per symptom.

## Step 7: Use the Abliterated Model

The output is a standard HuggingFace model directory — load it with `transformers.AutoModelForCausalLM.from_pretrained`, upload with `huggingface-cli upload <user>/<name>-abliterated ./abliterated-models/<model>`, or serve directly with `vllm serve ./abliterated-models/<model>`.

## CLI Command Reference

| Command | Description |
|:--------|:------------|
| `obliteratus obliterate` | Main abliteration command |
| `obliteratus info <model>` | Print model architecture details |
| `obliteratus models --tier <tier>` | Browse curated models by compute tier |
| `obliteratus recommend <model>` | Telemetry-driven method/param suggestion |
| `obliteratus interactive` | Guided setup wizard |
| `obliteratus tourney <model>` | Tournament: all methods head-to-head |
| `obliteratus run <config.yaml>` | Execute ablation study from YAML |
| `obliteratus strategies` | List all registered ablation strategies |
| `obliteratus report <results.json>` | Regenerate visual reports |
| `obliteratus ui` | Launch Gradio web interface |
| `obliteratus aggregate` | Summarize community telemetry data |

## Analysis Modules

OBLITERATUS includes 28 analysis modules for mechanistic interpretability, plus a reversible steering-vector alternative to permanent weight modification. Module descriptions, which 5 to run first (alignment_imprint, concept_geometry, logit_lens, anti_ouroboros, causal_tracing), CLI/YAML invocation, and the steering-vectors Python API: read `references/analysis-modules.md`.

## Ablation Strategies

Beyond direction-based abliteration, OBLITERATUS includes structural ablation strategies:
- **Embedding Ablation** — Target embedding layer components
- **FFN Ablation** — Feed-forward network block removal
- **Head Pruning** — Attention head pruning
- **Layer Removal** — Full layer removal

List all available: `obliteratus strategies`

## Evaluation

OBLITERATUS includes built-in evaluation tools:
- Refusal rate benchmarking
- Perplexity comparison (before/after)
- LM Eval Harness integration for academic benchmarks
- Head-to-head competitor comparison
- Baseline performance tracking

## Platform Support

- **CUDA** — Full support (NVIDIA GPUs)
- **Apple Silicon (MLX)** — Supported via MLX backend
- **CPU** — Supported for tiny models (&lt; 1B params)

## YAML Config Templates

Load templates for reproducible runs via `skill_view`:
- `templates/abliteration-config.yaml` — Standard single-model config
- `templates/analysis-study.yaml` — Pre-abliteration analysis study
- `templates/batch-abliteration.yaml` — Multi-model batch processing

## Telemetry

OBLITERATUS can optionally contribute anonymized run data to a global research dataset.
Enable with `--contribute` flag. No personal data is collected — only model name, method, metrics.

## Common Pitfalls

Top invariants: **AGPL license** — never `import obliteratus` in MIT/Apache projects, CLI invocation only. **Models under ~1B respond poorly** — expect 20-40% residual refusal; models 3B+ are cleaner. **`aggressive` can make small models worse** — only escalate to it if `advanced` leaves > 10% refusals on a 3B+ model. **Always check perplexity** — a spike > 15% means the model is damaged, reduce aggressiveness.

The remaining pitfalls (MoE handling, re-quantization, VRAM spikes, reasoning-model sensitivity, telemetry recommendations, large-model flag, spectral-certification false negatives): read `references/methods-guide.md` (Common Pitfalls section).

## Complementary Skills

- **vllm** — Serve abliterated models with high throughput
- **gguf** — Convert abliterated models to GGUF for llama.cpp
- **huggingface-tokenizers** — Work with model tokenizers
