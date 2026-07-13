---
title: "Memento Flashcards — Spaced-repetition flashcard system"
sidebar_label: "Memento Flashcards"
description: "Spaced-repetition flashcard system"
---

{/* This page is auto-generated from the skill's SKILL.md by website/scripts/generate-skill-docs.py. Edit the source SKILL.md, not this page. */}

# Memento Flashcards

Spaced-repetition flashcard system. Create cards from facts or text, chat with flashcards using free-text answers graded by the agent, generate quizzes from YouTube transcripts, review due cards with adaptive scheduling, and export/import decks as CSV.

## Skill metadata

| | |
|---|---|
| Source | Optional — install with `hermes skills install official/productivity/memento-flashcards` |
| Path | `optional-skills/productivity/memento-flashcards` |
| Version | `1.0.0` |
| Author | Memento AI |
| License | MIT |
| Platforms | macos, linux |
| Tags | `Education`, `Flashcards`, `Spaced Repetition`, `Learning`, `Quiz`, `YouTube` |

## Reference: full SKILL.md

:::info
The following is the complete skill definition that Hermes loads when this skill is triggered. This is what the agent sees as instructions when the skill is active.
:::

# Memento Flashcards — Spaced-Repetition Flashcard Skill

## Overview

Memento gives you a local, file-based flashcard system with spaced-repetition scheduling.
Users can chat with their flashcards by answering in free text and having the agent grade the response before scheduling the next review.
Use it whenever the user wants to:

- **Remember a fact** — turn any statement into a Q/A flashcard
- **Study with spaced repetition** — review due cards with adaptive intervals and agent-graded free-text answers
- **Quiz from a YouTube video** — fetch a transcript and generate a 5-question quiz
- **Manage decks** — organise cards into collections, export/import CSV

All card data lives in a single JSON file. No external API keys are required — you (the agent) generate flashcard content and quiz questions directly.

User-facing response style for Memento Flashcards:
- Use plain text only. Do not use Markdown formatting in replies to the user.
- Keep review and quiz feedback brief and neutral. Avoid extra praise, pep, or long explanations.

## When to Use

Use this skill when the user wants to:
- Save facts as flashcards for later review
- Review due cards with spaced repetition
- Generate a quiz from a YouTube video transcript
- Import, export, inspect, or delete flashcard data

Do not use this skill for general Q&A, coding help, or non-memory tasks.

## Quick Reference

| User intent | Action |
|---|---|
| "Remember that X" / "save this as a flashcard" | Generate a Q/A card, call `memento_cards.py add` |
| Sends a fact without mentioning flashcards | Ask "Want me to save this as a Memento flashcard?" — only create if confirmed |
| "Create a flashcard" | Ask for Q, A, collection; call `memento_cards.py add` |
| "Review my cards" | Call `memento_cards.py due`, present cards one-by-one |
| "Quiz me on [YouTube URL]" | Call `youtube_quiz.py fetch VIDEO_ID`, generate 5 questions, call `memento_cards.py add-quiz` |
| "Export my cards" | Call `memento_cards.py export --output PATH` |
| "Import cards from CSV" | Call `memento_cards.py import --file PATH --collection NAME` |
| "Show my stats" | Call `memento_cards.py stats` |
| "Delete a card" | Call `memento_cards.py delete --id ID` |
| "Delete a collection" | Call `memento_cards.py delete-collection --collection NAME` |

## Card Storage

Cards are stored in a JSON file at:

```
~/.hermes/skills/productivity/memento-flashcards/data/cards.json
```

**Never edit this file directly.** Always use `memento_cards.py` subcommands. The script handles atomic writes (write to temp file, then rename) to prevent corruption.

The file is created automatically on first use.

## Procedure

### Creating Cards from Facts

### Activation Rules

Not every factual statement should become a flashcard. Use this three-tier check:

1. **Explicit intent** — the user mentions "memento", "flashcard", "remember this", "save this card", "add a card", or similar phrasing that clearly requests a flashcard → **create the card directly**, no confirmation needed.
2. **Implicit intent** — the user sends a factual statement without mentioning flashcards (e.g. "The speed of light is 299,792 km/s") → **ask first**: "Want me to save this as a Memento flashcard?" Only create the card if the user confirms.
3. **No intent** — the message is a coding task, a question, instructions, normal conversation, or anything that is clearly not a fact to memorize → **do NOT activate this skill at all**. Let other skills or default behavior handle it.

When activation is confirmed (tier 1 directly, tier 2 after confirmation), generate a flashcard:

**Step 1:** Turn the statement into a Q/A pair. Use this format internally:

```
Turn the factual statement into a front-back pair.
Return exactly two lines:
Q: <question text>
A: <answer text>

Statement: "{statement}"
```

Rules:
- The question should test recall of the key fact
- The answer should be concise and direct

**Step 2:** Call the script to store the card:

```bash
python3 ~/.hermes/skills/productivity/memento-flashcards/scripts/memento_cards.py add \
  --question "What year did World War 2 end?" \
  --answer "1945" \
  --collection "History"
```

If the user doesn't specify a collection, use `"General"` as the default.

The script outputs JSON confirming the created card.

### Manual Card Creation

When the user explicitly asks to create a flashcard, ask them for:
1. The question (front of card)
2. The answer (back of card)
3. The collection name (optional — default to `"General"`)

Then call `memento_cards.py add` as above.

### Reviewing Due Cards

Fetch due cards with `memento_cards.py due` (optionally `--collection NAME`).
Full free-text grading procedure — the exact interaction pattern, grading
rubric, feedback wording, and the spaced-repetition interval table — is
mandatory reading before your first review turn: `references/review-flow.md`.

### YouTube Quiz Generation

Fetch the transcript with `youtube_quiz.py fetch VIDEO_ID`, then generate and
store 5 questions. Full procedure — video-ID extraction, the exact
quiz-generation prompt, validation, storage, and per-question presentation
flow — read before running a quiz: `references/youtube-quiz.md`.

### Export/Import CSV & Statistics

`memento_cards.py export --output PATH`, `import --file PATH --collection NAME`,
and `stats` cover data management. Full column formats, JSON stats shape,
known pitfalls (transcript failures, missing deps, video-ID formats), and
verification commands: `references/data-management.md`.
