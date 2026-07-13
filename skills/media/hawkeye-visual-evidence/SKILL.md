---
name: hawkeye-visual-evidence
description: "Use when Hawkeye must inspect a UI, screenshot, rendered document, or image and return reproducible visual observations separated from inference."
version: 1.0.0
author: Hermes War Room
license: MIT
platforms: [macos]
metadata:
  hermes:
    bundle: true
    domain: hawkeye-visual-evidence
    tags: [bundle, hawkeye, vision, ui, ocr, documents]
    related_skills: [computer-use, dogfood, ocr-and-documents, nano-pdf, segment-anything-model]
---

# Hawkeye Visual Evidence

## Boundary

Inspect pixels, rendered pages, and live UI state. Do not generate final assets,
conduct broad research, or implement production code beyond a necessary test fixture.

## Routing Table

| Evidence | Skill | Inference mode |
|---|---|---|
| Live application interaction | `computer-use` | Deterministic actions and screenshots |
| Product-flow visual QA | `dogfood` | Deterministic reproduction and checkpoints |
| Text in images or documents | `ocr-and-documents` | Deterministic extraction before interpretation |
| PDF layout and page evidence | `nano-pdf` | Deterministic page rendering |
| Object or region isolation | `segment-anything-model` | Deterministic coordinates and masks |

## Orchestration Workflow

1. Capture the authoritative pixels or render before making a claim.
2. Use Qwen3-VL in non-thinking mode for observation, OCR, coordinates, and
   concise descriptions; do not ask it to invent missing visual evidence.
3. Separate observations from inferences and attach a screenshot or file path.
4. Repeat the same deterministic action after any fix and compare evidence.
5. Route asset creation to Canvas and code changes to Vanguard.

## Handoff Record

Record source path or URL, viewport or page, action sequence, observed facts,
inferences, screenshots, confidence, and unresolved visual ambiguity.

## Stop Conditions

- The source pixels cannot be accessed or rendered.
- Private content would leave the task boundary.
- A claim depends on hidden state rather than visible evidence.

## Completion Gate

- [ ] The actual pixels or rendered pages were inspected
- [ ] Observation and inference are clearly separated
- [ ] OCR, coordinates, or UI actions are reproducible
- [ ] Evidence paths are included
- [ ] Post-change visual verification was run when applicable
