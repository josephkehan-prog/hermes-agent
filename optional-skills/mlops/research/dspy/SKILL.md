---
name: dspy
description: "DSPy: declarative LM programs, auto-optimize prompts, RAG."
version: 1.0.0
author: Orchestra Research
license: MIT
dependencies: [dspy, openai, anthropic]
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [Prompt Engineering, DSPy, Declarative Programming, RAG, Agents, Prompt Optimization, LM Programming, Stanford NLP, Automatic Optimization, Modular AI]

---

# DSPy: Declarative Language Model Programming

## When to Use This Skill

Use DSPy when you need to:
- **Build complex AI systems** with multiple components and workflows
- **Program LMs declaratively** instead of manual prompt engineering
- **Optimize prompts automatically** using data-driven methods
- **Create modular AI pipelines** that are maintainable and portable
- **Improve model outputs systematically** with optimizers
- **Build RAG systems, agents, or classifiers** with better reliability

**GitHub Stars**: 22,000+ | **Created By**: Stanford NLP

## Installation

```bash
# Stable release
pip install dspy

# Latest development version
pip install git+https://github.com/stanfordnlp/dspy.git

# With specific LM providers
pip install dspy[openai]        # OpenAI
pip install dspy[anthropic]     # Anthropic Claude
pip install dspy[all]           # All providers
```

## Quick Start

### Basic Example: Question Answering

```python
import dspy

# Configure your language model
lm = dspy.Claude(model="claude-sonnet-4-5-20250929")
dspy.settings.configure(lm=lm)

# Define a signature (input → output)
class QA(dspy.Signature):
    """Answer questions with short factual answers."""
    question = dspy.InputField()
    answer = dspy.OutputField(desc="often between 1 and 5 words")

# Create a module
qa = dspy.Predict(QA)

# Use it
response = qa(question="What is the capital of France?")
print(response.answer)  # "Paris"
```

## Core Concepts

### 1. Signatures

Signatures define the structure of your AI task (inputs → outputs):

```python
# Inline signature (simple)
qa = dspy.Predict("question -> answer")

# Class signature (detailed)
class Summarize(dspy.Signature):
    """Summarize text into key points."""
    text = dspy.InputField()
    summary = dspy.OutputField(desc="bullet points, 3-5 items")

summarizer = dspy.ChainOfThought(Summarize)
```

**When to use each:**
- **Inline**: Quick prototyping, simple tasks
- **Class**: Complex tasks, type hints, better documentation

### 2. Modules

Modules are reusable components that transform inputs to outputs. The four core ones:
- **`dspy.Predict`** — basic prediction from a signature
- **`dspy.ChainOfThought`** — generates reasoning steps (`.rationale`) before the final answer
- **`dspy.ReAct`** — agent-like reasoning that calls tools
- **`dspy.ProgramOfThought`** — generates and executes code to compute the answer

Full usage, plus advanced modules (`TypedPredictor`, `Retry`, `Assert`, `MultiChainComparison`, `majority`), composition patterns (sequential/conditional/parallel), batch processing, and save/load: read `references/modules.md`.

### 3. Optimizers

Optimizers improve your modules automatically using training data. Core ones: **BootstrapFewShot** (learns few-shot demos from examples), **MIPRO** (iterative prompt search), **BootstrapFinetune** (exports fine-tuning data), plus COPRO and KNNFewShot.

Full compile() usage per optimizer, writing metrics (binary/continuous/multi-factor), train/val/test workflow, and common pitfalls (overfitting, mismatched metrics, insufficient data): read `references/optimizers.md`.

### 4. Building Complex Systems

Modules compose into multi-stage pipelines by subclassing `dspy.Module` and defining `forward()` — e.g. a multi-hop QA system that generates a search query, retrieves, then answers. Full multi-stage pipeline, RAG-with-optimization, multi-hop RAG, agent systems, and classifier examples: read `references/examples.md`.

## LM Provider Configuration

### Anthropic Claude

```python
import dspy

lm = dspy.Claude(
    model="claude-sonnet-4-5-20250929",
    api_key="your-api-key",  # Or set ANTHROPIC_API_KEY env var
    max_tokens=1000,
    temperature=0.7
)
dspy.settings.configure(lm=lm)
```

### OpenAI

```python
lm = dspy.OpenAI(
    model="gpt-4",
    api_key="your-api-key",
    max_tokens=1000
)
dspy.settings.configure(lm=lm)
```

### Local Models & Multiple Models

`dspy.OllamaLocal(model="llama3.1", base_url="http://localhost:11434")` for local inference. For mixed pipelines, scope a cheaper model to retrieval and a stronger one to reasoning with `with dspy.settings.context(lm=...)`.

## Common Patterns

Structured output via `dspy.TypedPredictor` + Pydantic models, assertion-driven optimization (`dspy.Assert` + backtracking), self-consistency (sample N times, take majority answer), and retrieval-with-reranking are all common compositions of the modules above. Full code for each: read `references/examples.md` and `references/modules.md` (TypedPredictor/Assert/majority sections).

## Evaluation and Metrics

Write a metric function `(example, pred, trace=None) -> bool | float` (exact-match, F1, or custom), then run it with `dspy.evaluate.Evaluate(devset=testset, metric=metric, num_threads=4)` — call the evaluator on both the baseline and optimized module to measure improvement.

Metric design (binary/continuous/multi-factor), train/val/test splitting, and cross-validation: read `references/optimizers.md` (Writing Metrics, Evaluation Best Practices).

## Best Practices

1. **Start simple, iterate** — `Predict` → `ChainOfThought` → optimizer, only adding complexity once the simpler stage is validated.
2. **Use descriptive signatures** — name fields and write docstrings/`desc=` instead of generic `input`/`output`; DSPy's optimizers use these descriptions.
3. **Optimize with representative, diverse training data** — and hold out a separate validation set for the metric.
4. **Save/load optimized modules** — `module.save("path.json")` / `module.load("path.json")` so a compile step isn't repeated.
5. **Enable tracing when debugging** — `dspy.settings.configure(lm=lm, trace=[])`, then inspect `dspy.settings.trace` for the actual prompts/responses sent.

## Comparison to Other Approaches

| Feature | Manual Prompting | LangChain | DSPy |
|---------|-----------------|-----------|------|
| Prompt Engineering | Manual | Manual | Automatic |
| Optimization | Trial & error | None | Data-driven |
| Modularity | Low | Medium | High |
| Type Safety | No | Limited | Yes (Signatures) |
| Portability | Low | Medium | High |
| Learning Curve | Low | Medium | Medium-High |

**When to choose DSPy:**
- You have training data or can generate it
- You need systematic prompt improvement
- You're building complex multi-stage systems
- You want to optimize across different LMs

**When to choose alternatives:**
- Quick prototypes (manual prompting)
- Simple chains with existing tools (LangChain)
- Custom optimization logic needed

## Resources

- **Documentation**: https://dspy.ai
- **GitHub**: https://github.com/stanfordnlp/dspy (22k+ stars)
- **Discord**: https://discord.gg/XCGy2WDCQB
- **Twitter**: @DSPyOSS
- **Paper**: "DSPy: Compiling Declarative Language Model Calls into Self-Improving Pipelines"

## See Also

- `references/modules.md` - Detailed module guide (Predict, ChainOfThought, ReAct, ProgramOfThought)
- `references/optimizers.md` - Optimization algorithms (BootstrapFewShot, MIPRO, BootstrapFinetune)
- `references/examples.md` - Real-world examples (RAG, agents, classifiers)


