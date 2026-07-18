---
name: prediction-market-analysis
description: "Find mispriced Polymarket outcomes using local LLM probability estimation, multi-stage scanning pipelines, Kelly Criterion risk management. Covers model selection for your hardware, edge detection strategies, and trading workflow."
version: 1.0.0
author: Hermes Agent
tags: [polymarket, prediction-markets, local-llm, ollama, quantitative-trading, risk-management]
---

# Prediction Market Analysis with Local LLMs

Find edges on Polymarket by running active markets through a multi-stage local LLM pipeline: fast filter → deep probability estimation → edge ranking → Kelly-sized position. Zero API cost since inference runs on your own GPU.

## When to Use

- User asks about Polymarket strategy, finding mispriced markets, or prediction market trading
- User wants to estimate true probabilities using local models and compare against crowd pricing
- User needs model recommendations for financial reasoning / probability estimation on their hardware
- User asks about Kelly Criterion position sizing or risk management for prediction markets

## Hardware-Aware Model Hierarchy

For an Apple M5 Max with 64GB unified RAM running Ollama:

### Tier 1 — Deep Probability Estimation (Stage 2)

| Model | Fit | Notes |
|-------|-----|-------|
| **DeepSeek-R1** (32B Q4 ≈42 GB) | #1 open-source for quantitative reasoning, multi-step probability estimation from evidence and base rates | Needs pull: `ollama pull deepseek-r1:32b` |
| **Qwen3-Coder-Next** (MoE 3B active, 132 tok/s) | Already running. Excellent at parsing resolution criteria fine print, spotting edge cases in contract language that crowd pricing misses | ✅ Pre-loaded |

### Tier 2 — Volume Screening & Sentiment (Stage 1)

| Model | Fit | Notes |
|-------|-----|-------|
| **Qwen3.6:27b** (≈17 GB) | General analysis, news sentiment synthesis, drafting trade theses | ✅ Pre-loaded |
| **Finance-Llama-8B** (≈6 GB, Q8_0) | Fine-tuned on 500K finance examples — QA, reasoning, sentiment, NER. Speed filter for initial market screening | Needs pull: `ollama pull finance-llama:8b` or from Ollama library |

## Multi-Stage Scan Pipeline (Production Pattern)

Based on `loki128/asgard` architecture and academic validation (arXiv 2026):

```
Stage 1: Fast Filter — small model scans ALL active markets
  └─ Inputs: Polymarket Gamma API market list + metadata
  └─ Model: Qwen3.6:27b or Finance-Llama-8B
  └─ Filters: volume > $10K, days_to_resolution > 3, liquidity > $5K
  └─ Output: ~200 surviving candidates from 2,000+ markets
  └─ Rejects 90% at zero compute cost

Stage 2: Deep Estimation — reasoning model estimates TRUE probability
  └─ Inputs: resolution criteria text, relevant recent news/events, base rates from comparable historical markets
  └─ Model: DeepSeek-R1 or Qwen3-Coder-Next
  └─ Output: p_model with confidence interval + reasoning chain

Stage 3: Edge Ranking — compare p_model vs p_market
  └─ Edge = |p_model - p_market| in percentage points
  └─ Minimum edge threshold: 10pp (configurable, see references/mispricing-strategies.md)
  └─ Markets with 15+ point gaps resolve in AI's direction significantly above chance

Stage 4: Kelly Sizing — position sizing from edge and odds
  └─ f = (p_model * b - q) / b where b = yes_price / no_price, q = 1 - p_model
  └─ Use fractional Kelly (0.25x-0.50x) to reduce variance
```

## High-Edge Market Categories

Ranked by mispricing frequency (see `references/mispricing-strategies.md`):

1. **Low-volume markets** — fewer informed traders = wider crowd-vs-reality gaps
2. **Stale markets post-news** — information lag is pure edge; market hasn't repriced within hours of headline
3. **Resolution-criteria traps** — crowd prices the headline question, LLM parses the fine print and finds easier/harder technical definition (this is where local LLMs have outsized advantage)
4. **Cross-market arbitrage** — correlated or mutually-exclusive markets with inconsistent pricing (A=70%, "NOT A"=45% after fees = free money)

## Workflow

1. Use the `polymarket` skill to query active markets via Gamma API
2. Pipe market list through Stage 1 filter model
3. Run surviving candidates through Stage 2 reasoning model with prompt template from `templates/edge-detection-prompt.md`
4. Compare estimates against current crowd prices
5. Flag edges above threshold, size positions with Kelly Criterion
6. Re-scan every 6-12 hours (edges compress within 12-48h once public)

## Risk Management

- **Never trust a single model's estimate** — use panel approach: run through both Tier 1 models and average if they agree, reject if they diverge >10pp
- **Always check resolution criteria first** — misreading the contract is the #1 cause of losses
- **Fees eat small edges** — Polymarket takes ~2% maker fee; edge must clear fees + spread to be worthwhile
- **Position sizing matters more than prediction accuracy** — over-sizing on a 55/45 call will blow your bankroll even with positive EV

## Data Sources

- Polymarket Gamma API: `gamma-api.polymarket.com` (market discovery, metadata)
- Polymarket CLOB API: `clob.polymarket.com` (orderbook, real-time prices)
- Polymarket Data API: `data-api.polymarket.com` (trades, positions, PnL)
- All read-only, no authentication required

## Related Skills

- `polymarket` — query market data, prices, orderbooks, trade history
- See `references/mispricing-strategies.md` for resolved mispricing patterns, fee calculations, and platform-specific quirks