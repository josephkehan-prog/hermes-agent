---
name: knowledge-workflow-bundle
description: Capture and transform knowledge across documents.
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    bundle: true
    domain: knowledge-workflow
    tags: [bundle, knowledge-management, documents, notes]
    related_skills: [obsidian, apple-notes, notion, google-workspace, ocr-and-documents, nano-pdf, powerpoint]
---

# Knowledge Workflow Bundle

## Boundary

Coordinate knowledge work that crosses capture, extraction, organization, and
presentation. Use a focused member directly when the request concerns only one
known file or one note system.

## Routing Table

| Knowledge surface | Primary skill | Role |
|---|---|---|
| Local linked knowledge base | `obsidian` | Canonical Markdown notes and links |
| Native macOS note capture | `apple-notes` | Locate or capture Apple Notes content |
| Structured collaborative workspace | `notion` | Pages, databases, and organization |
| Google documents and files | `google-workspace` | Search, create, update, and share |
| Scans and mixed documents | `ocr-and-documents` | Extract and normalize source content |
| PDF-specific manipulation | `nano-pdf` | Inspect or transform PDF artifacts |
| Presentation output | `powerpoint` | Build and verify slide deliverables |

## Orchestration Workflow

1. Identify source artifacts, owning system, target audience, final formats,
   and which location remains canonical.
2. Extract before summarizing. Preserve page, URL, note, or file provenance for
   every important statement.
3. Normalize concepts, dates, names, and headings into one intermediate outline
   without overwriting the source.
4. Write back to the chosen canonical system, then derive PDFs, slides, or
   secondary notes from that version.
5. Render and inspect every visual document. Verify links and sharing state only
   when the user requested external access.

## Handoff Record

Record source IDs/paths, extraction method, provenance map, canonical output,
derived artifacts, unresolved OCR ambiguities, render checks, and sharing
permissions. Distinguish created content from source quotations.

## Stop Conditions

- The canonical source or overwrite authority is unclear.
- OCR ambiguity changes a material name, number, or legal/medical meaning.
- A file contains secrets that should not move to the target workspace.
- Sharing or sending an artifact has not been authorized.

## Completion Gate

- [ ] All requested sources were captured or explicitly unavailable
- [ ] Material claims retain source provenance
- [ ] One canonical version is identified
- [ ] Derived formats agree with the canonical content
- [ ] PDFs/slides/documents were rendered and visually inspected
- [ ] Sharing permissions match the user's request and nothing broader

## Common Pitfalls

- Summarizing before extraction is complete
- Creating multiple conflicting canonical copies
- Treating OCR output as exact for names and numbers
- Verifying file existence without inspecting rendered layout
