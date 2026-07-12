# Comps Analysis: Visual Conventions, Template Layout, and Formula Reference

Read this when formatting the sheet, laying out a template from scratch, or
looking up an Excel formula. All defaults here are overridden by user
preferences or an uploaded template — see SKILL.md's Overview section.

## Visual Convention Standards (OPTIONAL — user preferences and uploaded templates always override)

**IMPORTANT: These are suggested defaults only. Always prioritize:**
1. User's explicit formatting preferences
2. Formatting from any uploaded template files
3. Company/team style guides
4. These defaults (only if no other guidance provided)

**Suggested Font & Typography:**
- **Font family**: Times New Roman (professional, readable, industry standard)
- **Font size**: 11pt for data cells, 12pt for headers
- **Bold text**: Section headers, company names, statistic labels

**Default Color & Shading — Professional Blue/Grey Palette (minimal is better):**
- **Keep it restrained** — only blues and greys. Do NOT introduce greens, oranges, reds, or multiple accent colors. A clean comps sheet uses 3-4 colors total.
- **Section headers** (e.g., "OPERATING STATISTICS & FINANCIAL METRICS"):
  - Dark blue background (`#1F4E79` or `#17365D` navy)
  - White bold text
  - Full row shading across all columns
- **Column headers** (e.g., "Company", "Revenue", "Margin"):
  - Light blue background (`#D9E1F2` or similar pale blue)
  - Black bold text
  - Centered alignment
- **Data rows**:
  - White background for company data
  - Black text for formulas; blue text for hardcoded inputs
- **Statistics rows** (Maximum, 75th Percentile, etc.):
  - Light grey background (`#F2F2F2`)
  - Black text, left-aligned labels
- **That's the whole palette**: dark blue + light blue + light grey + white. Nothing else unless the user's template says otherwise.

**Suggested Formatting Conventions:**
- **Decimal precision**:
  - Percentages: 1 decimal (12.3%)
  - Multiples: 1 decimal (13.5x)
  - Dollar amounts: No decimals, thousands separator (69,632)
  - Margins shown as percentages: 1 decimal (68.7%)
- **Borders**: No borders (clean, minimal appearance)
- **Alignment**: All metrics center-aligned for clean, uniform appearance
- **Cell dimensions**: All column widths should be uniform/even, all row heights should be consistent (creates clean, professional grid)

**Note:** If the user provides a template file or specifies different formatting, use that instead.

## Excel Formatting Checklist (Optional — adapt to user preferences)
- [ ] Font set to user's preferred style (default: Times New Roman, 11pt data, 12pt headers)
- [ ] Section headers formatted per user's template (default: dark blue #17365D with white bold text)
- [ ] Column headers formatted per user's template (default: light blue/gray #D9E2F3 with black bold text)
- [ ] Statistics rows formatted per user's template (default: light gray #F2F2F2)
- [ ] No borders applied (clean, minimal appearance)
- [ ] **Column widths set to uniform/even width** (creates clean, professional appearance)
- [ ] **Row heights set to consistent height** (typically 20-25pt for data rows)
- [ ] Numbers formatted with proper decimal precision and thousands separators
- [ ] **All metrics center-aligned** for clean, uniform appearance
- [ ] **One blank row for separation between company data and statistics rows**
- [ ] **No separate "SECTOR STATISTICS" or "VALUATION STATISTICS" header rows**
- [ ] **Every hard-coded input cell has a comment with either: (1) exact data source, OR (2) assumption explanation**
- [ ] **Hyperlinks added to cells where applicable** (SEC filings, data provider pages, reports)

## Example Template Layout

**Simple Version (Start here):**
```
┌─────────────────────────────────────────────────────────────┐
│ TECHNOLOGY - COMPARABLE COMPANY ANALYSIS                    │
│ Microsoft • Alphabet • Amazon                               │
│ As of Q4 2024 | All figures in USD Millions                │
├─────────────────────────────────────────────────────────────┤
│ OPERATING METRICS                                           │
├──────────┬─────────┬─────────┬──────────┬──────────────────┤
│ Company  │ Revenue │ Growth  │ Gross    │ EBITDA  │ EBITDA │
│          │ (LTM)   │ (YoY)   │ Margin   │ (LTM)   │ Margin │
├──────────┼─────────┼─────────┼──────────┼─────────┼────────┤
│ MSFT     │ 261,400 │ 12.3%   │ 68.7%    │ 205,100 │ 78.4%  │
│ GOOGL    │ 349,800 │ 11.8%   │ 57.9%    │ 239,300 │ 68.4%  │
│ AMZN     │ 638,100 │ 10.5%   │ 47.3%    │ 152,600 │ 23.9%  │
│          │         │         │          │         │        │ [blank row]
│ Median   │ =MEDIAN │ =MEDIAN │ =MEDIAN  │ =MEDIAN │=MEDIAN │
│ 75th %   │ =QUART  │ =QUART  │ =QUART   │ =QUART  │=QUART  │
│ 25th %   │ =QUART  │ =QUART  │ =QUART   │ =QUART  │=QUART  │
├─────────────────────────────────────────────────────────────┤
│ VALUATION MULTIPLES                                         │
├──────────┬──────────┬──────────┬──────────┬────────────────┤
│ Company  │ Mkt Cap  │ EV       │ EV/Rev   │ EV/EBITDA │ P/E│
├──────────┼──────────┼──────────┼──────────┼───────────┼────┤
│ MSFT     │3,550,000 │3,530,000 │ 13.5x    │ 17.2x     │36.0│
│ GOOGL    │2,030,000 │1,960,000 │  5.6x    │  8.2x     │24.5│
│ AMZN     │2,226,000 │2,320,000 │  3.6x    │ 15.2x     │58.3│
│          │          │          │          │           │    │ [blank row]
│ Median   │ =MEDIAN  │ =MEDIAN  │ =MEDIAN  │ =MEDIAN   │=MED│
│ 75th %   │ =QUART   │ =QUART   │ =QUART   │ =QUART    │=QRT│
│ 25th %   │ =QUART   │ =QUART   │ =QUART   │ =QUART    │=QRT│
└──────────┴──────────┴──────────┴──────────┴───────────┴────┘
```

**Add complexity only when needed:**
- Include quarterly AND LTM if seasonality matters
- Add FCF metrics if cash generation is key story
- Include industry-specific metrics (Rule of 40 for SaaS, etc.)
- Add more statistics rows if you have >5 companies

## Advanced Features

### Dynamic Headers
For columns showing calculations, use clear unit labels:
```
Revenue Growth (YoY) % | EBITDA Margin | FCF Margin | Rule of 40
```

### Quartile Analysis Benefits
Instead of just mean/median, quartiles show:
- **75th percentile** = "Premium" companies trade here
- **Median** = Typical market valuation
- **25th percentile** = "Discount" territory

This helps answer: "Is our target company trading rich or cheap vs. peers?"

### Industry-Specific Modifications

**Software/SaaS:**
- Add: ARR, Net Dollar Retention, CAC Payback Period
- Emphasize: Rule of 40, FCF margins, gross margins >70%

**Healthcare:**
- Add: R&D/Revenue, Pipeline value, Regulatory status
- Emphasize: EBITDA margins, growth rates, reimbursement risk

**Industrials:**
- Add: Backlog, Order book trends, Geographic mix
- Emphasize: ROIC, asset turnover, cyclical adjustments

**Consumer:**
- Add: Same-store sales, Customer acquisition cost, Brand value
- Emphasize: Revenue growth, gross margins, inventory turns

## Industry-Specific Additions (Optional)

Only add these if they're critical to your analysis. Most comps work fine with just core metrics.

**Software/SaaS:** Add if relevant: ARR, Net Dollar Retention, Rule of 40

**Financial Services:** Add if relevant: ROE, Net Interest Margin, Efficiency Ratio

**E-commerce:** Add if relevant: GMV, Take Rate, Active Buyers

**Healthcare:** Add if relevant: R&D/Revenue, Pipeline Value, Patent Timeline

**Manufacturing:** Add if relevant: Asset Turnover, Inventory Turns, Backlog

## Formulas Reference Guide

### Essential Excel Formulas
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

### Common Ratio Formulas
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

### Formula Examples (Operating Metrics — Row 7 as example)
```excel
// Core ratios - these are always calculated
Gross Margin (F7): =E7/C7
EBITDA Margin (H7): =G7/C7

// Optional ratios - include if relevant
FCF Margin: =[FCF]/[Revenue]
Net Margin: =[Net Income]/[Revenue]
Rule of 40: =[Growth %]+[FCF Margin %]
```

### Formula Examples (Valuation Multiples)
```excel
// Core multiples - always include these
EV/Revenue: =[Enterprise Value]/[LTM Revenue]
EV/EBITDA: =[Enterprise Value]/[LTM EBITDA]
P/E Ratio: =[Market Cap]/[Net Income]

// Optional multiples - include if data available
FCF Yield: =[LTM FCF]/[Market Cap]
PEG Ratio: =[P/E]/[Growth Rate %]
```
