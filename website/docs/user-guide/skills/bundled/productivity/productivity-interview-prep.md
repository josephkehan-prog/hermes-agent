---
title: "Interview Prep"
sidebar_label: "Interview Prep"
description: "Prepare for a teaching-role interview from a specific job posting — generate likely behavioral, pedagogy, and demo-lesson questions, scaffold STAR answers, a..."
---

{/* This page is auto-generated from the skill's SKILL.md by website/scripts/generate-skill-docs.py. Edit the source SKILL.md, not this page. */}

# Interview Prep

Prepare for a teaching-role interview from a specific job posting — generate likely behavioral, pedagogy, and demo-lesson questions, scaffold STAR answers, and produce a one-page cheat sheet. No cloud API.

## Skill metadata

| | |
|---|---|
| Source | Bundled (installed by default) |
| Path | `skills/productivity/interview-prep` |
| Version | `1.0.0` |
| Author | Hermes Agent |
| License | MIT |
| Platforms | linux, macos, windows |
| Tags | `interview-prep`, `job-search`, `career`, `teaching`, `star-method` |
| Related skills | [`job-search-tracking`](/docs/user-guide/skills/bundled/productivity/productivity-job-search-tracking), [`resume-tailor`](/docs/user-guide/skills/bundled/productivity/productivity-resume-tailor), [`cover-letter`](/docs/user-guide/skills/bundled/productivity/productivity-cover-letter) |

## Reference: full SKILL.md

:::info
The following is the complete skill definition that Hermes loads when this skill is triggered. This is what the agent sees as instructions when the skill is active.
:::

# Interview Prep

Turn a job posting into a one-page prep sheet: likely questions,
STAR-scaffolded answers, and a few questions to ask the interviewer.

## When to Use

User has an interview/phone screen scheduled, or asks "what will they ask
me" for a specific posting. Needs: the posting text, the user's resume or
relevant experience notes, and optionally the interview format if known.

## Procedure

### 1. Generate likely questions

Read the posting and produce 3 categories, 3-4 questions each:

- **Behavioral** — from responsibilities/requirements in the posting (e.g.
  "Tell me about a time you managed a difficult classroom situation.")
- **Pedagogy** — teaching-philosophy questions tied to the subject/grade
  band in the posting (e.g. "How do you differentiate instruction for a
  mixed-level virtual classroom?")
- **Demo-lesson** — only if the posting mentions a teaching demo; otherwise
  ask about lesson design instead (objectives, assessment, remote pacing).

### 2. Scaffold STAR answers

For each behavioral/pedagogy question, build a fill-in scaffold from the
user's actual experience — never invent specifics:

```
Q: <question>
S: <1 sentence, where/when — from user's background>
T: <1 sentence, what was required>
A: <2-3 sentences, what the user specifically did>
R: <1 sentence, outcome — real number only if the user gave one>
```

If detail is missing, write `[ASK USER: ...]` rather than guessing.

### 3. Questions to ask the interviewer

Generate 3-4 genuine questions sourced from gaps or specifics in the
posting (e.g. curriculum used, caseload size for virtual roles, evaluation
cadence). Avoid generic questions answerable by the posting itself.

## Output Format (one-page cheat sheet)

```markdown
# Interview Prep: <Role> at <Org>

## Quick Facts
- Cert required: <yes/no, which>
- Format: <phone screen / panel / demo lesson / unknown>

## Behavioral Questions
1. <question> — STAR: S/T/A/R one-liners

## Pedagogy Questions
1. <question> — STAR: S/T/A/R one-liners

## Demo-Lesson Notes (if applicable)
- <objective/pacing/assessment reminders>

## Questions to Ask Them
1. <question>
```

Keep the sheet to roughly one page — trim to the strongest 3-4 items per section.

## Related Skills

- `resume-tailor` — reuse the keyword extraction to decide likely questions.
- `cover-letter` — reuse org-specific research already gathered.
- `job-search-tracking` — after prep, `job_tracker.py update` status to `interview`.
