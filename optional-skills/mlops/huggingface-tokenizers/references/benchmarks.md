# Performance Benchmarks

Detailed throughput, training-speed, and memory numbers for HuggingFace Tokenizers.

## Training speed

| Corpus Size | BPE (30k vocab) | WordPiece (30k) | Unigram (8k) |
|-------------|-----------------|-----------------|--------------|
| 10 MB       | 15 sec          | 18 sec          | 25 sec       |
| 100 MB      | 1.5 min         | 2 min           | 4 min        |
| 1 GB        | 15 min          | 20 min          | 40 min       |

**Hardware**: 16-core CPU, tested on English Wikipedia

## Tokenization speed

| Implementation | 1 GB corpus | Throughput    |
|----------------|-------------|---------------|
| Pure Python    | ~20 minutes | ~50 MB/min    |
| HF Tokenizers  | ~15 seconds | ~4 GB/min     |
| **Speedup**    | **80×**     | **80×**       |

**Test**: English text, average sentence length 20 words

## Memory usage

| Task                    | Memory  |
|-------------------------|---------|
| Load tokenizer          | ~10 MB  |
| Train BPE (30k vocab)   | ~200 MB |
| Encode 1M sentences     | ~500 MB |

## Supported pretrained models

Pre-trained tokenizers available via `from_pretrained()`:

**BERT family**:
- `bert-base-uncased`, `bert-large-cased`
- `distilbert-base-uncased`
- `roberta-base`, `roberta-large`

**GPT family**:
- `gpt2`, `gpt2-medium`, `gpt2-large`
- `distilgpt2`

**T5 family**:
- `t5-small`, `t5-base`, `t5-large`
- `google/flan-t5-xxl`

**Other**:
- `facebook/bart-base`, `facebook/mbart-large-cc25`
- `albert-base-v2`, `albert-xlarge-v2`
- `xlm-roberta-base`, `xlm-roberta-large`

Browse all: https://huggingface.co/models?library=tokenizers
