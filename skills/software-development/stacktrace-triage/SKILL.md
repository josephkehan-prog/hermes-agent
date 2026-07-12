---
name: stacktrace-triage
description: "Use when the user pastes an error stack trace or traceback and wants to know where the failure originates and what to look at."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    domain: software-development
    tags: [stacktrace, traceback, debugging, error]
    related_skills: [systematic-debugging, git-bisect]
---

# Stacktrace Triage

## Boundary

Localize where a stack trace or traceback fails and point at the frame to
investigate. Use to read a trace, not to fix the bug — hand the fix itself to
systematic-debugging once the origin is known.

## Read Bottom-Up (or Top, per language)

Know where the actual error is by language convention:

| Language | Error line is | Culprit frame |
|---|---|---|
| Python | LAST line (`ExceptionType: message`) | BOTTOM-most frame, then nearest frame in project code |
| JavaScript/Node | FIRST line (`Error: message`) | TOP frame below the message |
| Java/Kotlin | FIRST line (`Exception in thread ...`) | TOP `at ...` frame; scan for `Caused by:` |
| Go | `panic:` line | first `goroutine` frame after the panic |
| Rust | `thread 'main' panicked at` line | the `at` location; run with `RUST_BACKTRACE=1` if absent |

## Procedure

1. Extract the exception/error TYPE and MESSAGE — quote them exactly.
2. Find the innermost frame that lives in PROJECT code (not stdlib,
   node_modules, site-packages, or the runtime). That file:line is the primary
   suspect — most bugs are in your own frame nearest the error, not the library
   it called.
3. For chained errors (`Caused by:`, `During handling of the above
   exception`, `from exc`), report the ORIGINAL cause, then the wrapping one.
4. Map the error type to its usual meaning (e.g. `KeyError` → missing dict key;
   `NoneType has no attribute` → a value expected to exist was None;
   `ECONNREFUSED` → nothing listening at that host:port). State the concrete
   file:line to inspect.

## Output

Report, in order:
1. **Error**: exact type and message.
2. **Origin**: `file:line` in project code, with the one-line reason it's the
   suspect.
3. **Chain**: the root cause if the trace is wrapped, else "single error".
4. **Look at**: the specific variable, call, or condition at the origin line to
   check — never a guess about the fix.

## Rules

1. Quote the error type and message verbatim; do not paraphrase them.
2. Distinguish library frames from project frames; do not blame a library frame
   when a project frame sits closer to the error.
3. If the trace is truncated or the project frame is not shown, say so and name
   what additional context is needed (full trace, source of a named file).
4. Do not invent line numbers or file names not present in the trace.

## Stop Conditions

- No recognizable trace in the input: ask for the actual traceback.
- Trace is entirely library/runtime frames (no project code): report that the
  failure surfaces inside a dependency and name the entry call from project
  code that reached it.

## Completion Gate

Done when the error type/message, the project-code origin `file:line`, the
cause chain, and the specific thing to inspect are all reported, with no
invented locations.
