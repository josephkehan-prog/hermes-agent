---
title: "Cover Letter"
sidebar_label: "Cover Letter"
description: "Draft a structured, 4-paragraph cover letter for a specific job posting — hook, fit evidence, org-specific detail, close"
---

{/* This page is auto-generated from the skill's SKILL.md by website/scripts/generate-skill-docs.py. Edit the source SKILL.md, not this page. */}

# Cover Letter

Draft a structured, 4-paragraph cover letter for a specific job posting — hook, fit evidence, org-specific detail, close. Tuned for teaching roles and for small local models that need explicit step-by-step instructions.

## Skill metadata

| | |
|---|---|
| Source | Bundled (installed by default) |
| Path | `skills/productivity/cover-letter` |
| Version | `1.0.0` |
| Author | Hermes Agent |
| License | MIT |
| Platforms | linux, macos, windows |
| Tags | `cover-letter`, `job-search`, `career`, `teaching`, `writing` |
| Related skills | [`job-search-tracking`](/docs/user-guide/skills/bundled/productivity/productivity-job-search-tracking), [`resume-tailor`](/docs/user-guide/skills/bundled/productivity/productivity-resume-tailor), [`interview-prep`](/docs/user-guide/skills/bundled/productivity/productivity-interview-prep) |

## Reference: full SKILL.md

:::info
The following is the complete skill definition that Hermes loads when this skill is triggered. This is what the agent sees as instructions when the skill is active.
:::

# Cover Letter

Write one letter per posting. Follow the 4-paragraph template exactly, in
order. Do not skip a paragraph or merge two together.

## When to Use

User asks for a cover letter for a specific job posting, or to revise/shorten
an existing one.

## Inputs Needed

The job posting text (org name, role, requirements), the user's resume or a
short list of relevant experience, and optionally anything specific the
user wants mentioned.

## The 4-Paragraph Template

Write each paragraph as its own block, 3-5 sentences, ~350-400 words total.

**Paragraph 1 — Hook.** Name the role and org in the first sentence, plus
one sentence on why this specific role/org — not a generic "I am excited
to apply."

**Paragraph 2 — Fit evidence.** Pick the 2-3 strongest matches between the
posting's requirements and the user's actual experience (reuse the
keyword mapping from `resume-tailor` if already done). State each as:
what you did + the result. No unverified numbers or claims not in the resume.

**Paragraph 3 — Org-specific detail.** Reference one concrete, real detail
about the school/org (mission line, program name, grade band, curriculum
framework mentioned in the posting). If no such detail exists, tell the
user instead of inventing one.

**Paragraph 4 — Close.** Restate interest in one sentence, state
certification/availability if relevant ("NYS certified, available for
remote instruction"), and a plain call to action. No "please find
attached" filler.

## Rules for Teaching-Role Letters

- State certification status plainly if the posting requires one (NYS
  cert, subject endorsement) — don't bury it.
- If the role is remote, say so explicitly; if the user has no virtual
  experience, write "eager to bring in-person practice to a virtual
  setting" instead of skipping the topic.
- Avoid jargon clichés ("passionate about student success") unless
  followed by a concrete example. Never claim results not in the resume.

## Tone Guidance (for small local models)

- Plain, direct sentences. One idea per sentence. No nested clauses.
- Use periods, not em dashes or semicolons.
- After drafting, re-check paragraph 3: confirm the detail it references
  actually appears in the posting text. If not, remove or flag it.

## Output Format

```markdown
Dear <Hiring Manager / named contact>,

<Paragraph 1 - hook>
<Paragraph 2 - fit evidence>
<Paragraph 3 - org-specific detail>
<Paragraph 4 - close>

Sincerely,
<User's name>
```

## Related Skills

- `resume-tailor` — run first for the keyword-to-experience mapping used in paragraph 2.
- `job-search-tracking` — log the application once the letter is sent.
- `interview-prep` — reuse org-specific research from paragraph 3.
