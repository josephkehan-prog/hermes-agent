---
name: research-paper-writing
title: Research Paper Writing Pipeline
description: "Write ML papers for NeurIPS/ICML/ICLR: design→submit."
version: 1.1.0
author: Orchestra Research
license: MIT
dependencies: [semanticscholar, arxiv, habanero, requests, scipy, numpy, matplotlib, SciencePlots]
platforms: [linux, macos]
metadata:
  hermes:
    tags: [Research, Paper Writing, Experiments, ML, AI, NeurIPS, ICML, ICLR, ACL, AAAI, COLM, LaTeX, Citations, Statistical Analysis]
    category: research
    related_skills: [arxiv, ml-paper-writing, subagent-driven-development, plan]
    requires_toolsets: [terminal, files]

---

# Research Paper Writing Pipeline

End-to-end pipeline for publication-ready ML/AI papers for **NeurIPS, ICML, ICLR, ACL, AAAI, COLM**: design, execution, analysis, writing, review, submission. **Not linear** — an iterative loop; Phase 4/6 results commonly feed back into Phase 2/5. Phases: 0 Setup → 1 Literature → 2 Experiment Design → 3 Execution/Monitoring → 4 Analysis → 5 Drafting → 6 Self-Review → 7 Submission → 8 Post-Acceptance. Use for: a paper from a codebase/idea, designing/running experiments, writing/revising sections, venue conversion, responding to reviews, non-empirical papers ([paper-types.md](references/paper-types.md)), human evaluations, post-acceptance work ([post-acceptance.md](references/post-acceptance.md)).

## Core Philosophy

1. **Be proactive** — deliver complete drafts, not questions; iterate on feedback.
2. **Never hallucinate citations** — ~40% error rate in AI-generated citations. Fetch programmatically; unverifiable → `[CITATION NEEDED]`.
3. **Paper is a story**, not a pile of experiments — one contribution, one sentence.
4. **Experiments serve claims** — every experiment states which claim it supports, or don't run it.
5. **Commit early and often** — every experiment batch and draft update; git log is the experiment history.

**Proactivity**: draft first, ask with the draft. High confidence → full draft; medium → draft + flagged uncertainties; low (major unknowns) → 1-2 `clarify` questions then draft. Block only for: unclear venue, contradictory framings, incomplete results, or explicit review-first request.

---

## Phase 0: Project Setup

Explore the repo (`README`, `results/`, `configs/`, `.bib`); organize `paper/ experiments/ code/ results/ tasks/ human_eval/`. `git init`, branch per paper, commit every completed batch. Identify the contribution — What (one sentence) / Why (evidence) / So What — propose to the scientist for confirmation. Keep a `todo` list as cross-session state (contribution → literature → experiments → analysis → draft → review → submit). Estimate compute budget before running anything; cost-tracker code: [experiment-patterns.md#compute-budget-tracking](references/experiment-patterns.md#compute-budget-tracking). Multi-author: agree on conventions before anyone writes.

## Phase 1: Literature Review

Seed from the codebase (`grep -r "arxiv\|doi\|cite"`, `find . -name "*.bib"`); load the `arxiv` skill for search+BibTeX. **Breadth-then-depth**: Round 1 = 4-6 parallel broad queries, Round 2 = follow-ups from Round 1 terms, Round 3 = targeted gaps; stop when a round returns >80% already-found papers. Delegate rounds via `delegate_task`. **Verify every citation, never from memory**: search → verify in 2+ sources → BibTeX via DOI content negotiation → validate the claim is in the paper → add; any step fails → `[CITATION NEEDED]`. API code, `CitationManager`: [citation-workflow.md](references/citation-workflow.md). Organize related work **by methodology**, not paper-by-paper.

## Phase 2: Experiment Design

Map claims → experiments → expected evidence explicitly; no mapped claim, don't run it. Baselines: naive, strong, ablation, compute-matched. Define the eval protocol first (metrics+direction, aggregation, tests, sample sizes). Scripts: incremental saving, preserve intermediate artifacts, separate generation/eval/visualization — patterns: [experiment-patterns.md](references/experiment-patterns.md). Human eval: pairwise > Likert, 100+ items/3+ annotators, Krippendorff's alpha for agreement — guide, IRB: [human-evaluation.md](references/human-evaluation.md).

## Phase 3: Execution & Monitoring

Launch with `nohup ... &`; watch API rate limits above ~4 concurrent runs. Monitor on a cron cycle: process alive → tail log → new results? → structured report → commit if complete → `[SILENT]` if nothing changed — template: [experiment-patterns.md#monitoring-cron-pattern](references/experiment-patterns.md#monitoring-cron-pattern). Failures: rate limit → wait & rerun; crash → resume from checkpoint; timeout → kill/skip/note; bad config → fix & rerun. Maintain an `experiment_journal.jsonl` (hypothesis/plan/result/analysis/next-steps per attempt) — the exploration tree git misses, useful for Methods and honest failure reporting: [experiment-patterns.md#experiment-journal-pattern](references/experiment-patterns.md#experiment-journal-pattern).

## Phase 4: Result Analysis

Aggregate into per-task and summary tables; always report error bars, 95% CIs, pairwise tests, effect sizes: [experiment-patterns.md](references/experiment-patterns.md). Identify the story: main finding in one sentence, what surprised you, what failed (report honestly), needed follow-ups. Null/negative result → reframe as analysis or target TMLR/NeurIPS D&B/workshops: [paper-types.md](references/paper-types.md). Figures/tables: vector PDF, colorblind-safe, self-contained captions, `booktabs` with bold best value and $\uparrow$/$\downarrow$. Decide: claims supported → Phase 5; inconclusive → back to Phase 2. Write `experiment_log.md` before drafting — bridges results to prose so the writer doesn't re-derive the story from raw JSON: [experiment-patterns.md#experiment-log-bridge-to-writeup](references/experiment-patterns.md#experiment-log-bridge-to-writeup).

---

## Iterative Refinement: Strategy Selection

Any output can be refined via **autoreason** (critic → revise → synthesize → blind judge panel, k=2 convergence): best for mid-tier model + constrained task, where the generation-evaluation gap is widest; frontier model + unconstrained task or concrete technical tasks do better with critique-and-revise or single pass. For paper drafts: give the critic ground-truth data (without it, models hallucinate fake ablations/CIs), use 3+ working judges, scope-constrain the revision. Full loop, strategy table, prompts: [autoreason-methodology.md](references/autoreason-methodology.md).

---

## Phase 5: Paper Drafting

Large projects: load `experiment_log.md` plus section-relevant configs (not raw JSON/full lit notes), delegate one section's context at a time.

**Narrative Principle**: the paper is a story, one contribution. By end of intro: What (1-3 claims), Why (evidence), So What must be clear — no one-sentence contribution, no paper yet. Full writing philosophy: [writing-guide.md](references/writing-guide.md).

**Workflow**: contribution sentence → Figure 1 → abstract (5-sentence formula) → intro (1-1.5pp) → methods → experiments (state claim per result) → related work (by methodology) → conclusion/discussion → limitations (REQUIRED) → appendix (never the *only* place for critical evidence) → checklist. **Two-pass**: draft+refine per section while fresh, then a full-paper-context pass for redundancy/gaps. Ethics/broader-impact statement expected at most venues — name specific risks, not "no negative impacts."

**LaTeX**: copy the whole template dir from `templates/`, verify it compiles before editing, fill section by section. Preamble, diagrams, `latexdiff`, page limits, post-edit quality checklist: [latex-tooling.md](references/latex-tooling.md). Plots: [experiment-patterns.md#visualization-best-practices](references/experiment-patterns.md#visualization-best-practices).

## Phase 6: Self-Review & Revision

**Ensemble review**: N=3-5 independent critical reviews (default negative bias), then a meta-review resolving disagreement, strongest available model regardless of writer model: [reviewer-guidelines.md#ensemble-review-simulation-multi-agent-pattern](references/reviewer-guidelines.md#ensemble-review-simulation-multi-agent-pattern). **Visual review** (VLM on the PDF) catches figure/layout issues text misses; **claim verification** — a fresh sub-agent traces every claim to its source result, flags gaps `[VERIFY]`: [reviewer-guidelines.md#visual-review-pass-vlm](references/reviewer-guidelines.md#visual-review-pass-vlm). Prioritize: Critical (may need new experiments) > High > Medium > Low. Rebuttals: point-by-point, address every concern, `latexdiff` for a marked-up diff: [reviewer-guidelines.md#how-to-address-reviewer-feedback](references/reviewer-guidelines.md#how-to-address-reviewer-feedback). Snapshot versions at milestones.

---

## Phase 7: Submission, and Beyond

Complete the venue's mandatory checklist ([checklists.md](references/checklists.md)) — incomplete ones cause desk rejection. Double-blind venues: run the full anonymization checklist (no names/affiliations, third-person self-citation, Anonymous GitHub for code) — a common desk-rejection cause. Before compiling: automated validation (chktex, citation/figure/label checks). Converting between venues: never copy preambles, copy content sections only, adjust for the new page limit. Validation scripts, camera-ready, arXiv strategy, code-release packaging: [submission-prep.md](references/submission-prep.md).

Post-acceptance (Phase 8): posters, talks, blog/social, workshop/short-paper variant: [post-acceptance.md](references/post-acceptance.md). Non-empirical paper types: [paper-types.md](references/paper-types.md).

---

## Hermes Agent Integration

Compose with: **arxiv** (Phase 1), **subagent-driven-development** (Phase 5 parallel drafting), **plan** (Phase 0), **qmd** (Phase 1 local KB), **diagramming**/**data-science** (Phase 4-5). Supersedes `ml-paper-writing`.

Core tools: `terminal`/`process` (LaTeX, git, experiments), `execute_code` (citations, stats), `delegate_task` (fresh subagent per section, no shared context), `todo` (cross-session state), `memory` (~2200 char bound), `cronjob` (`[SILENT]` when nothing changed), `clarify` (only when genuinely blocked). Session start: `todo("list")` → `memory("read")` → git log → running processes → report. Call examples: [hermes-integration.md](references/hermes-integration.md).

**Reviewer criteria**: Quality, Clarity, Significance, Originality — NeurIPS 6-point scale, Strong Reject(1)–Strong Accept(6): [reviewer-guidelines.md](references/reviewer-guidelines.md).

## Common Issues

Generic abstract → cut any opener that could prepend any ML paper. Intro >1.5pp → split into Related Work, front-load bullets. Experiments lack explicit claims → add "This tests whether [claim]..." per experiment. Missing significance → add error bars/tests/CIs. Scope creep → every experiment maps to a claim or gets cut. Weak human eval → [human-evaluation.md](references/human-evaluation.md). Reproducibility questioned → release code, document hyperparams/seeds ([submission-prep.md](references/submission-prep.md)). Negative/null results → reframe as analysis or target TMLR/workshops (Phase 4). Resubmitting → address concerns, don't reference the prior review ([submission-prep.md](references/submission-prep.md)).

## Reference Documents

All in `references/`: [writing-guide.md](references/writing-guide.md) (clarity, figures) · [citation-workflow.md](references/citation-workflow.md) (APIs, BibTeX) · [checklists.md](references/checklists.md) (per-venue) · [reviewer-guidelines.md](references/reviewer-guidelines.md) (criteria, review sim, rebuttals) · [sources.md](references/sources.md) (bibliography) · [experiment-patterns.md](references/experiment-patterns.md) (patterns, monitoring, cost, journal/log, SciencePlots) · [autoreason-methodology.md](references/autoreason-methodology.md) (loop, prompts) · [human-evaluation.md](references/human-evaluation.md) (design, IRB) · [paper-types.md](references/paper-types.md) (theory/survey/benchmark/position) · [latex-tooling.md](references/latex-tooling.md) (templates, TikZ, latexdiff) · [submission-prep.md](references/submission-prep.md) (anonymization, camera-ready, arXiv) · [post-acceptance.md](references/post-acceptance.md) (posters, talks, workshops) · [hermes-integration.md](references/hermes-integration.md) (tool-call patterns). Conference LaTeX templates: `templates/` ([README](templates/README.md)).
