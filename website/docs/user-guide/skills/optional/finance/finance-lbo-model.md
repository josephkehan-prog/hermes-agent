---
title: "Lbo Model"
sidebar_label: "Lbo Model"
description: "Build leveraged buyout models in Excel — sources & uses, debt schedule, cash sweep, exit multiple, IRR/MOIC sensitivity"
---

{/* This page is auto-generated from the skill's SKILL.md by website/scripts/generate-skill-docs.py. Edit the source SKILL.md, not this page. */}

# Lbo Model

Build leveraged buyout models in Excel — sources & uses, debt schedule, cash sweep, exit multiple, IRR/MOIC sensitivity. Pairs with excel-author. Use for PE screening, sponsor-case valuation, or illustrative LBO in a pitch.

## Skill metadata

| | |
|---|---|
| Source | Optional — install with `hermes skills install official/finance/lbo-model` |
| Path | `optional-skills/finance/lbo-model` |
| Version | `1.0.0` |
| Author | Anthropic (adapted by Nous Research) |
| License | Apache-2.0 |
| Platforms | linux, macos, windows |
| Tags | `finance`, `valuation`, `lbo`, `private-equity`, `excel`, `openpyxl`, `modeling` |
| Related skills | [`excel-author`](/docs/user-guide/skills/optional/finance/finance-excel-author), [`pptx-author`](/docs/user-guide/skills/optional/finance/finance-pptx-author), [`dcf-model`](/docs/user-guide/skills/optional/finance/finance-dcf-model), [`3-statement-model`](/docs/user-guide/skills/optional/finance/finance-3-statement-model) |

## Reference: full SKILL.md

:::info
The following is the complete skill definition that Hermes loads when this skill is triggered. This is what the agent sees as instructions when the skill is active.
:::

## Environment

This skill assumes **headless openpyxl** — you are producing an .xlsx file on disk.
Follow the `excel-author` skill's conventions for cell coloring, formulas, named ranges, and sensitivity tables.
Recalculate before delivery: `python /path/to/excel-author/scripts/recalc.py ./out/model.xlsx`.

---

## TEMPLATE REQUIREMENT

**This skill uses templates for LBO models. Always check for an attached template file first.**

Before starting any LBO model:
1. **If a template file is attached/provided**: Use that template's structure exactly - copy it and populate with the user's data
2. **If no template is attached**: Ask the user: *"Do you have a specific LBO template you'd like me to use? If not, I can use the standard template which includes Sources & Uses, Operating Model, Debt Schedule, and Returns Analysis."*
3. **If using the standard template**: Copy `examples/LBO_Model.xlsx` as your starting point and populate it with the user's assumptions

**IMPORTANT**: When a file like `LBO_Model.xlsx` is attached, you MUST use it as your template - do not build from scratch. Even if the template seems complex or has more features than needed, copy it and adapt it to the user's requirements. Never decide to "build from scratch" when a template is provided.

---

## CRITICAL INSTRUCTIONS — READ FIRST

Use Python/openpyxl. Write formula strings (`ws["D20"] = "=B5*B6"`), then run the `excel-author` skill's `recalc.py` helper before delivery.

### Core Principles
* **Every calculation must be an Excel formula** - NEVER compute values in Python and hardcode results into cells. When using openpyxl, write `cell.value = "=B5*B6"` (formula string), NOT `cell.value = 1250` (computed result). The model must be dynamic and update when inputs change.
* **Use the template structure** - Follow the organization in `examples/LBO_Model.xlsx` or the user's provided template. Do not invent your own layout.
* **Use proper cell references** - All formulas should reference the appropriate cells. Never type numbers that should come from other cells.
* **Maintain sign convention consistency** - Follow whatever sign convention the template uses (some use negative for outflows, some use positive). Be consistent throughout.
* **Work section by section, verify with user at each step** - Complete one section fully, show the user what was built, run the section's verification checks, and get confirmation BEFORE moving to the next section. Do NOT build the entire model end-to-end and then present it — later sections depend on earlier ones, so catching a mistake in Sources & Uses after the returns are already built means rework everywhere.

### Formula Color Conventions
* **Blue (0000FF)**: Hardcoded inputs - typed numbers that don't reference other cells
* **Black (000000)**: Formulas with calculations - any formula using operators or functions (`=B4*B5`, `=SUM()`, `=-MAX(0,B4)`)
* **Purple (800080)**: Links to cells on the **same tab** - direct references with no calculation (`=B9`, `=B45`)
* **Green (008000)**: Links to cells on **different tabs** - cross-sheet references (`=Assumptions!B5`, `='Operating Model'!C10`)

### Fill Color Palette — Professional Blues & Greys (Default unless user/template specifies otherwise)
* **Keep it minimal** — only use blues and greys for cell fills. Do NOT introduce greens, yellows, reds, or multiple accents. A professional LBO model uses restraint.
* **Default fill palette:**
  * **Section headers** (Sources & Uses, Operating Model, etc.): Dark blue `#1F4E79` with white bold text
  * **Column headers** (Year 1, Year 2, etc.): Light blue `#D9E1F2` with black bold text
  * **Input cells**: Light grey `#F2F2F2` (or just white) — the blue *font* is the signal, fill is secondary
  * **Formula/calculated cells**: White, no fill
  * **Key outputs** (IRR, MOIC, Exit Equity): Medium blue `#BDD7EE` with black bold text
* **That's the whole palette.** 3 blues + 1 grey + white. If the template uses its own colors, follow the template instead.
* Note: The blue/black/purple/green **font** colors above are for distinguishing inputs vs formulas vs links. Those are separate from the **fill** palette here — both work together.

### Number Formatting Standards
* **Currency**: `$#,##0;($#,##0);"-"` or `$#,##0.0` depending on template
* **Percentages**: `0.0%` (one decimal)
* **Multiples**: `0.0"x"` (one decimal)
* **MOIC/Detailed Ratios**: `0.00"x"` (two decimals for precision)
* **All numeric cells**: Right-aligned

---

### Clarify Requirements First

Before filling any formulas:

* **Examine the template structure** - Identify all sections, understand the timeline (which columns are which periods), note any existing formulas
* **Ask the user if anything is unclear** - If the template structure, calculation methods, or requirements are ambiguous, ask before proceeding
* **Confirm key assumptions** - Any key inputs, calculation preferences, or specific requirements
* **ONLY AFTER understanding the template**, proceed to fill in formulas

---

## TEMPLATE ANALYSIS PHASE - DO THIS FIRST

Before filling any formulas, examine the template thoroughly: map the structure
(which sections feed into others), understand the timeline (which columns are
which periods, where projections start), identify input vs. formula cells
(color/border/shading conventions), read row/column labels carefully rather
than assuming, check for partially-filled formulas (don't overwrite unless
asked), and note template-specific sign conventions and tab organization.

---

## FILLING FORMULAS - GENERAL APPROACH

For each cell that needs a formula, follow this hierarchy:
1. **Check the template** — does the cell already have a formula, a comment, or an obvious pattern from neighboring cells?
2. **Check the user's instructions** — did they specify a calculation method or assumption that affects this cell?
3. **Apply standard practice** — if neither specifies, use standard LBO modeling conventions, document assumptions made, and ask the user if genuinely uncertain.

---

## COMMON PROBLEM AREAS

The following calculation patterns frequently cause issues across LBO models. Pay special attention when you encounter these:

### Balancing Sections
* When two sections must equal (e.g., Sources = Uses), one item is typically the "plug" (balancing figure)
* Identify which item is the plug and calculate it as the difference

### Tax Calculations
* Tax formulas should only reference the relevant income line and tax rate
* Should NOT reference unrelated sections (e.g., debt schedules)
* Consider whether losses create tax shields or are simply ignored

### Interest and Circular References
* Interest calculations can create circularity if they reference balances affected by cash flows
* Use **Beginning Balance** (not average or ending) to break circular references
* Pattern: Interest → Cash Flow → Paydown → Ending Balance (if interest uses ending balance, this circles back)

### Debt Paydown / Cash Sweeps
* When multiple debt tranches exist, there's usually a priority order
* Cash sweep should respect the priority waterfall
* Balances cannot go negative - use MAX or MIN functions appropriately

### Returns Calculations (IRR/MOIC)
* Cash flows must have correct signs: Investment = negative, Proceeds = positive
* If using XIRR, need corresponding dates
* If using IRR, cash flows should be in consecutive periods
* MOIC = Total Proceeds / Total Investment

### Sensitivity Tables
* **Use ODD dimensions** (5×5 or 7×7) — never 4×4 or 6×6. Odd dimensions guarantee a true center cell.
* **Center cell = base case.** Build the row and column axis values symmetrically around the model's actual assumptions (e.g., if base entry multiple = 10.0x, axis = `[8.0x, 9.0x, 10.0x, 11.0x, 12.0x]`). The center cell's IRR/MOIC MUST then equal the model's actual IRR/MOIC output — this is the proof the table is wired correctly.
* **Highlight the center cell** — medium-blue fill (`#BDD7EE`) + bold font so the base case is visually anchored.
* Excel's DATA TABLE function may not work with openpyxl — instead write explicit formulas that reference row/column headers
* Each cell should show a DIFFERENT value — if all same, formulas aren't varying correctly
* Use mixed references (e.g., `$A5` for row input, `B$4` for column input)

---

## VERIFICATION CHECKLIST - RUN AFTER COMPLETION

### Run Formula Validation
```bash
python /path/to/excel-author/scripts/recalc.py model.xlsx
```
Must return success with zero errors.

Then verify by section: Sources/Uses balance with a correct plug, IS/BS/CF
subtotals and roll-forwards tie, debt schedules don't go negative, IRR/MOIC
cash-flow signs and ranges are correct, sensitivity tables are ODD-dimensioned
with the center cell equal to the model's actual output, formatting matches
the color conventions above, and outputs pass logical sanity checks. Full
checklist (every item, plus the Common Errors table mapping each failure mode
to its fix): read
[references/verification-checklist.md](https://github.com/NousResearch/hermes-agent/blob/main/optional-skills/finance/lbo-model/references/verification-checklist.md).

---

## WORKING WITH THE USER — SECTION-BY-SECTION CHECKPOINTS

* **If the template structure is unclear**, ask before proceeding
* **If the user's requirements conflict with the template**, confirm their preference
* **After completing each major section**, STOP and verify with the user before continuing:
  - **After Sources & Uses** → show the balanced table, confirm the plug is correct, get sign-off before building the operating model
  - **After Operating Model / Projections** → show the projected P&L, confirm growth rates and margins look right, get sign-off before the debt schedule
  - **After Debt Schedule** → show beginning/ending balances and interest, confirm the waterfall logic, get sign-off before returns
  - **After Returns (IRR/MOIC)** → show the cash flow series and outputs, confirm signs and ranges, get sign-off before sensitivity tables
  - **After Sensitivity Tables** → show that each cell varies, confirm the base case lands where expected
* **If errors are found during verification**, fix them before moving to the next section
* **Show your work** - explain key formulas or assumptions when helpful
* **Never present a completed model without having checked in at each section** — it's faster to catch a wrong cell reference at the source than to trace it backwards from a broken IRR

---

**This skill produces investment banking-quality LBO models by filling templates with correct formulas, proper formatting, and validated calculations. The skill adapts to any template structure while ensuring financial accuracy and professional presentation standards.**


## Data sources — MCP first, web fallback

Many passages below say "use the S&P Kensho MCP / Daloopa MCP / FactSet MCP". Those are commercial financial-data MCPs from the original Cowork plugin context. In Hermes:

- **If you have any structured financial-data MCP configured** (Hermes supports MCP — see `native-mcp` skill), prefer it for point-in-time comps, precedent transactions, and filings.
- **Otherwise**, fall back to:
  - `web_search` / `web_extract` against SEC EDGAR (`https://www.sec.gov/cgi-bin/browse-edgar`) for US filings
  - Company IR pages for press releases, earnings decks
  - `browser_navigate` for interactive data portals
  - User-provided data (explicitly ask when the context doesn't have it)
- **Never fabricate**. If a multiple, precedent, or filing number can't be sourced, flag the cell as `[UNSOURCED]` and surface it to the user.

## Attribution

This skill is adapted from Anthropic's Claude for Financial Services plugin suite (Apache-2.0). The Office-JS / Cowork live-Excel paths have been removed; this version targets headless openpyxl via the `excel-author` skill's conventions. Original: https://github.com/anthropics/financial-services
