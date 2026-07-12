# Pitfalls: Full Detail

Rationale and mechanics behind each pitfall listed in SKILL.md. Read this
when you hit one of these situations and need the full "why", not just the
one-line rule.

- **Never disclose more than the broker already shows.** Submit only `disclosure_fields`. The engine
  never volunteers SSN/ID numbers; you must not either.
- **No consent, no action.** The engine enforces this; do not work around it to "research" a third party.
- **`send-email` is idempotent + rate-limited.** It refuses to re-send a case already `submitted`
  or beyond (use `--force` only if a genuine re-send is needed), and SMTP sends are paced by
  `email_min_interval_seconds` (default 20s) with retry/backoff. Do not loop it to "make sure" -
  a successful SMTP handoff is not proof of delivery; the due-queue re-scan is the real confirmation.
- **Ledger writes are locked.** Concurrent runs (cron + manual) serialize safely; if you ever see a
  lock timeout, another run is mid-write - let it finish, don't delete the `.lock` by hand.
- **Autonomy ≠ improvisation.** Full autonomy means not *asking* between steps; it does not loosen any
  gate. If a broker demands MORE than the planned `disclosure_fields` mid-flow, stop that case and
  queue it (`human_task_queued --reason`) rather than deciding alone to disclose extra PII.
- **Don't interrupt the run with questions.** Config choices are `setup --auto`'s job; human-only work
  goes to the digest. The only mid-run question that's ever warranted is a missing-identity fact that
  blocks scanning (e.g. no city at all) - and that should have been collected at intake.
- **Use `terminal`, not `execute_code`** for `pdd.py` (secret scrubbing + output redaction break it).
- **Dossiers are plaintext by default** (JSON, `0600` under `HERMES_HOME`). For at-rest encryption run
  `$PDD setup --encryption age` - it generates a local `age` key and encrypts dossiers + ledgers (the
  audit log holds field names only and stays plaintext). It guards casual/backup/commit exposure, not
  a full-`HERMES_HOME` read; set `PDD_AGE_IDENTITY` to a separate volume for real key separation.
  `$PDD doctor` shows whether encryption is *actually* engaged (not just whether `age` is installed).
- **"Hidden from free search" ≠ deleted.** Only mark `confirmed_removed` after verifying the record is
  actually gone; note paid-tier retention in the report.
- **Soft CAPTCHAs clear by default; don't fight the hard ones.** The default cloud browser passes
  managed/soft challenges as normal operation (those brokers stay T1). For a hard interactive one it
  genuinely can't pass, record `blocked` and let the stealth/operator-browser pass take it - never a
  third-party solver service or fingerprint spoofing.
- **Broker pages change.** If a flow breaks, `$PDD record ... blocked` and flag the broker file in
  `references/brokers/` for re-verification instead of guessing.
- **Verify non-field-verified records before submitting.** `confidence: auto` records came from
  parsing BADBOOL (read `optout.notes`/`optout.links`, confirm the real opt-out URL). `confidence:
  documented` records (several people-search sites) carry the correct published opt-out URL but have
  **not** been field-verified (they 403 datacenter IPs), so confirm the live flow via the operator's
  residential browser on first use, then set `last_verified`. Field-verified curated records (no
  `confidence`, e.g. the cluster parents) have checked mechanics and take precedence.
