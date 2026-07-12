# Comparison to Alternatives & Performance Characteristics

## Comparison to Alternatives

| Feature | Outlines | Instructor | Guidance | LMQL |
|---------|----------|------------|----------|------|
| Pydantic Support | Native | Native | No | No |
| JSON Schema | Yes | Yes | Limited | Yes |
| Regex Constraints | Yes | No | Yes | Yes |
| Local Models | Full | Limited | Full | Full |
| API Models | Limited | Full | Full | Full |
| Zero Overhead | Yes | No | Partial | Yes |
| Automatic Retrying | No | Yes | No | No |
| Learning Curve | Low | Low | Low | High |

**When to choose Outlines:** using local models (Transformers, llama.cpp,
vLLM); need maximum inference speed; want Pydantic model support; require
zero-overhead structured generation; need to control the token sampling
process.

**When to choose alternatives:** Instructor for API models with automatic
retrying; Guidance for token healing and complex workflows; LMQL for
declarative query syntax.

## Performance Characteristics

**Speed:**
- Zero overhead: structured generation as fast as unconstrained
- Fast-forward optimization: skips deterministic tokens
- 1.2-2x faster than post-generation validation approaches

**Memory:**
- FSM compiled once per schema (cached)
- Minimal runtime overhead
- Efficient with vLLM for high throughput

**Accuracy:**
- 100% valid outputs (guaranteed by FSM)
- No retry loops needed
- Deterministic token filtering
