# Full Verification Checklist

Run this after completing an LBO model, in addition to
`python /path/to/excel-author/scripts/recalc.py model.xlsx` (must return success
with zero errors).

### Section Balancing
- [ ] Any sections that must balance (Sources/Uses, Assets/Liabilities) balance exactly
- [ ] Plug items are calculated correctly as the balancing figure
- [ ] Amounts that should match across sections are consistent

### Income/Operating Projections
- [ ] Revenue/top-line builds correctly from drivers or growth rates
- [ ] All cost and expense items calculated appropriately
- [ ] Subtotals and totals sum correctly
- [ ] Margins and ratios are reasonable
- [ ] Links to assumptions are correct

### Balance Sheet (if applicable)
- [ ] Assets = Liabilities + Equity (must balance)
- [ ] All items link to appropriate schedules or roll-forwards
- [ ] Beginning balances = prior period ending balances
- [ ] Check row included and shows zero

### Cash Flow (if applicable)
- [ ] Starts with correct income figure
- [ ] Non-cash items added/subtracted appropriately
- [ ] Working capital changes have correct signs
- [ ] Ending Cash = Beginning Cash + Net Cash Flow
- [ ] Cash balances are consistent across statements

### Supporting Schedules
- [ ] Roll-forward schedules balance (Beginning + Changes = Ending)
- [ ] Schedules link correctly to main statements
- [ ] Calculated items use appropriate drivers
- [ ] All periods are calculated consistently

### Debt/Financing Schedules (if applicable)
- [ ] Beginning balances tie to sources or prior period
- [ ] Interest calculated on appropriate balance (typically beginning)
- [ ] Paydowns respect cash availability and priority
- [ ] Ending balances cannot be negative
- [ ] Totals sum tranches correctly

### Returns/Output Analysis
- [ ] Exit/terminal values calculated correctly
- [ ] All relevant adjustments included
- [ ] Cash flow signs are correct (negative for investment, positive for proceeds)
- [ ] IRR/MOIC formulas reference complete ranges
- [ ] Results are reasonable for the scenario

### Sensitivity Tables (if applicable)
- [ ] Grid dimensions are ODD (5×5 or 7×7) — there is a true center cell
- [ ] Row and column axis values are symmetric around the base case (`[base-2Δ, base-Δ, base, base+Δ, base+2Δ]`)
- [ ] Center cell output equals the model's actual IRR/MOIC — confirms the table is wired correctly
- [ ] Center cell is highlighted (medium-blue fill `#BDD7EE`, bold font)
- [ ] Row and column headers contain appropriate input values
- [ ] Each data cell contains a formula (not hardcoded)
- [ ] Each data cell shows a DIFFERENT value
- [ ] Values move in expected directions (higher exit multiple → higher IRR, etc.)

### Formatting
- [ ] Hardcoded inputs are blue (0000FF)
- [ ] Calculated formulas are black (000000)
- [ ] Same-tab links are purple (800080)
- [ ] Cross-tab links are green (008000)
- [ ] All numbers are right-aligned
- [ ] Appropriate number formats applied throughout
- [ ] No cells show error values (#REF!, #DIV/0!, #VALUE!, #NAME?)

### Logical Sanity Checks
- [ ] Numbers are reasonable order of magnitude
- [ ] Trends make sense (growth, decline, stabilization as expected)
- [ ] No obviously wrong values (negative where should be positive, impossible percentages, etc.)
- [ ] Key outputs are within reasonable ranges for the type of analysis

## Common Errors to Avoid

| Error | What Goes Wrong | How to Fix |
|-------|-----------------|------------|
| Hardcoding calculated values | Model doesn't update when inputs change | Always use formulas that reference source cells |
| Wrong cell references after copying | Formulas point to wrong cells | Verify all links, use appropriate $ anchoring |
| Circular reference errors | Model can't calculate | Use beginning balances for interest-type calcs, break the circle |
| Sections don't balance | Totals that should match don't | Ensure one item is the plug (calculated as difference) |
| Negative balances where impossible | Paying/using more than available | Use MAX(0, ...) or MIN functions appropriately |
| IRR/return errors | Wrong signs or incomplete ranges | Check cash flow signs and ensure formula covers all periods |
| Sensitivity table shows same value | Formula not varying with inputs | Check cell references - need mixed references ($A5, B$4) |
| Roll-forwards don't tie | Beginning ≠ prior ending | Verify links between periods |
| Inconsistent sign conventions | Additions become subtractions or vice versa | Follow template's convention consistently throughout |
