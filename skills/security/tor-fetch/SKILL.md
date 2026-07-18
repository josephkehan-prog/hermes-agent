---
name: tor-fetch
description: Fetch a webpage over Tor, including .onion sites.
version: 1.0.0
platforms: [macos, linux]
metadata:
  hermes:
    tags: [tor, onion, privacy, anonymity, socks, proxy, dark-web, hidden-service]
    related_skills: []
---

# Tor Fetch

Fetch clearnet or **.onion** URLs through the local Tor SOCKS5 proxy
(`socks5h://127.0.0.1:9050`). Hostname resolution happens inside Tor, so
`.onion` addresses work. Localhost is never routed through Tor.

## Fetch a URL over Tor

```bash
python3 ~/.hermes/skills/security/tor-fetch/scripts/tor_fetch.py "<url>"
```

Examples:

```bash
# An onion service
python3 ~/.hermes/skills/security/tor-fetch/scripts/tor_fetch.py \
  "https://duckduckgogg42xjoc72x3sjasowoarfbgcmvfimaftt6twagswzczad.onion/"

# Clearnet site, but routed through Tor for anonymity
python3 ~/.hermes/skills/security/tor-fetch/scripts/tor_fetch.py "https://check.torproject.org/"

# Save the full body instead of printing a truncated preview
python3 .../scripts/tor_fetch.py "<url>" --save /tmp/page.html

# Just the response headers
python3 .../scripts/tor_fetch.py "<url>" --headers-only
```

Options: `--save PATH`, `--headers-only`, `--timeout SECONDS` (default 60),
`--max-bytes N` (preview size; `0` = print all). Override the proxy with the
`TOR_SOCKS_URL` env var. Exit code `2` means the fetch failed (often the onion
service is offline, or tor isn't running).

This script always routes THIS request through Tor, independent of the global
toggle below — so onion fetches work even when Hermes' normal traffic is direct.

## Toggle Hermes' global Tor routing

Route *all* of Hermes' external traffic (web search, browser, external APIs)
through Tor, or turn it back off. Local models / MCP / bridges stay direct
either way.

```bash
hermes-tor status   # show state + tor daemon + current exit IP
hermes-tor on       # route external traffic via Tor (restarts the gateway)
hermes-tor off      # back to normal connection (restarts the gateway)
```

`on`/`off` edit the `TOR PROXY` block in `~/.hermes/.env` and restart the
gateway. `on` starts the tor service if it isn't already running.

## Notes & gotchas

- **Onion services are often flaky/offline.** A failure usually means that
  specific site, not your setup — verify with the DuckDuckGo onion above.
- **Latency is higher over Tor**, and some clearnet APIs block Tor exit IPs
  (HTTP 403). If a normal web tool starts failing with 403 after `hermes-tor on`,
  that's why — turn it `off` or fetch that site directly.
- Requires the `tor` Homebrew service (SOCKS on 127.0.0.1:9050).
- **SOCKS deps:** `requests`-based tools need **PySocks** (`requests[socks]`) to
  use the `socks5h://` proxy — without it they fail with
  `InvalidSchema: Missing dependencies for SOCKS support`. httpx already has it
  via `httpx[socks]`. `hermes-tor on` now preflight-checks both and refuses to
  enable Tor if either is missing.
