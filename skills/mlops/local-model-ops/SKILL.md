---
name: local-model-ops
description: Manage Hermes's local inference stack on the 64GB Mac — Qwen3.6 and Agents-A1 through llama-swap (localhost:1235), with specialist and embedding peers through Ollama (localhost:11434). Check load state, memory pressure, swaps, context budgets, endpoints, and common failures. Local only, no cloud APIs.
version: 1.0.0
author: Orchestra Research
license: MIT
platforms: [macos]
metadata:
  hermes:
    tags: [local-inference, ollama, llama-server, memory, health-check, model-swap]
    category: mlops
    requires_toolsets: [terminal]
---

# Local Model Ops

Run these exact commands. Do not use cloud APIs. Two serving lanes:
- llama-swap (`localhost:1235`): Agents-A1 plus Qwen3.6 daily and thinking routes.
- Ollama (`localhost:11434`): Qwen3-VL, Qwythos, Cydonia, BGE-M3, and other peers.

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
- Abliterated Qwen3.6 Q6 uses about 29-31GB including runtime overhead. Load only if free >= 40%.
- Run one heavyweight llama-swap model at a time; unload large Ollama peers before memory-intensive image work.
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

Port :1235 is llama-swap (launchd `com.josephhan.llama-swap`, KeepAlive). It swaps large models on demand, so a first request can take 20-60 seconds. Inspect `/tmp/llama-swap.log` if it is down. `curl localhost:1235/v1/models` lists Qwen3.6, Agents-A1, and the Ollama peers with load state.

## Qwen3.6 route policy

`ornith-uncensored` is retained only as the compatibility ID for the non-thinking abliterated Qwen3.6 route. Use it for JSON, tool calls, editing, and ordinary chat. `qwen3.6-think` uses the same abliterated Q6 weights with a 512-token preserved reasoning budget; allow at least 1024 output tokens so the final answer is not crowded out.

```json
{"model":"ornith-uncensored","messages":[...],"max_tokens":512}
```

Use Qwythos only for evidence synthesis and Cydonia only for prose. They stay on Ollama and should not be treated as general tool controllers.

## Specialist harness

Use `hermes-specialist` for explicit, bounded no-tool routing. `check` reads the
endpoint registries without loading weights; `run` loads only the selected role.

```bash
hermes-specialist list
hermes-specialist check
hermes-specialist run research --prompt-file /path/to/evidence.md
hermes-specialist run vision-fast --image /path/to/image.png --prompt "Describe visible facts."
hermes-specialist run writer --prompt-file /path/to/scene-brief.md --temperature 0.8
hermes-specialist run code --prompt-file /path/to/task.md
```

Use `vision-fast` for first-pass inspection and `vision-quality` only when the
8B result is uncertain or misses fine detail. The harness caps research/writer
at 32K and fast vision at 16K. It never sends tool schemas to peer models and
unloads Ollama weights after each request by default. Pass `--keep-alive 2m`
only for deliberate repeated calls to one specialist.
