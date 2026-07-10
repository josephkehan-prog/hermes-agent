# scripts/

`logtriage.py` — stdlib-only CLI, no network, no shell-out.

```bash
python3 logtriage.py scan <logfile> [--since-lines N] [--level ERROR]
python3 logtriage.py cluster <logfile> [--since-lines N] [--top-n N]
python3 logtriage.py summary <logfile> [--since-lines N]
```

Reads are capped at 50 MB and seek from the end of the file, so a
multi-gigabyte log never gets loaded into memory. See SKILL.md for the
severity/formats it recognizes and the incident-triage workflow.
