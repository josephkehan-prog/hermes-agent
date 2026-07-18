---
name: multi-source-investigation
description: |
  Multi-domain investigative framework for professional identity verification, supply chain forensics,
  and cross-platform data triangulation. Supports evidence-backed reporting across healthcare, tech, finance,
  and government databases with systematic hypothesis formation and validation protocols.
platforms: [linux, macos, windows]
category: research
triggers:
  - "investigate professional identity"
  - "verify practitioner credentials [name + identifier]"
  - "multi-database triangulation research"
  - "comprehensive forensic analysis of"
  - "intelligence gathering on"
  - "structured investigation with evidence validation"
  - "cross-platform verification for"
toolsets:
  - terminal
  - web
  - file
  - delegation
---

# Multi-Source Investigation Framework

A systematic investigative framework supporting diverse inquiry types including professional identity verification, 
supply chain forensics, cross-referenced intelligence gathering, and evidence-backed reporting. This skill adapts to 
multiple investigation domains while maintaining rigorous anti-hallucination standards throughout the process.

**Core Domains**: Healthcare provider systems | Open-source software supply chains | Professional credentialing 
| Cross-platform identity research

---

## ⚠️ Anti-Hallucination Guardrails

These protocols are mandatory for all investigations. Violation of these principles compromises report integrity.

1. **Evidence-First Rule**: Every factual claim MUST cite at least one evidence identifier (`EV-XXXX`). Unreferenced assertions are not permitted in final reports.

2. **Multi-Source Verification Standard**: Critical identifiers (NPI numbers, license credentials, professional IDs) must be confirmed from at least two independent sources before stating as verified fact.

3. **Fact vs. Hypothesis Separation**: All inferences require explicit `[HYPOTHESIS]` marking. Only data directly sourced and validated may be stated as established fact.

4. **No Evidence Fabrication**: Hypothesis validation requires mechanical verification that every cited evidence ID actually exists in the investigation record. Missing IDs constitute automatic rejection criteria.

5. **Alternative Explanation Protocol**: Dismissing a hypothesis requires specific, evidence-backed counter-argumentation. Absence of confirming evidence alone renders findings `[INCONCLUSIVE]`, not disproven.

6. **Identifier Double-Verification**: Any professional credential number, URL, or database identifier must be independently confirmed across 2+ sources before marked as verified.

7. **Geographic-Professional Correlation**: Location claims should correlate with known service areas of identified databases and regulatory authorities when applicable.

8. **Audit Trail Integrity**: All investigation artifacts (IOC registries, evidence stores, reports) must maintain timestamps and source attribution for complete reproducibility.

---

## Phase 0: Investigation Initialization

### 1. Establish Working Directory Structure

```bash
# Create organized workspace with date-stamped directory
mkdir -p ~/mac/Hermes/investigation_[TARGET_ID]_$(date +%Y%m%d)
cd investigation_[TARGET_ID]_$(date +%Y%m%d)

# Initialize core files
touch iocs.md evidence-store.json investigation-report.md chain-of-custody.log
```

**Working Directory Convention**: All session output defaults to `/Users/josephhan/mac/Hermes/investigation_<target-identifier>` for cross-session continuity and organized archival.

### 2. Capture Investigation Meta-Data

Record in `chain-of-custody.log`:
- Investigation start timestamp (ISO format)
- Target identifier(s): Name, professional credentials, contact identifiers
- Primary investigation goals and scope boundaries
- Data sources identified for triangulation
- Agent session ID for reproducibility tracking

### 3. Establish IOC Registry Template

Initialize `iocs.md` with structure supporting:
```markdown
# Indicators of Interest (IOIs) - Investigation [TARGET_ID]

## Target Identity Summary
- **Primary Name/Entity**: [Target]
- **Core Identifier(s)**: License/Credential numbers, phone contacts, professional IDs
- **Investigation Domain**: Professional identity | Supply chain | Cross-platform verification
- **Established Date**: ISO timestamp
```

---

## Pitfalls

### Don't assume a source is confirmed without navigating it yourself
When you see a URL (LinkedIn, The Knot, Instagram, etc.), actually navigate to it. `web_extract` only returns metadata/metadata snippets — the page content may reveal details that confirm or deny your claim. Two sessions ago: "The Knot only shows first names + last initial" was asserted without navigating; user had to do `/interupt Source`. The lesson: for interactive public records, prefer `browser_navigate` → `browser_snapshot`.

### Keep summary output lean
Don't append assessment paragraphs or extra commentary beyond the extracted facts. User said "Spruce" — meaning clean up verbosity. Output the data; skip the editorializing about what the person is like based on their LinkedIn activity.

### Don't deep-dive only one target when given multiple markers
When user provides a name plus a phone number or geo marker (e.g., "Nathan Downey; +1 (631) 992-8085"), treat them as the SAME target until confirmed otherwise — don't deep-dive LinkedIn first without cross-referencing. The phone number/geo marker is a stronger identity anchor than a LinkedIn URL. If the phone number points to Suffolk County NY but only LinkedIn found Seattle WA, escalate immediately: that's a different Nathan or deeper institutional data is needed. User said "Wrong Nathan focus on New York" — meaning stop at LinkedIn when geo doesn't match.

**Explicit Step in Phase 1**: Before launching parallel evidence collection, cross-reference all provided identifiers (name + phone + geo marker) against each other. If they point to different jurisdictions or institutions, flag as [INCONCLUSIVE] and prioritize deeper institutional data over shallow profile extraction.

---

## Pitfall: NY DOS API — Connection Reset

**Symptom:** All endpoints return `ERR_CONNECTION_RESET` or `net::ERR_NAME_NOT_RESOLVED`. This includes:
- `https://apps.dos.ny.gov/api/public/entity/search?q=downey+nathan&type=entity`
- `https://apps.dos.ny.gov/publicInquiry/`

**Cause:** NY DOS API was unreachable during investigation session (July 7, 2026). May be intermittent or rate-limited.

**Workaround:** Use the **Socrata Open Data mirror** at `https://data.ny.gov/api/views/n9v6-gdp6/rows.json` for bulk entity search by name. API accepts JSON queries with `search=%25downey%25&limit=100`. Returns structured data including:
- `current_entity_name`, `county`, `entity_type`
- `dos_process_name`, `registered_agent_name`

**Note:** Socrata mirror may also return 0 results — that's a valid result, not necessarily a blocker. The NY DOS API itself is authoritative; the mirror is convenience-only.

---

## Pitfall: Suffolk County Clerk — Cloudflare Bot Detection

**Symptom:** `Just a moment...` page with bot detection challenge. Blocks automated navigation.

**Cause:** Aggressive bot protection on government sites.

**Workaround:** Use alternative public records interfaces:
- `http://www.suffolk.nydeeds.com/` — CGI-based deed search (lighter, no bot detection)
- `https://opengovny.com/corporation?county=Suffolk&search=downey+nathan` — OpenGovNY mirror of NY DOS data

---

## Pitfall: NY Attorney Registry — Fully Accessible

**Status:** Fully accessible. Returns structured attorney registration data including:
- Registration number, full name, company, address, phone, law school, year admitted, status

**Note:** NY OCA registry is public per 22 NYCRR Part 118 and Uniform Rules of Trial Courts §468-a. All attorneys must file registration every two years (within 30 days after birthday).

---

## Phase 1: Prompt Parsing & IOC Extraction

**Goal**: Extract all investigative targets from user request and establish baseline indicators.

### Actions Required

Parse user prompt to identify:

#### Primary Identifiers
- Target name(s) and credential designations (DC, MD, PhD, etc.)
- Professional/numeric identifiers (license numbers, NPIs, employee IDs)
- Contact points: phone numbers with area codes, email addresses
- Geographic markers from provided data

#### Investigation Scope Elements
- Time windows of interest when applicable
- Professional domain or industry sector designation
- Cross-reference target platforms (healthcare databases, professional registries, etc.)
- Any user-supplied context notes on specific focus areas

### IOC Registry Output Format

Each Indicator requires:

| Field | Required Values | Example |
|-------|----------------|---------|
| **Type** | NAME, PROFESSIONAL_IDENTITY, CREDENTIAL_NUMBER, CONTACT_POINT, GEOGRAPHIC_MARKER, TIME_RANGE, PLATFORM_REFERENCE | `CREDENTIAL_NUMBER` |
| **Value** | The extracted identifier or marker text | `(305) 898-1022` |
| **Source Attributed to** | USER_PROVIDED, DATABASE_RETRIEVED, CROSS_REFERENCED, INFERRED_ANALYSIS | `USER_PROVIDED` |
| **Verification Status** | [VERIFIED], [INFERRED], [PENDING] | `[VERIFIED]` |

---

## Phase 2: Parallel Evidence Collection (Multi-Source Triangulation)

This phase employs targeted research across multiple independent platforms to validate and enrich primary IOCs.

### Database Research Strategy

**Primary Data Sources by Domain**:

#### Healthcare Provider Systems
| Database/Platform | Data Type | Access Method | Verification Value |
|-------------------|-----------|---------------|-------------------|
| **NPPES (Federal NPI Registry)** | Provider enumeration, practice locations, taxonomy codes | Public web extraction / API query | Federal-level authoritative record |
| **State Office of Professions** | Licensure status, registration history, disciplinary records | License verification portal navigation | State regulatory authority |
| **Healthcare Directories (WebMD, ShareCare)** | Patient-facing listings, ratings, service modalities | Platform profile extraction | Independent commercial databases |

#### Professional Identity (Cross-Domain)
| Database/Platform | Data Type | Access Method | Verification Value |
|-------------------|-----------|---------------|-------------------|
| **National Regulatory Databases** | Credentials, certifications, status records | Official verification portals | Government-issued authoritative data |
| **Professional Association Portals** | Member directories, practice areas | Membership/association websites | Professional community validation |
| **Commercial Intelligence Platforms** | Corporate affiliations, employment history | Business registry searches | Multi-entity relationship tracking |

### Parallel Execution Framework

Employ parallel queries across identified platforms where independence permits:

```bash
# Example concurrent research approach
# Query 1: NPPES database for provider record extraction
web_search("NPI number verification [ID]") OR web_extract(NPPES_provider_URL)

# Query 2: State license portal cross-reference  
browser_navigate(state_verification_portal + "profession/chiropractic/license/[LICENSE_NUMBER]") 

# Query 3: Commercial healthcare platform profile aggregation
web_search("[NAME] AND (WebMD OR ShareCare) provider directory")
```

### Evidence Collection Protocol

For each data source queried, capture:
- **Evidence ID** format: `EV-SOURCE_ACRONYM-SEQ`
  - Example: `EV-NPPES-001` for first NPPES record, `EV-WEBMD-003` for third WebMD dataset
- **Source Authority Name**: Full database/platform name with type designation
- **Critical Data Points Extracted**: Specific identifiers, dates, and verification markers
- **Consistency Flags**: Cross-source alignment indicators

---

## Phase 3: Evidence Consolidation & Geographic Intelligence Mapping

### Evidence Integration Framework

#### A. Chronological Timeline Construction

Organize all timestamped evidence into sequenced narrative revealing key milestones and status changes.

**Sequence Priority**: Registration/enumeration dates → Licensure actions → Practice establishment markers → Current operational status updates

#### B. Multi-Location Infrastructure Analysis

Where dual or multi-location practice/geographic patterns emerge:

1. **Primary Operating Site Documentation**
   - Physical address with coordinates/region designation  
   - Service scope at primary location
   - Patient/community accessibility considerations

2. **Secondary Location/Administrative Hub Mapping**
   - Geographic span analysis across service zones
   - Functional differentiation per location (patient-facing vs administrative)
   - Cross-regional coordination model indicators

3. **Professional Ecosystem Contextualization**
   - Co-location specialist density and types
   - Inter-disciplinary referral pathway potential
   - Community healthcare infrastructure assessment

---

## Phase 4: Hypothesis Formation & Validation Protocol

### Evidence-Backed Hypothesis Construction

Each hypothesis requires explicit structure:

```markdown
### [HYPOTHESIS H-NUMBER]: Brief Claim Statement

**Premise**: One to two sentence articulation of the proposed insight or inference pattern.

**Supporting Evidence Citations**: EV-XXXX, EV-YYYY with brief annotation on relevance per citation.

**Alternative Explanation Consideration**: What alternative patterns could generate similar evidence?

**Disconfirmation Criteria**: Specific indicators that would invalidate the hypothesis.
```

### Common Hypothesis Templates by Investigation Domain

#### Professional Identity Investigations
| Template ID | Pattern Focus | Evidence Requirements |
|-------------|--------------|---------------------|
| **HI-01** | Multi-State Operational Footprint | Confirmed physical locations in 2+ jurisdictions, dual contact channels with different geographic assignments |
| **HI-02** | Integrated Healthcare Ecosystem Positioning | Practice location within multi-specialty corridor, documented co-location network of complementary providers |
| **HI-03** | Contemporary Patient-Centered Service Model | Telehealth capability enabled, patient portal availability, satisfaction rating aggregation across platforms |

### Validation Protocol Steps

The validation phase executes systematic verification:

1. **Evidence ID Existence Verification**: Confirm all cited EV-XXXX identifiers appear in evidence registry
2. **Multi-Source Confirmation Check**: Validate that [VERIFIED] claims have ≥2 independent source confirmations  
3. **Temporal Coherence Analysis**: Verify chronology supports hypothesis narrative without contradictory sequence markers
4. **Geographic Consistency Review**: Ensure location patterns align with known professional service models and regulatory jurisdiction boundaries

**Validation Outcome Designators**:
- `VALIDATED` — All criteria met, evidence robust, no plausible alternative pattern identified
- `INCONCLUSIVE` — Evidence supports premise but alternative explanations exist or data gaps present  
- `REJECTED` — Missing foundational evidence IDs, logical inconsistencies detected, or single-source unverified claims

---

## Phase 5: Structured Report Synthesis

The final investigation report synthesizes all validated intelligence into professional-formatted output.

### Mandatory Sections Structure

#### Executive Summary
| Element | Content Standard |
|---------|-----------------|
| **Status Designation** | VERIFIED PROFESSIONAL PRESENCE / ESTABLISHED PRACTICE IDENTIFICATION / COMPREHENSIVE INTELLIGENCE ACHIEVED |
| Target Identifier Block | Name, credential designations, primary identifiers (NPI/License), contact points |
| Geographic Footprint Summary | Primary operating location(s) with service region scope |
| Confidence Assessment | HIGH/MEDIUM assessment based on evidence density and multi-source verification count |
| Key Verifications Listed | Achievement bullets summarizing major confirmations |

#### Evidence Registry Table
Complete enumeration of all EV-XXXX items with source authority, data type extracted, verification status designation.

#### Hypothesis Validation Summary
All hypotheses with assigned ID, premise statement, supporting evidence citations, validation outcome designator.

#### Chain of Custody Log
Sequential record documenting: investigation phases executed, toolsets employed per phase, data sources accessed, timestamps for each collection activity.

### Report Integrity Requirements

- **Citation Density Standard**: Every factual assertion contains at least one `[EV-XXXX]` reference
- **Verification Status Notation**: All findings carry explicit [VERIFIED], [INFERRED], or [ANALYZED] designation  
- **Confidence Level Declaration**: Executive summary states HIGH/MEDIUM/LOW confidence with rationale
- **Geographic Coordinate Mapping**: Practice locations include region identifiers and ecosystem context

---

## Phase 6: Investigation Completion & Knowledge Preservation

### Final Evidence Synthesis Actions

1. **Evidence Inventory Reconciliation** — Confirm all planned data sources accessed, gaps noted where applicable  
2. **Investigation Directory Archival** — Organize complete workspace for potential future reference or expansion  
3. **Intelligence Expansion Pathways Documentation** — Enumerate available next-phase research directions should deeper investigation be warranted

### Deliverable Output Structure

```
/Users/josephhan/mac/Hermes/investigation_[TARGET_ID]/
├── iocs.md                          # Indicators of Interest registry with extraction and validation status  
├── investigation-report.md          # Comprehensive forensic intelligence synthesis (primary deliverable)
└── personal-profile-[TARGET].md     # [OPTIONAL] Extended professional/personal attributes deep-dive analysis
```

---

## Investigation Methodology Notes

### Anti-Hallucination Framework Active
- All claims mapped to EV-XXXX evidence identifiers with source authority attribution
- Geographic and operational infrastructure confirmed through convergent multi-source data triangulation  
- Patient engagement metrics sourced from healthcare platform aggregators where available

### Multi-Domain Adaptability
This methodology framework successfully deploys across diverse investigation types:
- **Healthcare Provider Investigation**: Federal/state database cross-reference, patient experience intelligence gathering  
- **Supply Chain Forensic Analysis**: Multi-platform repository and registry triangulation with evidence-backed findings  
- **Professional Credential Verification**: Regulatory authority validation, association membership confirmation, multi-database consistency checking

### Data Currency Consideration  
Provider enumeration and professional registration records should note enumeration/issuance date ranges when available to establish information currentcy context for the investigation period.

---

## Reference Support Materials (For Extended Deployments)

When investigations expand beyond baseline verification complexity:

**Support Documentation Options**:
- Detailed regulatory framework summaries per domain  
- Database-specific API and verification protocol reference guides  
- Professional association membership validation procedures  

These can be appended to the `references/` directory for reusable session access.

---

*Investigation Framework v1.0 — Multi-Sector Intelligence Gathering Protocol*