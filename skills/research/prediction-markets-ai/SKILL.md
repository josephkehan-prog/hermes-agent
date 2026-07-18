---
name: prediction-markets-ai
description: Find mispriced prediction markets with local LLMs.
version: 1.0.0
author: Hermes Agent
tags: [prediction-markets, polymarket, kalshi, ollama, ai-trading, quantitative]
---

# AI-Assisted Prediction Market Edge Detection with Local LLMs

## Trigger conditions  
- User asks about Polymarket odds, prediction market analysis, or "where's the edge"
- User wants to find mispriced markets using AI/local models
- User asks about Kelly Criterion, position sizing, or arbitrage in prediction contracts
- Context involves comparing model estimates vs. crowd pricing on any binary prediction market

## Overview

Prediction markets encode crowdwisdom as prices (0¢–100¢ = implied 0%–100% probability). The edge exists where your independently estimated true probability diverges meaningfully from the crowd price. A two-stage local-LLM pipeline finds these edges at zero token cost by pre-filtering thousands of markets cheaply, then deep-analyzing only high-signal candidates with a reasoning model on your own GPU.

See `references/model-selection.md` for benchmark-backed model recommendations per task stage.  
See `scripts/polymarket_scan.py` for a ready-to-run Python scan pipeline.

## Two-Stage Pipeline — The Core Pattern

### Stage 1: Pre-filter (cheap, fast)
Small model or rule-based step scans the full active market universe and rejects ~90%. Criteria:
- Volume > $30K → liquid enough to enter/exit without killing edge in spreads
- Days to resolution < 90 → meaningful runway but not pure-guesswork territory
- Market price between 10%–90% → extreme prices leave no room for edge detection
- Category filter: politics, macro, geopolitics tend to have more structural mispricing than crypto

**Recommended model**: `qwen3.6:27b` or any 8B-class generalist. This stage is about volume, not reasoning depth.

### Stage 2: Deep probability estimation (reasoning model)
For surviving candidates (~50–200 markets), the LLM estimates TRUE probability using base rates, resolution criteria parsing, current events as of the analysis date, and structural factors. The difference between its estimate and the crowd price = your edge.

**Recommended models** (ranked by research benchmarks for quantitative reasoning):
1. `deepseek-r1:32b` — Best open-source model for complex multi-step reasoning (arXiv 2026 arbitrage paper validated this)
2. `qwen3-coder-next` — Consensus #1 local coder; excels at parsing resolution criteria fine print that crowds ignore

### Prompt Template for Stage 2

```
You are an expert prediction market analyst as of [CURRENT_DATE]. For each binary prediction-market question below, estimate the TRUE probability (0-100%) that "Yes" occurs.

Respond ONLY in JSON:
[
  {"question": "...", "estimated_probability": NUMBER, 
   "gap_vs_market": NUMBER, "confidence": "HIGH/MEDIUM/LOW",
   "key_reasoning": "brief reason"}
]
```

## Cross-Market Arbitrage Detection

Feed a batch of correlated or related markets to the LLM and ask it to find:
- Mutually exclusive pairs where combined YES probabilities < 100% (free-money if arbitrable on same platform)
- Positively correlated markets priced far apart despite logical dependency  
- "NOT X" contracts whose price is inconsistent with X's implied probability
- Overlapping multi-option markets where the sum of outcome prices < 100%

An academic paper (arXiv:2508.03474) demonstrated this using DeepSeek-R1-Distill-Qwen-32B — the model successfully mapped market state spaces and found probability inconsistencies that human traders missed.

## Risk Management

Use Kelly Criterion for position sizing once you have an edge estimate:
- `f* = (p * b - q) / b` where p = your estimated YES probability, b = decimal odds ((1-p_market)/p_market), q = 1-p
- Most experienced traders use half-Kelly or quarter-Kelly to reduce variance
- Never size a position larger than your model confidence supports — LOW confidence = tiny size or skip

Markets with Poly-Sim Score >70 (composite: gap + liquidity + time horizon) resolved in the AI's direction significantly above crowd-implied probability according to their published accuracy study covering 180 days of resolved markets.

## Market Data Sources

| API | Base URL | Auth | Key Endpoints |
|-----|---------|------|--------------|
| Gamma API (Polymarket catalog) | `gamma-api.polymarket.com` | None — public | `/markets`, `/events`, search |
| CLOB API (orderbook/prices) | `clob.polymarket.com` | API key for trading; public for reads | `/prices/level2/<token_id>`, `/trades` |
| Data API (positions/activity) | `data-api.polymarket.com` | None — public | User positions, trade history |

Gamma API is the primary entry point for discovery. Rate limits are generous (300 req/min). All read-only endpoints work without authentication.

## Platforms Beyond Polymarket

- **Kalshi** — US-based regulated binary options market; same edge-detection principles apply
- **Metaculus/Manifold** — Reputation-based prediction markets; good for cross-referencing probability estimates
- **Intigriti/YesWeHack** — European platforms with different researcher demographics → potential systematic mispricing in under-covered categories

## Pitfalls

1. **Information asymmetry ≠ edge**: A large gap might mean the AI is WRONG and the crowd knows something you don't. Always check WHY a market hasn't corrected yet — liquidity constraints? resolution criteria confusion? or genuinely overlooked information?
2. **Fees and spreads eat thin edges**: A 3-point "edge" can vanish after bid-ask spread + platform fees. Minimum viable edge is ~5 points on liquid markets.
3. **Near-resolution noise**: Markets expiring <24 hours show chaotic pricing from last-minute traders. Skip these — the LLM's estimate hasn't had time to reflect new information.
4. **Overconfidence trap**: The LLM will confidently produce numbers even for questions where no good evidence exists. LOW confidence outputs should be deprioritized or sized very small.
5. **Regional trading access**: Some jurisdictions restrict prediction market participation. Reading data is generally unrestricted but placing trades may require specific wallet/chain setup.
6. **API instability during events**: During high-attention periods (election results, major announcements), Polymarket APIs can return stale prices or hit rate limits faster. Add retry logic with exponential backoff in production scripts.
