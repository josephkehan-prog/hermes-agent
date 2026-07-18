---
name: workspace-rag
description: Local semantic search over Hermes workspace notes.
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [macos]
metadata:
  hermes:
    tags: [RAG, sqlite-vec, Ollama, Embeddings, Local, Search, Memory]
    category: research
    requires_toolsets: [terminal, ollama]
    related_skills: [last30days, local-model-ops]
---

# Workspace RAG

Local semantic search over Hermes workspace text (memory notes, improvement
logs, docs). Single SQLite file with a `sqlite-vec` `vec0` table; embeddings
from local Ollama (`nomic-embed-text`, 768-dim). No server, no external API
calls, no `requests` dep (stdlib `urllib` only).

Promoted from the quarantined pilot at `~/mac/quarantine/sqlite-vec/`
(see `PILOT.md` there for the raw evaluation).

## One-time setup

```bash
cd /Users/josephhan/mac/Hermes/skills/research/workspace-rag
/Users/josephhan/mac/Hermes/bin/uv venv .venv
/Users/josephhan/mac/Hermes/bin/uv pip install --python .venv/bin/python sqlite-vec
```

Requires Ollama running locally with `nomic-embed-text` pulled
(`ollama pull nomic-embed-text` if missing; check with
`curl -s localhost:11434/api/tags`).

## Usage

Always invoke through the wrapper (uses skill venv python, not system):

```bash
workspace-rag index [path...]        # default: memories/ IMPROVEMENTS.md WORKSPACE.md
workspace-rag query "<question>" [-k N]
workspace-rag status
```

`index` walks each path, chunks `.md`/`.txt` files (~800 chars, paragraph
boundaries), embeds via Ollama, stores in
`/Users/josephhan/mac/Hermes/state/workspace-rag.db`. Unchanged files
(by mtime) are skipped.

`query` embeds the question, runs KNN, prints `[distance] path` + snippet
per result. Vectors are L2-normalized before insert so vec0's default L2
metric behaves as cosine distance (pilot's noted pitfall).

`status` prints file count, chunk count, DB size.

## Notes

- Ollama down → clear stderr message, exit code 1, no silent failures.
- Re-index after edits is cheap: only changed files re-embed.
- DB is WAL mode, single-writer; do not run concurrent `index` commands.
