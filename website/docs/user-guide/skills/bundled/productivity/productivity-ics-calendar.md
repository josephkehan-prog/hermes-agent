---
title: "Ics Calendar — Use when the user wants to create an"
sidebar_label: "Ics Calendar"
description: "Use when the user wants to create an"
---

{/* This page is auto-generated from the skill's SKILL.md by website/scripts/generate-skill-docs.py. Edit the source SKILL.md, not this page. */}

# Ics Calendar

Use when the user wants to create an .ics calendar file or invite for an event they can import into any calendar app.

## Skill metadata

| | |
|---|---|
| Source | Bundled (installed by default) |
| Path | `skills/productivity/ics-calendar` |
| Version | `1.0.0` |
| Author | Hermes Agent |
| License | MIT |
| Platforms | linux, macos, windows |
| Tags | `calendar`, `ics`, `icalendar`, `event`, `invite` |
| Related skills | [`apple-reminders`](/docs/user-guide/skills/bundled/apple/apple-apple-reminders), [`google-workspace`](/docs/user-guide/skills/bundled/productivity/productivity-google-workspace) |

## Reference: full SKILL.md

:::info
The following is the complete skill definition that Hermes loads when this skill is triggered. This is what the agent sees as instructions when the skill is active.
:::

# ICS Calendar

## Boundary

Produce a valid iCalendar (`.ics`, RFC 5545) file for one or more events the
user describes. Use to generate a portable invite; do not use to send email,
book a room, or write into a live calendar account (hand those to the calendar
platform skill).

## Required Facts (ask if missing)

Do not invent any of these — ask when absent:

- **Summary** (event title).
- **Start** date-time and **end** date-time (or a duration).
- **Time zone** — if not given, ask; do not assume the machine's.

Optional: location, description, attendees (emails), a reminder lead time.

## Structure

Emit exactly this skeleton, one property per line, CRLF line endings:

```
BEGIN:VCALENDAR
VERSION:2.0
PRODID:-//Hermes Agent//ics-calendar//EN
CALSCALE:GREGORIAN
BEGIN:VEVENT
UID:<unique>@hermes
DTSTAMP:<UTC now, YYYYMMDDTHHMMSSZ>
DTSTART;TZID=<zone>:<YYYYMMDDTHHMMSS>
DTEND;TZID=<zone>:<YYYYMMDDTHHMMSS>
SUMMARY:<summary>
END:VEVENT
END:VCALENDAR
```

## Rules

1. **Timestamps**: local event times use `DTSTART;TZID=Area/City:YYYYMMDDTHHMMSS`
   (no trailing Z). `DTSTAMP` is always UTC with a trailing `Z`. An all-day
   event uses `DTSTART;VALUE=DATE:YYYYMMDD` and a `DTEND` of the next day.
2. **UID**: unique per event; reuse the same UID only when updating an existing
   event (and bump `SEQUENCE`).
3. **Escaping**: in text values, escape `\`, `;`, `,` with a backslash and
   newlines as `\n`. Fold any line longer than 75 octets with a CRLF + single
   space.
4. **Reminders**: add a `VALARM` with `TRIGGER:-PT<N>M` inside the VEVENT only
   when the user asked for one.
5. Do not fabricate attendees or a location; include only what the user gave.

## Stop Conditions

- Start/end/time zone missing and unobtainable: stop and ask; never guess a
  time or zone.
- End before start: report the inconsistency instead of emitting it.

## Completion Gate

Done when the `.ics` content parses as one `VCALENDAR` with the required
properties, `DTSTAMP` is UTC, local times carry a `TZID`, text values are
escaped, and no detail the user did not provide was invented.
