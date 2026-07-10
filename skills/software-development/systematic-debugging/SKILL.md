---
name: systematic-debugging
description: "4-phase root cause debugging: understand bugs before fixing."
version: 1.1.0
author: Hermes Agent (adapted from obra/superpowers)
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [debugging, troubleshooting, problem-solving, root-cause, investigation]
    category: software-development
    related_skills: [test-driven-development, plan, subagent-driven-development]
---

# Systematic Debugging

## Overview

Random fixes waste time and create new bugs. Quick patches mask underlying issues.

**Core principle:** ALWAYS find root cause before attempting fixes. Symptom fixes are failure.

**Violating the letter of this process is violating the spirit of debugging.**

## The Iron Law

```
NO FIXES WITHOUT ROOT CAUSE INVESTIGATION FIRST
```

If you haven't completed Phase 1, you cannot propose fixes.

## The Feedback Loop Rule

The feedback loop is the debugging work. Before reading code to build a theory, create or identify a **tight** command that can go red on the user's exact symptom and green when the bug is fixed. A tight loop is fast, deterministic, agent-runnable, and specific enough to catch this bug — not merely "doesn't crash".

When a clean repro is hard, spend disproportionate effort building the loop. Guessing without a red-capable loop is the failure mode this skill exists to prevent. See REFERENCE.md for the ranked list of loop-construction strategies and loop-tightening tactics.

## When to Use

Use for ANY technical issue: test failures, bugs in production, unexpected behavior, performance problems, build failures, integration issues.

**Use this ESPECIALLY when:** under time pressure, "just one quick fix" seems obvious, you've already tried multiple fixes, previous fix didn't work, you don't fully understand the issue.

**Don't skip when:** issue seems simple (simple bugs have root causes too), you're in a hurry (rushing guarantees rework), someone wants it fixed NOW (systematic is faster than thrashing).

## The Four Phases

You MUST complete each phase before proceeding to the next.

### Phase 1: Root Cause Investigation

BEFORE attempting ANY fix:

1. **Read error messages carefully** — don't skip past errors/warnings, read stack traces completely, note line numbers/file paths/error codes.
2. **Build a tight feedback loop** — can you trigger the user's exact symptom with one command? Does it fail for this bug and pass once fixed? Is it fast and deterministic? If not reproducible, gather more data, don't guess. (Full strategy list in REFERENCE.md.)
3. **Check recent changes** — `git log --oneline -10`, `git diff`, `git log -p --follow <file>` — what changed that could cause this?
4. **Gather evidence in multi-component systems** — before proposing fixes, add diagnostic instrumentation at each component boundary (what enters, what exits, config/state), run once, then analyze evidence to find the failing component.
5. **Trace data flow** — when the error is deep in the call stack, find where the bad value originates, keep tracing upstream, fix at the source not the symptom.

**Phase 1 completion checklist:**
- [ ] Error messages fully read and understood
- [ ] A tight loop command exists and has been run at least once
- [ ] Loop is red-capable: asserts the user's exact symptom, not a nearby failure
- [ ] Loop is deterministic, or a flaky bug has a high enough reproduction rate to debug
- [ ] Recent changes identified and reviewed
- [ ] Evidence gathered (logs, state, data flow)
- [ ] Problem isolated to specific component/code
- [ ] Root cause hypotheses can be stated and tested

**STOP:** Do not proceed to Phase 2 until you understand WHY it's happening.

### Phase 2: Pattern Analysis

Find the pattern before fixing:

0. **Minimize the reproduction** — once the loop is red, shrink it to the smallest scenario that still goes red. Cut inputs/callers/config/data/steps one at a time, re-running after each cut. Done when removing anything remaining makes it green.
1. **Find working examples** — locate similar working code in the same codebase. What works that's similar to what's broken?
2. **Compare against references** — if implementing a pattern, read the reference implementation COMPLETELY, don't skim.
3. **Identify differences** — list every difference between working and broken, however small. Don't assume "that can't matter."
4. **Understand dependencies** — what other components, settings, config, environment, and assumptions does this need?

### Phase 3: Hypothesis and Testing

Scientific method:

1. **Form ranked falsifiable hypotheses** — generate 3-5 plausible hypotheses before testing any one. Rank by likelihood and cheapness to falsify. State the prediction each makes: "If X is the cause, then changing/observing Y should make Z happen." If the user is present, show the ranked list first — they may re-rank it with domain knowledge.
2. **Test minimally** — test the highest-ranked hypothesis with the smallest probe. Change one variable at a time. Prefer debugger/REPL inspection over logs. If you add logs, tag every temporary line with a unique prefix such as `[DEBUG-a4f2]` so cleanup is a single search.
3. **Verify before continuing** — worked → Phase 4. Didn't work → form a NEW hypothesis. Don't add more fixes on top.
4. **When you don't know** — say "I don't understand X", don't pretend to know, ask the user for help, research more.

### Phase 4: Implementation

Fix the root cause, not the symptom:

1. **Create a failing test case** — simplest possible reproduction, automated if possible, MUST exist before fixing (use `test-driven-development` skill).
2. **Implement a single fix** — address the identified root cause, ONE change at a time, no "while I'm here" improvements, no bundled refactoring.
3. **Verify the fix**:
   ```bash
   pytest tests/test_module.py::test_regression -v   # the specific regression test
   pytest tests/ -q                                   # full suite — no regressions
   ```
4. **If the fix doesn't work — the Rule of Three:** STOP. Count how many fixes you've tried. If < 3, return to Phase 1 and re-analyze with new information. **If ≥ 3, STOP and question the architecture** — don't attempt fix #4 without that discussion.
5. **If 3+ fixes failed, question the architecture.** Pattern indicating an architectural problem: each fix reveals new shared state/coupling in a different place, fixes require "massive refactoring," each fix creates new symptoms elsewhere. STOP and ask: is this pattern fundamentally sound, or are we sticking with it through sheer inertia? Discuss with the user before attempting more fixes — this is NOT a failed hypothesis, it's a wrong architecture.

## Red Flags — STOP and Follow Process

If you catch yourself thinking:
- "Quick fix for now, investigate later"
- "Just try changing X and see if it works"
- "Add multiple changes, run tests"
- "Skip the test, I'll manually verify"
- "It's probably X, let me fix that"
- "I don't fully understand but this might work"
- "Pattern says X but I'll adapt it differently"
- "Here are the main problems: [lists fixes without investigation]"
- Proposing solutions before tracing data flow
- **"One more fix attempt" (when already tried 2+)**
- **Each fix reveals a new problem in a different place**

**ALL of these mean: STOP. Return to Phase 1.** If 3+ fixes failed, question the architecture (Phase 4 step 5).

## Quick Reference

| Phase | Key Activities | Success Criteria |
|-------|---------------|------------------|
| **1. Root Cause** | Read errors, reproduce, check changes, gather evidence, trace data flow | Understand WHAT and WHY |
| **2. Pattern** | Find working examples, compare, identify differences | Know what's different |
| **3. Hypothesis** | Form theory, test minimally, one variable at a time | Confirmed or new hypothesis |
| **4. Implementation** | Create regression test, fix root cause, verify | Bug resolved, all tests pass |

See REFERENCE.md for: full loop-construction strategy list and Action code examples for each phase, the Common Rationalizations table, Hermes Agent Integration (`search_files`/`read_file`/`terminal`/`delegate_task` usage), and Real-World Impact stats.

**No shortcuts. No guessing. Systematic always wins.**
