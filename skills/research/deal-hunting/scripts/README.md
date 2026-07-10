# scripts/

`deals.py` — search and watch deal feeds. stdlib only, no API keys.

```bash
python3 deals.py search "ssd" --source slickdeals --limit 10
python3 deals.py search "gpu" --source all
python3 deals.py watch "steam deck" --out watchlist.json --source reddit-gamedeals
```

`search` prints a table (source/title/price/date/link). `watch` appends new
matches to a JSON file, deduped by SHA-256 of the link. See `../SKILL.md` for
source details and pitfalls.
