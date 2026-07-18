---
name: ics-calendar
description: Create an .ics calendar file or event invite.
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    domain: productivity
    tags: [calendar, ics, icalendar, event, invite]
    related_skills: [apple-reminders, google-workspace]
---

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
