---
name: specialist-routing
description: "Route a task to the right local specialist model via hermes-specialist — decision table, commands, and the never-promote-a-specialist-to-default rule."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [macos]
prerequisites:
  commands: [hermes-specialist]
metadata:
  hermes:
    tags: [specialist, routing, local-inference, vision, writer, research, ollama, llama-swap]
    category: mlops
    requires_toolsets: [terminal]
    related_skills: [local-model-ops]
---

# Specialist Routing

One command, seven roles. `hermes-specialist` routes a single bounded, no-tool
request to the right local model and unloads Ollama weights afterward.

## Which role? (decision table)

| Task looks like… | Role | Model | Context cap |
|---|---|---|---|
| Ordinary chat, editing, JSON, tool calls | *(no specialist — default route)* | Qwen3.6 35B-A3B ablit (`ornith-uncensored`, kept warm, ~95 tok/s) | 128K |
| Hard reasoning, deliberate multi-step thought | `think` | Qwen3.6 35B ablit, bounded reasoning | 128K |
| Coding task handed off as one prompt | `code` | Qwen3.6 35B ablit main route | 64K policy |
| Multi-step agent / tool controller | `controller` | Agents-A1 34.7B (swap-on-demand) — ⚠ NOT abliterated | 160K |
| Describe / OCR / analyze an image, first pass | `vision-fast` | Qwen3.6 35B base (has vision) | 128K |
| Evidence synthesis, claims + confidence + caveats | `research` | Qwythos 9B ablit | 32K |
| Creative prose, scenes, fiction | `writer` | Cydonia 24B v4 heretic | 32K |

Vision: `vision-fast` = the base 35B model's own projector (free, already warm) — the only vision lane. The abliterated VL-8B (2026-07-17) and Qwen3-VL 30B (2026-07-18) escalation lanes were both pruned; the base handles all image work now.

⚠ **Agents-A1 (`controller`) is the only big model with intact safety training —
it refuses.** Verified 2026-07-17: it answers dual-use security questions
(SQL injection with example payload, authorized-pentest framing) but refuses
NSFW/explicit content generation. Use it as an executor for tool/agent loops,
not as a content generator. For an uncensored response route to an abliterated
model instead: default 35B or `writer` (Cydonia heretic).

## Commands

```bash
hermes-specialist list                 # role table, no models loaded
hermes-specialist check                # verify endpoints, no weights loaded
hermes-specialist run <role> --prompt "…"            # inline prompt
hermes-specialist run <role> --prompt-file /path.md  # file prompt (or pipe stdin)
hermes-specialist run vision-fast --image /path.png --prompt "Describe visible facts."
```

Flags for `run`:

- `--max-tokens N` — 1–8192, default 768. Raise for long outputs.
- `--temperature X` — 0–2, default 0.2. Writer typically 0.8.
- `--context N` — 4096 up to the role's cap.
- `--image PATH` — vision roles only; others reject it.
- `--keep-alive 2m` — only for deliberate repeated calls; default unloads immediately.

## Hard rules

1. **Never promote an Ollama specialist to the hermes default model.** Default
   is `ornith-uncensored` = Qwen3.6 35B-A3B ablit (llama-swap :1235, ttl 0 =
   kept warm, preloaded at startup). On 2026-07-17 the 8B `vision-fast`
   model was set as default; result was a queue deadlock in Ollama
   (one-model slot fight with the 30B) and a frozen agent.
2. Specialists are single-shot and tool-free — no tool schemas reach them.
   Anything needing tools goes to the default route or `controller`.
3. `think` and `code` share weights with the default route via llama-swap;
   swaps are cheap. Ollama roles (`research`, `writer`) each load
   fresh — do not fire them concurrently on this 64GB machine.
4. Check RAM before big Ollama roles: `memory_pressure -Q`. Unload stragglers
   with `ollama stop <model>` (never for llama-swap-owned models — see
   [[local-model-ops]]).
