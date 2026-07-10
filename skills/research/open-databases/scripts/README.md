# scripts/

`dbquery.py` — stdlib-only CLI for the databases in this skill.

```bash
python3 dbquery.py openalex "CRISPR gene editing" --type works --limit 5
python3 dbquery.py crossref "CRISPR" --limit 5
python3 dbquery.py wikidata --query-file query.rq
python3 dbquery.py edgar '"Apple Inc"' --forms 10-K
python3 dbquery.py wayback example.com --limit 20
```

Add `--sqlite FILE --table NAME` to any subcommand to dump the parsed rows into
a local SQLite table (parameterized inserts, table name validated). No deps,
no API keys. Exits 2 on network/HTTP/parse errors.
