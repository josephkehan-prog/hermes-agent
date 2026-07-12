# Query Cookbook

Copy-paste `curl` examples for each source in the catalog. All are keyless GET requests.

## OpenAlex — works and authors

```bash
curl -s "https://api.openalex.org/works?search=CRISPR%20gene%20editing&per-page=5&mailto=you@example.com" | python3 -m json.tool
curl -s "https://api.openalex.org/authors?search=Jennifer%20Doudna&mailto=you@example.com" | python3 -m json.tool
```

## Crossref — works by keyword or DOI

```bash
curl -s "https://api.crossref.org/works?query=CRISPR&rows=5&mailto=you@example.com" | python3 -m json.tool
curl -s "https://api.crossref.org/works/10.1126/science.1231143" | python3 -m json.tool
```

## PubMed E-utilities (keyless tier)

```bash
# Search -> list of PMIDs
curl -s "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi?db=pubmed&term=CRISPR+AND+2024[pdat]&retmode=json&retmax=10"

# Fetch summaries for PMIDs
curl -s "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi?db=pubmed&id=38000000,38000001&retmode=json"
```

## Wikidata SPARQL

```bash
curl -s -H "Accept: application/sparql-results+json" \
  --data-urlencode 'query=SELECT ?item ?itemLabel WHERE {
    ?item wdt:P31 wd:Q5 .
    ?item wdt:P106 wd:Q901 .
    SERVICE wikibase:label { bd:serviceParam wikibase:language "en". }
  } LIMIT 10' \
  "https://query.wikidata.org/sparql"
```

## SEC EDGAR full-text search + company facts

```bash
# Full-text search across filings (User-Agent is mandatory, see Pitfalls)
curl -s -H "User-Agent: research-agent you@example.com" \
  "https://efts.sec.gov/LATEST/search-index?q=%22Apple+Inc%22&forms=10-K"

# Company facts (XBRL) by CIK, zero-padded to 10 digits
curl -s -H "User-Agent: research-agent you@example.com" \
  "https://data.sec.gov/api/xbrl/companyfacts/CIK0000320193.json" | python3 -m json.tool
```

## archive.org advancedsearch + Wayback CDX

```bash
# Search archive.org's item catalog
curl -s "https://archive.org/advancedsearch.php?q=title%3A%28CRISPR%29&fl%5B%5D=identifier&fl%5B%5D=title&output=json&rows=5"

# List every archived snapshot of a URL
curl -s "https://web.archive.org/cdx/search/cdx?url=example.com&output=json&limit=10"

# Fetch a specific snapshot
curl -s "http://web.archive.org/web/20020120142510/http://example.com/"
```

## OpenLibrary

```bash
curl -s "https://openlibrary.org/search.json?q=the+selfish+gene&limit=5" | python3 -m json.tool
curl -s "https://openlibrary.org/isbn/9780198788607.json" | python3 -m json.tool
```

## WHOIS / DNS

```bash
whois example.com
dig +short example.com A
dig +short example.com MX
dig +short -x 93.184.216.34   # reverse lookup
```

## data.gov / EU Open Data Portal

```bash
# data.gov's CKAN API now lives under api.gsa.gov and requires api_key=
# (the shared public DEMO_KEY works with no registration, rate-limited)
curl -s "https://api.gsa.gov/technology/datagov/v3/action/package_search?q=climate&rows=5&api_key=DEMO_KEY" | python3 -m json.tool
curl -s "https://data.europa.eu/api/hub/search/search?q=climate&limit=5" | python3 -m json.tool
```
