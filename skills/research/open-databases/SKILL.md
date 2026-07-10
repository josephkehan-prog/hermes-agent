---
name: open-databases
description: Query free public research databases with no API key — OpenAlex, Crossref, Wikidata SPARQL, SEC EDGAR, archive.org/Wayback, OpenLibrary, PubMed, WHOIS/DNS. Includes scripts/dbquery.py.
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [Research, Databases, Open Data, SPARQL, Academic]
    related_skills: [arxiv, scrapling, duckduckgo-search]
---

# Open Databases

Query free, keyless public databases for research: academic literature (OpenAlex,
Crossref, PubMed), structured knowledge (Wikidata), regulatory filings (SEC EDGAR),
archived web content (archive.org, Wayback CDX), books (OpenLibrary), domain/network
records (WHOIS/DNS), and government open-data portals. Every source below works with
plain HTTP GET and no signup — `curl` or `scripts/dbquery.py` is all you need.

For arXiv-specific search (papers, Semantic Scholar citations, BibTeX), use the
`arxiv` skill instead — it's covered in depth there and only cross-linked here.

## When to Use

- Looking up academic papers, citation counts, or author profiles without a paywall
- Verifying facts, dates, or structured entity data (Wikidata SPARQL)
- Researching a public company's filings, financials, or disclosures (EDGAR)
- Checking what a webpage looked like at a past date, or whether a URL ever existed
- Looking up book metadata/editions (OpenLibrary)
- Basic domain/network reconnaissance (WHOIS, DNS) for a research or security task
- Any research task where you'd otherwise reach for a paid API and a free one exists

## Source Catalog

| Source | Base URL | Auth-free limits | Example query URL |
|---|---|---|---|
| OpenAlex | `api.openalex.org` | Generous; "polite pool" (faster, prioritized) if you pass `mailto=` | `https://api.openalex.org/works?search=CRISPR&mailto=you@example.com` |
| Crossref | `api.crossref.org` | Generous; "polite pool" via `mailto=` param | `https://api.crossref.org/works?query=CRISPR&mailto=you@example.com` |
| arXiv API | `export.arxiv.org/api` | ~1 req / 3s | see the `arxiv` skill |
| PubMed E-utilities | `eutils.ncbi.nlm.nih.gov/entrez/eutils` | 3 req/s keyless (10 req/s with a free NCBI API key) | `https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi?db=pubmed&term=CRISPR&retmode=json` |
| Wikidata SPARQL | `query.wikidata.org/sparql` | Shared endpoint; 60s query timeout | `https://query.wikidata.org/sparql?query=SELECT...&format=json` |
| SEC EDGAR full-text | `efts.sec.gov/LATEST/search-index` | Requires descriptive `User-Agent`; ~10 req/s | `https://efts.sec.gov/LATEST/search-index?q=%22Apple+Inc%22&forms=10-K` |
| SEC EDGAR company facts | `data.sec.gov/api/xbrl` | Same UA requirement | `https://data.sec.gov/api/xbrl/companyfacts/CIK0000320193.json` |
| archive.org advancedsearch | `archive.org/advancedsearch.php` | Generous | `https://archive.org/advancedsearch.php?q=title:(CRISPR)&output=json` |
| Wayback CDX | `web.archive.org/cdx/search/cdx` | Generous | `https://web.archive.org/cdx/search/cdx?url=example.com&output=json` |
| OpenLibrary | `openlibrary.org` | Generous | `https://openlibrary.org/search.json?q=the+selfish+gene` |
| WHOIS | system `whois` command | Registry-dependent rate limits | `whois example.com` |
| DNS | system `dig` command | Local resolver | `dig +short example.com A` |
| data.gov | `api.gsa.gov/technology/datagov/v3/action` (CKAN API) | Needs `api_key=` param; public `DEMO_KEY` works, no signup | `https://api.gsa.gov/technology/datagov/v3/action/package_search?q=climate&api_key=DEMO_KEY` |
| EU Open Data Portal | `data.europa.eu/api/hub/search` | Generous | `https://data.europa.eu/api/hub/search/search?q=climate` |

## Query Cookbook

### OpenAlex — works and authors

```bash
curl -s "https://api.openalex.org/works?search=CRISPR%20gene%20editing&per-page=5&mailto=you@example.com" | python3 -m json.tool
curl -s "https://api.openalex.org/authors?search=Jennifer%20Doudna&mailto=you@example.com" | python3 -m json.tool
```

### Crossref — works by keyword or DOI

```bash
curl -s "https://api.crossref.org/works?query=CRISPR&rows=5&mailto=you@example.com" | python3 -m json.tool
curl -s "https://api.crossref.org/works/10.1126/science.1231143" | python3 -m json.tool
```

### PubMed E-utilities (keyless tier)

```bash
# Search -> list of PMIDs
curl -s "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi?db=pubmed&term=CRISPR+AND+2024[pdat]&retmode=json&retmax=10"

# Fetch summaries for PMIDs
curl -s "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi?db=pubmed&id=38000000,38000001&retmode=json"
```

### Wikidata SPARQL

```bash
curl -s -H "Accept: application/sparql-results+json" \
  --data-urlencode 'query=SELECT ?item ?itemLabel WHERE {
    ?item wdt:P31 wd:Q5 .
    ?item wdt:P106 wd:Q901 .
    SERVICE wikibase:label { bd:serviceParam wikibase:language "en". }
  } LIMIT 10' \
  "https://query.wikidata.org/sparql"
```

### SEC EDGAR full-text search + company facts

```bash
# Full-text search across filings (User-Agent is mandatory, see Pitfalls)
curl -s -H "User-Agent: research-agent you@example.com" \
  "https://efts.sec.gov/LATEST/search-index?q=%22Apple+Inc%22&forms=10-K"

# Company facts (XBRL) by CIK, zero-padded to 10 digits
curl -s -H "User-Agent: research-agent you@example.com" \
  "https://data.sec.gov/api/xbrl/companyfacts/CIK0000320193.json" | python3 -m json.tool
```

### archive.org advancedsearch + Wayback CDX

```bash
# Search archive.org's item catalog
curl -s "https://archive.org/advancedsearch.php?q=title%3A%28CRISPR%29&fl%5B%5D=identifier&fl%5B%5D=title&output=json&rows=5"

# List every archived snapshot of a URL
curl -s "https://web.archive.org/cdx/search/cdx?url=example.com&output=json&limit=10"

# Fetch a specific snapshot
curl -s "http://web.archive.org/web/20020120142510/http://example.com/"
```

### OpenLibrary

```bash
curl -s "https://openlibrary.org/search.json?q=the+selfish+gene&limit=5" | python3 -m json.tool
curl -s "https://openlibrary.org/isbn/9780198788607.json" | python3 -m json.tool
```

### WHOIS / DNS

```bash
whois example.com
dig +short example.com A
dig +short example.com MX
dig +short -x 93.184.216.34   # reverse lookup
```

### data.gov / EU Open Data Portal

```bash
# data.gov's CKAN API now lives under api.gsa.gov and requires api_key=
# (the shared public DEMO_KEY works with no registration, rate-limited)
curl -s "https://api.gsa.gov/technology/datagov/v3/action/package_search?q=climate&rows=5&api_key=DEMO_KEY" | python3 -m json.tool
curl -s "https://data.europa.eu/api/hub/search/search?q=climate&limit=5" | python3 -m json.tool
```

## Helper Script

`scripts/dbquery.py` wraps the highest-traffic sources (OpenAlex, Crossref,
Wikidata, EDGAR, Wayback) with URL-safe query building, a compact table
printer, and an optional SQLite dump:

```bash
python3 scripts/dbquery.py openalex "CRISPR gene editing" --type works --limit 5
python3 scripts/dbquery.py crossref "CRISPR" --limit 5
python3 scripts/dbquery.py wikidata --query-file query.rq
python3 scripts/dbquery.py edgar '"Apple Inc"' --forms 10-K
python3 scripts/dbquery.py wayback example.com --limit 20

# Dump any of the above into local SQLite for further querying
python3 scripts/dbquery.py openalex "CRISPR" --limit 20 --sqlite papers.db --table crispr_works
```

See `scripts/README.md`. No dependencies beyond the Python standard library;
exits 2 on network/HTTP/parse errors.

## Local Analysis: JSON/CSV -> SQLite or DuckDB

Once you've pulled results (via `curl` or `dbquery.py --sqlite`), do the
actual analysis locally instead of re-fetching or eyeballing raw JSON.

**stdlib SQLite** (always available):

```python
import json
import sqlite3

data = json.load(open("works.json"))
conn = sqlite3.connect(":memory:")
conn.execute("CREATE TABLE works (doi TEXT, title TEXT, year INTEGER, citations INTEGER)")
rows = [(w["doi"], w["display_name"], w["publication_year"], w["cited_by_count"])
        for w in data["results"]]
conn.executemany("INSERT INTO works VALUES (?, ?, ?, ?)", rows)
for row in conn.execute("SELECT * FROM works ORDER BY citations DESC LIMIT 5"):
    print(row)
```

**DuckDB, if installed** (`pip install duckdb` — not installed by this skill;
faster for larger JSON/CSV and can query files directly without loading them
into Python first):

```bash
duckdb -c "SELECT title, publication_year, cited_by_count
           FROM read_json_auto('works.json', records=true)
           ORDER BY cited_by_count DESC LIMIT 5"
```

Check for DuckDB before relying on it: `command -v duckdb`. Fall back to
stdlib `sqlite3` when it's absent — never install it silently.

## Model Wiring

For research workflows that need to normalize or synthesize across these
sources, two local endpoints are wired (see the `scrapling` skill for the
full pattern; summarized here for this skill's use case):

| Task | Model | Endpoint | Why |
|------|-------|----------|-----|
| Deterministic field extraction/normalization (e.g. "pull DOI/title/year as JSON from this record") | **agent1** | Ollama `http://localhost:11434/api/chat`, `"options": {"temperature": 0}` | Temperature 0 for repeatable structured output |
| Cross-source synthesis (e.g. "reconcile what OpenAlex, Crossref, and Wikidata say about this entity") | **ornith** | llama-swap `http://localhost:1235/v1/chat/completions`, `"chat_template_kwargs": {"enable_thinking": false}` | Reasoning model with thinking disabled for fast, terse synthesis |

```python
import json
import urllib.request

# agent1: deterministic normalization, temperature 0
payload = {
    "model": "hf.co/InternScience/Agents-A1-Q4_K_M-GGUF:latest",
    "messages": [
        {"role": "system", "content": "Extract structured data as JSON only. No prose, no markdown fences."},
        {"role": "user", "content": f"Normalize this record to {{doi, title, year, source}}.\n\n{record_text}"},
    ],
    "options": {"temperature": 0},
    "stream": False,
}
req = urllib.request.Request(
    "http://localhost:11434/api/chat",
    data=json.dumps(payload).encode(),
    headers={"Content-Type": "application/json"},
)
result = json.loads(urllib.request.urlopen(req, timeout=120).read())["message"]["content"]
```

```python
# ornith: cross-source synthesis, thinking disabled
payload = {
    "model": "ornith-uncensored",
    "messages": [{"role": "user", "content": f"Reconcile these records from OpenAlex, Crossref, and Wikidata; note any disagreements.\n\n{combined_records}"}],
    "chat_template_kwargs": {"enable_thinking": False},
    "stream": False,
}
req = urllib.request.Request(
    "http://localhost:1235/v1/chat/completions",
    data=json.dumps(payload).encode(),
    headers={"Content-Type": "application/json"},
)
result = json.loads(urllib.request.urlopen(req, timeout=120).read())["choices"][0]["message"]["content"]
```

Verify wiring before relying on it:

```bash
curl -s http://localhost:11434/api/tags | grep -o '"hf.co/InternScience/Agents-A1[^"]*"'
curl -s http://localhost:1235/v1/models | grep -o '"ornith-uncensored"'
```

## Pitfalls

- **Rate limits**: OpenAlex and Crossref have generous default limits but
  reward a `mailto=` param with the "polite pool" — faster, more reliable
  service. Always pass it (`MAILTO` constant in `dbquery.py` — replace the
  placeholder with a real contact address).
- **EDGAR User-Agent requirement**: `efts.sec.gov` and `data.sec.gov` reject
  requests without a descriptive `User-Agent` header identifying the
  requester (e.g. `"research-agent you@example.com"`). A generic/missing UA
  gets a 403 or a soft block. `dbquery.py` sets this automatically.
- **SPARQL timeouts**: `query.wikidata.org` is a shared public endpoint with
  a ~60s server-side timeout. Add `LIMIT`, avoid unbound triple patterns
  across the full graph, and expect occasional 500s under load — retry once
  before concluding the query itself is wrong.
- **Wikidata query encoding**: always URL-encode the `query` param (or use
  `--data-urlencode` in curl / `urllib.parse.urlencode` in Python) — raw
  SPARQL has characters (`{`, `}`, spaces, `?`) that break naive
  concatenation.
- **archive.org/Wayback rate limiting**: bursty CDX queries can get
  temporarily throttled; space out requests for bulk snapshot listing.
- **EDGAR CIK format**: `data.sec.gov` company-facts endpoints require the
  CIK zero-padded to 10 digits (`CIK0000320193`, not `CIK320193`).
- **PubMed keyless tier**: 3 req/s without an API key; get a free NCBI API
  key (`api_key=` param) to raise this to 10 req/s if doing bulk lookups.
- **WHOIS output is unstructured**: format varies by registry/TLD — parse
  defensively (regex per-field) rather than assuming a fixed layout.
- **data.gov moved its API**: the old `catalog.data.gov/api/3/action/*` CKAN
  endpoints now 404. Current API is `api.gsa.gov/technology/datagov/v3/action/*`
  and requires an `api_key=` param — the shared public `DEMO_KEY` works with
  no registration, but is rate-limited; get a free key at data.gov for
  heavier use.
- **Don't reinvent arXiv or DuckDuckGo search**: this skill deliberately
  excludes arXiv (see the `arxiv` skill) and general web search (see the
  `duckduckgo-search` skill) — use those directly.
