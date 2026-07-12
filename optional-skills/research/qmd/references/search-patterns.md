# Search Patterns, Query Syntax & Pipeline Internals

Read this when a basic `qmd search`/`qmd query` isn't precise enough — e.g.
combining lex + vector modes, using HyDE, scoping to a collection, or when
you need to explain/tune why results rank the way they do.

## Fast Keyword Search (BM25)

Best for: exact terms, code identifiers, names, known phrases.
No models loaded — near-instant results.

```bash
qmd search "authentication middleware"
qmd search "handleError async"
```

## Semantic Vector Search

Best for: natural language questions, conceptual queries.
Loads embedding model (~3s first query).

```bash
qmd vsearch "how does the rate limiter handle burst traffic"
qmd vsearch "ideas for improving onboarding flow"
```

## Hybrid Search with Reranking (Best Quality)

Best for: important queries where quality matters most.
Uses all 3 models — query expansion, parallel BM25+vector, reranking.

```bash
qmd query "what decisions were made about the database migration"
```

## Structured Multi-Mode Queries

Combine different search types in a single query for precision:

```bash
# BM25 for exact term + vector for concept
qmd query $'lex: rate limiter\nvec: how does throttling work under load'

# With query expansion
qmd query $'expand: database migration plan\nlex: "schema change"'
```

## Query Syntax (lex/BM25 mode)

| Syntax | Effect | Example |
|--------|--------|---------|
| `term` | Prefix match | `perf` matches "performance" |
| `"phrase"` | Exact phrase | `"rate limiter"` |
| `-term` | Exclude term | `performance -sports` |

## HyDE (Hypothetical Document Embeddings)

For complex topics, write what you expect the answer to look like:

```bash
qmd query $'hyde: The migration plan involves three phases. First, we add the new columns without dropping the old ones. Then we backfill data. Finally we cut over and remove legacy columns.'
```

## Scoping to Collections

```bash
qmd search "query" --collection notes
qmd query "query" --collection project-docs
```

## Output Formats

```bash
qmd search "query" --json        # JSON output (best for parsing)
qmd search "query" --limit 5     # Limit results
qmd get "#abc123"                # Get by document ID
qmd get "path/to/file.md"       # Get by file path
qmd get "file.md:50" -l 100     # Get specific line range
qmd multi-get "journals/*.md" --json  # Batch retrieve by glob
```

## CLI Usage (Without MCP)

When MCP is not configured, use qmd directly via terminal:

```
terminal(command="qmd query 'what was decided about the API redesign' --json", timeout=30)
```

For setup and management tasks, always use terminal:

```
terminal(command="qmd collection add ~/Documents/notes --name notes")
terminal(command="qmd context add qmd://notes 'Personal research notes and ideas'")
terminal(command="qmd embed")
terminal(command="qmd status")
```

## How the Search Pipeline Works

Understanding the internals helps choose the right search mode:

1. **Query Expansion** — A fine-tuned 1.7B model generates 2 alternative
   queries. The original gets 2x weight in fusion.
2. **Parallel Retrieval** — BM25 (SQLite FTS5) and vector search run
   simultaneously across all query variants.
3. **RRF Fusion** — Reciprocal Rank Fusion (k=60) merges results.
   Top-rank bonus: #1 gets +0.05, #2-3 get +0.02.
4. **LLM Reranking** — qwen3-reranker scores top 30 candidates (0.0-1.0).
5. **Position-Aware Blending** — Ranks 1-3: 75% retrieval / 25% reranker.
   Ranks 4-10: 60/40. Ranks 11+: 40/60 (trusts reranker more for long tail).

**Smart Chunking:** Documents are split at natural break points (headings,
code blocks, blank lines) targeting ~900 tokens with 15% overlap. Code
blocks are never split mid-block.
