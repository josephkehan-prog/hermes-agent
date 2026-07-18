# Framework Checklist — Per-Stack Commands

Each framework has its own runtime, weights location, and verification commands. Use this table when auditing any project claiming "local mode."

## Ollama (LLM)

| Check | Command | Notes |
|-------|---------|-------|
| Install | `which ollama` | `/usr/local/bin/ollama` on macOS |
| Running | `ps aux \| grep ollama` | Process should be running as daemon |
| Models | `ollama list` | Shows all local models with sizes and modification dates |
| Delete | `ollama rm <name>` | Removes model from disk |
| Weights path | `~/Library/Application Support/Ollama/models/` | Ollama manages everything internally — no separate files needed |

## MLX (Apple Silicon, Flux2Klein)

| Check | Command | Notes |
|-------|---------|-------|
| Runtime | `python3 -c "import mlx.core as mx; print('MLX', mx.__version__)"` | System Python check — may not reflect venv state |
| Package | `pip show mlx` or `uv pip show mlx` | Check whichever manager is in use |
| Weights | `find ~/mac -name "*.gguf" -type f` | GGUF text encoder files stored separately from main weights |
| Repo | `ls ~/ultra-fast-image-gen/` | Expected path for mflux upstream repo |

## ComfyUI (image gen)

| Check | Command | Notes |
|-------|---------|-------|
| CLI | `command -v comfy && comfy --version` | Via comfy-cli |
| Server running | `curl -s http://127.0.0.1:8188/system_stats 2>/dev/null` | Returns JSON if server is live, nothing otherwise |
| Models installed | `comfy model list` or `ls ~/Documents/comfy/ComfyUI/models/checkpoints/` | Both via CLI and filesystem |
| Health check | `python3 scripts/health_check.py` | From the comfyui skill's scripts directory |

## llama.cpp (GGUF)

| Check | Command | Notes |
|-------|---------|-------|
| Install | `which llama-server || which llama-cli` | Either may be installed depending on build |
| Server running | `ps aux \| grep llama-server` or check listening port | Default port 8080 |
| Weights path | wherever the user cloned it — no standard location | Check git clone history if needed |

## General Checks (any framework)

| Check | Command | Notes |
|-------|---------|-------|
| Processes running | `ps aux \| grep -E "(ollama\|python.*flux\|llama-server\|comfy)" \| grep -v grep` | Look for ML-related processes |
| Background sessions | `process list` (Hermes) or check active terminal sessions | Workers may be backgrounded in a terminal session |
| Disk usage estimate | Sum sizes from model listings / `du -sh ~/Library/Application Support/Ollama/models/` | Gives total footprint |

## Dead-Code Detection

When all three checks fail for a project:

1. **Runtime missing** — no package installed, or wrong Python env
2. **Weights missing** — no GGUF/safetensors on disk at expected location
3. **Process not running** — worker script exists but nothing is executing it

Report pattern:
> "Project has `X_worker.py` as interface code but nothing's actually running:
> - No upstream repo installed at expected path (`~/ultra-fast-image-gen/`)
> - No MLX in system Python
> - No GGUF files on disk
> The worker would error immediately trying to import mflux."

This is the class of finding that matters most — scripts exist as code, but they're not operational. Users often forget to check this and assume "we have the script so it works."
