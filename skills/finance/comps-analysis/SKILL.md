---
name: comps-analysis
description: Build comparable company analysis in Excel — operating metrics, valuation multiples, statistical benchmarking vs peer sets. Pairs with excel-author. Use for public-company valuation, IPO pricing, sector benchmarking, or outlier detection.
version: 1.0.0
author: Anthropic (adapted by Nous Research)
license: Apache-2.0
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [finance, valuation, comps, excel, openpyxl, modeling, investment-banking]
    related_skills: [excel-author, pptx-author, dcf-model, lbo-model]
---

## Environment

Headless **openpyxl** — producing an `.xlsx` on disk. Follow `excel-author` conventions (cell coloring, formulas, named ranges, sensitivity tables). Recalc before delivery: `python /path/to/excel-author/scripts/recalc.py ./out/model.xlsx`.

Full template layout + worked example (MSFT/GOOGL/AMZN sample data), verbatim long form: `REFERENCE.md` next to this file. Example workbook: `examples/comps_example.xlsx`.

# Comparable Company Analysis

## ⚠️ Data Source Priority (READ FIRST)
1. **FIRST: MCP data sources** — if S&P Kensho MCP, FactSet MCP, or Daloopa MCP available, use them exclusively.
2. **DO NOT use web search** if those MCPs available.
3. **ONLY if MCPs unavailable:** Bloomberg Terminal, SEC EDGAR filings, other institutional sources.
4. **NEVER use web search as primary source** — lacks accuracy, audit trails, reliability for institutional-grade work.

MCP sources give verified data with citations; web results can be outdated/inaccurate.

## Overview
Build institutional-grade comps combining operating metrics, valuation multiples, statistical benchmarking. Output = structured Excel readable by someone who didn't build it. Example workbook `examples/comps_example.xlsx`: use for structural hierarchy, rigor level, principles (clear headers, transparent formulas, audit trails) — NOT for copying exact format/metrics/layout/visual style.

Ask first: (1) preferred format or adapt template? (2) audience (investment committee, board, quick reference, memo)? (3) key question (valuation, growth, positioning, efficiency)? (4) context (M&A, investment decision, sector benchmarking, performance review)? Adapt: mega-caps ≠ SaaS startups; add sector metrics early (cloud ARR, enterprise customers); M&A ≠ portfolio monitoring. Use template *principles*, vary *execution*. User examples/preferences override defaults.

## Core Philosophy
"Build the right structure first, then let the data tell the story." Headers force strategic thinking → clean input data → transparent formulas → statistics emerge automatically.

## ⚠️ Formulas Over Hardcodes + Step-by-Step Verification

**Formulas, not hardcodes:**
- Every derived value (margin, multiple, statistic) MUST be an Excel formula referencing input cells — never a pre-computed number.
- In openpyxl: write `cell.value = "=E7/C7"` (formula string), NOT `cell.value = 0.687`.
- Only hardcoded values = raw input data (revenue, EBITDA, share price) — each gets a cell comment with its source.
- Why: model must auto-update when an input changes. A hardcoded margin is a silent bug.

**Verify step-by-step with user** (don't build end-to-end then present):
- After structure → show header layout before filling data.
- After raw inputs → confirm sources/periods before formulas.
- After operating-metrics formulas → show margins, sanity-check before valuation.
- After valuation multiples → confirm reasonable before adding statistics.

## Section 1: Document Structure & Setup

### Header Block (Rows 1-3)
```
Row 1: [ANALYSIS TITLE] - COMPARABLE COMPANY ANALYSIS
Row 2: [List of Companies with Tickers] • [Company 1 (TICK1)] • [Company 2 (TICK2)] • [Company 3 (TICK3)]
Row 3: As of [Period] | All figures in [USD Millions/Billions] except per-share amounts and ratios
```
Establishes context immediately: what, when, how to interpret numbers.

### Visual Conventions (OPTIONAL — user prefs / uploaded templates / style guides override these defaults, in that priority order)

**Font:** Times New Roman; 11pt data cells, 12pt headers; bold for section headers, company names, statistic labels.

**Color — restrained blue/grey only (3-4 colors total; NO greens/oranges/reds/multiple accents):**
- **Section headers** (e.g. "OPERATING STATISTICS & FINANCIAL METRICS"): dark blue bg `#1F4E79` or `#17365D` navy, white bold text, full-row shading.
- **Column headers** ("Company", "Revenue", "Margin"): light blue bg `#D9E1F2`, black bold text, centered.
- **Data rows**: white bg; black text for formulas, blue text for hardcoded inputs.
- **Statistics rows** (Maximum, 75th Percentile, ...): light grey bg `#F2F2F2`, black text, left-aligned labels.
- Whole palette: dark blue + light blue + light grey + white.

**Formatting:**
- Decimals: percentages 1dp (12.3%); multiples 1dp (13.5x); dollars no decimals + thousands separator (69,632); margins as % 1dp (68.7%).
- Borders: none (clean, minimal).
- Alignment: all metrics center-aligned.
- Cell dimensions: uniform column widths, consistent row heights.

## Section 2: Operating Statistics & Financial Metrics

### Core Columns
1. **Company** 2. **Revenue** (LTM/quarterly/annual) 3. **Revenue Growth** (YoY %) 4. **Gross Profit** (Rev − COGS) 5. **Gross Margin** (GP/Revenue) 6. **EBITDA** 7. **EBITDA Margin** (EBITDA/Revenue).

### Optional Additions (by industry/purpose)
Quarterly vs LTM (seasonality); Free Cash Flow; FCF Margin (FCF/Rev); Net Income; Operating Income; CapEx metrics; Rule of 40 (SaaS: Growth% + Margin%); FCF Conversion (advanced).

### Formula Examples (Row 7 as example)
```excel
// Core ratios - these are always calculated
Gross Margin (F7): =E7/C7
EBITDA Margin (H7): =G7/C7

// Optional ratios - include if relevant
FCF Margin: =[FCF]/[Revenue]
Net Margin: =[Net Income]/[Revenue]
Rule of 40: =[Growth %]+[FCF Margin %]
```
**Golden Rule:** every ratio = [Something]/[Revenue] or [Something]/[Something on this sheet].

### Statistics Block (after company data)
Add statistics formulas for all comparable metrics (ratios, margins, growth rates, multiples):
```
[Leave one blank row for visual separation]
- Maximum: =MAX(B7:B9)
- 75th Percentile: =QUARTILE(B7:B9,3)
- Median: =MEDIAN(B7:B9)
- 25th Percentile: =QUARTILE(B7:B9,1)
- Minimum: =MIN(B7:B9)
```
**NEED statistics** (comparable): Revenue Growth %, Gross Margin %, EBITDA Margin %, EPS, EV/Revenue, EV/EBITDA, P/E, Dividend Yield %, Beta.
**DON'T need statistics** (size metrics): Revenue, EBITDA, Net Income, Market Cap, Enterprise Value.
- One blank row between data and stats. Do NOT add "SECTOR STATISTICS" or "VALUATION STATISTICS" header rows.
- Quartiles show distribution, not just average (75th pct = "premium" trading level).

## Section 3: Valuation Multiples & Investment Metrics

### Core Columns
1. **Company** (same order as operating) 2. **Market Cap** 3. **Enterprise Value** (Mkt Cap ± Net Debt/Cash) 4. **EV/Revenue** 5. **EV/EBITDA** 6. **P/E Ratio**.

### Optional Metrics (by context)
FCF Yield (FCF/Mkt Cap); PEG (P/E÷Growth); Price/Book; ROE/ROA; Revenue/EBITDA CAGR; Asset Turnover (Rev/Assets); Debt/Equity. Include 3-5 core multiples that matter; don't dump every metric.

### Formula Examples
```excel
// Core multiples - always include these
EV/Revenue: =[Enterprise Value]/[LTM Revenue]
EV/EBITDA: =[Enterprise Value]/[LTM EBITDA]
P/E Ratio: =[Market Cap]/[Net Income]

// Optional multiples - if data available
FCF Yield: =[LTM FCF]/[Market Cap]
PEG Ratio: =[P/E]/[Growth Rate %]
```

### Cross-Reference Rule
**CRITICAL:** valuation multiples MUST reference the operating-metrics section. Never input the same raw data twice. If revenue is in C7, EV/Revenue references C7.

### Statistics Block
Same as operating: Max, 75th, Median, 25th, Min per metric. One blank separator row. No "VALUATION STATISTICS" header row.

## Section 4: Notes & Methodology Documentation

- **Data Sources & Quality:** where from (S&P Kensho MCP, FactSet MCP, Daloopa MCP, Bloomberg, SEC filings); period (Q4 2024, audited); verification (cross-checked vs 10-K/10-Q). Prioritize MCP sources.
- **Key Definitions:** EBITDA method (Gross Profit + D&A, or Operating Income + D&A); FCF formula (Operating CF − CapEx); special metrics (Rule of 40, FCF Conversion); time-period defs (LTM, CAGR periods).
- **Valuation Methodology:** EV calc (Mkt Cap + Net Debt); growth rates used (historical CAGR, forward estimates); adjustments (one-time items excluded, normalized margins).
- **Analysis Framework:** investment thesis; which metrics matter most; how to read the statistics (quartiles = context).

## Section 5: Choosing Metrics (Decision Framework)

Start from "What question am I answering?":
- **Undervalued?** → EV/Revenue, EV/EBITDA, P/E, Market Cap. Skip operational/growth details.
- **Most efficient?** → Gross Margin, EBITDA Margin, FCF Margin, Asset Turnover. Skip size metrics.
- **Growing fastest?** → Revenue Growth %, EBITDA CAGR, User/Customer Growth. Skip margins/leverage.
- **Best cash generator?** → FCF, FCF Margin, FCF Conversion, CapEx intensity. Skip EBITDA/P/E.

### Industry-Specific Selection
- **Software/SaaS:** must=Revenue Growth, Gross Margin, Rule of 40; opt=ARR, Net Dollar Retention, CAC Payback; skip Asset Turnover, Inventory.
- **Manufacturing/Industrials:** must=EBITDA Margin, Asset Turnover, CapEx/Revenue; opt=ROA, Inventory Turns, Backlog; skip Rule of 40, SaaS metrics.
- **Financial Services:** must=ROE, ROA, Efficiency Ratio, P/E; opt=Net Interest Margin, Loan Loss Reserves; skip Gross Margin, EBITDA.
- **Retail/E-commerce:** must=Revenue Growth, Gross Margin, Inventory Turnover; opt=Same-Store Sales, CAC; skip heavy R&D/CapEx.

### "5-10 Rule"
5 operating metrics (Revenue, Growth, 2-3 margins/efficiency) + 5 valuation metrics (Market Cap, EV, 3 multiples) = 10 columns. >15 metrics = probably noise. Edit ruthlessly.

## Section 6: Best Practices & Quality Checks

### Before You Start
1. Define peer group (comparable business model, scale, geography). 2. Choose period (LTM smooths seasonality; quarterly shows trends). 3. Standardize units upfront (millions vs billions). 4. Map data sources.

### As You Build
1. Input all raw data first (complete blue text before formulas).
2. **Add cell comments to ALL hard-coded inputs** (right-click → Insert Comment). Document source OR assumption:
   - Sourced: cite exactly — e.g. "Bloomberg Terminal - MSFT Equity DES, accessed 2024-10-02"; "Q4 2024 10-K filing, page 42, line item 'Total Revenue'"; "FactSet consensus estimate as of 2024-10-02". Include hyperlinks (right-click → Link → SEC filing URL) when possible.
   - Assumption: explain reasoning — e.g. "Assumed 15% EBITDA margin based on peer median, company does not disclose"; "Estimated EV as Market Cap + $50M net debt (Q3 balance sheet, Q4 not yet available)"; "Forward P/E based on street consensus EPS of $3.45 (avg of 12 analyst estimates)".
   - Why: audit trails, data verification, assumption transparency, future updates.
3. Build formulas row by row (test each). 4. Absolute references for headers ($C$6 locks header row). 5. Format consistently (percentages as percentages). 6. Conditional formatting to highlight outliers.

### Sanity Checks
- **Margin test:** Gross margin > EBITDA margin > Net margin (always, by definition).
- **Multiple reasonableness:** EV/Revenue ~0.5-20x (varies by industry); EV/EBITDA ~8-25x (fairly consistent); P/E ~10-50x (depends on growth).
- **Growth-multiple correlation:** higher growth → higher multiples.
- **Size-efficiency trade-off:** larger companies often have better margins.

### Common Mistakes to Avoid
❌ Mixing market cap and enterprise value in formulas
❌ Different time periods for numerator/denominator (LTM vs quarterly)
❌ Hardcoding numbers into formulas instead of cell references
❌ Hard-coded inputs without cell comments citing source OR explaining assumption
❌ Missing hyperlinks to SEC filings/data sources when available
❌ Too many metrics without clear purpose
❌ Non-comparable companies (different business models)
❌ Outdated data without disclosure
❌ Averaging percentages incorrectly (should be median)

## Section 6: Advanced Features

- **Dynamic Headers:** clear unit labels, e.g. `Revenue Growth (YoY) % | EBITDA Margin | FCF Margin | Rule of 40`.
- **Quartile Analysis:** 75th pct = "premium" companies; median = typical valuation; 25th pct = "discount". Answers "is target trading rich or cheap vs peers?"
- **Industry-Specific Modifications:**
  - Software/SaaS: add ARR, Net Dollar Retention, CAC Payback; emphasize Rule of 40, FCF margins, gross margins >70%.
  - Healthcare: add R&D/Revenue, Pipeline value, Regulatory status; emphasize EBITDA margins, growth, reimbursement risk.
  - Industrials: add Backlog, Order book trends, Geographic mix; emphasize ROIC, asset turnover, cyclical adjustments.
  - Consumer: add Same-store sales, CAC, Brand value; emphasize revenue growth, gross margins, inventory turns.

## Section 7: Workflow & Practical Tips

### Step-by-Step Process
1. **Structure** (~30m): create headers; format cells (blue inputs, black formulas); lock units/date refs.
2. **Gather data** (~60-90m): pull from primary sources (Kensho/FactSet/Daloopa MCP if available; else Bloomberg, SEC); input raw in blue; document sources.
3. **Build formulas** (~30m): simple ratios (margins) → multiples (EV/Revenue) → cross-checks.
4. **Add statistics** (~15m): copy formula structure across columns; verify ranges (B7:B9, not B7:B10); check quartile logic.
5. **QC** (~30m): sanity checks; verify references; check #DIV/0!/#REF!; compare vs known benchmarks.
6. **Documentation** (~15m): complete notes; add sources; define methodologies; date-stamp.

### Pro Tips
Save templates; color-code outliers (conditional formatting >2 std dev); hyperlink to source files; version control ("Comps_v1_2024-12-15"); have someone else check formulas.

### Excel Formatting Checklist (adapt to user prefs)
- [ ] Font (default Times New Roman 11pt data / 12pt headers)
- [ ] Section headers (default dark blue #17365D, white bold)
- [ ] Column headers (default light blue/gray #D9E2F3, black bold)
- [ ] Statistics rows (default light gray #F2F2F2)
- [ ] No borders
- [ ] Uniform column widths; consistent row heights (~20-25pt data rows)
- [ ] Proper decimal precision + thousands separators
- [ ] All metrics center-aligned
- [ ] One blank separator row between company data and statistics
- [ ] No separate "SECTOR STATISTICS"/"VALUATION STATISTICS" header rows
- [ ] Every hard-coded input cell has comment: (1) exact source OR (2) assumption explanation
- [ ] Hyperlinks added where applicable (SEC filings, data provider pages, reports)

## Section 8: Example Template Layout
Full ASCII template + worked example (Technology comp: MSFT/GOOGL/AMZN sample numbers): **REFERENCE.md Section 8**.
Add complexity only when needed: quarterly AND LTM (seasonality); FCF metrics (cash story); industry metrics (Rule of 40 for SaaS); more stat rows if >5 companies.

## Section 9: Industry-Specific Additions (Optional)
Only add if critical. Software/SaaS: ARR, Net Dollar Retention, Rule of 40. Financial Services: ROE, Net Interest Margin, Efficiency Ratio. E-commerce: GMV, Take Rate, Active Buyers. Healthcare: R&D/Revenue, Pipeline Value, Patent Timeline. Manufacturing: Asset Turnover, Inventory Turns, Backlog.

## Section 10: Red Flags & Warning Signs
- **Data quality:** 🚩 inconsistent time periods (quarterly vs annual); 🚩 missing data unexplained; 🚩 >10% variance between data sources.
- **Valuation:** 🚩 negative-EBITDA companies valued on EBITDA multiples (use revenue multiples); 🚩 P/E >100x without hypergrowth story; 🚩 margins that don't fit the industry.
- **Comparability:** 🚩 different fiscal year ends (timing problems); 🚩 mixing pure-play and conglomerates; 🚩 materially different business models labeled "comps".
- When in doubt, exclude. 3 perfect comps > 6 questionable ones.

## Section 11: Formulas Reference Guide
```excel
// Statistical Functions
=AVERAGE(range)          // Simple mean
=MEDIAN(range)           // Middle value
=QUARTILE(range, 1)      // 25th percentile
=QUARTILE(range, 3)      // 75th percentile
=MAX(range)              // Maximum value
=MIN(range)              // Minimum value
=STDEV.P(range)          // Standard deviation

// Financial Calculations
=B7/C7                   // Simple ratio (Margin)
=SUM(B7:B9)/3            // Average of multiple companies
=IF(B7>0, C7/B7, "N/A")  // Conditional calculation
=IFERROR(C7/D7, 0)       // Handle divide by zero

// Cross-Sheet References
='Sheet1'!B7             // Reference another sheet
=VLOOKUP(A7, Table1, 2)  // Lookup from data table
=INDEX(MATCH())          // Advanced lookup

// Formatting
=TEXT(B7, "0.0%")        // Format as percentage
=TEXT(C7, "#,##0")       // Thousands separator
```
```excel
Gross Margin = Gross Profit / Revenue
EBITDA Margin = EBITDA / Revenue
FCF Margin = Free Cash Flow / Revenue
FCF Conversion = FCF / Operating Cash Flow
ROE = Net Income / Shareholders' Equity
ROA = Net Income / Total Assets
Asset Turnover = Revenue / Total Assets
Debt/Equity = Total Debt / Shareholders' Equity
```

## Key Principles Summary
1. Structure drives insight. 2. Less is more (5-10 metrics beat 20). 3. Choose metrics for your question (valuation ≠ efficiency). 4. Statistics show patterns (median/quartiles > average). 5. Transparency beats complexity. 6. Comparability is king (exclude rather than force). 7. Document your choices in notes.

## Output Checklist
- [ ] All companies truly comparable
- [ ] Consistent time periods
- [ ] Units clearly labeled (millions/billions)
- [ ] Formulas reference cells, not hardcoded values
- [ ] All hard-coded input cells have comments: (1) exact source with citation OR (2) clear assumption with explanation
- [ ] Hyperlinks where relevant (SEC EDGAR filings, Bloomberg pages, research reports)
- [ ] Statistics include ≥5 metrics (Max, 75th, Med, 25th, Min)
- [ ] Notes section documents sources and methodology
- [ ] Visual formatting follows conventions (blue = input, black = formula)
- [ ] Sanity checks pass (margins logical, multiples reasonable)
- [ ] Date stamp current ("As of [Date]")
- [ ] Formula auditing shows no errors (#DIV/0!, #REF!, #N/A)

## Continuous Improvement
After each comp, ask: did statistics reveal unexpected insights? were there data gaps? did stakeholders want metrics you didn't include? time taken vs expected? what would make it more useful next time? Save templates, learn from feedback, refine structure.

## Data sources — MCP first, web fallback
Passages above referencing S&P Kensho / Daloopa / FactSet MCP are commercial financial-data MCPs from the original Cowork plugin. In Hermes:
- **If any structured financial-data MCP is configured** (see `native-mcp` skill), prefer it for point-in-time comps, precedent transactions, filings.
- **Otherwise fall back to:** `web_search`/`web_extract` against SEC EDGAR (`https://www.sec.gov/cgi-bin/browse-edgar`) for US filings; company IR pages (press releases, earnings decks); `browser_navigate` for interactive data portals; user-provided data (ask when missing).
- **Never fabricate.** If a multiple, precedent, or filing number can't be sourced, flag the cell as `[UNSOURCED]` and surface it to the user.

## Attribution
Adapted from Anthropic's Claude for Financial Services plugin suite (Apache-2.0). Office-JS / Cowork live-Excel paths removed; targets headless openpyxl via `excel-author` conventions. Original: https://github.com/anthropics/financial-services
