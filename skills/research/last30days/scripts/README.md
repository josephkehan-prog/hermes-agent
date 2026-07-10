# scripts/

`last30days.py` — fetch recent (~30 day) public chatter from keyless sources.
stdlib only, no API keys.

```bash
python3 last30days.py search "bitcoin" --sources reddit,hn --limit 10
python3 last30days.py search "rust async" --sources all --json
python3 last30days.py hn "claude code" --limit 5
python3 last30days.py polymarket "election"
python3 last30days.py github "agent framework" --limit 10
```

Sources: `reddit` (search JSON, `t=month`), `hn` (Algolia `search_by_date`,
`created_at_i` filtered to the last 30 days), `polymarket` (Gamma `/markets`,
filtered client-side by the query against `question`), `github` (repo search,
`pushed:>=` the 30-day cutoff).

`search` prints a merged table (source/title/metric/date/link) plus a
per-source count line; add `--json` for a structured `{entries, counts,
errors}` payload instead. Per-source subcommands (`reddit`, `hn`,
`polymarket`, `github`) query one source only. A source that errors is
skipped with a warning on stderr — the others still run; if every requested
source fails the process exits 2. See `../SKILL.md` for endpoint details and
coverage limits (X/YouTube/TikTok are not covered — no keyless API exists).
