---
name: canvas-local-visual-production
description: "Use when Canvas must turn a visual brief into a locally rendered, reproducible image and verify the result with visual evidence."
version: 1.0.0
author: Hermes War Room
license: MIT
platforms: [macos]
metadata:
  hermes:
    bundle: true
    domain: canvas-local-visual-production
    tags: [bundle, canvas, image-generation, local, reproducible]
    related_skills: [flux-local, comfyui, segment-anything-model, baoyu-infographic, huggingface-hub]
---

# Canvas Local Visual Production

## Boundary

Create and verify local visual assets. Do not perform broad UI diagnosis,
external hosted generation, factual research, or production software changes.

## Routing Table

| Need | Skill | Inference mode |
|---|---|---|
| Direct local prompt-to-image generation | `flux-local` | Seeded render by default |
| Node-based or multi-pass workflow | `comfyui` | Deterministic workflow graph |
| Isolate a subject or region | `segment-anything-model` | Deterministic mask generation |
| Build a data-led visual | `baoyu-infographic` | Bounded composition, deterministic export |
| Acquire a local model or adapter | `huggingface-hub` | Deterministic artifact identity |

## Orchestration Workflow

1. Resolve size, composition, style, content boundary, and output path.
2. Use an explicit seed and fixed parameters for production and revision; vary
   seeds only during a labeled exploratory pass.
3. Render locally with Z-Image-Turbo or the requested local workflow.
4. Inspect every render with the deterministic vision lane before delivery.
5. Record prompt, seed, model, adapter, dimensions, steps, quantization, and path.

## Handoff Record

Record brief, prompt, negative constraints, model and adapter, seed, dimensions,
steps, quantization, output paths, inspection result, and revision notes.

## Stop Conditions

- The request would send private inputs to a hosted generator.
- Required model or adapter provenance is unclear.
- The requested content violates the profile's safety boundary.
- The output cannot be opened and visually inspected.

## Completion Gate

- [ ] The render is local and the output file opens
- [ ] Production parameters are reproducible
- [ ] Exploratory and deterministic passes are labeled
- [ ] Visual inspection passed
- [ ] Exact artifact paths and settings are reported
