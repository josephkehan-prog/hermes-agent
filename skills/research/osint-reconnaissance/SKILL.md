---
name: osint-reconnaissance  
description: Digital footprint OSINT via Sherlock and Google Dorks.
version: 1.0.0  
author: hermes-agent  
license: MIT  
platforms: [linux, macos, windows]  
metadata:
  hermes:
    tags: [osint, reconnaissance, digital-footprint, username-analysis, social-media-intelligence, browser-dorking]
    category: research
prerequisites:
  commands: [sherlock]
  tools: [terminal, browser tool set (optional for extended analysis)]
---

# OSINT Reconnaissance and Digital Footprint Analysis

Combines automated username detection via Sherlock with manual verification through Google Dorks and browser-based profile analysis.

Full verbatim examples, report templates, dork query lists, and phase walkthroughs: `REFERENCE.md` next to this file.

## Evidence Discipline (anti-hallucination — READ FIRST)

Local models fabricate OSINT specifics under pressure — names, employers,
addresses, emails, handles that were never fetched. In OSINT a made-up detail is
worse than a gap. Rules, in order:

1. **Every concrete claim binds to a fetched artifact.** A name, URL, email,
   handle, phone, or address goes in the report ONLY if it appears in a payload
   you actually retrieved (footprint JSON, a page you opened, a dork hit). If you
   did not fetch it, you do not know it.
2. **Never upgrade "possible" to "confirmed".** `footprint.py` soft-404 sites are
   `[man]` (manual-verify), not present. Third-party scrapers are derivative —
   confirm against the platform's live URL or tag `UNVERIFIED`.
3. **Gaps stay gaps.** Write "not found" / "could not verify" — never invent a
   plausible filler. No numbers, dates, or relationships without a source.
4. **Run the gate before emitting.** Save fetched payloads to an evidence dir,
   then:
   ```bash
   python3 skills/research/osint-reconnaissance/scripts/evidence_check.py \
       --report draft.md --evidence ./evidence/
   ```
   Exit 2 + an UNSUPPORTED list means those tokens are not in any payload —
   delete them or fetch a real source. Exit 0 = every specific is grounded.
   (The gate catches invented specifics; it does not prove a grounded claim true.)
5. **Cite inline.** Each finding carries its source link/path so a human can
   re-check. Uncited specific = treat as hallucinated.

## When to Use
- Username or social media account discovery across platforms
- "Where is this person online?" footprint queries
- OSINT reconnaissance explicitly requested
- Digital presence mapping (professional, creative, academic identities)
- Enhanced intelligence gathering beyond simple username verification (triggers extension workflow)

## Requirements
- **Zero-install fallback (always available)**: `scripts/footprint.py` — stdlib-only, keyless username presence check across 18 platforms. Use FIRST when sherlock/maigret are not installed:
  ```bash
  python3 skills/research/osint-reconnaissance/scripts/footprint.py <username> [--json]
  ```
  Reports `[ + ]` confirmed (reliable 404 sites), `[man]` soft-404 (open URL to verify), `[ ? ]` bot-blocked. No paid keys, no pip. Escalate to sherlock for 500+ site coverage.
- **Sherlock CLI**: core username verification tool (install: `pipx install sherlock-project`, `pip install sherlock-project`, or `docker run -it --rm sherlock/sherlock <username>`)
- **Maigret CLI**: `pip3 install maigret` (Python 3.9+ — see aiosignal compat pitfall below)
- Network access to query 500+ social platforms
- Extended analysis (optional): browser tools with CDP connection for dorking + vision-enabled profile extraction

## Procedure

### Phase 1: Environment Initialization
1. Verify Sherlock: `sherlock --version`; install if missing (see Requirements)
2. Extract target username verbatim from user message (preserve case/underscores/hyphens); only clarify if ambiguous
3. Determine scope: does the request warrant the extended browser-dorking workflow (deep analysis requested, CDP session available, engagement/professional intelligence needed)?

Full step text: REFERENCE.md "Phase 1: Environment Initialization".

### Phase 2: Core Username Scan (Sherlock)
- Command: `sherlock --print-found --no-color "<username>" --timeout 90`
- Optional flags: `--nsfw` (include NSFW platforms), `--tor` (Tor routing), `--site <platform>` (target subset)
- Run via terminal with 180s timeout
- Parse `[+]` markers for confirmed accounts; note account count, platform-categorized URLs, and default output file `<username>.txt`

Full command/JSON example: REFERENCE.md "Phase 2: Core Username Scan (Sherlock)".

### Phase 2.5: Academic/Publications Layer
Check university/departmental publications before browser dorking — often richer than social profiles (hobbies, majors, military service, family info).
- University newsletters/announcements: `site:<university>.edu` searches
- PDF-based academic publications (thesis titles, mentors, event recaps)
- Athletics rosters (`site:ncaa.com` etc. — height, position, high school, years active)
- Departmental PDFs (personal anecdotes, thesis presentations)
- Yearbook PDFs (major/emphasis, quotes, age signals, cohort markers, associated names) — often exceed 100K chars, extract via `web_extract` then paginate
- **Signal to pivot early**: if social media is empty and athletics is the only public profile, query `site:<university>` immediately
- Pitfall: PDFs may load slowly or as embedded iframes — use `browser_snapshot(full=true)` or wait for full load

Full walkthrough, example queries, and "key sites" table: REFERENCE.md "Phase 2.5: Academic/Publications Layer".

### Extended Browser Dorking Workflow (Steps 7-9)
Trigger: "dork him" / deep reconnaissance requested, browser tools available via CDP, need for engagement/professional intelligence.

> **Browser access**: dorking uses the `browser` toolset, not `computer_use`. If the browser tool errors with "no CDP endpoint", run `bin/hermes-browser` then `/browser connect ws://127.0.0.1:9222` (see the `browser-first` skill). Never screen-control the web.

- **Step 7 — Google Dorks Queries**: social media expansion (`site:twitter.com`/`site:x.com`), developer platform detection (`inurl:github.com`/`inurl:gitlab.com`), professional presence (`site:linkedin.com/in/`), image-based identity verification (`intext:"username"` via Images tab). Full query strings: REFERENCE.md "Step 7. Execute Google Dorks Queries".
- **Step 8 — Visual Profile Analysis**: `browser_navigate` to each discovery, `browser_vision` (annotated) for follower/following metrics, bio content, cross-platform links, activity patterns; compile handle variations, tenure markers, geographic/industry signals.
- **Step 9 — Cross-Reference Intelligence Layer**: build Username Pattern Matrix (handle variations, separators, suffixes), Platform Correlation Map, Engagement Level Assessment (High/Medium/Low).

### Phase 3: Deep Search / Profile Class (progressive depth)
Triggered by "deep search," "profile," or "onion crawl." One focused section per layer in output — no editorializing/assessment padding.
- **Level 1 — Professional**: LinkedIn extraction, employment history, education, political-leaning signals
- **Level 2 — Personal Life**: family connections, hobbies, interests, obituary records, university publications
- **Level 3 — Relationships/Dating**: wedding/engagement sites (The Knot, Zola), Instagram/Facebook relationship signals
- **Level 4 — Onion/Clearnet Deep**: Tor search engines, `.onion` page fetches, pastebin mirrors; pivot to clearnet when onion infra pages repeat (see `references/osint-failures.md`)
- **Institutional records layer**: business registrations (NY DOS/LLC), property/real estate (NYC ACRIS), court records (NYSCEF eCourts), professional licenses, family obituaries

Full level descriptions: REFERENCE.md "Phase 3: Deep Search / Profile Class".

### Phone Number Identity Discovery
When target is a phone number, Sherlock returns gaming/community sites (Chess.com, BoardGameGeek, Gravatar) instead of mainstream social — this is expected, not a failure.
- **Prefix Reputation Analysis** (before owner lookup): check `phoneregistry.org/us/number/<number>/`, note NXX prefix, check "Similar Reported Numbers" section, sum sibling complaint totals — a clean individual line can still ride a high-risk prefix (~25K+ complaints across siblings)
- **Multi-Source Enrichment — Primary Path**: ThatsThem (`thatsthem.com/phone/<number>`) for owner names + address (free, no account) → `web_search` on `"Full Name" "<City> <State>"` (different backend than browser dorking, bypasses CAPTCHA) → cross-reference profiles
- **Deep Path** (only if primary yields nothing): property records (FloridaParcels.com, RealtyTrac), Clerk of Courts/Odyssey, Healthcare NPI (`npiregistry.hhs.gov`), Spokeo/Intelius paid lookups
- Caveat: Miami-Dade Property Appraiser site is JS-heavy/breaks in browser — use FloridaParcels.com (accepts folio number queries) instead

Full example walkthroughs (prefix reputation case, Fez Ghani multi-source case): REFERENCE.md "Phone Number Identity Discovery".

### Phase 4: Comprehensive Reporting
Report sections (all required when applicable):
- **Executive Summary** — platform coverage, confidence level, intelligence depth
- **Primary Findings (Sherlock Layer)** — confirmed registrations by category
- **Extended Intelligence Section** — Social Media Intelligence, Professional Network Mapping, Cross-Platform Username Patterns Table
- **Geographic Distribution Analysis** — regions, industry clustering, institutional affiliations
- **Actionable Recommendations** — profile verification priorities, related username searches, temporal tracking guidance, cross-reference opportunities

Full report template text and example table: REFERENCE.md "Phase 4: Comprehensive Reporting — Full Report Template".

## OpenOSINT Python API Pitfalls
Using `from openosint.tools.* import run_*_osint`:
- **Signature mismatch**: `run_dork_osint()` doesn't accept `timeout_seconds=` (TypeError); only `run_github_osint()` does — call each tool per its own documented signature, don't use a uniform wrapper
- **Dependency chain failure**: `run_email_osint()` requires `holehe` package — if install fails, email sweep is dead (not a tool-brokenness issue)
- **Network timeout**: `run_paste_osint()` hits psbdmp.ws which may be unreachable — environment-dependent, not tool brokenness
- Key takeaway: each tool has its own signature; use `terminal()` for direct script execution when `execute_code` consent gate blocks async ops

Full pitfall text: REFERENCE.md "OpenOSINT Execution Pitfalls".

## Pitfalls
- **Don't write multiple partial extract scripts** — write ONE complete consolidated report file in a single pass instead of several extract scripts (`compile_deep.py`, `deep_sweep.py`, `extract_profiles.py`) that each produce partial output; extract scripts only for >50 pages
- **Don't over-verbosify after onion crawl** — one focused section per depth layer, no editorializing/assessment paragraphs
- **Instalker / third-party scrapers are derivative, not authoritative** — cross-reference against the platform's real URL; flag unverified if you can't reach the live profile
- **Python 3.9 + aiosignal compat bug** — Maigret installs but fails to run due to `aiosignal` vs. Python 3.9 TypeVarTuple incompatibility. Fix: `pip3 install 'aiosignal<=1.3.2' --force-reinstall --no-deps`
- **Sherlock returns 0 results ≠ "no target"** — likely a username-format mismatch; try wildcard variants (`sherlock "user?name"`) or email-based search before pivoting to deep OSINT
- **Phone number as username → expect fewer social matches** — gaming/community sites are correct behavior, not failure
- **Limited/incomplete detection** (privacy settings, dormant accounts, nonstandard usernames) — mitigate with browser dorking
- **Engagement level inference** — follower ratios/bio/posting timestamps add context Sherlock can't provide; default to at least one dork query when browser is available
- **Username variation discovery** — check separator transforms and suffixes; use `"user?name"` wildcards
- **Cross-platform identity correlation** — combine LinkedIn/GitHub signals with social presence for full footprint, not just existence

Full pitfall write-ups and examples (EXAMPLE_NAME, Fez Ghani cases): REFERENCE.md "Pitfalls — Full Text".

## Keyless by Default
- All core sources are free/no-key: Sherlock, Maigret, Google Dorks (browser), ThatsThem, public records (NY DOS, ACRIS, NYSCEF, NPI registry).
- **Paid lookups (Spokeo, Intelius, RealtyTrac premium) are opt-in only** — never spend on them without an explicit user request. Exhaust the free path first.
- No cloud OSINT API keys required; runs on Hermes's local tools + the open web.

## Ethical Use Considerations
- Focus on usernames the user owns, manages, or has explicit permission to investigate
- Align with platform terms of service for automated account checks
- Apply for constructive professional mapping, not surveillance or monitoring without consent
- Maintain data privacy awareness when sharing reconnaissance findings across channels

## Session Reference Patterns
The `sherlock` skill provides core username verification. This skill adds: structured browser-dorking extension workflow, enhanced reporting templates with professional-network intelligence, and cross-platform pattern analysis with actionable recommendations. Invoke Sherlock via terminal first for baseline detection, then extend with browser reconnaissance when depth/engagement metrics are warranted.

Typical flow and worked example (`EXAMPLE_NAME` case): REFERENCE.md "Session Reference Patterns".
