---
title: "Comps Analysis"
sidebar_label: "Comps Analysis"
description: "Build comparable company analysis in Excel — operating metrics, valuation multiples, statistical benchmarking vs peer sets"
---

{/* This page is auto-generated from the skill's SKILL.md by website/scripts/generate-skill-docs.py. Edit the source SKILL.md, not this page. */}

# Comps Analysis

Build comparable company analysis in Excel — operating metrics, valuation multiples, statistical benchmarking vs peer sets. Pairs with excel-author. Use for public-company valuation, IPO pricing, sector benchmarking, or outlier detection.

## Skill metadata

| | |
|---|---|
| Source | Optional — install with `hermes skills install official/finance/comps-analysis` |
| Path | `optional-skills/finance/comps-analysis` |
| Version | `1.0.0` |
| Author | Anthropic (adapted by Nous Research) |
| License | Apache-2.0 |
| Platforms | linux, macos, windows |
| Tags | `finance`, `valuation`, `comps`, `excel`, `openpyxl`, `modeling`, `investment-banking` |
| Related skills | [`excel-author`](/docs/user-guide/skills/optional/finance/finance-excel-author), [`pptx-author`](/docs/user-guide/skills/optional/finance/finance-pptx-author), [`dcf-model`](/docs/user-guide/skills/optional/finance/finance-dcf-model), [`lbo-model`](/docs/user-guide/skills/optional/finance/finance-lbo-model) |

## Reference: full SKILL.md

:::info
The following is the complete skill definition that Hermes loads when this skill is triggered. This is what the agent sees as instructions when the skill is active.
:::

## Environment

This skill assumes **headless openpyxl** — you are producing an .xlsx file on disk.
Follow the `excel-author` skill's conventions for cell coloring, formulas, named ranges, and sensitivity tables.
Recalculate before delivery: `python /path/to/excel-author/scripts/recalc.py ./out/model.xlsx`.

# Comparable Company Analysis

## ⚠️ CRITICAL: Data Source Priority (READ FIRST)

**Data source hierarchy, always:** (1) structured financial-data MCP (S&P
Kensho, FactSet, Daloopa) if available — use exclusively, do not fall back to
web search. (2) Only if no MCP: Bloomberg Terminal, SEC EDGAR filings, other
institutional sources. (3) Never use web search as a primary source — it
lacks the accuracy, audit trail, and reliability institutional-grade analysis
requires.

---

## Overview
This skill teaches the agent to build institutional-grade comparable company analyses that combine operating metrics, valuation multiples, and statistical benchmarking. The output is a structured Excel/spreadsheet that enables informed investment decisions through peer comparison.

An example is provided in `examples/comps_example.xlsx` — use it to learn
structural hierarchy and the level of rigor expected, not for exact
reproduction of format/metrics regardless of audience.

**Before building, ask:** preferred format? Who's the audience (investment
committee, board, quick reference, memo)? What's the key question (valuation,
growth, positioning, efficiency)? What's the context (M&A, investment
decision, sector benchmarking)? Adapt metrics and depth accordingly — vary
execution by context, since the goal is institutional-quality analysis, not
institutional-looking templates. User-provided examples and explicit
preferences always take precedence over these defaults.

**Core Philosophy:** *"Build the right structure first, then let the data
tell the story."* Headers that force strategic thinking, clean inputs,
transparent formulas, statistics that emerge automatically — a good comp is
immediately readable by someone who didn't build it.

---

## ⚠️ CRITICAL: Formulas Over Hardcodes + Step-by-Step Verification

**Formulas, not hardcodes:** every derived value (margin, multiple,
statistic) MUST be an Excel formula referencing input cells — never a
pre-computed number pasted in. In openpyxl: `cell.value = "=E7/C7"`, NOT
`cell.value = 0.687`. The only hardcoded values are raw inputs (revenue,
EBITDA, share price), and every one gets a cell comment with its source. Why:
the model must update automatically when an input changes — a hardcoded
margin is a silent bug waiting to happen.

**Verify step-by-step with the user** — do NOT build the entire sheet
end-to-end and then present it: show the header layout before filling data →
show the input block and confirm sources/periods before building formulas →
show calculated operating margins and sanity-check before moving to
valuation → show valuation multiples and confirm they look reasonable before
adding statistics.

---

## Section 1: Document Structure & Setup

### Header Block (Rows 1-3)
```
Row 1: [ANALYSIS TITLE] - COMPARABLE COMPANY ANALYSIS
Row 2: [List of Companies with Tickers] • [Company 1 (TICK1)] • [Company 2 (TICK2)] • [Company 3 (TICK3)]
Row 3: As of [Period] | All figures in [USD Millions/Billions] except per-share amounts and ratios
```

Font, color palette, decimal precision, and the full ASCII template layout
(defaults only — user preferences and uploaded templates always win): read
`references/visual-and-templates.md` when formatting the sheet.

---

## Section 2: Operating Statistics & Financial Metrics

### Core Columns (start with these)
Company (consistent naming) · Revenue (size metric — LTM/quarterly/annual)
· Revenue Growth (YoY %) · Gross Profit (Revenue − COGS) · Gross Margin
(GP/Revenue) · EBITDA (earnings before interest, tax, D&A) · EBITDA Margin
(EBITDA/Revenue).

**Optional additions** (choose based on industry/purpose): Quarterly vs LTM
(if seasonality matters), Free Cash Flow + FCF Margin (capital-intensive/SaaS),
Net Income (mature/profitable companies), Operating Income (varying D&A),
CapEx metrics (asset-heavy industries), Rule of 40 (SaaS: Growth % + Margin %),
FCF Conversion (quality-of-earnings, advanced).

Core formula pattern: `Gross Margin (F7): =E7/C7`, `EBITDA Margin (H7): =G7/C7`.
More formula examples (optional ratios, cross-sheet references, statistical
functions): read `references/visual-and-templates.md`.

**Golden Rule:** Every ratio should be [Something] / [Revenue] or [Something] / [Something from this sheet]. Keep it simple.

### Statistics Block (After company data)

**CRITICAL: Add statistics formulas for all comparable metrics** (ratios,
margins, growth rates, multiples), after one blank row: `Maximum: =MAX(B7:B9)`,
`75th Percentile: =QUARTILE(B7:B9,3)`, `Median: =MEDIAN(B7:B9)`,
`25th Percentile: =QUARTILE(B7:B9,1)`, `Minimum: =MIN(B7:B9)`.

**Needs statistics** (ratios, comparable across scale): Revenue Growth %,
Gross/EBITDA Margin %, EPS, EV/Revenue, EV/EBITDA, P/E, Dividend Yield %, Beta.
**Doesn't need statistics** (absolute size varies by company): Revenue,
EBITDA, Net Income, Market Cap, Enterprise Value.

**Note:** Add one blank row between company data and statistics rows for visual separation. Do NOT add a "SECTOR STATISTICS" or "VALUATION STATISTICS" header row.

**Why quartiles matter:** They show distribution, not just average. A 75th percentile multiple tells you what "premium" companies trade at.

---

## Section 3: Valuation Multiples & Investment Metrics

### Core Valuation Columns (start with these)
Company (same order as operating section) · Market Cap · Enterprise Value
(Market Cap ± Net Debt/Cash) · EV/Revenue · EV/EBITDA · P/E Ratio.

**Optional valuation metrics** (choose based on context): FCF Yield
(cash-focused), PEG Ratio (growth companies), Price/Book (asset-heavy),
ROE/ROA (profitability comparison), Revenue/EBITDA CAGR (trend analysis),
Asset Turnover (operational efficiency), Debt/Equity (capital structure).

**Key Principle:** Include 3-5 core multiples that matter for your industry. Don't include every possible metric just because you can.

Core formula pattern: `EV/Revenue: =[Enterprise Value]/[LTM Revenue]`,
`EV/EBITDA: =[Enterprise Value]/[LTM EBITDA]`, `P/E Ratio: =[Market Cap]/[Net Income]`.
More formula examples (FCF Yield, PEG Ratio, and other optional multiples):
read `references/visual-and-templates.md`.

### Cross-Reference Rule
**CRITICAL:** Valuation multiples MUST reference the operating metrics section. Never input the same raw data twice. If revenue is in C7, then EV/Revenue formula should reference C7.

### Statistics Block
Same structure as operating section: Max, 75th, Median, 25th, Min for every metric. Add one blank row for visual separation between company data and statistics. Do NOT add a "VALUATION STATISTICS" header row.

---

## Section 4: Notes & Methodology Documentation

A notes section must document data sources/quality, key definitions, the
valuation methodology, and the analysis framework. Full breakdown of what
belongs in each: read `references/metric-selection-and-workflow.md`.

---

## Section 5: Choosing the Right Metrics (Decision Framework)

Start from "what question am I answering?" (undervalued vs. efficient vs.
growing fastest vs. best cash generator each point at different metrics),
then narrow by industry. Rule of thumb: **5 operating + 5 valuation metrics =
10 total columns** — more than 15 metrics is probably noise.

Full decision framework (per-question metric focus, industry must-have/skip
tables): read `references/metric-selection-and-workflow.md`.

---

## Section 6: Best Practices & Quality Checks

Before you start: define the peer group, pick the period, standardize units,
map data sources. While building: enter raw data before formulas, and **add
a cell comment to every hard-coded input** citing its source or explaining
the assumption (audit trail, not optional).

### Sanity Checks
- **Margin test**: Gross margin > EBITDA margin > Net margin (always true by definition)
- **Multiple reasonableness**: EV/Revenue ~0.5-20x, EV/EBITDA ~8-25x, P/E ~10-50x (varies by industry/growth)
- **Growth-multiple correlation**: Higher growth usually means higher multiples
- **Size-efficiency trade-off**: Larger companies often have better margins (scale benefits)

### Common Mistakes to Avoid
Mixing market cap and enterprise value in formulas; mismatched numerator/denominator
periods (LTM vs quarterly); hardcoding numbers instead of cell references;
hard-coded inputs missing a source/assumption comment or hyperlink; too many
metrics without clear purpose; non-comparable companies included; outdated
data used without disclosure; averaging percentages instead of taking the
median.

Full cell-comment citation examples, a time-boxed step-by-step build process,
and the formatting checklist: read `references/metric-selection-and-workflow.md`
and `references/visual-and-templates.md`.

---

## Section 10: Red Flags & Warning Signs

🚩 **Data quality**: inconsistent time periods (quarterly mixed with annual),
missing data without explanation, >10% variance between data sources.
🚩 **Valuation**: negative-EBITDA companies valued on EBITDA multiples (use
revenue multiples instead), P/E >100x without a hypergrowth story, margins
that don't make sense for the industry.
🚩 **Comparability**: different fiscal year ends, mixing pure-play and
conglomerates, materially different business models labeled as "comps".

**When in doubt, exclude the company.** Better to have 3 perfect comps than 6 questionable ones.

---

## Section 11: Formulas Reference Guide

Full Excel formula cheatsheet (statistical functions, cross-sheet references,
common ratio formulas): read `references/visual-and-templates.md`.

---

**Key principles:** structure drives insight (right headers force right
thinking); less is more (5-10 metrics beat 20); choose metrics for your
question (valuation ≠ efficiency analysis); statistics show patterns
(median/quartiles reveal more than average); transparency beats complexity
(simple formulas everyone understands); comparability is king (exclude
rather than force a bad comp); document your choices in the notes section.

---

## Output Checklist

Before delivering, verify: all companies truly comparable · consistent time
periods · units clearly labeled · formulas reference cells (never
hardcoded) · every hard-coded input has a comment citing source or
assumption, with hyperlinks where available · statistics include all 5
(Max/75th/Med/25th/Min) · notes document sources and methodology · visual
formatting follows conventions (blue = input, black = formula) · sanity
checks pass · date stamp current · no formula errors (#DIV/0!, #REF!, #N/A).

---

**Continuous improvement:** after each analysis, ask what surprised you, what
data gaps limited it, and what metrics stakeholders wanted that you didn't
include. Time-boxed build process and pro tips: read
`references/metric-selection-and-workflow.md`.

## Data sources — MCP first, web fallback

"S&P Kensho MCP / Daloopa MCP / FactSet MCP" above refers to commercial
financial-data MCPs from the original Cowork plugin context. In Hermes: if
any structured financial-data MCP is configured (see `native-mcp` skill),
prefer it. Otherwise fall back to `web_search`/`web_extract` against SEC
EDGAR, company IR pages, `browser_navigate` for interactive portals, or ask
the user. **Never fabricate** — flag unsourced cells `[UNSOURCED]`.

## Attribution

This skill is adapted from Anthropic's Claude for Financial Services plugin suite (Apache-2.0). The Office-JS / Cowork live-Excel paths have been removed; this version targets headless openpyxl via the `excel-author` skill's conventions. Original: https://github.com/anthropics/financial-services
