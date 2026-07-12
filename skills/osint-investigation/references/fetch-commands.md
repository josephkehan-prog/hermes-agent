# Fetch command reference

Full invocation examples for every `fetch_*.py` script in `SKILL_DIR/scripts/`,
grouped the same way as the source wiki entries. All outputs are normalized
CSV with a header row. Re-run scripts idempotently.

## Federal financial / regulatory

```bash
# SEC EDGAR filings (corporate disclosures)
python3 SKILL_DIR/scripts/fetch_sec_edgar.py --cik 0000320193 \
    --types 10-K,10-Q --out data/edgar_filings.csv

# USAspending federal contracts
python3 SKILL_DIR/scripts/fetch_usaspending.py --recipient "EXAMPLE CORP" \
    --fy 2024 --out data/contracts.csv

# Senate LD-1 / LD-2 lobbying disclosures
python3 SKILL_DIR/scripts/fetch_senate_ld.py --client "EXAMPLE CORP" \
    --year 2024 --out data/lobbying.csv

# OFAC SDN sanctions list (full snapshot)
python3 SKILL_DIR/scripts/fetch_ofac_sdn.py --out data/ofac_sdn.csv

# ICIJ Offshore Leaks — downloads ~70 MB bulk CSV on first use,
# then searches it locally. Cached for 30 days under
# $HERMES_OSINT_CACHE/icij/ (default: ~/.cache/hermes-osint/icij/).
python3 SKILL_DIR/scripts/fetch_icij_offshore.py --entity "EXAMPLE CORP" \
    --out data/icij.csv
```

## Identity / property / litigation / archives / news

```bash
# NYC property records (deeds, mortgages, liens) — ACRIS via Socrata
python3 SKILL_DIR/scripts/fetch_nyc_acris.py --name "SMITH, JOHN" \
    --out data/acris.csv
python3 SKILL_DIR/scripts/fetch_nyc_acris.py --address "571 HUDSON" \
    --out data/acris_addr.csv

# OpenCorporates — 130+ jurisdiction corporate registry
# (free token required; set OPENCORPORATES_API_TOKEN or pass --token)
python3 SKILL_DIR/scripts/fetch_opencorporates.py --query "Example Corp" \
    --jurisdiction us_ny --out data/opencorporates.csv

# CourtListener — federal + state court opinions, PACER dockets
python3 SKILL_DIR/scripts/fetch_courtlistener.py --query "Smith v. Example Corp" \
    --type opinions --out data/courts.csv

# Wayback Machine — historical web captures
python3 SKILL_DIR/scripts/fetch_wayback.py --url "example.com" \
    --match host --collapse digest --out data/wayback.csv

# Wikipedia + Wikidata — narrative bio + structured facts
# Set HERMES_OSINT_UA=your-app/1.0 (your@email) to identify yourself
python3 SKILL_DIR/scripts/fetch_wikipedia.py --query "Bill Gates" \
    --out data/wp.csv

# GDELT — global news in 100+ languages, ~2015→present
python3 SKILL_DIR/scripts/fetch_gdelt.py --query '"Example Corp"' \
    --timespan 1y --out data/gdelt.csv
```

## Private-individual coverage gaps

When a private individual won't be in a source (e.g. SEC EDGAR for a non-public-
company person, USAspending for someone who isn't a federal contractor, Senate
LDA for someone who isn't a lobbying client), the script returns 0 rows with a
clear warning rather than silently writing an empty CSV. EDGAR specifically
flags when the company-name resolver matched an individual Form 3/4/5 filer
rather than a corporate registrant.

## Rate limits and API keys

Rate-limit notes are in each source's wiki entry (`references/sources/`).
Default fetchers sleep politely between paginated requests. **API keys raise
rate limits** for sources that support them (`SEC_USER_AGENT`,
`SENATE_LDA_TOKEN`, `OPENCORPORATES_API_TOKEN`, `COURTLISTENER_TOKEN`). All
scripts surface 429 responses immediately with the upstream's quota message
so the user knows to slow down or supply a key.
