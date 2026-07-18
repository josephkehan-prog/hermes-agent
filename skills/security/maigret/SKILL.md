---
name: maigret
description: OSINT username search across networks via Maigret.
version: 1.0.0
author: hermes-agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [osint, security, username, social-media, reconnaissance]
    category: security
prerequisites:
  commands: [maigret]
  python: ">=3.9"
---

# Maigret OSINT Username Search

Hunt down accounts across 500+ platforms using the [Maigret Project](https://github.com/superpikor/maigret). Superior to Sherlock — returns email-linked accounts, international sites, professional platform presence (TechNet, Xing, HackerNews), and engagement metrics via deep profile extraction.

## When to Use

- User requests username or social media account discovery across platforms
- User wants "where is this person online?" or similar footprint queries
- OSINT reconnaissance explicitly mentioned or requested
- Need deeper results than Sherlock returns (email links, professional presence, international sites)

## Requirements

- **Maigret CLI**: `pip3 install maigret` (Python 3.9+)
- Network access to query 500+ social platforms

### Pitfall: Python 3.9 + aiosignal Compat Bug
Maigret installs clean but fails on run due to `aiosignal>=1.4.0` using `TypeVarTuple(..., default=...)` which requires Python 3.11+. Fix before or after install:
```bash
pip3 install 'aiosignal<=1.3.2' --force-reinstall --no-deps
```

## Procedure

### Phase 1: Environment Initialization

**Step 1. Verify Maigret Availability**
```bash
/Users/josephhan/Library/Python/3.9/bin/maigret --version
```
If not on PATH (common on macOS pip installs), use the full path above or add it to PATH:
```bash
export PATH="$PATH:/Users/josephhan/Library/Python/3.9/bin"
```

**Step 2. Extract Target Username**
Parse directly from user message — exact formatting preserved. No clarify needed for straightforward requests.

### Phase 2: Core Scan (Maigret)

**Step 3. Build Command**
```bash
maigret --no-color "<username>" --timeout 90
```
Note: `--print-found` is not a valid flag in Maigret (unlike Sherlock). Just use `--no-color`.

**Step 4. Execute Terminal Search**
```json
{
  "command": "/Users/josephhan/Library/Python/3.9/bin/maigret --no-color \"<username>\" --timeout 90",
  "timeout": 300
}
```

Track execution time (~2 minutes for full scan) and the final summary line:
- `Search by username X returned Y accounts.`
- `Extended info extracted from Z accounts.`
- `Countries: ...` (geographic spread)
- `Interests (tags): ...` (tag taxonomy)

### Phase 3: Parse & Categorize Findings

Extract results and present in organized tables. Maigret output includes:
1. **Email verification** — confirms email linked to account (`email_username`, `gravatar_url`)
2. **VIP status** — premium/verified accounts (`is_vip`)
3. **Community status** — community members (`is_community`)
4. **Full names** — extracted from profiles where available
5. **Bio content** — profile descriptions, self-identified occupation

Categorize by: Professional (TechNet, Xing, HackerNews), Gaming/Community (Strava, Lichess, PCGamer), Developer (PyPi, hashnode, Kaggle), International/Regional (banki.ru, Virgool, Kaskus).

### Phase 4: Deep OSINT Extension

After core scan, pivot to Google Dorks + browser for engagement metrics and profile details. See `osint-reconnaissance` skill for the full deep search workflow including yearbook PDFs, academic publications, and onion crawl techniques.

## Pitfalls

### Third-Party Scrapers Are Derivative
When pulling social media presence via Google Dorks or sites like Instalker.org, treat as **secondary/derivative**. Not authoritative primary source — may return stale, merged, or fabricated profiles. Always cross-reference with the platform's actual URL if you can navigate to it. Flag unverified findings.

### Sherlock Returns 0 Results
When `sherlock` returns 0 accounts for a target, don't immediately pivot to deep OSINT layer. First try similar usernames with wildcards (`sherlock "user?name"`) or variants like camelCase/hyphens. Also try email-based search instead of username (many platforms use email as primary identifier).

### No Results Found
If Maigret finds few accounts, this is often correct — the target may have minimal footprint or privacy settings enabled. Pivot to Google Dorks for social media expansion and academic/publications layer for richer details.

## Ethical Use

Legitimate OSINT and research purposes only. Only search usernames user owns or has permission to investigate. Respect platform terms of service.