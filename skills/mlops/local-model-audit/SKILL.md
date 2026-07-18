---
name: local-model-audit
description: "Verify whether a project's claimed 'local mode' for ML inference actually works — check runtime, weights, and processes across any framework (Ollama, ComfyUI, mflux/MLX, llama.cpp, etc.). Use when the user says 'check local models', 'audit my setup', or asks about 'local mode' status. Covers both LLM stacks and image-gen stacks."
version: 1.0.0
author: Orchestra Research
license: MIT
platforms: [macos, linux, windows]
metadata:
  hermes:
    tags: [local-model-audit, local-inference, ML-state-check, Ollama, ComfyUI, mflux, llama.cpp, dead-code-detection]
---

# Local Model Audit

Verify whether a project's claimed "local mode" for ML inference actually works.
This is NOT about installing anything — it's about checking what's already there and whether scripts can run against it.

## When to Use

- User says "check local models", "audit my setup", or asks about "local mode" status
- User points you at a model-worker script (e.g., `mflux_resident_worker.py`) and wants to know if it works
- You find project code claiming local inference but nothing is installed
- User asks whether they should delete/keep a model or fix the env

## The Three Checks (in order)

Every audit runs these three checks, regardless of framework:

### 1. Runtime exists?

```bash
# Ollama — check it's installed and running
which ollama && ollama list

# MLX — check Python package availability
python3 -c "import mlx.core as mx; print('MLX', mx.__version__)"

# llama.cpp — check CLI/server
which llama-server || which llama-cli

# ComfyUI — check comfy-cli + running server
command -v comfy && curl -s http://127.0.0.1:8188/system_stats 2>/dev/null
```

If a runtime is missing, report it immediately. Don't proceed to the next step until you know whether the user wants to install or just audit.

### 2. Weights present on disk?

```bash
# GGUF files anywhere in workspace
find ~/mac -name "*.gguf" -type f 2>/dev/null | head -20

# safetensors (ComfyUI / PyTorch)
find ~/mac -name "*.safetensors" -type f 2>/dev/null | head -20

# Framework-specific stores:
ls ~/Library/Application\ Support/Ollama/models/  # Ollama default path
comfy model list  # ComfyUI via comfy-cli
```

Report what exists and total disk usage. If nothing found, the scripts are dead code.

### 3. Something actually running?

```bash
# Active processes related to ML inference
ps aux | grep -E "(ollama|python.*flux|llama-server|comfy)" | grep -v grep

# Background terminal sessions with model workers
process list
```

If nothing is running, the worker scripts exist but aren't executing — they're dead code.

## The Dead-Code Pattern

When you find all three checks failing (no runtime, no weights, no processes), report:

> "Project has `X_worker.py` as interface code but nothing's actually running:
> - No upstream repo installed at expected path (`~/ultra-fast-image-gen/`)
> - No MLX in system Python
> - No GGUF files on disk
> The worker would error immediately trying to import mflux."

This is the class of finding that matters most — scripts exist as code, but they're not operational. Users often forget to check this and assume "we have the script so it works."

## Framework-Specific Notes

### Ollama (LLM stack)
- Models stored at `~/Library/Application Support/Ollama/models/`
- `ollama list` shows all local models with sizes
- `ollama rm <name>` deletes a model
- No separate weights files — Ollama manages everything internally

### ComfyUI (image-gen, via comfy-cli)
- Already covered by the `comfyui` skill's `hardware_check.py` and `health_check.py`
- Use those when specifically auditing ComfyUI state

### mflux/MLX (Flux2Klein, local image gen on Apple Silicon)
- Requires: ultra-fast-image-gen repo installed + MLX package in Python env
- Worker scripts expect `from mflux.models.flux2.model.flux2_transformer import ...`
- GGUF text encoder files stored separately from main model weights
- No safetensors — uses GGUF quantization via MLX

### llama.cpp (GGUF inference)
- Covered by the `llama-cpp` skill for its specific stack

## Pitfalls

1. **Don't assume scripts = operational.** A worker script exists in the repo ≠ it's running. Always check all three conditions.
2. **Framework-specific default paths vary.** Ollama uses macOS app support path; ComfyUI uses comfy-cli workspace; llama.cpp uses wherever you cloned it. Check each.
3. **Python env mismatch.** System Python may not have MLX/torch even if the package is installed in a venv — `python3 -c "import mlx"` checks system, not virtualenv state. Note this distinction when reporting.
4. **Don't install without asking.** If runtime is missing, report it and ask whether to install or just audit. Don't run setup commands during an audit-only conversation.

## References

- **[framework-checklist.md](references/framework-checklist.md)** — per-framework command reference for runtime/weights/process checks
- **[dead-code-signals.md](references/dead-code-signals.md)** — examples of projects with worker scripts but missing env components, how to report each case
