# scripts/

`portfolio.py` -- stdlib-only CLI to value a crypto portfolio from a local holdings file.

```bash
python3 portfolio.py check sample-holdings.json
python3 portfolio.py value sample-holdings.json [--vs usd]
```

No deps, no API keys. Holdings file is plaintext JSON you maintain --
never put private keys or secrets in it. Exits 2 on invalid input,
malformed holdings, or network/HTTP/parse errors.
