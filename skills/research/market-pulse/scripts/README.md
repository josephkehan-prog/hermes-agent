# scripts/

`pulse.py` — stdlib-only CLI that synthesizes crypto + prediction-market
data into one combined dashboard.

```bash
python3 pulse.py snapshot
python3 pulse.py snapshot --json
```

No deps, no API keys. Composes CoinGecko, alternative.me, and Polymarket
Gamma — each source is fetched and parsed in isolation, so one source
being down or rate-limited still shows the other two. Exits 0 if at
least one source succeeded, 2 if all three failed.
