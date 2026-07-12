---
name: unbroker
description: Autonomously remove your info from data-broker sites.
version: 1.0.0
author: SHL0MS (github.com/SHL0MS)
license: MIT
platforms: [linux, macos, windows]
prerequisites:
  commands: [python3]
metadata:
  hermes:
    tags: [privacy, data-broker, opt-out, ccpa, gdpr, security, doxxing]
    category: security
    related_skills: [google-workspace, agentmail, himalaya, scrapling, osint-investigation]
    homepage: https://github.com/NousResearch/hermes-agent
---

# unbroker

Find where a person's personal information (name, addresses, phone, email, relatives) is exposed on
data brokers and people-search sites, then remove it — automatically where possible, with guided
human steps only where a site demands a CAPTCHA, government ID, phone call, or fax. Manages multiple
people independently. It does **not** defeat anti-bot systems, act on anyone without recorded
consent, or remove public records (voter/property/court) or accounts the person controls.

The Python CLI (`scripts/pdd.py`) owns the deterministic state — config, dossiers + consent, the
broker database, tier planning, the ledger, drafts, reports, email sending (SMTP), verification-link
polling (IMAP), and the autonomous action queue (`next`). You (the agent) do the scanning and
form-driving with native tools (`web_extract`, `browser_navigate`) and `cronjob` for recurring re-scans.

## Autonomy contract

This skill runs **hands-off**. After intake (+ recorded consent) there are exactly TWO legitimate
human touchpoints: the intake conversation, and ONE consolidated human-task digest at the end
(`$PDD tasks`). Between those: never ask the operator to choose configuration (`setup --auto` picks
the most autonomous valid config itself); never pause before individual submissions when
`autonomy=full` (the default — consent at intake is standing authorization for T0-T2 opt-outs;
`autonomy=assisted` restores per-submission confirmation, honor `confirm_first` in `next` output);
never interrupt the run for human-only work (record `human_task_queued --reason "..."` and keep
going — it surfaces once in the final digest); drive the whole run as a loop over `$PDD next
<subject>`, executing every returned action, recording outcomes, re-running `next` until
`done_for_now`, then present the digest/report and schedule the cron.

Hard limits autonomy never overrides: no acting without recorded consent, no disclosure beyond
`disclosure_fields`, no CAPTCHA/anti-bot bypass, `confirmed_removed` only after a verifying re-scan.

## When to Use

"Remove my (or my family member's) data from data brokers/people-search sites." "Opt me out",
"delete me from Spokeo/Whitepages/etc.", "clean up after a doxxing." "Set up recurring privacy
monitoring" (brokers re-list people). Checking which brokers still expose someone and why.

## Prerequisites

`python3` (stdlib only). **Optional upgrades** (zero-config without these; `setup --auto` turns on
every one it detects, reading creds from the shell env and `$HERMES_HOME/.env`): a cloud browser
(`BROWSERBASE_API_KEY`) to clear soft CAPTCHAs; email via browser mode (`setup --email-mode browser`,
no password, `$PDD cdp` drives the operator's Chrome) or SMTP/IMAP (`EMAIL_ADDRESS`+`EMAIL_PASSWORD`);
a Sheets tracker (`google-workspace` skill); stealth pages (`scrapling` skill). Full detail: read
`references/setup.md`.

## How to Run

Run everything through the `terminal` tool (not `execute_code` — that sandbox scrubs env and redacts
output, breaking dossier reads). From this skill's directory: `PDD="python3 scripts/pdd.py"`. Data
lives under `$PDD_DATA_DIR` (default `$HERMES_HOME/unbroker`), written `0600`.

## Quick Reference

| Command | Purpose |
|---|---|
| `$PDD setup --auto` | Autonomous setup: detect capabilities, pick the most autonomous valid config |
| `$PDD doctor` | Readiness check: config, broker count, upgrades on/available |
| `$PDD intake --full-name "..." ... --consent` | Create a consenting subject; prints `subject_id` |
| `$PDD next <subject>` | **The loop driver**: ordered agent actions right now + human digest + `next_wake_at` |
| `$PDD plan <subject> --batch` | Reduce view: groups by next action, collapses ownership clusters, parents-first `parent_playbook` |
| `$PDD fanout <subject> [--size 5]` | Batch brokers into parallel `delegate_task` subagents |
| `$PDD record <subject> <broker> <state> [--found true] [--evidence JSON]` | Update the ledger (validated state machine) |
| `$PDD send-email <subject> <broker> --listing <url> [--kind ...]` | Render + record a request (recipient locked to the broker's own address) |
| `$PDD poll-verification <subject>` / `$PDD verify-link ... --text '<body>'` | Programmatic (IMAP) / browser-mode verification-link handling |
| `$PDD drop <subject> [--filed]` | One-shot: a CA DROP request deletes from ALL registered brokers at once |
| `$PDD tasks <subject>` | ONE consolidated human-task digest (present at END of run) |
| `$PDD status <subject>` | Markdown status report |

Full command list (every flag, `cdp`, `brokers`, `refresh-brokers`,
`registry`, `show`, `render-email`, `due`, `report --sheets`, etc.): read
`references/cli-reference.md`.

## Batch operation (two-phase: crawl-all, then delete)

For anything past a couple of brokers, run this as **map → reduce → act**, not broker-by-broker:

- **Phase 1 - DISCOVER (read-only, parallel, idempotent).** Crawl *every* broker first, record a
  verdict each (`found`/`not_found`/`indirect_exposure`/`blocked`). Default: parent drives
  `web_extract` directly (fast); escalate to `browser_*` only for JS-only sites, and to
  `delegate_task` subagents only for reasoning-heavy namesake/relative disambiguation — never hand a
  subagent a big broker list to crawl (times out; 10x the cost of parent `web_extract`). Parent
  re-verifies subagent `found` claims before trusting them.
- **REDUCE - `$PDD plan <subject> --batch`.** Groups by next action, collapses ownership clusters
  (one parent removal clears N children), prints `next_actions`.
- **Phase 2 - DELETE (sequential, irreversible).** Work reduced groups **parents first** per the
  `parent_playbook` `plan --batch` emits; re-scan a parent's children after it confirms (they usually
  drop out); send `indirect_exposure` as CCPA/GDPR emails; defer `blocked` to the stealth-browser
  pass. One at a time, carefully — the opposite of fan-out. Don't pause per submission in
  `autonomy=full`; confirm each in `assisted`.
- **Blind opt-out is the DEFAULT, not a fallback** — submit on every site with an accessible removal
  channel even without a confirmed listing (discloses only the subject's own identifiers to the
  broker's own channel; doesn't violate least-disclosure). Full posture, the blocked-form → cited-email
  fallback rule, and CAPTCHA policy: read `references/methods.md`.
- **PeopleConnect delete-wipes-suppression (permanent rule).** A PeopleConnect *deletion* wipes the
  suppression and the subject re-lists across the whole affiliate cluster — if a completion email ever
  appears, re-run suppression and re-verify (see `references/brokers/intelius.json`).

Full ownership-cluster doctrine, per-broker recipes, and the meta-search skip-list: read
`references/methods.md` and `references/site-playbooks.md`.

## Procedure (the autonomous loop)

1. **Setup (once, no questions).** Run `$PDD setup --auto` — it configures the most autonomous valid
   combination itself. Then `$PDD doctor` and show the operator the readiness output **for
   information, not as a question** — proceed immediately; mention what would unlock more automation
   but don't wait for it.
2. **Intake + consent (the ONE human conversation).** `$PDD intake ...` with `--consent` (and
   `--consent-method`) — without consent the engine refuses to plan or act. Collect everything in one
   pass (names/aliases, current + prior cities, emails, phones) so you never come back with questions.
   For California subjects, `next` surfaces a `drop_submit` one-shot (`references/legal/drop.md`) that
   deletes from every registered broker (~545) at once — the single highest-leverage action; file it,
   then `drop <subject> --filed`. Non-CA subjects: cover the registry with targeted CCPA/GDPR emails
   (`registry --search`, then `send-email`); people-search sites are worked directly either way.
3. **Drain the queue.** Loop:

   ```
   while true:
     q = $PDD next <subject>
     if q.actions is empty: break
     execute EVERY action in order; record each outcome via $PDD record
   ```

   `next` emits, in order: `refresh_brokers`, `fanout_scan`/`scan_inline` (Phase 1), `poll_verification`,
   `verify_removal`, `optout_web_form`/`optout_email_send` (Phase 2, parents-first), `indirect_email_send`,
   `stealth_rescan`. Human-only work never appears as an action — it accumulates in `q.human_digest`.
   Execute without pausing in `autonomy=full`; honor `confirm_first` in `assisted`.
4. **Scanning (when `next` says so).** `fanout_scan`: run `$PDD fanout <subject>` and spawn one
   `delegate_task` subagent per `batch` in parallel with its ready-made `brief` — never scan
   sequentially yourself. `scan_inline`: scan the few brokers yourself. Record with `$PDD record
   <subject> <broker> <found|not_found|indirect_exposure|blocked> --found <bool> --evidence
   '{"listing_urls":[...]}'`. A 404 is INCONCLUSIVE, not `not_found`; parent re-verifies subagent
   `found` claims. Full scan ladder and false-positive traps: read `references/methods.md`.
5. **Opt-outs (when `next` says so).** Pre-ordered parents-first with `steps` from each broker's
   field-verified `optout.playbook`. Deletion usually beats suppression except PeopleConnect
   (`prefer_suppression`). Per-method execution details: read `references/methods.md`.
6. **Verification (when `next` says so).** Programmatic: `$PDD poll-verification <subject>` polls
   IMAP. Browser mode: `$PDD verify-link <subject> <broker> --text '<body>'` scores a link read from
   webmail. Either way, open the link **in the same browser** used to submit (session binding),
   finish the flow, record `awaiting_processing`. `confirmed_removed` ONLY after a verifying re-scan.
7. **Wrap up (once per run).** When `next` returns no actions: present `$PDD tasks <subject>` (human
   digest) if non-empty, then `$PDD status <subject>`; append `$PDD report <subject> --sheets` if on.
8. **Schedule the next wake-up.** `next` returns `next_wake_at`. Create ONE `cronjob` that re-runs the
   loop for the subject (*"run the unbroker loop for <subject_id>: `$PDD next` and execute all
   actions"*) — everything flows through the same queue, so the case advances with zero human attention.

## Pitfalls

Never disclose more than `disclosure_fields` (never SSN/ID). No consent, no action. `send-email` is
idempotent + rate-limited — don't loop it "to make sure"; the due-queue re-scan is the real
confirmation. Ledger writes are locked — a lock timeout means another run is mid-write, let it finish.
Autonomy skips *asking*, not any gate — a broker demanding more than planned mid-flow gets queued
(`human_task_queued`), not extra disclosure. Don't interrupt the run with questions (config is
`setup --auto`'s job). Use `terminal`, not `execute_code`, for `pdd.py`. Dossiers are plaintext by
default (`0600`) — `setup --encryption age` for at-rest encryption. "Hidden from free search" ≠
deleted — verify before `confirmed_removed`. Soft CAPTCHAs clear by default; don't fight hard ones —
record `blocked`, never a solver service. Broker pages change — flag `references/brokers/` for
re-verification rather than guessing. Verify non-field-verified (`confidence: auto`/`documented`)
records live before trusting them; field-verified cluster parents take precedence.

Full rationale for each pitfall: read `references/pitfalls.md`.

## Verification

`scripts/run_tests.sh tests/skills/test_unbroker_skill.py` (hermetic; no network), or the
dependency-free runner `python3 tests/skills/test_unbroker_skill.py`. Dry run: `$PDD setup --auto &&
$PDD doctor && SID=$($PDD intake --full-name "Test Person" --email t@example.com --consent |
python3 -c 'import sys,json;print(json.load(sys.stdin)["subject_id"])') && $PDD next "$SID"` and
confirm a readiness summary plus an ordered action queue.
