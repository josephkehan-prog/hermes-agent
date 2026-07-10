---
name: resume-tailor
description: Tailor a base resume to a specific job posting — extract required keywords, map them to the user's existing experience, and produce edited bullet points. No cloud API, no paid resume tools.
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [resume, job-search, career, teaching, keywords]
    category: productivity
    requires_toolsets: [terminal]
    related_skills: [job-search-tracking, cover-letter, interview-prep]
---

# Resume Tailor

Rewrite resume bullets to match one job posting at a time. Work from the
user's base resume text — never invent experience, certifications, or
numbers that aren't already in it.

## When to Use

- User pastes/points to a job posting and asks to tailor their resume.
- User asks "does my resume match this posting" or "what should I change."

## Inputs Needed

Ask for these if not already provided:
1. Base resume text (or path to a file).
2. The job posting text (or URL contents already fetched).

## Procedure

1. **Extract keywords from the posting.** Read it and list, verbatim where
   possible:
   - Required certifications (e.g. NYS teaching cert, subject endorsement)
   - Subject/grade level (e.g. "grades 6-8 math", "virtual instruction")
   - Required skills/tools (e.g. Google Classroom, IEP experience, LMS name)
   - Repeated phrases or buzzwords (e.g. "differentiated instruction",
     "data-driven", "asynchronous")

2. **Map each keyword to existing experience.** Build a simple table:
   `keyword -> resume bullet or experience it matches (or "no match")`.
   Do not fabricate a match — if nothing in the base resume supports a
   keyword, mark it `no match` and skip it rather than inventing a claim.

3. **Rewrite matched bullets.** For each bullet with a match, edit it to:
   - Start with a strong action verb
   - Include the keyword or a close synonym naturally
   - Keep any existing quantifiable result (students taught, score gains,
     class size) — never add a number that wasn't in the original
   - Stay one line, ~15-25 words

4. **Reorder.** Put the most-relevant-to-this-posting bullets first within
   each job entry. Don't reorder job entries themselves (chronology stays).

5. **Checklist before finalizing:**
   - [ ] Every rewritten bullet still true to the original experience
   - [ ] No invented certifications, tools, or numbers
   - [ ] Top 3 posting keywords each appear at least once
   - [ ] No bullet exceeds ~25 words
   - [ ] Resume still fits original length (don't grow it)

## Output Format

```markdown
## Keyword Match Table
| Keyword | Matched Experience | Status |
|---|---|---|

## Tailored Bullets
### <Job Title, Employer>
- <original bullet>  ->  <tailored bullet>

## Unmatched Requirements (flag to user)
- <requirement with no match in base resume>
```

## Related Skills

- `job-search-tracking` — after tailoring, log the application
  (`job_tracker.py add ...`) with the posting URL and note "resume tailored".
- `cover-letter` — draft the matching cover letter using the same keyword
  extraction from step 1.
- `interview-prep` — reuse the posting to generate likely interview questions.
