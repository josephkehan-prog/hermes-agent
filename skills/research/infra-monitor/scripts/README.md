# scripts/

`infra_snapshot.py` — stdlib-only CLI for infrastructure drift snapshotting.

```bash
python3 infra_snapshot.py snapshot example.com --out snap-2026-07-10.json
python3 infra_snapshot.py diff snap-2026-07-01.json snap-2026-07-10.json
python3 infra_snapshot.py diff old.json new.json --json --fail-on-change
```

No deps, no API keys. Domain input is validated against a hostname regex
before use; every network read is capped at 10 MB. Exits 2 on
network/HTTP/parse/validation errors; `diff --fail-on-change` exits 1 when
drift is found, for cron/alerting workflows.
