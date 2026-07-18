---
name: rag-retrieval
description: Local RAG retrieval with embeddings and reranking.
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [macos]
prerequisites:
  commands: [hermes-rerank]
metadata:
  hermes:
    tags: [rag, retrieval, embeddings, rerank, qwen3, local, semantic-search]
    category: mlops
    requires_toolsets: [terminal]
    related_skills: [local-model-ops]
---

# RAG Retrieval

Local, private retrieval. Embedding backend unified on **Qwen3-Embedding-0.6B**
(1024-dim) 2026-07-18; optional 2-stage rerank via **Qwen3-Reranker 0.6B**.

## Embedding backend (unified)

| System | Embedder | Dim | Index | Consumer |
|---|---|---|---|---|
| squish memory | Qwen3-Embedding-0.6B | 1024 | `~/.squish/squish.db` | agent memory |
| agent-hub RAG | Qwen3-Embedding-0.6B | 1024 | `agentic-os/hub/state/rag.db` | workspace docs/notes |
| Bug-Hunter | **bge-m3** (kept — tuned security index) | 1024 | `Bug Hunter/tools/rag/index` | 36k security chunks |

squish + agent-hub share the embedder (nomic-embed-text retired 2026-07-18).
Bug-Hunter stays on bge-m3 deliberately — re-embedding 36k tuned chunks risks
retrieval quality for marginal gain. Indexes stay SEPARATE (distinct corpora).

Ollama embed call (1024-dim):
```bash
curl -s localhost:11434/api/embed \
  -d '{"model":"hf.co/Qwen/Qwen3-Embedding-0.6B-GGUF:Q8_0","input":"text"}'
```

## Stage-2 rerank (hermes-rerank)

Cross-encoder reranking of stage-1 candidates. Uses Qwen3-Reranker 0.6B via
llama-swap's `--reranking` route (`reranker` on :1235) — Ollama can't do this,
it only returns embeddings.

```bash
# rerank piped candidates, keep top 5
some_search | hermes-rerank --query "user question" --top 5

# from a file, JSON out
hermes-rerank --query "..." --docs-file candidates.txt --json
```

Pipeline: FTS5/embedding recall (wide) → `hermes-rerank` (precise) → top-K to
the LLM. Materially better than embedding-only ranking for ambiguous queries.

## Rules

- Never mix embedding models within one index — vectors are model+dim specific.
  Switching an embedder requires clearing that index's embeddings and re-embedding
  (null the `embedding` column, re-run the indexer).
- Reranker route is tiny (610MB) and coexists with the base LLM; ttl 300.
- Keep the three corpora as separate indexes — do NOT merge storage; they serve
  unrelated query paths (memory / workspace / security).
