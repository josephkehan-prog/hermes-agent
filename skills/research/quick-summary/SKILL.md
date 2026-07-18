---
name: quick-summary
description: Summarize or extract key points from text.
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    domain: research
    tags: [summary, condense, extraction, reading]
    related_skills: [research-paper-writing, workspace-rag]
---

# Quick Summary

## Boundary

Condense text the user supplies or points to. Use only when the goal is a
shorter faithful rendering, not analysis, translation, or fact-checking. Do not
summarize a source you have not actually read — fetch or read it first.

## Inputs

The user gives one of: pasted text, a file path, or a URL. Resolve it to actual
text before summarizing:

| Input | Resolve by |
|---|---|
| Pasted text | Use as-is |
| File path | Read the file |
| URL | Fetch the page text |

If the source cannot be read, stop and say why. Never summarize from the title
or filename alone.

## Length Target

Pick the output size from the request, defaulting to ~10% of the source:

| User says | Target |
|---|---|
| "TL;DR" / "one line" | 1 sentence |
| "brief" / "quick" | 3–5 bullet points |
| "summary" (unqualified) | ~10% of source length, capped at 200 words |
| "detailed summary" | ~25% of source length |

## Procedure

1. Read the whole source once before writing anything.
2. Identify the source's own thesis and main supporting points. Do not add
   points the source does not make.
3. Write the summary at the target length. Lead with the single most important
   point.
4. Preserve the source's stance and hedging — if the source says "may", do not
   write "will".
5. Keep names, numbers, and quoted figures exact. If a number is central, cite
   it; never round or invent one.

## Output Shape

- One line: a single plain sentence.
- Bullets: a flat list, most important first, no nesting.
- Paragraph: for "detailed summary", 1–3 short paragraphs.

Add a one-line "Not covered:" note only if the user asked about something the
source does not address.

## Stop Conditions

- Source unreadable or empty: stop, report it, do not fabricate a summary.
- Source shorter than the target length: return it as-is and say it was already
  short enough.
- Source is a list of unrelated items with no thesis: say so and list the item
  headers instead of forcing a narrative.

## Completion Gate

Done when the summary meets the target length, contains no claim absent from
the source, and preserves every central number. Deliver it with no preamble.
