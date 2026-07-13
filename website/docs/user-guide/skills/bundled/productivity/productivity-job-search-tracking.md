---
title: "Job Search Tracking"
sidebar_label: "Job Search Tracking"
description: "Track job applications and monitor new listings locally — CSV-backed tracker plus RSS watchers for remote/education job boards"
---

{/* This page is auto-generated from the skill's SKILL.md by website/scripts/generate-skill-docs.py. Edit the source SKILL.md, not this page. */}

# Job Search Tracking

Track job applications and monitor new listings locally — CSV-backed tracker plus RSS watchers for remote/education job boards. No cloud account required.

## Skill metadata

| | |
|---|---|
| Source | Bundled (installed by default) |
| Path | `skills/productivity/job-search-tracking` |
| Version | `1.0.0` |
| Author | Hermes Agent |
| License | MIT |
| Platforms | linux, macos, windows |
| Tags | `job-search`, `career`, `tracker`, `applications`, `teaching`, `rss`, `cron` |
| Related skills | [`resume-tailor`](/docs/user-guide/skills/bundled/productivity/productivity-resume-tailor), [`cover-letter`](/docs/user-guide/skills/bundled/productivity/productivity-cover-letter), [`interview-prep`](/docs/user-guide/skills/bundled/productivity/productivity-interview-prep) |

## Reference: full SKILL.md

:::info
The following is the complete skill definition that Hermes loads when this skill is triggered. This is what the agent sees as instructions when the skill is active.
:::

# Job Search Tracking

A local, file-based application tracker plus listing watchers — no job-board
account, no paid API. State lives in a single CSV file.

## When to Use

- User asks to log/track a job application, or "add this job to my tracker."
- User asks what applications are pending, need follow-up, or have upcoming deadlines.
- User wants to be notified when new listings matching their search appear.

## Data file

`$HERMES_HOME/job-search/applications.csv` (default `~/.hermes/job-search/`).
Columns: `id, date_applied, company, role, url, status, remote, cert_required, next_action, next_action_date, notes`.
Statuses: `saved, applied, screen, interview, offer, rejected, withdrawn`.

## Quick start

```bash
TRACK="${HERMES_SKILL_DIR}/scripts/job_tracker.py"
python3 "$TRACK" init

# Log a new application
python3 "$TRACK" add --company "NYC DOE Virtual" --role "Remote HS Math Teacher" \
  --url "https://..." --status applied --cert-required \
  --next-action "follow up" --next-action-date 2026-07-17 \
  --notes "Applied via Indeed, requires NYS cert"

# List everything, or filter
python3 "$TRACK" list
python3 "$TRACK" list --status interview
python3 "$TRACK" list --upcoming 7          # next_action_date within 7 days

# Move a card forward
python3 "$TRACK" update 1 --status interview --next-action "phone screen" --next-action-date 2026-07-22

# Pipeline counts
python3 "$TRACK" stats
```

## Monitoring new listings (optional)

Reuse the `watchers` skill's `watch_rss.py` to poll job-board RSS feeds instead
of manually re-searching. Indeed exposes RSS search feeds without an API key:

```bash
python $HERMES_HOME/skills/devops/watchers/scripts/watch_rss.py \
  --name teaching-remote-ny \
  --url "https://www.indeed.com/rss?q=remote+teacher+certified&l=New+York+State" \
  --max 10
```

Wire it into cron (see the `watchers` skill): every few hours, run the watcher;
if it prints new items, review them and `job_tracker.py add` the ones worth
applying to. Many ATS platforms (Greenhouse, Lever, SchoolSpring/Frontline)
also expose feeds per employer — search `site:boards.greenhouse.io "remote teacher"`.

## Weekly review

Suggest a cron/heartbeat check: `python3 "$TRACK" list --upcoming 7` to surface
follow-ups due this week, and `stats` to see pipeline health at a glance.

## Pitfalls

- CSV holds no secrets — safe to keep in the workspace, but don't store SSNs
  or full addresses in `notes`.
- `id` is a simple row count, not stable across manual edits to the CSV — use
  `list` to look up the current `id` before `update`, don't hardcode old ones.
- `--cert-required` only records that a role requires NYS certification; it
  does not verify certification status. Track TEACH renewal deadlines separately.
