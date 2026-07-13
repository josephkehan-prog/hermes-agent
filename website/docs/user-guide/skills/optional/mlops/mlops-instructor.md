---
title: "Instructor"
sidebar_label: "Instructor"
description: "Extract structured data from LLM responses with Pydantic validation, retry failed extractions automatically, parse complex JSON with type safety, and stream ..."
---

{/* This page is auto-generated from the skill's SKILL.md by website/scripts/generate-skill-docs.py. Edit the source SKILL.md, not this page. */}

# Instructor

Extract structured data from LLM responses with Pydantic validation, retry failed extractions automatically, parse complex JSON with type safety, and stream partial results with Instructor - battle-tested structured output library

## Skill metadata

| | |
|---|---|
| Source | Optional — install with `hermes skills install official/mlops/instructor` |
| Path | `optional-skills/mlops/instructor` |
| Version | `1.0.0` |
| Author | Orchestra Research |
| License | MIT |
| Dependencies | `instructor`, `pydantic`, `openai`, `anthropic` |
| Platforms | linux, macos, windows |
| Tags | `Prompt Engineering`, `Instructor`, `Structured Output`, `Pydantic`, `Data Extraction`, `JSON Parsing`, `Type Safety`, `Validation`, `Streaming`, `OpenAI`, `Anthropic` |

## Reference: full SKILL.md

:::info
The following is the complete skill definition that Hermes loads when this skill is triggered. This is what the agent sees as instructions when the skill is active.
:::

# Instructor: Structured LLM Outputs

## When to Use This Skill

Use Instructor when you need to:
- **Extract structured data** from LLM responses reliably
- **Validate outputs** against Pydantic schemas automatically
- **Retry failed extractions** with automatic error handling
- **Parse complex JSON** with type safety and validation
- **Stream partial results** for real-time processing
- **Support multiple LLM providers** with consistent API

**GitHub Stars**: 15,000+ | **Battle-tested**: 100,000+ developers

## Installation

```bash
# Base installation
pip install instructor

# With specific providers
pip install "instructor[anthropic]"  # Anthropic Claude
pip install "instructor[openai]"     # OpenAI
pip install "instructor[all]"        # All providers
```

## Quick Start

```python
import instructor
from pydantic import BaseModel
from anthropic import Anthropic

# Define output structure
class User(BaseModel):
    name: str
    age: int
    email: str

# Create instructor client
client = instructor.from_anthropic(Anthropic())

# Extract structured data
user = client.messages.create(
    model="claude-sonnet-4-5-20250929",
    max_tokens=1024,
    messages=[{
        "role": "user",
        "content": "John Doe is 30 years old. His email is john@example.com"
    }],
    response_model=User
)

print(user.name)   # "John Doe"
print(user.age)    # 30
print(user.email)  # "john@example.com"
```

Other providers (OpenAI, local Ollama) use the same `response_model=` pattern
with a different client factory: read `references/providers.md`.

## Core Concepts

### Response Models (Pydantic)

Response models define the structure and validation rules for LLM outputs —
plain Pydantic models with `Field(description=...)` for self-documenting,
type-safe, IDE-autocompleted extraction:

```python
from pydantic import BaseModel, Field

class Article(BaseModel):
    title: str = Field(description="Article title")
    author: str = Field(description="Author name")
    word_count: int = Field(description="Number of words", gt=0)
    tags: list[str] = Field(description="List of relevant tags")

article = client.messages.create(
    model="claude-sonnet-4-5-20250929",
    max_tokens=1024,
    messages=[{"role": "user", "content": "Analyze this article: [article text]"}],
    response_model=Article
)
```

Nested models, optional fields, enums, union types, dynamic (`create_model`)
models, custom `Mode.*` settings, and client context management: read
`references/advanced.md`.

### Validation

Pydantic validates LLM outputs automatically — built-in constraints
(`Field(ge=..., le=...)`, `EmailStr`, `HttpUrl`), custom `@field_validator`
and `@model_validator` methods, and error-message design so retries actually
correct themselves: read `references/validation.md` when defining a schema
with non-trivial validation rules or debugging retry loops.

### Automatic Retrying

Instructor retries automatically when validation fails, providing error
feedback to the LLM:

```python
user = client.messages.create(
    model="claude-sonnet-4-5-20250929",
    max_tokens=1024,
    messages=[{"role": "user", "content": "Extract user from: John, age unknown"}],
    response_model=User,
    max_retries=3  # Default is 3
)
```

**How it works:** LLM generates output → Pydantic validates → if invalid, the
error message is sent back to the LLM → LLM retries with that feedback →
repeats up to `max_retries`.

### Streaming

Stream partial objects (`client.messages.create_partial(...)`) or partial
list items (`client.messages.create_iterable(...)`) for real-time UI updates
instead of waiting for the full response. Full streaming examples and common
extraction patterns (classification, multi-entity, batch processing): read
`references/examples.md`.

## Error Handling

Catch `pydantic.ValidationError` for extractions that still fail after
`max_retries`, and catch other exceptions for API-level errors. Inspecting
individual field errors and writing validator messages the LLM can act on:
read `references/validation.md`.

## Best Practices (quick reference)

- Write descriptive `Field(description=...)` text — it is part of the prompt.
- Constrain values with `ge`/`le`/`min_length`/enums rather than free-text +
  a validator when possible.
- Give the LLM a worked example in the prompt for tricky formats.
- Make non-essential fields `Optional[...]` with sane defaults so extraction
  doesn't fail on missing data.

Full best-practices list with before/after code: read
`references/validation.md`.

## Provider Configuration & Comparison

Anthropic, OpenAI, and local Ollama client setup: `references/providers.md`.
Nested/optional/enum/union model patterns, custom modes, context management,
and a feature comparison against manual JSON / LangChain / DSPy:
`references/advanced.md`.

## Resources

- **Documentation**: https://python.useinstructor.com
- **GitHub**: https://github.com/jxnl/instructor (15k+ stars)
- **Cookbook**: https://python.useinstructor.com/examples
- **Discord**: Community support available

## See Also

- `references/validation.md` - Advanced validation patterns, error handling, best practices
- `references/providers.md` - Provider-specific configuration
- `references/examples.md` - Real-world use cases and streaming examples
- `references/advanced.md` - Modeling patterns, custom modes, comparison table
