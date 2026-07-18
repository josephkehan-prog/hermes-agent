---
name: dcf-model
description: Build DCF valuation models in Excel.
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

Full worked examples, CSV row-layout dumps, and WRONG-pattern illustrations (verbatim long form): `REFERENCE.md` next to this file.

## Overview

Creates institutional-quality DCF models for equity valuation following investment banking standards. Each analysis produces a detailed Excel model with sensitivity analysis at the bottom of the DCF sheet.

## Tools

- Default to using all of the information provided by the user and MCP servers available for data sourcing.

## Critical Constraints - Read These First

**Formulas Over Hardcodes (NON-NEGOTIABLE):**
- Every projection, margin, discount factor, PV, and sensitivity cell MUST be a live Excel formula — never a value computed in Python and written as a number
- `ws["D20"] = "=D19*(1+$B$8)"` is correct; `ws["D20"] = calculated_revenue` is WRONG
- Only hardcoded numbers permitted: (1) raw historical inputs, (2) assumption drivers (growth rates, WACC inputs, terminal g), (3) current market data (share price, debt balance)
- If you catch yourself computing something in Python and writing the result — STOP. The model must flex when the user changes an assumption.

**Verify Step-by-Step With the User (DO NOT build end-to-end):**
- After data retrieval → show raw inputs block (revenue, margins, shares, net debt), confirm
- After revenue projections → show projected top line + growth rates, confirm before margin build
- After FCF build → show full FCF schedule, confirm before computing WACC
- After WACC → show calculation + inputs, confirm before discounting
- After terminal value + PV → show equity bridge (EV → equity value → per share), confirm before sensitivity tables
- Catch errors at each stage — a wrong margin assumption found after sensitivity tables are built means rebuilding everything downstream

**Sensitivity Tables:**
- Use an ODD number of rows/columns (standard 5×5, sometimes 7×7) to guarantee a true center cell
- Center cell = base case: middle row/column headers must exactly equal the model's actual assumptions (e.g. base WACC 9.0% → middle row 9.0%); center cell output must equal the model's actual implied share price (sanity check)
- Highlight the center cell with medium-blue fill (`#BDD7EE`) + bold font
- Populate ALL cells (3 tables × 25 cells = 75) with full DCF recalculation formulas via openpyxl loops
- NO placeholder text, NO linear approximations, NO manual steps required

**Cell Comments:**
- Add cell comments AS each hardcoded value is created — not deferred to end, no "TODO: add source"
- Format: `Source: [System/Document], [Date], [Reference], [URL if applicable]`
- Every blue input must have a comment before moving to next section

**Model Layout Planning:**
- Define ALL section row positions BEFORE writing any formulas
- Write ALL headers/labels first, then ALL section dividers/blank rows, THEN write formulas using locked row positions
- Test formulas immediately after creation

**Formula Recalculation:**
- Run `python recalc.py model.xlsx 30` before delivery; fix ALL errors until status is "success"
- Zero formula errors required (#REF!, #DIV/0!, #VALUE!, etc.)

**Scenario Blocks:**
- Separate blocks for Bear/Base/Bull cases; assumptions shown horizontally across projection years within each block
- Use a consolidation column with INDEX/OFFSET formulas (not scattered IF statements) — see "Case Selector Implementation" below
- Verify formulas reference correct scenario block cells

## DCF Process Workflow

### Step 1: Data Retrieval and Validation

**Data Sources Priority:** 1) MCP Servers (structured data, e.g. Daloopa) 2) User-provided data 3) Web Search/Fetch (current prices, beta, debt, cash)

**Validation Checklist:** verify net debt vs net cash; confirm diluted shares outstanding (recent buybacks/issuances); validate historical margins consistent with business model; cross-check revenue growth vs industry benchmarks; verify tax rate reasonable (typically 21-28%)

### Step 2: Historical Analysis (3-5 years)

Analyze and document: revenue growth trends (CAGR, drivers); margin progression (gross, EBIT, FCF margin); capital intensity (D&A and CapEx % of revenue); working capital efficiency (NWC change % of revenue growth); return metrics (ROIC, ROE trends). Summary table template: REFERENCE.md — Historical Metrics Summary Template.

### Step 3: Build Revenue Projections

**Methodology:** start with latest actual revenue (LTM/most recent FY); apply growth rate per projection year; show both dollar amounts and calculated growth %.

**Growth Rate Framework:** Year 1-2 higher growth (near-term visibility) → Year 3-4 moderation toward industry average → Year 5+ approaching terminal growth rate.

**Formula structure:** `Revenue(Year N) = Revenue(Year N-1) × (1 + Growth Rate)`; `Growth %(Year N) = Revenue(Year N)/Revenue(Year N-1) - 1`

**Three-scenario ranges:** Bear 8-12%, Base 12-16%, Bull 16-20% (example only — full block: REFERENCE.md — Three-Scenario Growth Ranges Example).

### Step 4: Operating Expense Modeling

**Typical ranges (% of revenue, NOT gross profit):** S&M 15-40%; R&D 10-30% (tech); G&A 8-15% (should decline as company scales — operating leverage).

**Key principles:** all percentages based on revenue; model % declining as revenue scales; keep S&M/R&D/G&A as separate line items; `EBIT = Gross Profit - Total OpEx`.

Margin expansion framework example (Current State → Target State Year 5): REFERENCE.md — Margin Expansion Framework Example.

### Step 5: Free Cash Flow Calculation

**Build sequence:**
```
EBIT
(-) Taxes (EBIT × Tax Rate)
= NOPAT
(+) D&A (% of revenue)
(-) CapEx (% of revenue, typically 4-8%)
(-) Δ NWC
= Unlevered Free Cash Flow
```

**Working Capital:** % of revenue change (delta revenue); typical range -2% to +2%; negative = source of cash (release), positive = use of cash (build).

**CapEx split:** Maintenance ~2-3% of revenue (sustains operations); Growth CapEx +2-5% (supports expansion); total should align with growth strategy.

### Step 6: Cost of Capital (WACC) Research

**CAPM Cost of Equity:**
```
Cost of Equity = Risk-Free Rate + Beta × Equity Risk Premium
Risk-Free Rate = current 10-Year Treasury Yield
Beta = 5-year monthly stock beta vs market index
Equity Risk Premium = 5.0-6.0% (market standard)
```

**Cost of Debt:**
```
After-Tax Cost of Debt = Pre-Tax Cost of Debt × (1 - Tax Rate)
```
Pre-Tax Cost of Debt from: credit rating, current bond yield, or Interest Expense / Total Debt.

**Capital Structure Weights / WACC:**
```
Market Value Equity = Current Stock Price × Shares Outstanding
Net Debt = Total Debt - Cash & Equivalents
Enterprise Value = Market Cap + Net Debt
Equity Weight = Market Cap / Enterprise Value ; Debt Weight = Net Debt / Enterprise Value
WACC = (Cost of Equity × Equity Weight) + (After-Tax Cost of Debt × Debt Weight)
```

**Special cases:** Net Cash (Cash > Debt) → Net Debt negative, Debt Weight may be negative, WACC adjusts accordingly. No Debt → WACC = Cost of Equity.

**Typical WACC ranges:** Large Cap/Stable 7-9%; Growth Companies 9-12%; High Growth/Risk 12-15%.

### Step 7: Discount Rate Application (5-10 Year Forecast)

**Mid-Year Convention:** cash flows assumed mid-year; Discount Period = 0.5, 1.5, 2.5, 3.5, 4.5...; `Discount Factor = 1 / (1 + WACC)^Period`; `PV of FCF = Unlevered FCF × Discount Factor`. Worked numeric example (Year 1, FCF=$1,000, WACC=10%): REFERENCE.md — PV Calculation Worked Example (Step 7).

**Projection period:** 5 years standard; 7-10 years for high-growth (longer runway); 3 years for mature/stable businesses.

### Step 8: Terminal Value Calculation

**Perpetuity Growth Method (preferred):**
```
Terminal FCF = Final Year FCF × (1 + Terminal Growth Rate)
Terminal Value = Terminal FCF / (WACC - Terminal Growth Rate)
```
**Critical constraint: Terminal Growth < WACC** (otherwise infinite value).

**Terminal growth selection:** Conservative 2.0-2.5% (GDP growth); Moderate 2.5-3.5%; Aggressive 3.5-5.0% (market leaders only). Do not exceed risk-free rate or long-term GDP growth.

**Exit Multiple Method (alternative):**
```
Terminal Value = Final Year EBITDA × Exit Multiple
```
Exit multiple from industry comps or precedent transactions; typical range 8-15x EBITDA.

**PV of Terminal Value:**
```
PV of Terminal Value = Terminal Value / (1 + WACC)^Final Period
```
5-year model with mid-year convention: Final Period = 4.5.

**Sanity check:** Terminal Value should be 50-70% of Enterprise Value. >75% → over-reliant on terminal assumptions; <40% → check if terminal assumptions too conservative.

### Step 9: Enterprise to Equity Value Bridge

Bridge: `Sum of PV(FCFs) + PV(Terminal Value) = Enterprise Value; EV - Net Debt (or + Net Cash) = Equity Value; Equity Value / Diluted Shares = Implied Price per Share`. Full structure + valuation output CSV template: REFERENCE.md — Enterprise-to-Equity Bridge / Valuation Output Format.

**Critical adjustments:** Net Debt = Total Debt - Cash (positive → subtract from EV; negative/Net Cash → add to EV); use Diluted Shares (options, RSUs, convertibles); other adjustments if applicable: minority interests, pension liabilities, operating lease obligations.

### Step 10: Sensitivity Analysis

Build **three sensitivity tables** at the bottom of the DCF sheet:
1. WACC vs Terminal Growth
2. Revenue Growth vs EBIT Margin
3. Beta vs Risk-Free Rate

**Implementation:** simple 2D grids (NOT Excel's "Data Table" feature) with a full DCF-recalculation formula in every cell — 75 cells total (3×25). Use openpyxl loops.

## Correct Patterns (summary — full examples: REFERENCE.md)

**Scenario Block Selection:** separate assumption blocks per scenario, each with a column header row showing projection years (mandatory — without it users can't tell which value maps to which year). Case selector cell (e.g. B6) = 1/2/3. Build a **consolidation column** with `=INDEX(B10:D10, 1, $B$6)` pulling from the right block — NOT scattered `=IF($B$6=1,...,IF($B$6=2,...,...))` throughout. Full block layout: REFERENCE.md — Scenario Block Selection Pattern.

**Revenue Projection:** consolidation column formula first (`=INDEX([Bear FY1 growth]:[Bull FY1 growth], 1, $B$6)`), then projection references it (`=D29*(1+$E$10)`). Cleaner and easier to audit than embedded IFs.

**FCF Formula Pattern:** D&A/CapEx/ΔNWC each reference their own consolidation-column cell (e.g. `=E29*$E$21`); `Unlevered FCF = NOPAT + D&A - CapEx - ΔNWC`. Full table: REFERENCE.md — Correct FCF Formula Pattern.

**Cell Comment Format:** `Source: [System/Document], [Date], [Reference], [URL if applicable]`. Examples: REFERENCE.md — Correct Cell Comment Format.

**Assumption Table Structure — three MANDATORY elements per scenario block:** 1) section header row (merged), 2) column header row showing years (FY1...FY5 — do not skip), 3) data rows (Revenue Growth %, EBIT Margin %, Terminal Growth, WACC). Then a consolidation column (INDEX formulas) that projections reference. Full layout: REFERENCE.md — Correct Assumption Table Structure.

**Row Planning Process:** write ALL headers/labels first → ALL section dividers/blank rows → THEN formulas using locked positions → test immediately. ("Pour foundation, then build walls" — not the reverse.) Example row map: REFERENCE.md — Correct Row Planning Process.

**Sensitivity Table Implementation:** NOT Excel's Data Table feature — plain openpyxl-written formulas, ~75 total (3×25). 5×5 grid, ODD dimensions, base case centered: `axis_values = [base - 2*step, base - step, base, base + step, base + 2*step]`. Center cell (★) formula output must equal the model's actual implied share price; apply `#BDD7EE` fill + bold. Diagram + Python loop pseudocode: REFERENCE.md — Correct Sensitivity Table Implementation.

## Common Mistakes (lessons — full WRONG examples: REFERENCE.md)

1. **Linear-approximation / placeholder sensitivity tables** — don't use shortcuts like `=B88*(1+(0.096-0.116))` or leave "use Data Table feature" notes or blank cells; each cell must recalculate the full DCF. "Sensitivity tables are simple grids with formulas in each cell," not Excel's Data Table tool. Full WRONG blocks: REFERENCE.md — WRONG: Simplified Sensitivity Table Approximations.
2. **Missing cell comments** — don't defer to "later" or write "TODO: add source"; add as each hardcoded value is created.
3. **Formula row references off** — happens when formulas are written before headers are inserted, shifting rows and producing `#REF!`. Lock row layout FIRST.
4. **Single row per assumption across scenarios** (vertical layout) instead of a block per scenario with years horizontal — harder to review progression and compare scenarios. Full WRONG example: REFERENCE.md — WRONG: Single Row Per Assumption.
5. **No borders** — unprofessional, hard to navigate; add borders around all major sections.
6. **Wrong/missing font-color distinction** — all-black text or no font-color changes makes auditing impossible; blue = hardcoded inputs, black = formulas, green = sheet links.
7. **OpEx based on gross profit instead of revenue** — e.g. `S&M: =E33*0.15` (E33=Gross Profit, WRONG) vs `=E29*0.15` (E29=Revenue, CORRECT).

**WACC errors:** mixing book/market values in capital structure; using equity beta instead of asset/unlevered beta incorrectly; wrong tax rate on cost of debt; incorrect risk-free rate (must be current 10Y Treasury); failure to adjust for net debt vs net cash.

**Growth assumption flaws:** terminal growth > WACC (infinite value); projection growth inconsistent with historical performance; ignoring industry growth constraints; growth not aligned with unit economics; margin expansion without operational justification.

**Terminal value mistakes:** wrong growth method (perpetuity vs exit multiple); terminal value >80% of EV (over-reliance); inconsistent terminal margins with steady-state assumptions; wrong discount period for terminal value.

**Cash flow projection errors:** OpEx based on gross profit instead of revenue; D&A/CapEx % misaligned with business model; working capital changes miscalculated; tax rate inconsistent between years; NOPAT calculation errors.

## Excel File Creation

Uses the `xlsx` skill for all spreadsheet operations: standardized formula construction rules, number formatting conventions, automated formula recalculation via `recalc.py`, comprehensive error checking/validation. All files must have zero formula errors and proper recalculation.

## Quality Rubric

Maximize: (1) realistic revenue/margin assumptions based on historical performance; (2) appropriate cost of capital via proper CAPM; (3) comprehensive sensitivity analysis; (4) clear terminal value with supporting rationale; (5) professional model structure enabling scenario analysis; (6) transparent documentation of all key assumptions.

## Input Requirements

**Minimum:** company identifier (ticker/name); growth assumptions (or "use consensus"). **Optional:** projection period (default 5 years); scenario cases (Bear/Base/Bull growth+margin); terminal growth rate (default 2.5-3.0%); specific WACC inputs if not using CAPM.

## Excel Model Structure

**Sheet Architecture — two sheets:** 1) **DCF** — main valuation model with sensitivity analysis at bottom; 2) **WACC** — cost of capital calculation. Sensitivity tables go at the BOTTOM of the DCF sheet, not a separate sheet.

**Formula Recalculation (MANDATORY):**
```bash
python recalc.py [path_to_excel_file] [timeout_seconds]
```
Example:
```bash
python recalc.py AAPL_DCF_Model_2025-10-12.xlsx 30
```
Recalculates all formulas via LibreOffice, scans ALL cells for errors (#REF!, #DIV/0!, #VALUE!, #NAME?, #NULL!, #NUM!, #N/A), returns JSON (`status`, `total_errors`, `total_formulas`, `error_summary`). Full JSON examples: REFERENCE.md — recalc.py Output Format. Fix all errors and re-run until `status` is `"success"` before delivering.

### Formatting Standards

**Font colors (mandatory, from xlsx skill):** Blue (0,0,255) = ALL hardcoded inputs; Black (0,0,0) = ALL formulas/calculations; Green (0,128,0) = links to other sheets.

**Fill colors — default professional blue/grey palette (only, unless user specifies otherwise):**
- Section headers: dark blue `#1F4E79` bg, white bold text
- Sub/column headers: light blue `#D9E1F2` bg, black bold text
- Input cells: light grey `#F2F2F2` bg + blue font (or white bg for max minimalism)
- Calculated cells: white bg, black font
- Output/summary rows: medium blue `#BDD7EE` bg, black bold font
- Only 3 blues + 1 grey + white — no greens/yellows/oranges/extra accents

Font color = WHAT it is (input/formula/link); fill color = WHERE you are (header/data/output). User-provided templates/preferences always override these defaults.

### Border Standards (REQUIRED)

- **Thick (1.5pt):** around KEY INPUTS, PROJECTION ASSUMPTIONS, 5-YEAR CASH FLOW PROJECTION, TERMINAL VALUE, VALUATION SUMMARY, each SENSITIVITY ANALYSIS table
- **Medium (1pt):** between sub-sections (Company Details vs Historical Performance; Growth Assumptions vs EBIT Margin vs FCF Parameters)
- **Thin (0.5pt):** around data tables (Bear|Base|Bull|Selected scenario tables; historical vs projected matrix)
- **None:** individual cells within tables

### Number Formats (per xlsx skill)

- Years as text strings (`"2024"` not `"2,024"`)
- Percentages: `0.0%`
- Currency: `$#,##0` (millions), `$#,##0.00` (per-share) — specify units in headers ("Revenue ($mm)")
- Zeros formatted as `-` via `$#,##0;($#,##0);-`
- Large numbers: `#,##0`
- Negatives in parentheses `(#,##0)`, not minus sign

**Cell comments:** mandatory on ALL hardcoded inputs, format `Source: [System/Document], [Date], [Reference], [URL if applicable]`, added as cells are created (not deferred).

### DCF Sheet Detailed Structure

Full row-by-row CSV layouts for every section below: REFERENCE.md — DCF Sheet Detailed Structure.

- **Section 1 — Header:** company name/DCF Model title; Ticker/Date/Year End; Case Selector cell (1=Bear/2=Base/3=Bull); Case Name Display formula.
- **Section 2 — Market Data (not case-dependent):** Current Stock Price, Shares Outstanding, Market Cap (formula), Net Debt.
- **Section 3 — DCF Scenario Assumptions:** Bear/Base/Bull blocks with Revenue Growth %, EBIT Margin %, Tax Rate %, D&A % of Revenue, CapEx % of Revenue, NWC Change % of ΔRev, Terminal Growth Rate, WACC across projection years — structure per "Correct Assumption Table Structure" above.
- **Section 4 — Historical & Projected Financials:** Revenue (+% growth), Gross Profit (+% margin), OpEx (S&M/R&D/G&A/Total), EBIT (+% margin), Taxes (+tax rate), NOPAT — via consolidation column, per "Correct FCF/Revenue Formula Pattern" above.
- **Section 5 — Free Cash Flow Build:** NOPAT, (+) D&A (% of Rev), (-) CapEx (% of Rev), (-) Δ NWC (% of Δ Rev), = Unlevered FCF. Verify row references point to correct assumption rows before copying across.
- **Section 6 — Discounting & Valuation:** Unlevered FCF, Period, Discount Factor, PV of FCF per year; Terminal FCF/Value/PV; Valuation Summary rows mirroring the Step 9 bridge.

### WACC Sheet Structure

Full layout: REFERENCE.md — WACC Sheet Structure. Sections: Cost of Equity Calculation (Risk-Free Rate, Beta, Equity Risk Premium, Cost of Equity); Cost of Debt Calculation (Credit Rating, Pre-Tax Cost of Debt, Tax Rate link, After-Tax Cost of Debt); Capital Structure (Stock Price/Shares links, Market Cap, Total Debt, Cash, Net Debt, Enterprise Value); WACC Calculation (Weight/Cost/Contribution for Equity and Debt); Weighted Average Cost of Capital output.

### Sensitivity Analysis (Bottom of DCF Sheet)

Location: rows 87+ on DCF sheet — Table 1 WACC vs Terminal Growth (rows 87-100); Table 2 Revenue Growth vs EBIT Margin (rows 102-115); Table 3 Beta vs Risk-Free Rate (rows 117-130); each 5×5 = 25 cells, 75 total.

**Extra formatting beyond the base pattern:** conditional formatting green scale for higher values, red scale for lower; bold the base-case cell; leave 1-2 blank rows between tables.

## Case Selector Implementation

**Bear:** conservative growth (low end of historical range), margin compression/no expansion, higher WACC, lower terminal growth, higher CapEx.
**Base:** consensus/guidance growth, moderate margin expansion from operating leverage, current market-implied WACC, GDP-aligned terminal growth (2.5-3.0%), standard CapEx.
**Bull:** optimistic growth (high end), significant margin expansion, lower WACC, higher terminal growth (3.5-5.0%), reduced CapEx intensity.

**Formula:** same consolidation-column INDEX pattern as "Scenario Block Selection" under Correct Patterns above — not nested IFs.

## Deliverables Structure

File naming: `[Ticker]_DCF_Model_[Date].xlsx`. Two sheets and key features as specified in Excel Model Structure and Final Output Checklist above.

## Best Practices

**Construction:** build incrementally (complete each section before next); test with sample numbers as you build; use consistent structure for similar calculations; comment complex formulas; build in sum/balance checks.

**Documentation:** document all assumptions and reasoning; cite data sources; explain non-standard methodology; flag uncertainties/limited visibility.

**Quality Control:** cross-check calculations multiple ways; stress-test via sensitivity; peer review formulas; version-control saves as work progresses.

## Common Variations

- **High-Growth Technology:** 7-10yr projection; 20-30% initial growth; significant margin expansion; WACC 12-15%; model unit economics (users, ARPU, etc.)
- **Mature/Stable:** 3-5yr projection; GDP+1-3% growth; stable margins; WACC 7-9%; focus on cash generation/capital allocation
- **Cyclical:** model through full economic cycle; normalize margins at mid-cycle; consider trough/peak scenarios; adjust beta for cyclicality
- **Multi-Segment:** separate DCFs per business unit; different growth/margins by segment; sum-of-parts valuation; consider synergies

## Troubleshooting

Errors or unreasonable results: read [TROUBLESHOOTING.md](./TROUBLESHOOTING.md) for detailed debugging guidance.

## Workflow Integration

**During construction:** build with openpyxl using formulas (not hardcoded values); follow xlsx skill conventions; apply fill colors only if requested or per brand guidelines.

**Before delivering (MANDATORY), in order:**
1. Verify structure: scenario blocks, case selector, sensitivity tables at bottom of DCF sheet, font colors, cell comments, borders (see Final Output Checklist below)
2. Recalculate: `python recalc.py model.xlsx 30`
3. Check output: `status: "success"` → continue; `"errors_found"` → check `error_summary`, read TROUBLESHOOTING.md; fix and re-run until "success"
4. Spot-check: FCF formula references correct assumption rows; changing case selector updates consolidation column; revenue formulas reference consolidation column (not nested IFs)
5. Deliver model

## Final Output Checklist

**Required:** `recalc.py` status "success" (zero errors); two sheets (DCF with sensitivity at bottom, WACC); font colors blue/black/green; cell comments on all hardcoded inputs; sensitivity tables fully populated with formulas; professional borders.

**Validation:** OpEx based on revenue (not gross profit); terminal value 50-70% of EV; terminal growth < WACC; tax rate 21-28%; file naming `[Ticker]_DCF_Model_[Date].xlsx`.

## Data sources — MCP first, web fallback

References to "S&P Kensho MCP / Daloopa MCP / FactSet MCP" below are commercial financial-data MCPs from the original Cowork plugin context. In Hermes:

- If any structured financial-data MCP is configured (see `native-mcp` skill), prefer it for point-in-time comps, precedent transactions, and filings.
- Otherwise fall back to: `web_search`/`web_extract` against SEC EDGAR (`https://www.sec.gov/cgi-bin/browse-edgar`); company IR pages; `browser_navigate` for interactive data portals; user-provided data (ask explicitly when unavailable).
- **Never fabricate.** If a multiple/precedent/filing number can't be sourced, flag the cell as `[UNSOURCED]` and surface it to the user.

## Attribution

Adapted from Anthropic's Claude for Financial Services plugin suite (Apache-2.0). Office-JS/Cowork live-Excel paths removed; targets headless openpyxl via the `excel-author` skill's conventions. Original: https://github.com/anthropics/financial-services
