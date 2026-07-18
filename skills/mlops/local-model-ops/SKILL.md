---
name: local-model-ops
description: Operate Hermes local inference on this Mac.
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

Run these exact commands. Do not use cloud APIs. Two serving lanes:
- llama-swap (`localhost:1235`): persistent Agents-A1 controller plus swap-on-demand Qwen3.6 daily and thinking routes.
- Ollama (`localhost:11434`): Qwen3-VL, Qwythos, Cydonia, embeddings, and other peer models.

## 1. What is loaded / running?

```bash
ollama ps                      # models in RAM now
ollama list                    # models on disk
curl -s localhost:11434/api/tags | head -c 400     # Ollama API alive?
curl -s localhost:1235/v1/models                   # llama-swap inventory + load state
lsof -nP -iTCP:1235 -iTCP:11434 -sTCP:LISTEN       # which ports listen
```

## 2. Check free RAM BEFORE loading a big model

```bash
memory_pressure -Q       # look at "System-wide memory free percentage"
```

Rules on this 64GB Mac:
- Agents-A1 is the persistent controller; its two q8 KV slots are intentional.
- Abliterated Qwen3.6 27B VL Q6 uses about 22-24GB including runtime overhead and replaces Agents-A1 in llama-swap until the next controller request.
- Avoid loading multiple large Ollama peers while an image or model-generation job is active.
- Fallback check: `vm_stat | head -5` — "Pages free" x 16384 = free bytes.

## 3. Unload Ollama peers

```bash
ollama stop <model>       # unload one model from RAM now
ollama ps                 # confirm it is gone
# Load with auto-unload after 1 min (use "keep_alive":0 to unload now):
curl -s localhost:11434/api/generate -d '{"model":"<model>","keep_alive":"1m"}'
```

Do not use `ollama stop` for Agents-A1 or Qwen3.6; llama-swap owns them. Query `localhost:1235/v1/models` and let it swap them on demand.

## 4. Health checks (quick completion test)

```bash
# Ollama
curl -s localhost:11434/api/generate -d '{"model":"<model>","prompt":"hi","stream":false}' | head -c 300

# llama-server
curl -s localhost:1235/v1/chat/completions -H 'Content-Type: application/json' \
  -d '{"model":"agents-a1","messages":[{"role":"user","content":"hi"}],"max_tokens":64,"chat_template_kwargs":{"enable_thinking":false}}' | head -c 300
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

Port :1235 is llama-swap (launchd `com.josephhan.llama-swap`, KeepAlive). If it is down, inspect `/tmp/llama-swap.log` before restarting it and notify the user before the service interruption. A first request after swapping Agents-A1 and Qwen3.6 can take 20-60 seconds. `curl localhost:1235/v1/models` reports loaded/unloaded state.

## Qwen3.6 route policy

`ornith-uncensored` is retained only as the compatibility ID for the non-thinking abliterated Qwen3.6 route. Use it for JSON, tool calls, editing, and ordinary chat. `qwen3.6-think` uses the same abliterated Q6 weights with a 512-token preserved reasoning budget; allow at least 1024 output tokens so the final answer is not crowded out.

```json
{"model":"ornith-uncensored","messages":[...],"max_tokens":512}
```

Agents-A1 keeps its bounded controller reasoning. For Qwythos and Cydonia, use Ollama's native `/api/chat` with `think:false`; their OpenAI-compatible endpoints must not receive tool schemas. Cap Cydonia at 32K context and use it only as a prose engine behind Agents-A1.

## Specialist harness

Use `hermes-specialist` for explicit, bounded no-tool routing. `check` reads
endpoint registries without loading weights; `run` loads only the selected role.

```bash
hermes-specialist list
hermes-specialist check
hermes-specialist run research --prompt-file /path/to/evidence.md
hermes-specialist run vision-fast --image /path/to/image.png --prompt "Describe visible facts."
hermes-specialist run writer --prompt-file /path/to/scene-brief.md --temperature 0.8
hermes-specialist run code --prompt-file /path/to/task.md
```

Use `vision-fast` (the base 35B's own projector) for all image work — it
is the only vision lane (VL-8B and VL-30B escalation lanes pruned). Research/
writer cap at 32K.
No tool schemas reach peers. Ollama weights unload after every request by
default; pass `--keep-alive 2m` only for deliberate repeated calls.
