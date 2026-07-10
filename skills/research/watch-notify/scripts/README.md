# scripts/

`watch.py` — stdlib-only CLI for change detection and keyless alerts.

```bash
python3 watch.py check https://example.com --state state.json
python3 watch.py watch-json https://api.example.com/status --field data.status --state state.json
python3 watch.py notify "example.com changed" --topic watch-<random>
```

No deps, no API keys. URLs are checked for http(s) scheme, resolved and
rejected if private/loopback/link-local, and every response is capped at
10 MB, redirects included. Exits 2 on network/HTTP/parse/validation errors.
