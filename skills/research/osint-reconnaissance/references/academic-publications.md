# Academic/Publications Layer — Session Detail

## What We Found (Hugh Gleysteen, July 2026)

### USD English Dept Newsletter PDFs

**Sources:**
- `catcher.sandiego.edu/items/cas/engl_dept_newsletter_5-4-23.pdf` — April 2023
- `catcher.sandiego.edu/items/cas/engl_dept_newsletter_5-24-23.pdf` — May 2023

**Revealed details:**
- **Major:** English with Creative Writing emphasis
- **Faculty mentor:** Prof. Kathryn Statler (History dept)
- **Thesis/presentation title:** *"Momentum and Emotion: Rhetorical use of Subliminal Feelings in Narrative Histories"* — presented at Alcalá Review, May 2023
- **Military service:** "In September, he will be going to Quantico, Virginia to attend the Marine Officer Candidate Course" (from Sept 2023 newsletter)
- **Creative Writing Reading:** Cropper Center for Creative Writing Student Reading, April 2023
- **Personal anecdotes:** favorite book is *Moby Dick* ("all the characters are literally him IRL"), embarrasses himself less at dinner parties after being an English major
- **Hobbies:** hiking, camping, attending concerts (from athletics bio)
- **Family:** "Son of Rod and Mary Gleysteen"

### USD Honors Convocation PDF

**Source:** `catcher.sandiego.edu/items/usd/CAS-24-Honors-Convocation-Program_single-pages_web.pdf` — May 2024

**Revealed details:**
- **Graduation year:** Class of 2024, Honors Program graduate
- **Full name with middle initial:** "Hugh T. Gleysteen" (in the honors convocation program listing)
- **Scholastic achievement awards listed by department**

### Athletics Roster (USD Toreros)

**Source:** `usdtoreros.com/sports/mens-rowing/roster/hugh-gleysteen/10704`

**Revealed details:**
- Height: 6'1"
- Position in crew: Bow (in 8+)
- Years active: 2019–2023+
- High school: Garfield HS, Seattle, WA
- Club: Mount Baker Crew (2014–2019) — Lake Washington
- Family: "Son of Rod and Mary Gleysteen"

## Pattern: University PDFs as Intelligence Sources

University departmental newsletters/announcements often contain richer personal details than social profiles because they're written for a close-knit community audience. Look for:

1. **Thesis/presentation titles** — reveals academic focus, mentors
2. **Student readings/performances** — reveals creative work, participants
3. **Military service announcements** — reveals OCS attendance, commissioning timing
4. **Hobbies/anecdotes** — reveals personal details (favorite books, camp backgrounds)
5. **Family info** — parents' names, siblings
6. **Scholastic awards** — AP Scholar, honors program graduates

## Key Sites to Check

| Site | Content Type | Example Query |
|------|--------------|---------------|
| `site:sandiego.edu` | University PDFs (catcher.sandiego.edu) | `"Hugh Gleysteen" English dept newsletter` |
| `site:nyu.edu` | Student publications, announcements | `"Name" department newsletter` |
| `site:stanford.edu` | Academic publications, research week | `"Name" honors convocation` |
| `site:ncaa.com` | Collegiate athletes | `"Name" team roster` |
| `site:<university>.edu` | Athletics rosters (Sidearm Sports) | `"Name" men's rowing roster` |

## Pitfall: PDF Loading

University PDFs may load slowly or as embedded iframes in the browser. Use `browser_snapshot(full=true)` to extract text, or navigate directly and wait for full load before capturing.

## Signal to Pivot Early

If social media returns nothing and athletics is the only public profile → immediately query `site:<university>` for the target's institution — PDFs from university repos often contain richer details than LinkedIn profiles. This was the key pivot in the Hugh Gleysteen investigation: the English dept newsletter revealed Marine OCS attendance, major, hobbies, and family info that social media never surfaced.

---

## Yearbook PDFs — High-Value Deep Source

University yearbook PDFs are a distinct category of institutional data that reveals identity patterns beyond LinkedIn or newsletters:

### Breonnie Ford (Lehman College Class of 2024)

**Source:** `lehman.edu/media/Lehman-College-Website/classof2024/documents/Classof2024Yearbook_compressed.pdf`

**Revealed details:**
- **Major with emphasis:** Psychology, BA — Early childhood (not just "Psychology" but the specific career trajectory)
- **Personal quote/motto:** *"A sweet ending to a new beginning."*
- **Age signal:** Yearbook bio states "22.", graduation cohort marker "AA' 24" (August 2024) — birth-year estimate ~2002
- **Associated names:** Kiemara Francis, Jocelyn T. Freire listed in same yearbook entry — social network signals
- **Photo reference:** Profile photo embedded in PDF for visual identity verification

### Extraction Technique

Yearbook PDFs are typically hosted at: `site:<university>.edu/media/.../classofYYYY/documents/ClassofYYYYYearbook_compressed.pdf` or similar paths. Use `web_extract` on the URL; if PDF is too large (>100K chars), use `read_file` with pagination on the extracted markdown — yearbooks commonly exceed 100K chars and truncate on line boundaries.

Search for target's name in extracted content — entries are typically grouped by major/program, so extract surrounding context (major, quote, age) to confirm it's the right person, not just a name match.