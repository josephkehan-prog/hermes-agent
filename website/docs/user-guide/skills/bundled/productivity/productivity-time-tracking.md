---
title: "Time Tracking — Use when the user asks to start, stop, or report time spent on a task, project, or work session"
sidebar_label: "Time Tracking"
description: "Use when the user asks to start, stop, or report time spent on a task, project, or work session"
---

{/* This page is auto-generated from the skill's SKILL.md by website/scripts/generate-skill-docs.py. Edit the source SKILL.md, not this page. */}

# Time Tracking

Use when the user asks to start, stop, or report time spent on a task, project, or work session. Tracks intervals in a local JSONL ledger with tags.

## Skill metadata

| | |
|---|---|
| Source | Bundled (installed by default) |
| Path | `skills/productivity/time-tracking` |
| Version | `1.0.0` |
| Author | Hermes Agent |
| License | MIT |
| Platforms | linux, macos, windows |
| Tags | `time`, `tracking`, `productivity`, `ledger` |
| Related skills | `todo` |

## Reference: full SKILL.md

:::info
The following is the complete skill definition that Hermes loads when this skill is triggered. This is what the agent sees as instructions when the skill is active.
:::

# Time Tracking

## Boundary

Track work intervals only when the user explicitly asks (start/stop/status/report).
Do not start timers on your own initiative. Do not use for calendar events or
reminders.

## Ledger

Single file: `~/.hermes/time-tracking/ledger.jsonl` (create the directory on
first use). One JSON object per line:

```json
{"task": "<short-task-name>", "tags": ["tag1"], "start": "<ISO-8601>", "end": "<ISO-8601 or null>"}
```

An entry with `"end": null` is the running timer. At most ONE entry may have
`"end": null` at any time.

## Commands

| User intent | Action |
|---|---|
| "start tracking X" / "clock in on X" | If a timer is running: report it and ask stop-or-keep. Else append entry with `end: null`. Confirm task name and start time. |
| "stop" / "clock out" | Find the `end: null` entry, set `end` to now, report elapsed duration. No running timer: say so, do nothing. |
| "status" / "what am I tracking" | Report running entry (task, tags, elapsed) or "no timer running". |
| "report today/this week/for TAG" | Read ledger, sum durations of entries whose `start` falls in the window (or whose tags match), print table: task, total duration, entry count. |
| "discard the running timer" | Remove the `end: null` line. Confirm before removing. |

## Rules

1. Always read the ledger before writing; never keep timer state only in memory.
2. Rewrite the file atomically when closing or discarding a timer (write temp
   file, then replace).
3. Durations: report as `Hh MMm` (e.g. `2h 05m`). Under one minute: `<1m`.
4. Timestamps: local time, ISO-8601 with offset.
5. Never invent entries. Report gaps or malformed lines instead of repairing
   silently; skip malformed lines in reports and say how many were skipped.

## Stop Conditions

- Ledger unreadable or malformed beyond individual lines: stop, show the error.
- User asks for a report window the ledger cannot answer: say what range the
  ledger covers instead of guessing.

## Completion Gate

Done when the requested command's effect is visible in the ledger (start/stop/
discard) or the report table is printed. Confirm with one line, no extra
narration.
