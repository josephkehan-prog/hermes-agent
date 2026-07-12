---
name: huggingface-tokenizers
description: Fast tokenizers optimized for research and production. Rust-based implementation tokenizes 1GB in <20 seconds. Supports BPE, WordPiece, and Unigram algorithms. Train custom vocabularies, track alignments, handle padding/truncation. Integrates seamlessly with transformers. Use when you need high-performance tokenization or custom tokenizer training.
version: 1.0.0
author: Orchestra Research
license: MIT
dependencies: [tokenizers, transformers, datasets]
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [Tokenization, HuggingFace, BPE, WordPiece, Unigram, Fast Tokenization, Rust, Custom Tokenizer, Alignment Tracking, Production]

---

# HuggingFace Tokenizers - Fast Tokenization for NLP

Fast, production-ready tokenizers with Rust performance and Python ease-of-use.

## When to use HuggingFace Tokenizers

**Use HuggingFace Tokenizers when:**
- Need extremely fast tokenization (<20s per GB of text)
- Training custom tokenizers from scratch
- Want alignment tracking (token → original text position)
- Building production NLP pipelines
- Need to tokenize large corpora efficiently

**Performance**:
- **Speed**: <20 seconds to tokenize 1GB on CPU
- **Implementation**: Rust core with Python/Node.js bindings
- **Efficiency**: 10-100× faster than pure Python implementations

**Use alternatives instead**:
- **SentencePiece**: Language-independent, used by T5/ALBERT
- **tiktoken**: OpenAI's BPE tokenizer for GPT models
- **transformers AutoTokenizer**: Loading pretrained only (uses this library internally)

## Quick start

### Installation

```bash
# Install tokenizers
pip install tokenizers

# With transformers integration
pip install tokenizers transformers
```

### Load pretrained tokenizer

```python
from tokenizers import Tokenizer

# Load from HuggingFace Hub
tokenizer = Tokenizer.from_pretrained("bert-base-uncased")

# Encode text
output = tokenizer.encode("Hello, how are you?")
print(output.tokens)  # ['hello', ',', 'how', 'are', 'you', '?']
print(output.ids)     # [7592, 1010, 2129, 2024, 2017, 1029]

# Decode back
text = tokenizer.decode(output.ids)
print(text)  # "hello, how are you?"
```

### Train custom BPE tokenizer

```python
from tokenizers import Tokenizer
from tokenizers.models import BPE
from tokenizers.trainers import BpeTrainer
from tokenizers.pre_tokenizers import Whitespace

# Initialize tokenizer with BPE model
tokenizer = Tokenizer(BPE(unk_token="[UNK]"))
tokenizer.pre_tokenizer = Whitespace()

# Configure trainer
trainer = BpeTrainer(
    vocab_size=30000,
    special_tokens=["[UNK]", "[CLS]", "[SEP]", "[PAD]", "[MASK]"],
    min_frequency=2
)

# Train on files
files = ["train.txt", "validation.txt"]
tokenizer.train(files, trainer)

# Save
tokenizer.save("my-tokenizer.json")
```

**Training time**: ~1-2 minutes for 100MB corpus, ~10-20 minutes for 1GB

### Batch encoding with padding

```python
# Enable padding
tokenizer.enable_padding(pad_id=3, pad_token="[PAD]")

# Encode batch
texts = ["Hello world", "This is a longer sentence"]
encodings = tokenizer.encode_batch(texts)

for encoding in encodings:
    print(encoding.ids)
# [101, 7592, 2088, 102, 3, 3, 3]
# [101, 2023, 2003, 1037, 2936, 6251, 102]
```

## Tokenization algorithms

Three algorithms, chosen by model family: **BPE** (GPT-2/3, RoBERTa, BART — merges most-frequent character pairs), **WordPiece** (BERT, DistilBERT — merges by likelihood score, prefixes continuation subwords with `##`), and **Unigram** (ALBERT, T5, mBART — starts from a large vocabulary and prunes by loss, produces probabilistic tokenizations). Full algorithm walkthroughs, step-by-step merge examples, trainer code, and advantages/trade-offs for each: read `references/algorithms.md`.

## Tokenization pipeline

Full pipeline: **Normalization → Pre-tokenization → Model → Post-processing → Decoding**. Normalizers clean text (NFD/NFC, lowercase, strip accents); pre-tokenizers split into word-like units (whitespace, byte-level, metaspace); post-processors add special tokens (`[CLS]`/`[SEP]`, `<s>`/`</s>`); decoders reverse the process for output text. Full component reference (every normalizer/pre-tokenizer/model/post-processor/decoder with examples) and complete BERT/GPT-2/T5 pipeline builds: read `references/pipeline.md` when assembling a custom tokenizer.

## Alignment tracking

Track token positions in original text:

```python
output = tokenizer.encode("Hello, world!")

# Get token offsets
for token, offset in zip(output.tokens, output.offsets):
    start, end = offset
    print(f"{token:10} → [{start:2}, {end:2}): {text[start:end]!r}")

# Output:
# hello      → [ 0,  5): 'Hello'
# ,          → [ 5,  6): ','
# world      → [ 7, 12): 'world'
# !          → [12, 13): '!'
```

**Use cases**:
- Named entity recognition (map predictions back to text)
- Question answering (extract answer spans)
- Token classification (align labels to original positions)

## Integration with transformers

`AutoTokenizer.from_pretrained(...)` returns a fast tokenizer backed by this library automatically (check `tokenizer.is_fast`); a custom-trained tokenizer wraps into transformers via `PreTrainedTokenizerFast(tokenizer_file="my-tokenizer.json", unk_token=..., pad_token=..., cls_token=..., sep_token=..., mask_token=...)` and then behaves like any transformers tokenizer (padding, truncation, `return_tensors`). Special tokens, offset/word-ID mapping, sequence pairs, chat templates, and batching/caching patterns: read `references/integration.md`.

## Common patterns

- **Train from a large dataset without loading it all into memory**: use `tokenizer.train_from_iterator(batch_iterator(), trainer=trainer, length=len(dataset))` with a generator that yields text batches — processes ~1GB in 10-20 minutes.
- **Truncation/padding**: `tokenizer.enable_truncation(max_length=512)` and `tokenizer.enable_padding(pad_id=..., pad_token="[PAD]", length=512)`.
- **Multi-processing**: split the corpus into chunks and `Pool(n).map(tokenizer.encode_batch, chunks)` — 5-8× speedup with 8 cores.

Full training workflow (algorithm selection, trainer parameters per model type, domain-specific tokenizers for code/medical/multilingual text, vocabulary-size tuning, quality testing, troubleshooting): read `references/training.md` before training a production tokenizer.

## Performance & supported models

Rust core tokenizes ~1GB in ~15 seconds (vs ~20 minutes pure Python, ~80× speedup); training a 30k-vocab BPE/WordPiece tokenizer takes ~15-20 min on a 1GB corpus (16-core CPU). Pretrained tokenizers cover the standard BERT/GPT/T5/BART/ALBERT/XLM-RoBERTa families via `from_pretrained()` — browse the full list at https://huggingface.co/models?library=tokenizers. Detailed training-speed/tokenization-speed/memory tables: read `references/benchmarks.md`.

## References

- **[Training Guide](references/training.md)** - Train custom tokenizers, configure trainers, handle large datasets
- **[Algorithms Deep Dive](references/algorithms.md)** - BPE, WordPiece, Unigram explained in detail
- **[Pipeline Components](references/pipeline.md)** - Normalizers, pre-tokenizers, post-processors, decoders
- **[Transformers Integration](references/integration.md)** - AutoTokenizer, PreTrainedTokenizerFast, special tokens
- **[Benchmarks](references/benchmarks.md)** - Training/tokenization speed, memory usage, supported pretrained models

## Resources

- **Docs**: https://huggingface.co/docs/tokenizers
- **GitHub**: https://github.com/huggingface/tokenizers ⭐ 9,000+
- **Version**: 0.20.0+
- **Course**: https://huggingface.co/learn/nlp-course/chapter6/1
- **Paper**: BPE (Sennrich et al., 2016), WordPiece (Schuster & Nakajima, 2012)


