---
name: credit-card-investigation
description: Investigate leaked card data with BIN/IIN lookups.
tags: [deep-web, credit-card, bin-inquiry, carding-forum]
---

# Credit Card Investigation — Deep Web + BIN Layering

**Purpose:** When a stolen card number appears on a forum/dump (e.g., ascarding.net, BreachForums), layer clearnet BIN/IIN data alongside the raw dump to provide full context: issuer, scheme type, validity indicators, geographic routing, and PII exposure scope.

## Trigger conditions
- User provides a specific credit card number found on deep web
- User asks about a breach dump or leaked card file
- Deep-web search returns cardholder data in `|`-delimited format (e.g., `4403933633400558|03|2027|389|EXAMPLE_NAME|3000 NE 2nd avenue|Miami|FL|33137|3058981022||UNITED STATES`)

## Investigation workflow

### Phase 1: Deep-web extraction
1. Search the number across carding forums via `web_extract` on forum threads (ascarding.net, BreachForums, darkforums.st)
2. Extract raw dump entries — note the `|`-delimited format and identify all PII fields present

### Phase 2: BIN/IIN cross-reference
3. Run `web_search` for the first 6 digits (BIN/IIN) against clearnet databases:
   - **cardinata.com/bin/XXXXXX** — issuer, scheme type, country, validity percentage
   - **binlist.io/XXXXXX/** — bank name, card type (debit/credit/prepaid), length, validation algorithm
   - **freebinchecker.com/bin-lookup/XXXXXX/** — additional context on issuer and currency

4. Compile BIN data: which bank issued it, what scheme (Visa/MC/AmEx/Discover), geographic routing, validity indicators

### Phase 3: Seller identification
5. Identify who posted the dump — look for seller accounts in thread metadata (e.g., "TOPGAME" on ascarding.net)
6. Extract seller profile details: join date, message count, reaction score, marketplace domains

### Phase 4: PII exposure assessment
7. Document all exposed fields from the dump entry:
   - Card number + expiration + CVV (if present)
   - Name, address, phone, email (if present)
   - Geographic context (state/country routing for fraud operations)

8. Note gaps — some dumps omit emails or have blank fields; clearly state what's missing vs. exposed

## Key tools and sources

| Source | Purpose | Query format |
|--------|---------|--------------|
| ascarding.net threads | Forum dump extraction | `web_extract` on page URLs (page-71, page-196) |
| cardinata.com/bin/XXXXXX | BIN issuer lookup | Web search or direct URL access |
| binlist.io/XXXXXX/ | Bank/scheme context | Web search |
| freebinchecker.com/bin-lookup/XXXXXX/ | Additional BIN detail | Web search |

## Pitfalls

### Empty email fields in dumps
Some dump entries have blank email fields (the field between phone and country is empty). Don't assume the person has no email — it may just be missing from that particular dump. Cross-check with `web_search` for name + address combinations on LinkedIn, about.me, etc.

### Stop deep-web when generic (also: Dork pattern)
When user says "deep crawl" or wants personal identity lookups (email, phone, SSN), **don't keep running `search.py` against the same topic**. After 3-4 rounds of generic `.onion` pages (TorMart, Prime Market, Amnesia directories), immediately pivot to clearnet sources:
- **Pastebin dumps**: `site:pastebin.com "EXAMPLE_NAME" OR "Miami"`
- **Data recon**: `site:datarecon.com OR site:datatreff.com`
- **Corporate filings**: `site:sunbiz.org` (often contains more contact info than summary pages)
- **ICE/DOJ databases**: real leads on name + address combos
- **LinkedIn/social media**: cross-check name + location combinations

**Signal to stop deep-web searching**: generic `.onion` infrastructure pages repeated across multiple queries. Pivot immediately to clearnet sources for personal identity lookups.

### Forum pagination duplication
The same data often appears in identical form across different pages/threads of the same forum (e.g., ascarding.net page 71 vs page 196). Extract each and compare to confirm it's the same entry or a new one.

### BIN/IIN context matters for fraud routing
A Visa issued by Sutton Bank with US routing tells attackers where to target POS terminals, which gateways to test against (CVV-check strength), and what geographic profile is exposed. Layer this context into your report — not just "found on forum" but "AmEx/Sutton Bank/US routing/EXAMPLE_NAME/Miami FL".

### Seller identification
Always identify the seller account that posted the dump. Note join date, message count, reaction score, marketplace domains (e.g., `topgame.biz`, `.pw`, Tor exit). This provides attribution context for the breach.

## Output format

Present findings in this structure:
1. **Cardholder identity** — name + address from dump
2. **BIN/IIN context** — issuer, scheme type, geographic routing
3. **Seller attribution** — who posted it, marketplace info
4. **PII exposure scope** — what's exposed vs. missing (name, address, phone, email status)
5. **Next steps offer** — deep-crawl for additional sources if user wants

## Notes
- BIN data is clearnet-only; no Tor routing needed for this phase
- Forum dumps are often paginated and repeated across pages — extract each and compare
- Some entries omit emails; don't assume zero exposure, just missing from that dump
- Always layer BIN context alongside raw dump — it contextualizes the fraud risk
