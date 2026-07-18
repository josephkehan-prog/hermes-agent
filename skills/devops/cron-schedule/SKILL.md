---
name: cron-schedule
description: Write, read, fix, or explain cron expressions.
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    domain: devops
    tags: [cron, crontab, schedule, timing]
    related_skills: [changelog, self-healing]
---

# Cron Schedule

## Boundary

Produce or explain a single 5-field cron expression from a plain-language
schedule, or read an existing one back in words. Use for standard crontab
timing. Do not use to install the crontab entry, and do not invent seconds-level
precision — standard cron's finest granularity is one minute.

## The Five Fields

```
┌───────────── minute        (0-59)
│ ┌─────────── hour          (0-23)
│ │ ┌───────── day of month  (1-31)
│ │ │ ┌─────── month         (1-12)
│ │ │ │ ┌───── day of week   (0-6, 0=Sunday)
│ │ │ │ │
* * * * *
```

## Operators

| Operator | Meaning | Example |
|---|---|---|
| `*` | every value | `* * * * *` = every minute |
| `,` | list | `0 9,17 * * *` = 09:00 and 17:00 |
| `-` | range | `0 9-17 * * *` = hourly 09:00–17:00 |
| `/` | step | `*/15 * * * *` = every 15 min |

## Procedure

1. Restate the schedule in words (which minutes, hours, days).
2. Fill each field left to right; use `*` for any field the user did not
   constrain.
3. Verify the step divides its range cleanly — `*/7` on minutes fires at
   :00,:07…:56 then :00 (a 4-minute gap), which is usually NOT what "every 7
   minutes" means. Warn when the interval doesn't divide 60/24 evenly.
4. Read the finished expression back in plain words so the user can confirm.

## Common Recipes (verify, don't paste blindly)

| Intent | Expression |
|---|---|
| Every minute | `* * * * *` |
| Every 15 minutes | `*/15 * * * *` |
| Hourly, on the hour | `0 * * * *` |
| Daily at 02:30 | `30 2 * * *` |
| Weekdays at 09:00 | `0 9 * * 1-5` |
| Every Sunday midnight | `0 0 * * 0` |
| First of month, 00:00 | `0 0 1 * *` |

## Rules

1. Standard 5-field cron only. If the user needs seconds or `@reboot`/`@daily`
   macros, say which system supports them rather than forcing a 5-field form.
2. Note the day-of-week/day-of-month gotcha: when BOTH are set (not `*`), most
   crons run on EITHER match (OR), not both — call this out.
3. State the timezone the schedule assumes (usually the server's local time);
   do not assume UTC silently.
4. Never claim an expression is installed — this skill only writes/reads it.

## Stop Conditions

- Request needs sub-minute timing or a non-cron scheduler: say so and name the
  right tool (systemd timer, at, a loop).
- Ambiguous schedule ("a couple times a day"): ask for exact times rather than
  guessing.

## Completion Gate

Done when the 5-field expression is given, read back in words, uneven-step and
DOW/DOM-OR gotchas are flagged where relevant, and the assumed timezone is
stated.
