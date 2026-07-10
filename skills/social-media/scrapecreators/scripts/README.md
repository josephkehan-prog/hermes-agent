# scripts/

`scrapecreators.py` — CLI wrapper for the ScrapeCreators API (paid key required).

```bash
python3 scrapecreators.py profile tiktok someuser
python3 scrapecreators.py posts instagram someuser --limit 10
python3 scrapecreators.py search youtube "some query"
```

Reads `SCRAPECREATORS_API_KEY` from the environment; unset -> prints
`[NEEDS-KEY]` and exits 2 with no network call. stdlib only. See
`../SKILL.md` for the endpoint catalog and model wiring.
