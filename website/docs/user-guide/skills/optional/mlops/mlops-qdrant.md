---
title: "Qdrant Vector Search — High-performance vector similarity search engine for RAG and semantic search"
sidebar_label: "Qdrant Vector Search"
description: "High-performance vector similarity search engine for RAG and semantic search"
---

{/* This page is auto-generated from the skill's SKILL.md by website/scripts/generate-skill-docs.py. Edit the source SKILL.md, not this page. */}

# Qdrant Vector Search

High-performance vector similarity search engine for RAG and semantic search. Use when building production RAG systems requiring fast nearest neighbor search, hybrid search with filtering, or scalable vector storage with Rust-powered performance.

## Skill metadata

| | |
|---|---|
| Source | Optional — install with `hermes skills install official/mlops/qdrant` |
| Path | `optional-skills/mlops/qdrant` |
| Version | `1.0.0` |
| Author | Orchestra Research |
| License | MIT |
| Dependencies | `qdrant-client>=1.12.0` |
| Platforms | linux, macos, windows |
| Tags | `RAG`, `Vector Search`, `Qdrant`, `Semantic Search`, `Embeddings`, `Similarity Search`, `HNSW`, `Production`, `Distributed` |

## Reference: full SKILL.md

:::info
The following is the complete skill definition that Hermes loads when this skill is triggered. This is what the agent sees as instructions when the skill is active.
:::

# Qdrant - Vector Similarity Search Engine

High-performance vector database written in Rust for production RAG and semantic search.

## When to use Qdrant

**Use Qdrant when:**
- Building production RAG systems requiring low latency
- Need hybrid search (vectors + metadata filtering)
- Require horizontal scaling with sharding/replication
- Want on-premise deployment with full data control
- Need multi-vector storage per record (dense + sparse)
- Building real-time recommendation systems

**Key features:**
- **Rust-powered**: Memory-safe, high performance
- **Rich filtering**: Filter by any payload field during search
- **Multiple vectors**: Dense, sparse, multi-dense per point
- **Quantization**: Scalar, product, binary for memory efficiency
- **Distributed**: Raft consensus, sharding, replication
- **REST + gRPC**: Both APIs with full feature parity

**Use alternatives instead:**
- **Chroma**: Simpler setup, embedded use cases
- **FAISS**: Maximum raw speed, research/batch processing
- **Pinecone**: Fully managed, zero ops preferred
- **Weaviate**: GraphQL preference, built-in vectorizers

## Quick start

### Installation

```bash
# Python client
pip install qdrant-client

# Docker (recommended for development)
docker run -p 6333:6333 -p 6334:6334 qdrant/qdrant

# Docker with persistent storage
docker run -p 6333:6333 -p 6334:6334 \
    -v $(pwd)/qdrant_storage:/qdrant/storage \
    qdrant/qdrant
```

### Basic usage

```python
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct

# Connect to Qdrant
client = QdrantClient(host="localhost", port=6333)

# Create collection
client.create_collection(
    collection_name="documents",
    vectors_config=VectorParams(size=384, distance=Distance.COSINE)
)

# Insert vectors with payload
client.upsert(
    collection_name="documents",
    points=[
        PointStruct(
            id=1,
            vector=[0.1, 0.2, ...],  # 384-dim vector
            payload={"title": "Doc 1", "category": "tech"}
        ),
        PointStruct(
            id=2,
            vector=[0.3, 0.4, ...],
            payload={"title": "Doc 2", "category": "science"}
        )
    ]
)

# Search with filtering
results = client.search(
    collection_name="documents",
    query_vector=[0.15, 0.25, ...],
    query_filter={
        "must": [{"key": "category", "match": {"value": "tech"}}]
    },
    limit=10
)

for point in results:
    print(f"ID: {point.id}, Score: {point.score}, Payload: {point.payload}")
```

## Core concepts

### Points - Basic data unit

```python
from qdrant_client.models import PointStruct

# Point = ID + Vector(s) + Payload
point = PointStruct(
    id=123,                              # Integer or UUID string
    vector=[0.1, 0.2, 0.3, ...],        # Dense vector
    payload={                            # Arbitrary JSON metadata
        "title": "Document title",
        "category": "tech",
        "timestamp": 1699900000,
        "tags": ["python", "ml"]
    }
)

# Batch upsert (recommended)
client.upsert(
    collection_name="documents",
    points=[point1, point2, point3],
    wait=True  # Wait for indexing
)
```

### Collections - Vector containers

```python
from qdrant_client.models import VectorParams, Distance, HnswConfigDiff

# Create with HNSW configuration
client.create_collection(
    collection_name="documents",
    vectors_config=VectorParams(
        size=384,                        # Vector dimensions
        distance=Distance.COSINE         # COSINE, EUCLID, DOT, MANHATTAN
    ),
    hnsw_config=HnswConfigDiff(
        m=16,                            # Connections per node (default 16)
        ef_construct=100,                # Build-time accuracy (default 100)
        full_scan_threshold=10000        # Switch to brute force below this
    ),
    on_disk_payload=True                 # Store payload on disk
)

# Collection info
info = client.get_collection("documents")
print(f"Points: {info.points_count}, Vectors: {info.vectors_count}")
```

### Distance metrics

| Metric | Use Case | Range |
|--------|----------|-------|
| `COSINE` | Text embeddings, normalized vectors | 0 to 2 |
| `EUCLID` | Spatial data, image features | 0 to ∞ |
| `DOT` | Recommendations, unnormalized | -∞ to ∞ |
| `MANHATTAN` | Sparse features, discrete data | 0 to ∞ |

## Search operations

### Basic search

```python
# Simple nearest neighbor search
results = client.search(
    collection_name="documents",
    query_vector=[0.1, 0.2, ...],
    limit=10,
    with_payload=True,
    with_vectors=False  # Don't return vectors (faster)
)
```

### Filtered search

```python
from qdrant_client.models import Filter, FieldCondition, MatchValue, Range

# Complex filtering
results = client.search(
    collection_name="documents",
    query_vector=query_embedding,
    query_filter=Filter(
        must=[
            FieldCondition(key="category", match=MatchValue(value="tech")),
            FieldCondition(key="timestamp", range=Range(gte=1699000000))
        ],
        must_not=[
            FieldCondition(key="status", match=MatchValue(value="archived"))
        ]
    ),
    limit=10
)

# Shorthand filter syntax
results = client.search(
    collection_name="documents",
    query_vector=query_embedding,
    query_filter={
        "must": [
            {"key": "category", "match": {"value": "tech"}},
            {"key": "price", "range": {"gte": 10, "lte": 100}}
        ]
    },
    limit=10
)
```

### Batch search

```python
from qdrant_client.models import SearchRequest

# Multiple queries in one request
results = client.search_batch(
    collection_name="documents",
    requests=[
        SearchRequest(vector=[0.1, ...], limit=5),
        SearchRequest(vector=[0.2, ...], limit=5, filter={"must": [...]}),
        SearchRequest(vector=[0.3, ...], limit=10)
    ]
)
```

## RAG integration

### With sentence-transformers

```python
from sentence_transformers import SentenceTransformer
from qdrant_client import QdrantClient
from qdrant_client.models import VectorParams, Distance, PointStruct

# Initialize
encoder = SentenceTransformer("all-MiniLM-L6-v2")
client = QdrantClient(host="localhost", port=6333)

# Create collection
client.create_collection(
    collection_name="knowledge_base",
    vectors_config=VectorParams(size=384, distance=Distance.COSINE)
)

# Index documents
documents = [
    {"id": 1, "text": "Python is a programming language", "source": "wiki"},
    {"id": 2, "text": "Machine learning uses algorithms", "source": "textbook"},
]

points = [
    PointStruct(
        id=doc["id"],
        vector=encoder.encode(doc["text"]).tolist(),
        payload={"text": doc["text"], "source": doc["source"]}
    )
    for doc in documents
]
client.upsert(collection_name="knowledge_base", points=points)

# RAG retrieval
def retrieve(query: str, top_k: int = 5) -> list[dict]:
    query_vector = encoder.encode(query).tolist()
    results = client.search(
        collection_name="knowledge_base",
        query_vector=query_vector,
        limit=top_k
    )
    return [{"text": r.payload["text"], "score": r.score} for r in results]

# Use in RAG pipeline
context = retrieve("What is Python?")
prompt = f"Context: {context}\n\nQuestion: What is Python?"
```

### With LangChain / LlamaIndex

Both frameworks ship a Qdrant vector-store wrapper (`langchain_community.vectorstores.Qdrant`, `llama_index.vector_stores.qdrant.QdrantVectorStore`) that plugs into their standard retriever/query-engine APIs. Setup snippets for both: read `references/integrations.md`.

## Multi-vector support

A collection can hold multiple named vectors per point (e.g. `"dense"` for semantic embeddings + `"sparse"` for BM25/SPLADE keyword vectors), searched individually via `("name", query_vector)` or combined with Reciprocal Rank Fusion for hybrid search. Full named-vector and sparse-vector setup, hybrid-search RRF queries, and multi-stage coarse→fine retrieval: read `references/advanced-usage.md`.

## Quantization (memory optimization)

Scalar quantization (`ScalarQuantization`, INT8) gives ~4x memory reduction with minimal accuracy loss; product and binary quantization trade more accuracy for 16x/32x reduction. Always pair quantized search with `search_params={"quantization": {"rescore": True}}` to rescore top results against full-precision vectors. Full quantization configs and trade-offs per type: read `references/advanced-usage.md`.

## Payload indexing

```python
from qdrant_client.models import PayloadSchemaType

# Create payload index for faster filtering
client.create_payload_index(
    collection_name="documents",
    field_name="category",
    field_schema=PayloadSchemaType.KEYWORD
)

client.create_payload_index(
    collection_name="documents",
    field_name="timestamp",
    field_schema=PayloadSchemaType.INTEGER
)

# Index types: KEYWORD, INTEGER, FLOAT, GEO, TEXT (full-text), BOOL
```

## Production deployment

Connect to Qdrant Cloud with `QdrantClient(url="https://your-cluster.cloud.qdrant.io", api_key="your-api-key")`. Tune `HnswConfigDiff(ef_construct=..., m=...)` for search-speed/recall trade-offs, or `optimizer_config={"indexing_threshold": ...}` for bulk-load speed. Distributed clusters, sharding, replication, snapshots/backups, and multitenancy patterns: read `references/advanced-usage.md`.

## Best practices

1. **Batch operations** - Use batch upsert/search for efficiency
2. **Payload indexing** - Index fields used in filters
3. **Quantization** - Enable for large collections (>1M vectors)
4. **Sharding** - Use for collections >10M vectors
5. **On-disk storage** - Enable `on_disk_payload` for large payloads
6. **Connection pooling** - Reuse client instances

## Common issues

Slow filtered search → missing payload index (`create_payload_index` on the filtered field). Out of memory → enable quantization + `on_disk_payload=True`. Connection errors → set `timeout=30` and `prefer_grpc=True`. Full diagnostics for installation, connection, collection, search, upsert, memory, and cluster issues: read `references/troubleshooting.md` when a specific error needs root-causing.

## References

- **[Advanced Usage](https://github.com/NousResearch/hermes-agent/blob/main/optional-skills/mlops/qdrant/references/advanced-usage.md)** - Distributed mode, hybrid search, recommendations
- **[Troubleshooting](https://github.com/NousResearch/hermes-agent/blob/main/optional-skills/mlops/qdrant/references/troubleshooting.md)** - Common issues, debugging, performance tuning
- **[Integrations](https://github.com/NousResearch/hermes-agent/blob/main/optional-skills/mlops/qdrant/references/integrations.md)** - LangChain and LlamaIndex vector-store setup

## Resources

- **GitHub**: https://github.com/qdrant/qdrant (22k+ stars)
- **Docs**: https://qdrant.tech/documentation/
- **Python Client**: https://github.com/qdrant/qdrant-client
- **Cloud**: https://cloud.qdrant.io
- **Version**: 1.12.0+
- **License**: Apache 2.0
