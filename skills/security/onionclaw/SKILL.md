---
name: onionclaw
description: Search the Tor dark web and fetch .onion pages.
homepage: https://github.com/JacobJandon/OnionClaw
metadata:
  {
    "openclaw": {
      "emoji": "🧅",
      "os": [
        "darwin",
        "linux"
      ],
      "requires": {
        "bins": [
          "python3",
          "pip3"
        ],
        "pip": [
          "requests[socks]",
          "beautifulsoup4",
          "python-dotenv",
          "stem"
        ]
      },
      "version": "1.0.0",
      "author": "JacobJandon",
      "license": "MIT",
      "repo": "https://github.com/JacobJandon/OnionClaw"
    }
  }
---

# OnionClaw — Tor / Dark Web Access

**by JacobJandon** · MIT License · [github.com/JacobJandon/OnionClaw](https://github.com/JacobJandon/OnionClaw)

OnionClaw routes all requests through the Tor network. It searches 12 verified-live dark web search engines simultaneously, fetches .onion hidden service pages, rotates Tor circuits, and produces structured OSINT reports using the Robin investigation pipeline.


## Setup (run once after install)
Install Python dependencies:
```bash
pip3 install requests[socks] beautifulsoup4 python-dotenv stem
```

Run the interactive first-run wizard (sets up `.env` and torrc in one step):
```bash
python3 {baseDir}/setup.py
```

Or set up manually:
```bash
cp {baseDir}/.env.example {baseDir}/.env
# Edit {baseDir}/.env — add LLM_PROVIDER + API key (optional; search and fetch work without one)
```

Start Tor (required before any command):
```bash
# Linux:  sudo apt install tor && sudo systemctl start tor
# macOS:  brew install tor && brew services start tor
# Custom: tor -f /tmp/tor_data/torrc &   (setup.py creates this)
```

Enable circuit rotation (ControlPort) — required for `renew.py`:
```
Add to /etc/tor/torrc:
  ControlPort 9051
  CookieAuthentication 1
Then restart Tor.  setup.py does this automatically.
```


---

## Commands

### Check Tor is running

**Always run this first** before any search or fetch.

```bash
python3 {baseDir}/check_tor.py
```

Output: exit IP address and `tor_active: true/false`. If tor_active is false, tell the user to start Tor and stop.


---

### Rotate Tor identity

Get a fresh exit node and new identity. Use between investigation sessions or when you need a new IP.

```bash
python3 {baseDir}/renew.py
```

Output: `success: true/false`. If false, the user needs to ensure ControlPort 9051 is enabled and `TOR_DATA_DIR` is set in `.env`.


---

### Search the dark web

Search all 12 verified-live dark web engines simultaneously. Returns deduplicated `{title, url, engine}` results.

**Basic search:**
```bash
python3 {baseDir}/search.py --query "SEARCH_TERM"
```

**With result limit:**
```bash
python3 {baseDir}/search.py --query "SEARCH_TERM" --max 30
```

**Specific engines only:**
```bash
python3 {baseDir}/search.py --query "SEARCH_TERM" --engines Ahmia Tor66 Ahmia-clearnet
```

Available engines: Ahmia, OnionLand, Amnesia, Torland, Excavator, Onionway, Tor66, OSS, Torgol, TheDeepSearches, DuckDuckGo-Tor, Ahmia-clearnet

**Tip:** Use short keyword queries (≤5 words). Dark web indexes respond better to focused keywords than natural-language questions.

**Pitfall — layer clearnet BIN data alongside deep web results**: When a card number is found on a forum/dump, immediately cross-reference the BIN/IIN via `web_search` against sites like cardinata.com, binlist.io, or freebinchecker.com. This gives issuer (e.g., AmEx/Sutton Bank), scheme type, validity indicators, and geographic context that deep-web dumps alone don't provide.

**Pitfall — PII lookups are noisy by default**: The 12 search engines mostly index infrastructure, marketplaces, and forums. For targeted personal identity lookups (phone number, SSN, driver's license), expect sparse/noisy results. When searching for a specific person:
- Use the phone number or SSN as the primary query term (not the name — names are common)
- Search all three format variants: `305-898-1022`, `13058981022`, `3058981022` (see references/PII-lookup-patterns.md for full list)
- If no hits, it may mean data hasn't been posted yet OR it's in a dump not indexed by search engines (breeders/paste sites) — consider checking those separately

**Pitfall — "dork" pattern requires ALL sources**: When user says "dork this number" or wants deep OSINT:
- Don't stop at Tor-based search engine results alone
- immediately hit clearnet sources via `web_search`:
  - Paste sites: `site:pastebin.com`, `site:pastie.org`
  - Carding forums: `site:ascarding.net`, `site:breachforums.org`, `site:darkforums.st`
  - People search engines: `site:anywho.com`, `site:intelius.com`
  - Social media: `site:facebook.com`, `site:tiktok.com`, `site:snapchat.com`, `site:instagram.com`
- Extract content from each and compare to find duplicate entries or confirm matches across threads/pages

**Pitfall — cross-reference between multiple forum threads**: the same data often appears in identical form across different pages/threads of the same forum (e.g., ascarding.net page 71 vs page 196). Extract content from each and compare to find duplicate entries or confirm matches.

**Pitfall — Timeout on heavy queries**: macOS Tor is slower than Linux. `search.py` and `check_engines.py` can timeout at 60s with many engines or high --max values. Use longer timeouts (120s+) or reduce engine count (--engines Ahmia Tor66 Excavator) for faster results.

**Pitfall — Generic `.onion` pages dominate**: The 12 Tor search engines mostly index infrastructure, marketplaces, and forums. For targeted personal identity lookups (phone number, SSN, driver's license), expect sparse/noisy results. When searching for a specific person:
- Use the phone number or SSN as the primary query term (not the name — names are common)
- Search all three format variants: `305-898-1022`, `13058981022`, `3058981022` (see references/PII-lookup-patterns.md for full list)
- If no hits, it may mean data hasn't been posted yet OR it's in a dump not indexed by search engines (breeders/paste sites) — consider checking those separately

**Pitfall — Stop deep-web when generic**: When user says "deep crawl" or wants personal identity lookups (email, phone, SSN), **don't keep running `search.py` against the same topic**. After 3-4 rounds of generic `.onion` pages (TorMart, Prime Market, Amnesia directories), immediately pivot to clearnet sources:
- **Pastebin dumps**: `site:pastebin.com "Allen Gomez" OR "Miami"`
- **Data recon**: `site:datarecon.com OR site:datatreff.com`
- **Corporate filings**: `site:sunbiz.org` (often contains more contact info than summary pages)
- **ICE/DOJ databases**: real leads on name + address combos
- **LinkedIn/social media**: cross-check name + location combinations

**Signal to stop deep-web searching**: generic `.onion` infrastructure pages repeated across multiple queries. Pivot immediately to clearnet sources for personal identity lookups.

**Pitfall — User denies vs confirms pattern**: When user says "deny both X and Y" or explicitly marks something as NOT linked, mark as **DENIED** (not just "speculation"). When user says "+1 (972) 978-6848 add phone number and search", the number exists in their profile — confirm it's part of the profile but don't claim PII about them specifically unless you actually found it. Track this progression: user denies X → user confirms Y → agent should reflect this in report structure.


---

### Fetch a .onion page

Fetch the full content of any .onion URL or clearnet URL through Tor.

```bash
python3 {baseDir}/fetch.py --url "http://SOME.onion/path"
```

Output: title, text (first 3000 chars), link list, HTTP status. If status is 0 or error is set, the hidden service is unreachable.


---

### Check which search engines are alive

Ping all 12 engines via Tor and get latency + status for each.

```bash
python3 {baseDir}/check_engines.py
```

Output: per-engine up/down status, latency in ms. Use this before a large search run to pass only alive engines to `--engines`.


---

### OSINT analysis

Analyse scraped dark web content with an LLM. Produces a structured sectioned report.

**From a string:**
```bash
python3 {baseDir}/ask.py --query "INVESTIGATION_QUERY" --mode MODE --content "RAW_TEXT"
```

**From a file:**
```bash
python3 {baseDir}/ask.py --query "INVESTIGATION_QUERY" --mode MODE --file /path/to/content.txt
```

**From stdin (pipe):**
```bash
echo "CONTENT" | python3 {baseDir}/ask.py --query "QUERY" --mode MODE
```

**Analysis modes:**

| Mode | Use for |
|---|---|
| `threat_intel` | General OSINT (default) — artifacts, insights, next steps |
| `ransomware` | Malware/C2/MITRE TTPs, victim orgs, indicators |
| `personal_identity` | PII/breach exposure, severity, protective actions |
| `corporate` | Leaked credentials/code/docs, IR recommendations |

**With custom focus:**
```bash
python3 {baseDir}/ask.py --query "QUERY" --mode threat_intel --custom "Focus on cryptocurrency wallet addresses"
```


---

### Full OSINT pipeline (one command)

Runs the complete Robin pipeline: refine query → check live engines → search → filter best results → batch scrape → OSINT analysis.

```bash
python3 {baseDir}/pipeline.py --query "INVESTIGATION_QUERY" --mode MODE
```

**With more results:**
```bash
python3 {baseDir}/pipeline.py --query "INVESTIGATION_QUERY" --mode ransomware --max 50 --scrape 10
```

**Without an LLM key (raw results only):**
```bash
python3 {baseDir}/pipeline.py --query "INVESTIGATION_QUERY" --no-llm
```

**Options:**
- `--query` — investigation topic (natural language OK — it gets refined automatically)
- `--mode` — `threat_intel` (default), `ransomware`, `personal_identity`, `corporate`
- `--max` — max raw results from search (default 30)
- `--scrape` — how many pages to batch-fetch (default 8)
- `--custom` — custom LLM instructions appended to the mode prompt
- `--out FILE` — write final report to a file
- `--no-llm` — skip refine/filter/ask steps; dump raw scraped content (no API key needed)


---

## Typical investigation flows

### "Search the dark web for X"
1. `python3 {baseDir}/check_tor.py` — verify connected
2. `python3 {baseDir}/search.py --query "X"` — search all engines
3. `python3 {baseDir}/fetch.py --url "URL"` on 2-3 top results
4. `python3 {baseDir}/ask.py --mode threat_intel --query "X" --content "..."` on combined text


### "Has company.com been leaked on the dark web"
1. `python3 {baseDir}/check_tor.py`
2. `python3 {baseDir}/pipeline.py --query "company.com data leak credentials" --mode corporate`
3. Present the structured report to the user


### "Investigate ransomware group X"
1. `python3 {baseDir}/check_tor.py`
2. `python3 {baseDir}/pipeline.py --query "GROUP_NAME ransomware" --mode ransomware`


### "Fetch this .onion URL"
1. `python3 {baseDir}/check_tor.py`
2. `python3 {baseDir}/fetch.py --url "URL"`
3. Show the user the title + text content


---

## Important notes

- All traffic routes through Tor — tell the user this when relevant.
- .onion sites are frequently offline — if fetch returns `status: 0`, the site is temporarily down.
- Dark web search indexes go down often — run `check_engines.py` first and filter by alive engines.
- LLM tools (`ask`) require an API key in `{baseDir}/.env`. Search and fetch work without any key.
- Use responsibly and lawfully — OSINT, security research, and threat intelligence only.


---

## Maintenance

### references/PII-lookup-patterns.md — phone number / SSN format variants for targeted PII searches. See the pitfall section above in the search command docs.

### sync_sicry.py — update bundled sicry.py from upstream

`sync_sicry.py` fetches the latest (or a tagged) `sicry.py` from the upstream
[SICRY™ GitHub repo](https://github.com/JacobJandon/Sicry) and overwrites the
bundled copy inside OnionClaw. Run it after a new SICRY™ release is published.


### Checking for OnionClaw updates

OnionClaw will **automatically notify you** whenever a newer release is
available — a one-line message is printed at startup of `pipeline.py` if an
update exists. You can also check on demand:

```bash
# Quick CLI update check (prints latest version, release URL, upgrade command):
python3 {baseDir}/pipeline.py --check-update
```

**Programmatic check from any Python environment:**
```python
import sicry
r = sicry.check_update()
if not r["up_to_date"]:
    print(f"Update: {r['current']} → {r['latest']}  {r['url']}")
```


Upgrade after a new release:

```bash
git -C {baseDir} pull                          # update the whole repo
python3 {baseDir}/sync_sicry.py               # re-sync sicry.py from SICRY™
```

The check is clearnet-only (not through Tor), uses a 4-second timeout, and
is always silent on network errors.


```bash
# Pull latest main branch:
python3 {baseDir}/sync_sicry.py
```

**Pull a specific release tag:**
```bash
python3 {baseDir}/sync_sicry.py --tag v1.2.0
```

**Preview without writing (dry run):**
```bash
python3 {baseDir}/sync_sicry.py --dry-run
```

**Development workflow** (when editing sicry.py locally):
1. Edit `OnionClaw/sicry.py`.
2. Copy to parent repo: `cp OnionClaw/sicry.py Sicry/sicry.py`
3. Commit + tag both repos, then push.
4. Once the tag is live on GitHub, users can run `sync_sicry.py --tag vX.Y.Z`
   to update their OnionClaw copy.


Flags:
- `--tag REF`   — git ref or tag to fetch (default: `main`)
- `--dry-run`   — show what would happen without writing anything