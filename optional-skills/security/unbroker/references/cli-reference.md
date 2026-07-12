# Full CLI Reference

Every `scripts/pdd.py` subcommand, with full flag lists and behavior notes.
Read this when the SKILL.md Quick Reference doesn't cover the exact flag you
need.

| Command | Purpose |
|---|---|
| `$PDD setup --auto` | **Autonomous setup**: detect capabilities, pick the most autonomous valid config (no questions) |
| `$PDD doctor` | Readiness check: config, broker count, and which upgrades are on/available |
| `$PDD cdp [--check] [--print] [--port N]` | Launch/detect the operator's Chrome over CDP for Phase-2 browser + webmail (dedicated debug profile; the reliable way to send webmail and clear session-bound gates) |
| `$PDD intake --full-name "..." [--alias ...] [--email ... --phone ...] [--city --state] [--prior-location "City,ST"] --consent` | Create a consenting subject; captures aliases + multiple emails/phones + prior locations; prints `subject_id` |
| `$PDD next <subject>` | **The autonomous loop driver**: ordered agent actions right now + human digest + `next_wake_at` |
| `$PDD brokers [--priority crucial]` | List the people-search broker database (curated + live) |
| `$PDD refresh-brokers` | Pull the latest BADBOOL people-search list **and the CA Data Broker Registry** (`next` requeues this automatically when the cache is stale) |
| `$PDD registry [--search NAME]` | State registry coverage (CA ~545 ingested; VT/OR/TX portals surfaced); the DROP/email lane, not scanned |
| `$PDD drop <subject> [--filed]` | **The one-shot legal lever**: one CA DROP request deletes from ALL registered brokers; `--filed` records it |
| `$PDD plan <subject> [--priority crucial]` | Per-broker tier + method + `search_vectors` + the exact fields to disclose |
| `$PDD plan <subject> --batch` | **Reduce view**: overlays ledger state, groups brokers by next action (unscanned/found/indirect/blocked/in_progress/done), collapses ownership clusters, **orders `found` cluster-parents-first + emits a tailored `parent_playbook`**, prints `next_actions` |
| `$PDD fanout <subject> [--priority crucial] [--size 5]` | Batch brokers into parallel `delegate_task` subagents (auto for large runs; batches of 5 - 8+ time out) |
| `$PDD record <subject> <broker> <state> [--found true] [--evidence JSON] [--disclosed F --channel C] [--reason "..."]` | Update the ledger (validated state machine); **auto-stamps `next_recheck_at`** |
| `$PDD show <subject> <broker>` | Read back a case's recorded state + evidence + disclosure log (so the parent re-verifies a subagent's `found` without re-deriving the listing URL) |
| `$PDD send-email <subject> <broker> --listing <url> [--kind ccpa_indirect ...]` | Render + record the request (recipient locked to the broker's own address). **browser** mode returns a `compose` payload to send via webmail (no password); **programmatic** mode SMTP-sends |
| `$PDD verify-link <subject> <broker> --text '<body>'` | **browser mode**: extract a broker's verification link from webmail text you read (anti-phishing scored) |
| `$PDD poll-verification <subject> [--broker <id>]` | **programmatic mode**: poll IMAP for verification links (anti-phishing scored); auto-advances `submitted → verification_pending` |
| `$PDD render-email <subject> <broker> --listing <url>` | Draft only (fallback when no email mode is configured) |
| `$PDD due <subject>` | Cases whose recheck window arrived (the cron re-scan queue) |
| `$PDD tasks <subject>` | ONE consolidated human-task digest (present at END of run) |
| `$PDD status <subject>` | Markdown status report |
| `$PDD report <subject> --sheets` | Rows for the Google Sheets tracker |
