---
title: "Evidence Research Bundle"
sidebar_label: "Evidence Research Bundle"
description: "Use when answering a consequential research question with current web evidence, scholarly literature, public datasets, local knowledge, and a cited synthesis"
---

{/* This page is auto-generated from the skill's SKILL.md by website/scripts/generate-skill-docs.py. Edit the source SKILL.md, not this page. */}

# Evidence Research Bundle

Use when answering a consequential research question with current web evidence, scholarly literature, public datasets, local knowledge, and a cited synthesis. Routes discovery and verification by source type and claim strength.

## Skill metadata

| | |
|---|---|
| Source | Bundled (installed by default) |
| Path | `skills/research/evidence-research-bundle` |
| Version | `1.0.0` |
| Author | Hermes Agent |
| License | MIT |
| Platforms | linux, macos, windows |
| Tags | `bundle`, `research`, `evidence`, `synthesis`, `citations` |
| Related skills | [`duckduckgo-search`](/docs/user-guide/skills/bundled/duckduckgo-search/duckduckgo-search-duckduckgo-search), [`arxiv`](/docs/user-guide/skills/bundled/research/research-arxiv), [`open-databases`](/docs/user-guide/skills/bundled/research/research-open-databases), [`last30days`](/docs/user-guide/skills/bundled/research/research-last30days), [`workspace-rag`](/docs/user-guide/skills/bundled/research/research-workspace-rag), [`research-paper-writing`](/docs/user-guide/skills/bundled/research/research-research-paper-writing) |

## Reference: full SKILL.md

:::info
The following is the complete skill definition that Hermes loads when this skill is triggered. This is what the agent sees as instructions when the skill is active.
:::

# Evidence Research Bundle

## Boundary

Produce a traceable synthesis when a question needs multiple evidence classes.
Do not invoke the full bundle for a simple lookup, a local-document-only query,
or prose editing without new research.

## Routing Table

| Evidence need | Primary skill | Use for |
|---|---|---|
| Broad web discovery | `duckduckgo-search` | Candidate sources and terminology |
| Scholarly claims | `arxiv` | Papers, methods, and research lineage |
| Structured public facts | `open-databases` | Government and public datasets |
| Fast-changing discourse | `last30days` | Recent developments and reactions |
| Existing local knowledge | `workspace-rag` | Workspace decisions and prior evidence |
| Formal scholarly synthesis | `research-paper-writing` | Structured paper-grade argument |

## Orchestration Workflow

1. Decompose the question into claims and label each as current, scholarly,
   quantitative, local, or interpretive.
2. Route each claim to its strongest primary evidence source. Use broad search
   for discovery, not as the final authority when a primary source exists.
3. Capture publication date, event date, author/publisher, URL or local path,
   and the exact claim supported.
4. Reconcile contradictions explicitly; do not average incompatible evidence.
5. Synthesize only after every material claim has support or is labeled an
   inference, unknown, or disputed.

## Handoff Record

Use a claim ledger with: claim ID, claim text, evidence class, source, date,
support/contradiction status, confidence, and notes. The final narrative must
map back to this ledger.

## Stop Conditions

- The question requires private data or access not provided.
- Current evidence cannot be distinguished from stale evidence.
- Sources repeat one unverified origin rather than independently corroborate.
- A high-stakes claim lacks an authoritative primary source.

## Completion Gate

- [ ] Every material factual claim has nearby traceable support
- [ ] Current claims use current sources and distinguish event/publication date
- [ ] Scholarly and quantitative claims use appropriate primary evidence
- [ ] Contradictions, uncertainty, and inference are labeled
- [ ] Local memory is not presented as confirmed-current without verification
- [ ] The synthesis answers the original question, not merely lists sources

## Common Pitfalls

- Treating search snippets as evidence
- Counting syndicated copies as independent corroboration
- Mixing historical and current facts without dates
- Writing the conclusion before constructing the claim ledger
