---
name: dcf-model
description: Build institutional-quality DCF valuation models in Excel — revenue projections, FCF build, WACC, terminal value, Bear/Base/Bull scenarios, 5x5 sensitivity tables. Pairs with excel-author. Use for intrinsic-value equity analysis.
version: 1.0.0
author: Anthropic (adapted by Nous Research)
license: Apache-2.0
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [finance, valuation, dcf, excel, openpyxl, modeling, investment-banking]
    related_skills: [excel-author, pptx-author, comps-analysis, lbo-model, 3-statement-model]
---

## Environment

This skill assumes **headless openpyxl** — you are producing an .xlsx file on disk.
Follow the `excel-author` skill's conventions for cell coloring, formulas, named ranges, and sensitivity tables.
Recalculate before delivery: `python /path/to/excel-author/scripts/recalc.py ./out/model.xlsx`.

# DCF Model Builder

## Overview

This skill creates institutional-quality DCF models for equity valuation following investment banking standards. Each analysis produces a detailed Excel model (with sensitivity analysis included at the bottom of the DCF sheet).

## Tools

- Default to using all of the information provided by the user and MCP servers available for data sourcing.

## Critical Constraints - Read These First

These constraints apply throughout all DCF model building. Review before starting:

**Formulas over hardcodes (NON-NEGOTIABLE):** every projection, margin, discount
factor, PV, and sensitivity cell MUST be a live Excel formula, never a Python-computed
value written as a number — `ws["D20"] = "=D19*(1+$B$8)"` is correct, `ws["D20"] =
calculated_revenue` is WRONG. Only raw historical inputs, assumption drivers (growth
rates, WACC inputs, terminal g), and current market data (share price, debt balance)
may be hardcoded. Catching yourself writing a Python-computed result to a cell = STOP.

**Verify step-by-step with the user (do NOT build end-to-end):** confirm after each
of — raw inputs block, revenue projections, FCF schedule, WACC, and the terminal
value/equity bridge — before moving to the next stage. Catching a wrong assumption
late means rebuilding everything downstream.

**Sensitivity tables:** ODD grid (5×5 standard) so there's a true center cell; the
middle row/column headers must equal the model's actual base-case assumptions, so the
center cell's formula output equals the model's actual implied share price (this is
the correctness check) — highlight it with the medium-blue fill (`#BDD7EE`) + bold.
Populate ALL cells (75 total across 3 tables) with full DCF-recalculation formulas
written programmatically via openpyxl loops. NO placeholder text, NO linear
approximations, NO manual steps.

**Cell comments:** add one AS each hardcoded value is created (never deferred),
format `"Source: [System/Document], [Date], [Reference], [URL if applicable]"`.

**Model layout planning:** lock ALL section row positions and write ALL headers/labels/
dividers FIRST, then write formulas against the locked rows, then test immediately —
formulas-before-headers is how row references silently shift into #REF! errors.

**Formula recalculation:** run `python recalc.py model.xlsx 30` before delivery; fix
ALL errors until status is "success" — zero formula errors required.

**Scenario blocks:** separate Bear/Base/Bull blocks, assumptions horizontal across
projection years, referenced through a consolidation column with INDEX/OFFSET
formulas (e.g. `=INDEX(B10:D10, 1, $B$6)`) — never scatter nested IF formulas through
every projection row. Details: `references/patterns-and-mistakes.md`.

## DCF Process Workflow

Ten steps, built and confirmed with the user in order (see Critical Constraints
above — do not build end-to-end without checkpoints). **Full formula derivations,
worked numeric examples, and CSV output formats for every step: read
`references/workflow-formulas.md` while building that step.**

1. **Data retrieval & validation** — MCP first, then user data, then web search; validate net debt/cash, diluted shares, margins, tax rate (21-28%).
2. **Historical analysis (3-5yr)** — revenue CAGR, margin progression, D&A/CapEx % of revenue, NWC efficiency, ROIC/ROE.
3. **Revenue projections** — `Revenue(Year N) = Revenue(Year N-1) × (1 + Growth Rate)`, higher growth early, moderating toward terminal growth by year 5+; separate Bear/Base/Bull growth.
4. **Operating expenses** — S&M/R&D/G&A **as % of revenue** (never gross profit), each its own line; EBIT = Gross Profit − Total OpEx; opex % should decline with scale.
5. **Free cash flow** — `EBIT → (-)Taxes → NOPAT → (+)D&A → (-)CapEx → (-)ΔNWC → Unlevered FCF`; D&A/CapEx % of revenue, ΔNWC % of revenue change (~±2%).
6. **WACC** — Cost of Equity = CAPM (`Risk-Free Rate + Beta × ERP`, ERP 5.0-6.0%); After-Tax Cost of Debt = Pre-Tax × (1 − Tax Rate); `WACC = CoE×EquityWt + After-Tax CoD×DebtWt`. Net cash → debt weight can go negative; no debt → WACC = CoE.
7. **Discounting** — mid-year convention, periods 0.5, 1.5, 2.5…; `Discount Factor = 1/(1+WACC)^Period`. Standard window 5yr (3 mature, 7-10 high-growth).
8. **Terminal value** — perpetuity growth (preferred): `Terminal Value = Terminal FCF / (WACC − Terminal g)`, **g < WACC always**, g typically 2.0-3.5% and never above risk-free/GDP growth; should be 50-70% of EV.
9. **Enterprise → equity bridge** — `EV = ΣPV(FCF) + PV(Terminal Value)`; `Equity Value = EV − Net Debt` (add back if net cash); `Implied Price = Equity Value / Diluted Shares`.
10. **Sensitivity analysis** — three 5×5 grids at the bottom of the DCF sheet (WACC vs Terminal Growth, Revenue Growth vs EBIT Margin, Beta vs Risk-Free Rate), all 75 cells live full-DCF-recalc formulas, never linear approximations or placeholders. **Read `references/patterns-and-mistakes.md` first.**

## Excel File Creation, Quality Rubric, and Inputs

**Uses the `xlsx` skill for all spreadsheet operations** (formula construction rules, number formatting, `recalc.py`, error checking) — zero formula errors, proper recalculation, no exceptions.

Every model must maximize for: realistic revenue/margin assumptions grounded in history, a properly-derived CAPM WACC, comprehensive sensitivity analysis, a well-supported terminal value, professional scenario-ready structure, transparent assumption documentation.

**Minimum inputs**: company identifier, growth assumptions (or "use consensus"). **Optional**: projection period (default 5yr), Bear/Base/Bull assumptions, terminal growth rate (default 2.5-3.0%), explicit WACC inputs.

## Excel Model Structure

**Two sheets**: **DCF** (main valuation model, sensitivity tables at the bottom — not a separate sheet) and **WACC** (cost of capital calculation).

### Formula Recalculation (MANDATORY)

After creating or modifying the model, recalculate with the `excel-author` skill's
script: `python recalc.py [path_to_excel_file] [timeout_seconds]` (e.g.
`python recalc.py AAPL_DCF_Model_2025-10-12.xlsx 30`). Returns JSON with `status`
(`"success"`/`"errors_found"`), `total_errors`, `total_formulas`, and an
`error_summary` with cell locations on failure — **fix all errors and re-run until
"success"** before delivering. Full JSON shape: `references/excel-layout.md`.

### Formatting, Borders, Sheet Layout, Sensitivity Grid, Case Selector

**Read `references/excel-layout.md` before laying out cells.** It has the exact
row-by-row DCF/WACC sheet structure, the font-color/fill-color scheme, border
thickness rules, number formats, the three 5x5 sensitivity table locations, and the
INDEX/OFFSET case-selector pattern. Non-negotiables: font color = what it is (blue
input / black formula / green sheet-link), fill color = where you are (dark blue
section headers, light blue column headers, light grey inputs, medium blue `#BDD7EE`
key outputs — blues + grey + white only); borders mandatory at three weights (thick
around major sections, medium between sub-sections, thin around data tables); case
selector cell (1/2/3) feeds a consolidation column, never nested IFs; every hardcoded
input gets a sourced cell comment as it's created.

**File naming**: `[Ticker]_DCF_Model_[Date].xlsx`. Deliverable = DCF sheet with Bear/Base/Bull cases, case selector, consolidation-column formulas, three sensitivity tables, color-coded cells, sourced cell comments, professional borders — plus the WACC sheet.

## Best Practices, Company-Type Variations, and Full Workflow Integration

**Read `references/variations-and-practices.md`** when: adapting the standard 5-year
DCF for high-growth tech, mature, cyclical, or multi-segment companies (projection
length, WACC range, and terminal growth all shift by company type); or for the
detailed at-start / during-build / pre-delivery workflow checklist and best-practices
notes on documentation and QC.

**Condensed workflow**: gather market + historical data (MCP first, web/user fallback) →
build the Excel model with live formulas → before delivery, verify scenario blocks +
case selector + sensitivity tables + font/border formatting are all in place, run
`recalc.py` until `status: "success"`, spot-check that FCF/revenue formulas reference
the consolidation column (not nested IFs) → deliver.

## Troubleshooting

**If you encounter errors or unreasonable results, read [TROUBLESHOOTING.md](./TROUBLESHOOTING.md) for detailed debugging guidance.**

## Final Output Checklist

Before delivering: `recalc.py` status is "success" (zero formula errors); DCF sheet
(sensitivity at bottom) + WACC sheet both present; font colors, cell comments,
sensitivity formulas, and borders all match the standards above; and the validation
checks pass — OpEx is % of revenue (not gross profit), terminal value is 50-70% of EV,
terminal growth < WACC, tax rate 21-28%, file named `[Ticker]_DCF_Model_[Date].xlsx`.

## Data sources — MCP first, web fallback

References to "S&P Kensho MCP / Daloopa MCP / FactSet MCP" elsewhere are commercial
financial-data MCPs from the original Cowork plugin context. In Hermes: prefer any
structured financial-data MCP you have configured (see `native-mcp` skill) for
point-in-time comps, precedent transactions, and filings; otherwise fall back to
`web_search`/`web_extract` against SEC EDGAR, company IR pages, `browser_navigate`
for interactive portals, or user-provided data. **Never fabricate** — if a number
can't be sourced, flag the cell `[UNSOURCED]` and surface it to the user.

## Attribution

This skill is adapted from Anthropic's Claude for Financial Services plugin suite (Apache-2.0). The Office-JS / Cowork live-Excel paths have been removed; this version targets headless openpyxl via the `excel-author` skill's conventions. Original: https://github.com/anthropics/financial-services
