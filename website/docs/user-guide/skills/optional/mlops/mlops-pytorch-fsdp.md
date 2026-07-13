---
title: "Pytorch Fsdp"
sidebar_label: "Pytorch Fsdp"
description: "Expert guidance for Fully Sharded Data Parallel training with PyTorch FSDP - parameter sharding, mixed precision, CPU offloading, FSDP2"
---

{/* This page is auto-generated from the skill's SKILL.md by website/scripts/generate-skill-docs.py. Edit the source SKILL.md, not this page. */}

# Pytorch Fsdp

Expert guidance for Fully Sharded Data Parallel training with PyTorch FSDP - parameter sharding, mixed precision, CPU offloading, FSDP2

## Skill metadata

| | |
|---|---|
| Source | Optional — install with `hermes skills install official/mlops/pytorch-fsdp` |
| Path | `optional-skills/mlops/pytorch-fsdp` |
| Version | `1.0.0` |
| Author | Orchestra Research |
| License | MIT |
| Dependencies | `torch>=2.0`, `transformers` |
| Platforms | linux, macos |
| Tags | `Distributed Training`, `PyTorch`, `FSDP`, `Data Parallel`, `Sharding`, `Mixed Precision`, `CPU Offloading`, `FSDP2`, `Large-Scale Training` |

## Reference: full SKILL.md

:::info
The following is the complete skill definition that Hermes loads when this skill is triggered. This is what the agent sees as instructions when the skill is active.
:::

# Pytorch-Fsdp Skill

Comprehensive assistance with pytorch-fsdp development, generated from official documentation.

## When to Use This Skill

This skill should be triggered when:
- Working with pytorch-fsdp
- Asking about pytorch-fsdp features or APIs
- Implementing pytorch-fsdp solutions
- Debugging pytorch-fsdp code
- Learning pytorch-fsdp best practices

## Quick Reference

### Common Patterns

Eight recurring distributed-training patterns are documented in detail in `references/patterns.md` (raw excerpts from the official PyTorch docs — read the relevant one when implementing or debugging that API):

1. **Generic Join Context Manager** — `torch.distributed.algorithms.Join` for training with uneven inputs across ranks.
2. **torch.distributed — Distributed Communication Package** — the core API surface (backends, collectives, `init_process_group`, point-to-point ops). This is the largest and most-referenced section.
3. **Process Group Initialization** — `init_process_group()` requirements, env vars (`MASTER_ADDR`/`MASTER_PORT`), and backend selection (NCCL/Gloo/MPI).
4. **DDP Basic Example** — minimal `DistributedDataParallel` wrap-and-train snippet.
5. **Process Groups** — creating and using non-default (sub) process groups with `new_group()`.
6. **NCCL Concurrent Usage Warning** — ordering/synchronization requirements when multiple process groups or threads issue NCCL collectives concurrently.
7. **DDP + Distributed RPC / Autograd** — combining `DistributedDataParallel` with `torch.distributed.autograd`/`DistributedOptimizer`.
8. **DDP `static_graph` Option** — when/how to set `static_graph=True` for reentrant backward, repeated activation checkpointing, and unused-parameter cases.

For FSDP-specific sharding/mixed-precision/offloading configuration, read `references/other.md` (scraped official doc pages) alongside `references/patterns.md`.

## Reference Files

This skill includes comprehensive documentation in `references/`:

- **patterns.md** - The 8 common-usage patterns (Join context manager, torch.distributed API, process group init, DDP examples, NCCL concurrency, RPC/autograd integration, static_graph) in full detail.
- **other.md** - Other scraped documentation pages (FSDP/DDP design notes, API references).

Use `view` to read specific reference files when detailed information is needed.

## Working with This Skill

### For Beginners
Start with the getting_started or tutorials reference files for foundational concepts.

### For Specific Features
Use the appropriate category reference file (api, guides, etc.) for detailed information.

### For Code Examples
The quick reference section above contains common patterns extracted from the official docs.

## Resources

### references/
Organized documentation extracted from official sources. These files contain:
- Detailed explanations
- Code examples with language annotations
- Links to original documentation
- Table of contents for quick navigation

### scripts/
Add helper scripts here for common automation tasks.

### assets/
Add templates, boilerplate, or example projects here.

## Notes

- This skill was automatically generated from official documentation
- Reference files preserve the structure and examples from source docs
- Code examples include language detection for better syntax highlighting
- Quick reference patterns are extracted from common usage examples in the docs

## Updating

To refresh this skill with updated documentation:
1. Re-run the scraper with the same configuration
2. The skill will be rebuilt with the latest information
