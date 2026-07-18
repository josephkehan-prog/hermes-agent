---
name: csv-insights
description: Summarize, filter, and aggregate CSV or TSV files.
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    domain: productivity
    tags: [csv, data, tabular, analysis, spreadsheet]
    related_skills: [ocr-and-documents, jupyter-live-kernel]
---

# CSV Insights

## Boundary

Answer questions about a delimited data file (CSV/TSV/pipe). Use for structure,
summary statistics, filtering, and grouping. Do not use for editing the file in
place, for spreadsheets with formulas (`.xlsx`), or for datasets too large to
read into memory — hand those to a notebook or database skill.

## Read Deterministically

Always parse with a real CSV parser (Python `csv` or `pandas`), never by
splitting on commas — quoted fields contain commas. Steps:

1. Read the first 2 KB. Detect the delimiter (`,` `\t` `;` `|`) by counting
   candidates in the header line; pick the most frequent.
2. Treat the first row as the header unless the user says otherwise. Record
   column names and count.
3. Infer each column's type from a sample of up to 100 rows: integer, float,
   date, or text. A column with any non-numeric value is text.
4. Report row count and column count before answering anything else.

## Answering

| User asks | Do |
|---|---|
| "what's in this file" | Print columns, inferred types, row count, and 3 sample rows |
| "summary stats" | For numeric columns: min, max, mean, median, count of blanks. For text: distinct-value count, top 3 values |
| "filter WHERE X" | Return matching rows (cap at 50; report how many matched total) |
| "group by X" | Count or aggregate per distinct value of X, sorted descending |
| "how many …" | Return the count and the exact predicate you applied |

## Rules

1. State the predicate or aggregation you applied, in words, next to every
   answer — the user must be able to check it.
2. Blank and malformed cells: count them, never silently drop. Report "N blank"
   alongside stats.
3. Do not infer meaning of a column from its name alone; confirm against values.
4. Never modify the source file. All output is read-only analysis.
5. Numbers reported must come from the parsed data, never estimated.

## Stop Conditions

- File unreadable, not delimited, or a single column with no delimiter: stop and
  report what you found.
- Ragged rows (differing field counts): report the row numbers, analyze the
  consistent rows, and say how many were skipped.
- Encoding errors: report the byte offset; do not guess-replace characters.

## Completion Gate

Done when the answer states its predicate/aggregation, every reported number
came from the parsed rows, and blank/skipped counts are disclosed.
