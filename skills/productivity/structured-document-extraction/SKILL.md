---
name: structured-document-extraction
description: Extract JSON fields and tables from documents.
license: MIT
metadata:
  hermes:
    bundle: true
    domain: structured-document-extraction
    tags: [bundle, documents, extraction, ocr, json, qwen-vl]
    related_skills: [hawkeye-visual-evidence, ocr-and-documents, archivist-knowledge-pipeline]
---

# Structured Document Extraction

## Boundary

Convert authoritative document pixels into schema-valid records. Use the
existing local **vision lane** (the `vision-fast` specialist role — the base
model's own projector); do not install NuExtract or another model without swap
approval. Route general visual QA to Hawkeye and canonical
knowledge packaging to Archivist.

## Routing Table

| Stage | Skill | Output |
|---|---|---|
| Pixel/layout inspection | `hawkeye-visual-evidence` | Page observations and ambiguity |
| Literal OCR and document rendering | `ocr-and-documents` | Source text/page evidence |
| Canonical merge and provenance | `archivist-knowledge-pipeline` | Validated knowledge record |

## Orchestration Workflow

1. Define the target JSON schema, field types, required fields, page scope, and null policy before inference.
2. Render each source page deterministically and retain page/image paths.
3. Use OCR for literal text, then the vision lane (`vision-fast` role) for layout relationships and bounded field mapping.
4. Require source page and evidence text for every non-null field.
5. Parse the JSON, validate types/enums/required fields, and reject extra keys.
6. Reinspect low-confidence or contradictory fields against source pixels.
7. Hand validated records, rejected fields, evidence map, and source hashes to Archivist.

Read [references/schema-contract.md](references/schema-contract.md) before
designing a new extraction schema.

## Handoff Record

Record source hashes, rendered pages, declared schema, extraction model/mode,
validated JSON path, field evidence map, rejected fields, ambiguity, and next
Archivist action.

## Stop Conditions

- No target schema or authoritative source pixels exist.
- A field requires unsupported inference rather than extraction.
- Private source data would leave the local task boundary.
- Validation fails after one evidence-grounded correction pass.

## Completion Gate

- [ ] Output parses and validates against the declared schema
- [ ] Every value has page/evidence provenance or is explicitly null
- [ ] Tables preserve row/column relationships
- [ ] Low-confidence and rejected fields are surfaced
