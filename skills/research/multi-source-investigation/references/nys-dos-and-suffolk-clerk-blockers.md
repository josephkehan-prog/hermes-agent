# NY DOS & Suffolk County Clerk — Access Blockers

## NY DOS (apps.dos.ny.gov) — Connection Reset

**Symptom:** All endpoints return `ERR_CONNECTION_RESET` or `net::ERR_NAME_NOT_RESOLVED`. This includes:
- `https://apps.dos.ny.gov/api/public/entity/search?q=downey+nathan&type=entity`
- `https://apps.dos.ny.gov/publicInquiry/`

**Cause:** NY DOS API was unreachable during investigation session (July 7, 2026). May be intermittent or rate-limited.

**Workaround:** Use the **Socrata Open Data mirror** at `https://data.ny.gov/api/views/n9v6-gdp6/rows.json` for bulk entity search by name. API accepts JSON queries with `search=%25downey%25&limit=100`. Returns structured data including:
- `current_entity_name`, `county`, `entity_type`
- `dos_process_name`, `registered_agent_name`

**Note:** Socrata mirror may also return 0 results — that's a valid result, not necessarily a blocker. The NY DOS API itself is authoritative; the mirror is convenience-only.

## Suffolk County Clerk (clerk.suffolkcountyny.gov) — Cloudflare Bot Detection

**Symptom:** `Just a moment...` page with bot detection challenge. Blocks automated navigation.

**Cause:** Aggressive bot protection on government sites.

**Workaround:** Use alternative public records interfaces:
- `http://www.suffolk.nydeeds.com/` — CGI-based deed search (lighter, no bot detection)
- `https://opengovny.com/corporation?county=Suffolk&search=downey+nathan` — OpenGovNY mirror of NY DOS data

## NY Attorney Registry (opendatany.com / opengovny.com/attorney)

**Status:** Fully accessible. Returns structured attorney registration data including:
- Registration number, full name, company, address, phone, law school, year admitted, status

**Note:** NY OCA registry is public per 22 NYCRR Part 118 and Uniform Rules of Trial Courts §468-a. All attorneys must file registration every two years (within 30 days after birthday).

## Suffolk County Clerk — Alternative Access Paths

| Interface | Status | Notes |
|-----------|--------|-------|
| `clerk.suffolkcountyny.gov/kiosk` | Cloudflare blocked | Bot detection |
| `suffolk.nydeeds.com` | Accessible | CGI-based, no bot protection |
| `opengovny.com/corporation?county=Suffolk` | Accessible | NY DOS mirror for business entities |

## Key Takeaway

When government portals block automated access: fall back to third-party mirrors (OpenGovNY, suffolk.nydeeds.com) or Socrata Open Data APIs. The data is the same — just different delivery layer.