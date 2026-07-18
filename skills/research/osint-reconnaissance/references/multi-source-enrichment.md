# Multi-Source Enrichment Pattern

## When to Apply

After initial Sherlock scan returns few results or Spokeo/Intelius owner data with initials + address. **Do not stop at the first layer.**

## Technique

### 1. Owner Cross-Reference (name+address, not phone)
Take owner from lookup service (e.g. "Allen G", "Sandra M") and search:
- LinkedIn: `"<name>" "<initial>" Miami FL` or `"<name>" <company>`
- Healthcare NPI databases: `"<name>" "Miami" nurse practitioner`
- Property records: RealtyTrac/Realtor.com — address + ZIP code reveals who lives there

### 2. Fez Ghani Case Study (from session)
Intelius confirmed: **Fez Ghani**, age 64–66, **10060 NW 4th St #202, Pembroke Pines FL 33024**
- Multiple locations on file: Hialeah (W 54th St), Doral (NW 79th Ave), Homestead, Orlando
- Associated area codes: **954, 305, 407, 754** — this number routes between several lines/accounts
- FAA Pilot/Mechanic license listed

### 3. Shared Line Assessment
When multiple owners share same address (Allen G + Sandra M at SW 150th Pl) OR multiple area codes on one owner (Fez Ghani), conclude: **shared/forwarded line**. The primary subscriber is likely the young person, with older relatives as secondary accounts or forwarding numbers.

### 4. Present as Bullet Links
When URLs are available from Spokeo/Intelius/LinkedIn, present as clickable bullets. Note that paid lookups hold deeper data (full names, property records, email).

## Example Output Format

```
Allen G — likely Allen Greer:
• LinkedIn: https://linkedin.com/in/allengreer
• Company: Fuze Digital Inc., Miami FL
• Email: all*******@fuzeinc.com (on Salesgear.io)
• Address matches Spokeo: SW 150th Pl, Miami FL 33194

Sandra M — age 49 at same address, relatives all share "G" surname
• Full name not confirmed from free data

Fez Ghani — confirmed identity (Intelius):
• Address: 10060 NW 4th St #202, Pembroke Pines FL 33024
• Multiple locations: Hialeah, Doral, Homestead, Orlando
• Associated area codes: 954, 305, 407, 754

Summary: Shared/forwarded line. Allen Greer (young owner) at Miami address is likely primary subscriber, with Sandra M and Fez Ghani as relatives on same account or forwarding numbers.
```

## Pitfalls to Avoid

- Don't search by phone number for the person — search by **name+address** instead
- Don't assume "no results" means privacy settings — it often means it's a phone number, not a username
- Don't stop at the first layer of data (Spokeo initials) — follow up with multi-source enrichment