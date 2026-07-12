---
name: outlines
description: "Outlines: structured JSON/regex/Pydantic LLM generation."
version: 1.0.0
author: Orchestra Research
license: MIT
dependencies: [outlines, transformers, vllm, pydantic]
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [Prompt Engineering, Outlines, Structured Generation, JSON Schema, Pydantic, Local Models, Grammar-Based Generation, vLLM, Transformers, Type Safety]

---

# Outlines: Structured Text Generation

## When to Use This Skill

Use Outlines when you need to:
- **Guarantee valid JSON/XML/code** structure during generation
- **Use Pydantic models** for type-safe outputs
- **Support local models** (Transformers, llama.cpp, vLLM)
- **Maximize inference speed** with zero-overhead structured generation
- **Generate against JSON schemas** automatically
- **Control token sampling** at the grammar level

**GitHub Stars**: 8,000+ | **From**: dottxt.ai (formerly .txt)

## Installation

```bash
# Base installation
pip install outlines

# With specific backends
pip install outlines transformers  # Hugging Face models
pip install outlines llama-cpp-python  # llama.cpp
pip install outlines vllm  # vLLM for high-throughput
```

## Quick Start

### Basic Example: Classification

```python
import outlines
from typing import Literal

# Load model
model = outlines.models.transformers("microsoft/Phi-3-mini-4k-instruct")

# Generate with type constraint
prompt = "Sentiment of 'This product is amazing!': "
generator = outlines.generate.choice(model, ["positive", "negative", "neutral"])
sentiment = generator(prompt)

print(sentiment)  # "positive" (guaranteed one of these)
```

### With Pydantic Models

```python
from pydantic import BaseModel
import outlines

class User(BaseModel):
    name: str
    age: int
    email: str

model = outlines.models.transformers("microsoft/Phi-3-mini-4k-instruct")

# Generate structured output
prompt = "Extract user: John Doe, 30 years old, john@example.com"
generator = outlines.generate.json(model, User)
user = generator(prompt)

print(user.name)   # "John Doe"
print(user.age)    # 30
print(user.email)  # "john@example.com"
```

## Core Concepts

### Constrained Token Sampling

Outlines converts a schema (JSON/Pydantic/regex) to a context-free grammar,
then a Finite State Machine, and filters invalid tokens at each generation
step (fast-forwarding when only one valid token exists). This gives zero
runtime overhead versus unconstrained generation and **guaranteed-valid**
output — no retry loops needed.

### Structured Generators

- `outlines.generate.choice(model, [...])` — multiple choice / classification
- `outlines.generate.json(model, PydanticModel)` — JSON matching a schema
- `outlines.generate.regex(model, pattern)` — text matching a regex
- `outlines.generate.integer(model)` / `.float(model)` — constrained numeric types

Full generator examples and JSON-schema-direct usage: read `references/json_generation.md`.

### Model Backends

Transformers (Hugging Face), llama.cpp (GGUF), vLLM (high-throughput
production), and limited OpenAI support — all take the same
`outlines.generate.*` calls once `model = outlines.models.<backend>(...)` is
constructed. GPU/quantization config, popular-model picks, and production
deployment: read `references/backends.md`.

### Pydantic Integration

First-class support for basic models, nested models, and `Enum`/`Literal`
constrained fields — schema translation is automatic. Full nested/enum/union
examples, JSON Schema direct usage, recursive models, and caching generators
for performance: read `references/json_generation.md`.

## Common Patterns

Data extraction, classification (binary/multi-class/with-confidence),
structured forms, multi-entity extraction, code generation, and batch
processing — all follow the same `generator = outlines.generate.json(model,
Schema)` shape with a task-specific Pydantic model. Full worked examples
including production patterns (error handling, caching, monitoring, rate
limiting): read `references/examples.md`.

## Best Practices (quick reference)

- Use specific types (`float`/`int`/`bool`), not everything as `str`.
- Add `Field` constraints (`min_length`, `ge`/`le`, `pattern`) — they narrow the FSM and improve accuracy.
- Prefer `Enum`/`Literal` over free-form strings for fixed categories.
- Give the prompt clear context, not just the bare input text.
- Make non-essential fields `Optional[...]` with defaults so extraction can still succeed on incomplete data.

Full before/after examples for each: read `references/json_generation.md`.

## Comparison & Performance

Outlines vs. Instructor/Guidance/LMQL feature matrix, when to choose each,
and speed/memory/accuracy characteristics: read `references/comparison.md`.

## Resources

- **Documentation**: https://outlines-dev.github.io/outlines
- **GitHub**: https://github.com/outlines-dev/outlines (8k+ stars)
- **Discord**: https://discord.gg/R9DSu34mGd
- **Blog**: https://blog.dottxt.co

## See Also

- `references/json_generation.md` - Comprehensive JSON and Pydantic patterns, best practices
- `references/backends.md` - Backend-specific configuration and performance tuning
- `references/examples.md` - Production-ready examples
- `references/comparison.md` - Alternatives comparison and performance characteristics


