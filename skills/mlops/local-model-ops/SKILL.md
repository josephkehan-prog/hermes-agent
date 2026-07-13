---
name: local-model-ops
description: Operate Hermes local inference safely on this 64GB Mac.
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
- llama-swap (`localhost:1235`): persistent Agents-A1 controller and swap-on-demand Ornith reference model.
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
- Ornith replaces Agents-A1 in llama-swap and causes a cold reload on the next controller request.
- Avoid loading multiple large Ollama peers while an image or model-generation job is active.
- Fallback check: `vm_stat | head -5` — "Pages free" x 16384 = free bytes.

## 3. Unload Ollama peers

```bash
ollama stop <model>       # unload one model from RAM now
ollama ps                 # confirm it is gone
# Load with auto-unload after 1 min (use "keep_alive":0 to unload now):
curl -s localhost:11434/api/generate -d '{"model":"<model>","keep_alive":"1m"}'
```

Do not use `ollama stop` for Agents-A1 or Ornith; llama-swap owns both. Query `localhost:1235/v1/models` and let it swap them on demand.

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

Port :1235 is llama-swap (launchd `com.josephhan.llama-swap`, KeepAlive). If it is down, inspect `/tmp/llama-swap.log` before restarting it and notify the user before the service interruption. A first request after swapping Agents-A1 and Ornith can take 20-60 seconds. `curl localhost:1235/v1/models` reports loaded/unloaded state.

## Reasoning policy

Agents-A1 and Ornith both run with `--reasoning-budget 512`. Hawkeye and Canvas disable controller thinking through their profile provider overrides because their specialist engines perform the expensive visual work.

Request-level override still available — disable thinking entirely for a call via the chat template's `enable_thinking` var:
```json
{"model":"agents-a1","messages":[...],"max_tokens":200,
 "chat_template_kwargs":{"enable_thinking": false}}
```
Use the same override for Ornith. For Qwythos and Cydonia, use Ollama's native `/api/chat` with `think:false`; their OpenAI-compatible endpoints must not receive tool schemas. Cap Cydonia at 32K context and use it only as a prose engine behind Agents-A1.
