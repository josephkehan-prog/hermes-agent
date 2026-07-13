---
title: "Regex Craft — Use when the user wants help writing, fixing, testing, or explaining a regular expression"
sidebar_label: "Regex Craft"
description: "Use when the user wants help writing, fixing, testing, or explaining a regular expression"
---

{/* This page is auto-generated from the skill's SKILL.md by website/scripts/generate-skill-docs.py. Edit the source SKILL.md, not this page. */}

# Regex Craft

Use when the user wants help writing, fixing, testing, or explaining a regular expression.

## Skill metadata

| | |
|---|---|
| Source | Bundled (installed by default) |
| Path | `skills/software-development/regex-craft` |
| Version | `1.0.0` |
| Author | Hermes Agent |
| License | MIT |
| Platforms | linux, macos, windows |
| Tags | `regex`, `regular-expression`, `pattern`, `text` |
| Related skills | [`systematic-debugging`](/docs/user-guide/skills/bundled/software-development/software-development-systematic-debugging), [`sql-review`](/docs/user-guide/skills/bundled/software-development/software-development-sql-review) |

## Reference: full SKILL.md

:::info
The following is the complete skill definition that Hermes loads when this skill is triggered. This is what the agent sees as instructions when the skill is active.
:::

# Regex Craft

## Boundary

Build, repair, or explain one regular expression against concrete examples. Use
when the pattern's behavior can be checked against sample strings. Do not use
for full parsing of nested/recursive structures (HTML, JSON, code) — recommend a
real parser instead.

## Always Work From Examples

Never hand back a pattern you have not checked. Require, or ask for:

- **Should-match** strings (at least 2, covering the variation).
- **Should-NOT-match** strings (at least 1 near-miss).

Then verify the pattern accepts all should-match and rejects all should-not
before delivering it.

## Procedure

1. Restate the goal as a rule in words ("digits, then '-', then 2 letters").
2. Draft the smallest pattern that satisfies it. Prefer explicit character
   classes over `.`; anchor with `^`/`$` when matching a whole string.
3. Test against every provided example. Fix and re-test until all pass.
4. State the target flavor (PCRE / Python `re` / JavaScript / POSIX) — escaping
   and features differ; call out anything non-portable.
5. Explain the pattern token by token so the user can maintain it.

## Catastrophic Backtracking (report as a risk)

Flag and rewrite patterns that can blow up on adversarial input:

- Nested quantifiers: `(a+)+`, `(a*)*`, `(.*)*`.
- Overlapping alternation under a quantifier: `(a|a)*`, `(\d+|\w+)*`.
- Prefer possessive quantifiers/atomic groups where supported, or anchor and
  make classes disjoint. Note the danger explicitly; do not ship an
  exponential pattern silently.

## Rules

1. Deliver only a pattern you have verified against the examples; say which you
   ran it against.
2. Escape correctly for the named flavor; if the flavor is unknown, ask before
   assuming.
3. Prefer readable patterns (named groups, comments/`x` flag) over clever dense
   ones when the tool supports them.
4. For anything requiring balanced/recursive matching, stop and recommend a
   parser — do not force a fragile regex.

## Stop Conditions

- No examples provided and the user cannot give any: explain the pattern is
  unverifiable and ask for sample strings first.
- Requirement needs recursion/balancing a regex cannot express: say so and name
  the parser approach instead.

## Completion Gate

Done when the pattern matches every should-match example, rejects every
should-not example, the flavor is named, backtracking risk is assessed, and a
token-by-token explanation is given.
