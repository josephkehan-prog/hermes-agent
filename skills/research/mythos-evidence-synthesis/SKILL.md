---
name: mythos-evidence-synthesis
description: "Use when Mythos must reconcile multiple sources into a cited analytical brief while preserving contradictions, uncertainty, and the boundary between source claims and inference."
version: 1.0.0
author: Hermes War Room
license: MIT
platforms: [macos]
metadata:
  hermes:
    bundle: true
    domain: mythos-evidence-synthesis
    tags: [bundle, mythos, research, synthesis, citations]
    related_skills: [duckduckgo-search, arxiv, workspace-rag, open-databases, research-paper-writing, quick-summary]
---

# Mythos Evidence Synthesis

## Boundary

Own multi-source research and cited synthesis. Do not authorize commands,
operate services, make visual claims without Hawkeye, or draft fiction for Quill.

## Routing Table

| Stage | Skill | Inference mode |
|---|---|---|
| Discover current web sources | `duckduckgo-search` | Deterministic source collection |
| Locate scholarly evidence | `arxiv` | Deterministic paper metadata and methods |
| Recover local knowledge | `workspace-rag` | Deterministic retrieval |
| Verify structured public facts | `open-databases` | Deterministic query and provenance |
| Compress individual sources | `quick-summary` | Deterministic, preserve qualifications |
| Produce the final argument | `research-paper-writing` | Bounded synthesis after evidence closes |

## Orchestration Workflow

1. Decompose the question into claims and define an evidence class for each.
2. Build the claim ledger before drafting conclusions.
3. Call Qwythos through the bundled helper with `think:false`, no tools, and a
   bounded source packet; treat its output as an analytical draft that must map
   back to the ledger.
4. Reconcile contradictions explicitly and label every inference.
5. Produce the smallest format that answers the question with nearby citations.

```bash
python "$HERMES_HOME/hermes-agent/skills/research/mythos-evidence-synthesis/scripts/qwythos_synthesize.py" \
  --packet-file EVIDENCE-PACKET.md --output SYNTHESIS-DRAFT.md
```

Use the 32K default for normal evidence packets. Increase toward 128K only for
an explicit long-context job after checking memory pressure; the controller and
Qwythos are separate resident models on unified memory.

## Handoff Record

Record question, claim ledger path, source dates, support and contradiction
status, Qwythos prompt boundary, synthesis path, confidence, and open questions.

## Stop Conditions

- A consequential claim lacks a primary or authoritative source.
- Current and stale evidence cannot be distinguished.
- Qwythos output cannot be traced back to supplied evidence.

## Completion Gate

- [ ] Every material factual claim maps to evidence
- [ ] Source statements and inference are distinct
- [ ] Conflicts and uncertainty remain visible
- [ ] Qwythos was used only as a no-tool draft engine
- [ ] The result directly answers the original question
