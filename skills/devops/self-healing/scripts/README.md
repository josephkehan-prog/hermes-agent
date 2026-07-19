# scripts/

`selfheal.py` — stdlib-only monitor→detect→remediate CLI.

```bash
python3 selfheal.py check example.json          # run checks, report only
python3 selfheal.py run example.json             # dry-run: prints what WOULD remediate
python3 selfheal.py run example.json --confirm   # actually remediate gated actions
python3 selfheal.py status                       # coder/ornith/disk/load snapshot
```

No deps, no API keys. HTTP checks route through `tools.uptime_check_tool`
(SSRF-guarded); loopback-only `local_model` checks are the documented
exception (see script docstring). Remediation commands run as list-args
subprocess calls, never a shell string, and destructive actions are
dry-run unless `--confirm` is passed. Exits 2 on runbook errors, 1 if any
check failed, 0 if all passed (`status` always exits 0).
