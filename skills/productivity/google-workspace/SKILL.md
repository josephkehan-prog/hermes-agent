---
name: google-workspace
description: "Gmail, Calendar, Drive, Docs, Sheets via gws CLI or Python."
version: 1.1.0
author: Nous Research
license: MIT
platforms: [linux, macos, windows]
required_credential_files:
  - path: google_token.json
    description: Google OAuth2 token (created by setup script)
  - path: google_client_secret.json
    description: Google OAuth2 client credentials (downloaded from Google Cloud Console)
metadata:
  hermes:
    tags: [Google, Gmail, Calendar, Drive, Sheets, Docs, Contacts, Email, OAuth]
    homepage: https://github.com/NousResearch/hermes-agent
    related_skills: [himalaya]
---

# Google Workspace

Gmail, Calendar, Drive, Contacts, Sheets, and Docs — through Hermes-managed OAuth and a thin CLI wrapper. When `gws` is installed, the skill uses it as the execution backend for broader Google Workspace coverage; otherwise it falls back to the bundled Python client implementation.

## References

- `references/gmail-search-syntax.md` — Gmail search operators (is:unread, from:, newer_than:, etc.)
- `references/setup.md` — full first-time OAuth setup walkthrough (triage questions, Steps 0-5, notes). Read it before running any setup step.
- `references/api.md` — full command reference (Gmail/Calendar/Drive/Contacts/Sheets/Docs examples) and the JSON output shape per command. Read it before constructing a `$GAPI` call or parsing its output.

## Scripts

- `scripts/setup.py` — OAuth2 setup (run once to authorize)
- `scripts/google_api.py` — compatibility wrapper CLI. It prefers `gws` for operations when available, while preserving Hermes' existing JSON output contract.

## First-Time Setup (quick path)

The setup is fully non-interactive — you drive it step by step so it works
on CLI, Telegram, Discord, or any platform. Full walkthrough with the exact
copy to send the user: `references/setup.md`.

```bash
GSETUP="python ${HERMES_HOME:-$HOME/.hermes}/skills/productivity/google-workspace/scripts/setup.py"
$GSETUP --check   # if AUTHENTICATED, skip setup entirely
```

Overview: (0) check if already authenticated, (1) ask the user which services
they need — email-only users should use `himalaya` instead, not this skill —
and whether their account has Advanced Protection, (2) create a Google Cloud
OAuth Desktop client and pass `--client-secret`, (3) `--auth-url --services ...`
and send the URL, (4) `--auth-code` with the pasted redirect/code, (5)
`--check` to confirm `AUTHENTICATED`. Token lives at
`~/.hermes/google_token.json` and auto-refreshes. Revoke with `$GSETUP --revoke`.

## Usage

All commands go through the API script. Full command examples and output
JSON shapes for every subcommand: `references/api.md`.

```bash
GAPI="python ${HERMES_HOME:-$HOME/.hermes}/skills/productivity/google-workspace/scripts/google_api.py"
$GAPI gmail search "is:unread" --max 10
$GAPI calendar list
$GAPI drive search "quarterly report" --max 10
$GAPI sheets get SHEET_ID "Sheet1!A1:D10"
$GAPI docs get DOC_ID
```

Covers Gmail (search/get/send/reply/labels), Calendar (list/create/delete),
Drive (search/get/upload/download/create-folder/share/delete), Contacts
(list), Sheets (create/get/update/append), and Docs (get/create/append). All
commands return JSON — parse with `jq` or read directly.

## Rules

1. **Never send email, create/delete calendar events, delete Drive files, share files, or modify Docs/Sheets without confirming with the user first.** Show what will be done (recipients, file IDs, content, share role) and ask for approval. For `drive delete`, prefer the default trash (reversible) over `--permanent`.
2. **Check auth before first use** — run `setup.py --check`. If it fails, guide the user through setup.
3. **Use the Gmail search syntax reference** for complex queries — load it with `skill_view("google-workspace", file_path="references/gmail-search-syntax.md")`.
4. **Calendar times must include timezone** — always use ISO 8601 with offset (e.g., `2026-03-01T10:00:00-06:00`) or UTC (`Z`).
5. **Respect rate limits** — avoid rapid-fire sequential API calls. Batch reads when possible.

## Troubleshooting

Auth errors (`NOT_AUTHENTICATED`, `REFRESH_FAILED`, missing-scope, API-not-enabled)
and the fix for each: `references/api.md` (Troubleshooting section). Revoke
access anytime with `$GSETUP --revoke`.
