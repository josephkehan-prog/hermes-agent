---
name: local-model-ops
description: Manage Hermes's own local inference stack on the 64GB Mac — Agents-A1 via Ollama (localhost:11434) and ornith-uncensored 35B 4-bit via llama-server (localhost:1235). Check what's loaded, free RAM before loading, unload/swap models, health-check endpoints, fix common failures. Local only, no cloud APIs.
version: 1.0.0
author: Orchestra Research
license: MIT
platforms: [macos]
metadata:
  hermes:
    tags: [local-inference, ollama, llama-server, memory, health-check, model-swap]
    category: mlops
    requires_toolsets: [terminal]
    related_skills: [huggingface-hub, llama-cpp, workspace-rag]
---

# Local Model Ops

Run these exact commands. Do not use cloud APIs. Two servers:
- Ollama (Agents-A1): `localhost:11434`
- llama-server (ornith-uncensored 35B 4-bit): `localhost:1235`

## 1. What is loaded / running?

```bash
ollama ps                      # models in RAM now
ollama list                    # models on disk
curl -s localhost:11434/api/tags | head -c 400     # Ollama API alive?
curl -s localhost:1235/v1/models                   # llama-server alive?
lsof -nP -iTCP:1235 -iTCP:11434 -sTCP:LISTEN       # which ports listen
```

## 2. Check free RAM BEFORE loading a big model

```bash
memory_pressure -Q       # look at "System-wide memory free percentage"
```

Rules on this 64GB Mac:
- 35B 4-bit needs ~20-24GB. Load only if free >= 40%.
- Never run 35B and multiple Ollama models at once. Unload first (step 3).
- Fallback check: `vm_stat | head -5` — "Pages free" x 16384 = free bytes.

## 3. Unload / swap Ollama models

```bash
ollama stop <model>       # unload one model from RAM now
ollama ps                 # confirm it is gone
# Load with auto-unload after 1 min (use "keep_alive":0 to unload now):
curl -s localhost:11434/api/generate -d '{"model":"<model>","keep_alive":"1m"}'
```

## 4. Health checks (quick completion test)

```bash
# Ollama
curl -s localhost:11434/api/generate -d '{"model":"<model>","prompt":"hi","stream":false}' | head -c 300

# llama-server
curl -s localhost:1235/v1/chat/completions -H 'Content-Type: application/json' \
  -d '{"messages":[{"role":"user","content":"hi"}],"max_tokens":10}' | head -c 300
```

Reply with text = healthy. Empty/error = see step 5.

## 5. Troubleshooting

```bash
# Port not listening? Find the process (empty = server is down)
lsof -nP -iTCP:1235 -sTCP:LISTEN || echo "llama-server DOWN"
lsof -nP -iTCP:11434 -sTCP:LISTEN || echo "ollama DOWN"

# Ollama down: restart it
ollama serve &

# Model OOM / machine sluggish: free RAM, then retry
ollama ps                 # see what is hogging RAM
ollama stop <model>       # unload it
memory_pressure -Q        # confirm free % recovered
```

Port :1235 is now llama-swap (launchd com.josephhan.llama-swap, KeepAlive) — it auto-restarts on crash. If it's down anyway, check `/tmp/llama-swap.log` first; no need to ask the user before it self-restarts, but investigate the log if it keeps dying. llama-swap swaps models on demand — first request for a big model after a swap takes ~30-60s to load. `curl localhost:1235/v1/models` lists all models it serves (ornith-uncensored, agents-a1, plus qwen3-vl/bge-m3/nomic-embed-text proxied to Ollama) with load status.

## Reasoning budget (ornith)

Deployed state: ornith-uncensored is a Qwen3-style reasoning model, served via llama-swap (config: `llama-swap/config.yaml`). Its cmd runs `--reasoning-budget 512` (finite cap, fixed from the earlier unlimited `-1` setting), so thinking yields budget to content instead of consuming all of `max_tokens`.

Request-level override still available — disable thinking entirely for a call via the chat template's `enable_thinking` var:
```json
{"model":"ornith-uncensored","messages":[...],"max_tokens":200,
 "chat_template_kwargs":{"enable_thinking": false}}
```
Verified: `finish_reason:"stop"`, non-empty `content`, `reasoning_content` empty. `reasoning_effort` in the request body was tested and had no effect on this template — do not rely on it.
