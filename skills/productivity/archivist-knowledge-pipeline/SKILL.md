---
name: archivist-knowledge-pipeline
description: Turn documents into one canonical knowledge artifact.
version: 1.0.0
author: Hermes War Room
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    bundle: true
    domain: knowledge-pipeline
    tags: [bundle, knowledge, provenance, documents, canonical-source]
    related_skills: [quick-summary, ocr-and-documents, nano-pdf, obsidian, notion, google-workspace, powerpoint, llm-wiki, war-room-specialist-cascade]
---

# Archivist Knowledge Pipeline

## Boundary

Own one knowledge packet: source inventory, extraction, provenance map,
canonical artifact, derived formats, and render validation. Do not create
multiple canonical copies, overwrite sources, or share externally without authorization.

## Routing Table

| Surface | Skill | Mode |
|---|---|---|
| Source compression | `quick-summary` | Deterministic, preserve caveats |
| Scans and mixed documents | `ocr-and-documents` | Deterministic extraction |
| PDF inspection or transformation | `nano-pdf` | Deterministic plus visual verification |
| Local linked notes | `obsidian` | Deterministic organization |
| Structured workspace | `notion` | Deterministic API operations |
| Google documents and files | `google-workspace` | Deterministic API operations |
| Presentation derivative | `powerpoint` | Bounded composition, deterministic export |
| Local knowledge base | `llm-wiki` | Bounded structure from cited sources |
| Schema-first fields/tables from document pixels | `war-room-specialist-cascade` | Hidden `extractor` profile |

## Orchestration Workflow

1. Identify sources, owner, audience, requested formats, and canonical destination.
2. Extract before summarizing; preserve page, path, URL, note, or file provenance.
3. Normalize names, dates, claims, headings, and unresolved ambiguities into one outline.
4. Write the canonical artifact once, then derive secondary notes, PDFs, slides, or wiki pages.
5. Render visual derivatives and route pixel-level inspection to Hawkeye; verify links and sharing only when requested.
6. Route schema-first extraction through the hidden Extractor worker, then
   validate and merge its evidence-backed records into the canonical artifact.

## Handoff Record

Record source IDs and paths, extraction method, provenance map, canonical output,
derived artifacts, OCR ambiguities, render checks, and sharing state.

## Stop Conditions

- Canonical destination or overwrite authority is unclear.
- OCR ambiguity changes a material name, number, or regulated meaning.
- A source contains secrets that should not move to the target system.
- External sharing or sending is not explicitly authorized.

## Completion Gate

- [ ] Every material claim maps to a source
- [ ] One canonical version is identified
- [ ] Derived artifacts agree with the canonical version
- [ ] Visual documents were rendered and, when needed, inspected by Hawkeye
- [ ] Sharing state matches the exact request
