---
title: "Guidance"
sidebar_label: "Guidance"
description: "Control LLM output with regex and grammars, guarantee valid JSON/XML/code generation, enforce structured formats, and build multi-step workflows with Guidanc..."
---

{/* This page is auto-generated from the skill's SKILL.md by website/scripts/generate-skill-docs.py. Edit the source SKILL.md, not this page. */}

# Guidance

Control LLM output with regex and grammars, guarantee valid JSON/XML/code generation, enforce structured formats, and build multi-step workflows with Guidance - Microsoft Research's constrained generation framework

## Skill metadata

| | |
|---|---|
| Source | Optional — install with `hermes skills install official/mlops/guidance` |
| Path | `optional-skills/mlops/guidance` |
| Version | `1.0.0` |
| Author | Orchestra Research |
| License | MIT |
| Dependencies | `guidance`, `transformers` |
| Platforms | linux, macos, windows |
| Tags | `Prompt Engineering`, `Guidance`, `Constrained Generation`, `Structured Output`, `JSON Validation`, `Grammar`, `Microsoft Research`, `Format Enforcement`, `Multi-Step Workflows` |

## Reference: full SKILL.md

:::info
The following is the complete skill definition that Hermes loads when this skill is triggered. This is what the agent sees as instructions when the skill is active.
:::

# Guidance: Constrained LLM Generation

## When to Use This Skill

Use Guidance when you need to:
- **Control LLM output syntax** with regex or grammars
- **Guarantee valid JSON/XML/code** generation
- **Reduce latency** vs traditional prompting approaches
- **Enforce structured formats** (dates, emails, IDs, etc.)
- **Build multi-step workflows** with Pythonic control flow
- **Prevent invalid outputs** through grammatical constraints

**GitHub Stars**: 18,000+ | **From**: Microsoft Research

## Installation

```bash
# Base installation
pip install guidance

# With specific backends
pip install guidance[transformers]  # Hugging Face models
pip install guidance[llama_cpp]     # llama.cpp models
```

## Quick Start

### Basic Example: Structured Generation

```python
from guidance import models, gen

# Load model (supports OpenAI, Transformers, llama.cpp)
lm = models.OpenAI("gpt-4")

# Generate with constraints
result = lm + "The capital of France is " + gen("capital", max_tokens=5)

print(result["capital"])  # "Paris"
```

### With Anthropic Claude

```python
from guidance import models, gen, system, user, assistant

# Configure Claude
lm = models.Anthropic("claude-sonnet-4-5-20250929")

# Use context managers for chat format
with system():
    lm += "You are a helpful assistant."

with user():
    lm += "What is the capital of France?"

with assistant():
    lm += gen(max_tokens=20)
```

## Core Concepts

Five building blocks, each with full code examples in the linked reference:

1. **Context managers** (`system()`/`user()`/`assistant()`) — Pythonic chat-style role blocks; concatenate `lm +=` inside each. Natural flow, clear role separation.
2. **Constrained generation** — `gen(name, regex=...)` filters invalid tokens at the grammar level (guaranteed valid emails/dates/etc.); `select([...], name=...)` constrains to a fixed set of choices. Full regex/selection pattern library: `references/constraints.md`.
3. **Token healing** (on by default) — Guidance backs up one token at the prompt/generation boundary and regenerates, avoiding double-space/awkward-boundary artifacts from naive concatenation. Detail: `references/constraints.md` § Token Healing.
4. **Grammar-based generation** — define a context-free grammar (e.g. a JSON schema as `<gen ... regex=... >` placeholders) and pass it to `gen(name, grammar=...)` for guaranteed structural validity on complex/nested outputs. Full grammar examples: `references/constraints.md` § Grammar-Based Generation.
5. **`@guidance` functions** — the decorator turns a Python function into a reusable, composable generation unit; `@guidance(stateless=False)` supports stateful multi-round loops (e.g. a ReAct tool-use agent). Full function/agent examples: `references/examples.md` § Agent Systems.

Minimal illustration:

```python
from guidance import models, gen, select, system, user, assistant

lm = models.Anthropic("claude-sonnet-4-5-20250929")
with system():
    lm += "You are a JSON generation expert."
with user():
    lm += "What is the capital of France?"
with assistant():
    lm += gen("answer", max_tokens=20)

lm += "Sentiment: " + select(["positive", "negative", "neutral"], name="sentiment")
```

## Backend Configuration

Guidance supports API-based models (`models.Anthropic(...)`, `models.OpenAI(...)`, each reading the matching `*_API_KEY` env var by default) and local models (`guidance.models.Transformers(...)` for Hugging Face, `guidance.models.LlamaCpp(...)` for GGUF files with `n_ctx`/`n_gpu_layers`). Full setup code, available-model lists, and configuration options for every backend: read `references/backends.md` when wiring up a model.

## Common Patterns

Five production patterns — JSON generation, classification (sentiment/multi-label/intent), multi-step chain-of-thought reasoning, ReAct tool-use agents, and structured data extraction — each with full runnable code plus code-generation and production-tips sections beyond what's listed here: read `references/examples.md` before implementing any of these.

## Best Practices

Prefer the constrained primitive over free generation wherever the output has a known shape:
- **Regex over free-form** for anything with a validatable format (emails, dates, IDs) — `gen(name, regex=...)` not `gen(name, max_tokens=N)`.
- **`select()` over free-form** for fixed categories — guarantees no typos/invalid values.
- **Token healing** needs no special handling — just concatenate `lm += "prefix " + gen(...)` naturally; it's on by default.
- **`stop=` sequences** for single-line outputs, to avoid the model running past the intended field.
- **Wrap repeated shapes in `@guidance` functions** rather than copy-pasting the same `gen()` chain.
- **Don't over-constrain** — a regex like `^(John|Jane)$` can fail or slow generation; keep patterns as loose as correctness allows (e.g. `[A-Za-z ]+` with a `max_tokens` cap).

## Comparison to Alternatives

| Feature | Guidance | Instructor | Outlines | LMQL |
|---------|----------|------------|----------|------|
| Regex Constraints | ✅ Yes | ❌ No | ✅ Yes | ✅ Yes |
| Grammar Support | ✅ CFG | ❌ No | ✅ CFG | ✅ CFG |
| Pydantic Validation | ❌ No | ✅ Yes | ✅ Yes | ❌ No |
| Token Healing | ✅ Yes | ❌ No | ✅ Yes | ❌ No |
| Local Models | ✅ Yes | ⚠️ Limited | ✅ Yes | ✅ Yes |
| API Models | ✅ Yes | ✅ Yes | ⚠️ Limited | ✅ Yes |
| Pythonic Syntax | ✅ Yes | ✅ Yes | ✅ Yes | ❌ SQL-like |
| Learning Curve | Low | Low | Medium | High |

**When to choose Guidance:**
- Need regex/grammar constraints
- Want token healing
- Building complex workflows with control flow
- Using local models (Transformers, llama.cpp)
- Prefer Pythonic syntax

**When to choose alternatives:**
- Instructor: Need Pydantic validation with automatic retrying
- Outlines: Need JSON schema validation
- LMQL: Prefer declarative query syntax

## Performance Characteristics

**Latency Reduction:**
- 30-50% faster than traditional prompting for constrained outputs
- Token healing reduces unnecessary regeneration
- Grammar constraints prevent invalid token generation

**Memory Usage:**
- Minimal overhead vs unconstrained generation
- Grammar compilation cached after first use
- Efficient token filtering at inference time

**Token Efficiency:**
- Prevents wasted tokens on invalid outputs
- No need for retry loops
- Direct path to valid outputs

## Resources

- **Documentation**: https://guidance.readthedocs.io
- **GitHub**: https://github.com/guidance-ai/guidance (18k+ stars)
- **Notebooks**: https://github.com/guidance-ai/guidance/tree/main/notebooks
- **Discord**: Community support available

## See Also

- `references/constraints.md` - Comprehensive regex and grammar patterns
- `references/backends.md` - Backend-specific configuration
- `references/examples.md` - Production-ready examples
