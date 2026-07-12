---
name: local-ai-lifecycle-bundle
description: "Use when selecting, acquiring, serving, evaluating, and operating local or self-hosted language models across hardware constraints and knowledge workflows. Coordinates the model lifecycle from requirements to measured runtime behavior."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    bundle: true
    domain: local-ai-lifecycle
    tags: [bundle, local-ai, mlops, inference, evaluation]
    related_skills: [local-model-ops, huggingface-hub, serving-llms-vllm, evaluating-llms-harness, workspace-rag]
---

# Local AI Lifecycle Bundle

## Boundary

Manage a local or self-hosted model across more than one lifecycle stage. Do
not invoke the bundle for a single model download, one inference command, or a
cloud-provider-only deployment.

## Routing Table

| Lifecycle stage | Primary skill | Exit evidence |
|---|---|---|
| Inventory, select, or operate local models | `local-model-ops` | Hardware-fit model and runtime state |
| Discover or acquire model artifacts | `huggingface-hub` | Pinned model identity and files |
| Serve high-throughput inference | `serving-llms-vllm` | Healthy endpoint and measured configuration |
| Compare quality or regressions | `evaluating-llms-harness` | Reproducible benchmark results |
| Ground responses in local knowledge | `workspace-rag` | Indexed corpus and retrieval check |

## Orchestration Workflow

1. Define task, quality floor, privacy boundary, latency/throughput target,
   context length, hardware, and storage budget.
2. Inventory the machine before selecting model size, format, or server.
3. Pin model repository, revision, quantization, tokenizer, and license before
   download or deployment.
4. Establish a direct inference baseline, then configure `serving-llms-vllm` only when its
   serving model and hardware requirements fit.
5. Evaluate the actual use case, not just generic benchmarks. Add
   `workspace-rag` only when external local knowledge is part of the outcome.
6. Record measured memory, latency, throughput, task quality, and failure modes.

## Handoff Record

Track use case, machine inventory, model/revision, artifact hashes, runtime
arguments, prompt/template, evaluation suite, results, corpus/index state, and
rollback or uninstall steps.

## Stop Conditions

- Model license or provenance is unclear.
- Estimated memory or disk use exceeds the approved budget.
- Evaluation data contains secrets outside the stated privacy boundary.
- A server configuration cannot be compared to a known direct baseline.

## Completion Gate

- [ ] Model and runtime fit the measured hardware constraints
- [ ] Artifact identity and revision are reproducible
- [ ] Endpoint or local invocation passes a real inference smoke test
- [ ] Quality is measured on representative tasks
- [ ] RAG retrieval is tested separately from answer generation if used
- [ ] Resource use, limitations, and cleanup steps are documented

## Common Pitfalls

- Choosing by parameter count without checking memory format
- Comparing models with different prompts or decoding settings
- Calling a server healthy because its process exists
- Blaming generation for a retrieval failure
