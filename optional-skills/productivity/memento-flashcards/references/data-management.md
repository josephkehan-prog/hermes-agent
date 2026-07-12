# Data Management, Pitfalls & Verification

Read this before an export/import/stats request, or when debugging an
unexpected script failure.

## Export/Import CSV

**Export:**
```bash
python3 ~/.hermes/skills/productivity/memento-flashcards/scripts/memento_cards.py export \
  --output ~/flashcards.csv
```

Produces a 3-column CSV: `question,answer,collection` (no header row).

**Import:**
```bash
python3 ~/.hermes/skills/productivity/memento-flashcards/scripts/memento_cards.py import \
  --file ~/flashcards.csv \
  --collection "Imported"
```

Reads a CSV with columns: question, answer, and optionally collection (column 3). If the collection column is missing, uses the `--collection` argument.

## Statistics

```bash
python3 ~/.hermes/skills/productivity/memento-flashcards/scripts/memento_cards.py stats
```

Returns JSON with:
- `total`: total card count
- `learning`: cards in active rotation
- `retired`: mastered cards
- `due_now`: cards due for review right now
- `collections`: breakdown by collection name

## Pitfalls

- **Never edit `cards.json` directly** — always use the script subcommands to avoid corruption
- **Transcript failures** — some YouTube videos have no English transcript or have transcripts disabled; inform the user and suggest another video
- **Optional dependency** — `youtube_quiz.py` needs `youtube-transcript-api`; if missing, tell the user to run `pip install youtube-transcript-api`
- **Large imports** — CSV imports with thousands of rows work fine but the JSON output may be verbose; summarize the result for the user
- **Video ID extraction** — support both `youtube.com/watch?v=ID` and `youtu.be/ID` URL formats

## Verification

Verify the helper scripts directly:

```bash
python3 ~/.hermes/skills/productivity/memento-flashcards/scripts/memento_cards.py stats
python3 ~/.hermes/skills/productivity/memento-flashcards/scripts/memento_cards.py add --question "Capital of France?" --answer "Paris" --collection "General"
python3 ~/.hermes/skills/productivity/memento-flashcards/scripts/memento_cards.py due
```

If you are testing from the repo checkout, run:

```bash
pytest tests/skills/test_memento_cards.py tests/skills/test_youtube_quiz.py -q
```

Agent-level verification:
- Start a review and confirm feedback is plain text, brief, and always includes the correct answer before the next card
- Run a YouTube quiz flow and confirm each answer receives visible feedback before the next question
