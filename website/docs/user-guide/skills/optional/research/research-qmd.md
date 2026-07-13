---
title: "Qmd"
sidebar_label: "Qmd"
description: "Search personal knowledge bases, notes, docs, and meeting transcripts locally using qmd — a hybrid retrieval engine with BM25, vector search, and LLM reranking"
---

{/* This page is auto-generated from the skill's SKILL.md by website/scripts/generate-skill-docs.py. Edit the source SKILL.md, not this page. */}

# Qmd

Search personal knowledge bases, notes, docs, and meeting transcripts locally using qmd — a hybrid retrieval engine with BM25, vector search, and LLM reranking. Supports CLI and MCP integration.

## Skill metadata

| | |
|---|---|
| Source | Optional — install with `hermes skills install official/research/qmd` |
| Path | `optional-skills/research/qmd` |
| Version | `1.0.0` |
| Author | Hermes Agent + Teknium |
| License | MIT |
| Platforms | macos, linux |
| Tags | `Search`, `Knowledge-Base`, `RAG`, `Notes`, `MCP`, `Local-AI` |
| Related skills | [`obsidian`](/docs/user-guide/skills/bundled/note-taking/note-taking-obsidian), `native-mcp`, [`arxiv`](/docs/user-guide/skills/bundled/research/research-arxiv) |

## Reference: full SKILL.md

:::info
The following is the complete skill definition that Hermes loads when this skill is triggered. This is what the agent sees as instructions when the skill is active.
:::

# QMD — Query Markup Documents

Local, on-device search engine for personal knowledge bases. Indexes markdown
notes, meeting transcripts, documentation, and any text-based files, then
provides hybrid search combining keyword matching, semantic understanding, and
LLM-powered reranking — all running locally with no cloud dependencies.

Created by [Tobi Lütke](https://github.com/tobi/qmd). MIT licensed.

## When to Use

- User asks to search their notes, docs, knowledge base, or meeting transcripts
- User wants to find something across a large collection of markdown/text files
- User wants semantic search ("find notes about X concept") not just keyword grep
- User has already set up qmd collections and wants to query them
- User asks to set up a local knowledge base or document search system
- Keywords: "search my notes", "find in my docs", "knowledge base", "qmd"

## Prerequisites

### Node.js >= 22 (required)

```bash
# Check version
node --version  # must be >= 22

# macOS — install or upgrade via Homebrew
brew install node@22

# Linux — use NodeSource or nvm
curl -fsSL https://deb.nodesource.com/setup_22.x | sudo -E bash -
sudo apt-get install -y nodejs
# or with nvm:
nvm install 22 && nvm use 22
```

### SQLite with Extension Support (macOS only)

macOS system SQLite lacks extension loading. Install via Homebrew:

```bash
brew install sqlite
```

### Install qmd

```bash
npm install -g @tobilu/qmd
# or with Bun:
bun install -g @tobilu/qmd
```

First run auto-downloads 3 local GGUF models (~2GB total):

| Model | Purpose | Size |
|-------|---------|------|
| embeddinggemma-300M-Q8_0 | Vector embeddings | ~300MB |
| qwen3-reranker-0.6b-q8_0 | Result reranking | ~640MB |
| qmd-query-expansion-1.7B | Query expansion | ~1.1GB |

### Verify Installation

```bash
qmd --version
qmd status
```

## Quick Reference

| Command | What It Does | Speed |
|---------|-------------|-------|
| `qmd search "query"` | BM25 keyword search (no models) | ~0.2s |
| `qmd vsearch "query"` | Semantic vector search (1 model) | ~3s |
| `qmd query "query"` | Hybrid + reranking (all 3 models) | ~2-3s warm, ~19s cold |
| `qmd get <docid>` | Retrieve full document content | instant |
| `qmd multi-get "glob"` | Retrieve multiple files | instant |
| `qmd collection add <path> --name <n>` | Add a directory as a collection | instant |
| `qmd context add <path> "description"` | Add context metadata to improve retrieval | instant |
| `qmd embed` | Generate/update vector embeddings | varies |
| `qmd status` | Show index health and collection info | instant |
| `qmd mcp` | Start MCP server (stdio) | persistent |
| `qmd mcp --http --daemon` | Start MCP server (HTTP, warm models) | persistent |

## Setup Workflow

### 1. Add Collections

Point qmd at directories containing your documents:

```bash
# Add a notes directory
qmd collection add ~/notes --name notes

# Add project docs
qmd collection add ~/projects/myproject/docs --name project-docs

# Add meeting transcripts
qmd collection add ~/meetings --name meetings

# List all collections
qmd collection list
```

### 2. Add Context Descriptions

Context metadata helps the search engine understand what each collection
contains. This significantly improves retrieval quality:

```bash
qmd context add qmd://notes "Personal notes, ideas, and journal entries"
qmd context add qmd://project-docs "Technical documentation for the main project"
qmd context add qmd://meetings "Meeting transcripts and action items from team syncs"
```

### 3. Generate Embeddings

```bash
qmd embed
```

This processes all documents in all collections and generates vector
embeddings. Re-run after adding new documents or collections.

### 4. Verify

```bash
qmd status   # shows index health, collection stats, model info
```

## Search Patterns

Three basic modes: `qmd search "..."` (BM25 keyword, instant, no models),
`qmd vsearch "..."` (semantic vector, ~3s), `qmd query "..."` (hybrid +
reranking, best quality). Scope any of them with `--collection NAME`.

Detailed query syntax (lex/BM25 operators, structured multi-mode queries,
HyDE, output formats, CLI-without-MCP usage) and how the ranking pipeline
works internally (query expansion → RRF fusion → LLM reranking →
position-aware blending): read `references/search-patterns.md` before
tuning a query that isn't returning good results.

## MCP Integration (Recommended)

qmd exposes an MCP server (`mcp_qmd_search`, `mcp_qmd_vsearch`,
`mcp_qmd_deep_search`, `mcp_qmd_get`, `mcp_qmd_status`) so the agent gets
native tools without loading this skill each time — the preferred setup over
calling the CLI via `terminal`. Full stdio-vs-HTTP-daemon config, launchd/
systemd daemon persistence, and the structured JSON query shape: read
`references/mcp-setup.md` before configuring `mcp_servers` in
`~/.hermes/config.yaml`.

## Best Practices

1. **Always add context descriptions** — `qmd context add` dramatically
   improves retrieval accuracy. Describe what each collection contains.
2. **Re-embed after adding documents** — `qmd embed` must be re-run when
   new files are added to collections.
3. **Use `qmd search` for speed** — when you need fast keyword lookup
   (code identifiers, exact names), BM25 is instant and needs no models.
4. **Use `qmd query` for quality** — when the question is conceptual or
   the user needs the best possible results, use hybrid search.
5. **Prefer MCP integration** — once configured, the agent gets native
   tools without needing to load this skill each time.
6. **Daemon mode for frequent users** — if the user searches their
   knowledge base regularly, recommend the HTTP daemon setup.
7. **First query in structured search gets 2x weight** — put the most
   important/certain query first when combining lex and vec.

## Troubleshooting & Data Storage

Index/vectors live at `~/.cache/qmd/index.sqlite`; everything runs locally,
no cloud dependencies. Fixes for cold-start latency, "unable to load
extension" on macOS, "No collections found", and multilingual embedding
overrides: read `references/troubleshooting.md` when a qmd command fails or
behaves unexpectedly. It also links the upstream GitHub repo and changelog.
