---
name: flux-local
description: "Generate images locally with FLUX.1-dev or FLUX.1-schnell via ComfyUI or a standalone diffusers script — no web UI needed for one-off generation."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [macos]
compatibility: "Requires either ComfyUI running locally OR pip-installed `diffusers` + `accelerate`/`torch`. M5 Max with 64 GB handles both paths."
prerequisites:
  commands: ["python3", "curl"]
metadata:
  hermes:
    tags: [flux, image-generation, stable-diffusion, local-model, creative]
    related_skills: [comfyui, z-image-turbo]
---

# Flux Local

Generate images locally with FLUX.1-dev or FLUX.1-schnell on your Mac. Two paths: ComfyUI (full node-graph) and a standalone script (one-shot generation). Pick the path based on what you need.

## When to Use

- User wants one image quickly without opening a browser — use **standalone script**.
- User needs img2img, ControlNet, upscaling, or a multi-step pipeline — use **ComfyUI** (`comfyui` skill).
- User is on Apple Silicon with ≥16 GB unified memory (M5 Max + 64 GB = no limits here).

## Model Sources

| Model | Size | Speed | Quality | Use when... |
|-------|------|-------|---------|-------------|
| `black-forest-labs/FLUX.1-dev` | ~23 GB | slow | best | dev pipeline, highest quality |
| `Comfy-Org/flux1-dev-fp8.safetensors` | ~12 GB | fast | good | disk-constrained, still great quality |
| `black-forest-labs/FLUX.1-schnell` | ~23 GB | fastest | good enough | quick drafts, no watermarking concerns |

## Path A: Standalone Script (one-off generation)

For when you want a single image without running a full ComfyUI server.

### Install deps

```bash
pip install diffusers accelerate safetensors torch --extra-index-url https://download.pytorch.org/whl/cpu
# For M5 Max MPS acceleration:
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu124  # or use your mise-managed Python
```

### Generate one image

```bash
python3 scripts/flux_one_shot.py \
  --prompt "a photo of a cat sitting in a sunlit room" \
  --model black-forest-labs/FLUX.1-dev \
  --output ./outputs/cat.png \
  --steps 50 \
  --guidance 3.5
```

Script auto-handles: model download (first run), MPS device, fp8 quantization hint, and saves directly to disk. No server running needed.

### Batch / variations

```bash
# Same prompt, different seeds
python3 scripts/flux_one_shot.py --prompt "ocean sunset" --count 5 --output-dir ./outputs/sunset/

# img2img: start from an existing image
python3 scripts/flux_one_shot.py \
  --prompt "make it watercolor style" \
  --input-image ./photo.png \
  --strength 0.6
```

### File paths

- `scripts/flux_one_shot.py` — the standalone generator
- `workflows/flux_dev.json` — ComfyUI API-format workflow (for full-node-graph path)

## Path B: ComfyUI (full pipeline)

Already covered by the `comfyui` skill. Use when you need ControlNet, img2img, or multi-step workflows.

```bash
# If ComfyUI isn't running:
bash scripts/comfyui_setup.sh --m-series

# Download Flux model:
comfy model download \
  --url "https://huggingface.co/Comfy-Org/flux1-dev/resolve/main/flux1-dev-fp8.safetensors" \
  --relative-path models/checkpoints

# Run the included workflow:
python3 scripts/run_workflow.py \
  --workflow workflows/flux_dev.json \
  --args '{"prompt": "a photo of a cat"}' \
  --output-dir ./outputs
```

## Decision Tree

| User says | Path | Command |
|-----------|------|---------|
| "make me an image" (one-off) | A: script | `python3 scripts/flux_one_shot.py --prompt "..."` |
| "8 variations with different seeds" | A: script | `--count 8 --randomize-seed` on the standalone script |
| "change this photo to watercolor style" (img2img) | B: ComfyUI | ComfyUI workflow path |
| "install Flux on my Mac" | B: ComfyUI | `bash scripts/comfyui_setup.sh --m-series` then download model |
| "check if everything is ready" | A or B | `python3 scripts/health_check.py` (A) or `comfy health check` (B) |

## Pitfalls

1. **VRAM on M5 Max** — FLUX-dev needs ~24 GB; fp8 variant fits in 16 GB. On your box it's fine either way, but note this for smaller Macs.
2. **fp8 vs full precision** — fp8 is 2-3x faster with minimal quality loss. Default to fp8 unless user asks for dev-quality (full).
3. **First run downloads the model (~12-23 GB)** — warn the user this takes time on slow connections. Offer to skip if they already have it cached.
4. **MPS vs CPU** — always use MPS on Apple Silicon; falling back to CPU is 10x slower.
5. **Output path safety** — filenames from the model are sanitized (no path traversal). Keep this protection in `flux_one_shot.py`.

## Verification Checklist

- [ ] Model downloaded and accessible locally
- [ ] Output image exists at expected path
- [ ] Image renders correctly (not garbage/noise)
- [ ] Steps/guidance parameters match user request
