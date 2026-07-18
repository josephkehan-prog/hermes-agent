---
name: pytorch-fsdp
description: Fully Sharded Data Parallel training with PyTorch.
version: 1.0.0
author: Orchestra Research
license: MIT
dependencies: [torch>=2.0, transformers]
platforms: [linux, macos]
metadata:
  hermes:
    tags: [Distributed Training, PyTorch, FSDP, Data Parallel, Sharding, Mixed Precision, CPU Offloading, FSDP2, Large-Scale Training]

---

# Pytorch-Fsdp Skill

PyTorch FSDP / torch.distributed guidance. Use when working with, debugging, or learning pytorch-fsdp.

Full doc extracts (all patterns below, verbatim long form): `REFERENCE.md` next to this file. Organized doc pages: `references/other.md` (index: `references/index.md`).

## Quick Reference

### Initialization
- Init with `torch.distributed.init_process_group(backend=None, init_method=None, timeout=None, world_size=-1, rank=-1, store=None, group_name='', pg_options=None, device_id=None)` or `torch.distributed.device_mesh.init_device_mesh()` before any other distributed call. Both block until all processes join.
- Two init modes: explicit `store` + `rank` + `world_size`, or `init_method` URL (default `env://`).
- Backends: `mpi`, `gloo`, `nccl`, `ucc` (experimental), `xccl`, or third-party plugin. Since 2.6, backend defaults by device: `nccl` for cuda, `gloo` for cpu, `xccl` for xpu; auto-detected if neither backend nor device_id given.
- Caveats: init is NOT thread-safe — create process groups from a single thread (inconsistent UUID assignment / hangs otherwise). With nccl and multiple processes per machine, each process needs exclusive access to its GPUs (sharing deadlocks or errors).
- `torch.distributed.is_available()` — True if the distributed package is built (`USE_DISTRIBUTED=1`; default 1 on Linux/Windows, 0 on MacOS).

### DeviceMesh
```
>>> from torch.distributed.device_mesh import init_device_mesh
>>> mesh_1d = init_device_mesh("cuda", mesh_shape=(8,))
>>> mesh_2d = init_device_mesh("cuda", mesh_shape=(2, 8), mesh_dim_names=("dp", "tp"))
```

### Process groups
- Default group = the world; all processes must enter each collective.
- `torch.distributed.new_group(ranks=None, timeout=None, backend=None, pg_options=None, use_local_synchronization=False, group_desc=None, device_id=None)` creates a subgroup; pass its handle as `group` to collectives.
- Caveats: ALL processes in the main group must call `new_group()`, even non-members; create groups in the same order on every process.
- NCCL multi-group safety: ensure a globally consistent execution order of collectives across ranks; explicit synchronization if multiple threads issue collectives. Async ops return a work object on a separate CUDA stream — call `work.wait()` before using another process group. See NCCL docs: using multiple communicators concurrently.

### Join context manager (uneven inputs)
- `torch.distributed.algorithms.Join(joinables, enable=True, throw_on_early_termination=False, **kwargs)` with classes `Join`, `Joinable`, `JoinHook`. Hooks shadow collectives of non-joined processes to prevent hangs.
- Caveats: each `Joinable` must call `notify_join_context()` before its per-iteration collectives; all `JoinHook` `process_group` attributes must match (device of the first is used).
- `enable=False` only when inputs are known even; `throw_on_early_termination=True` raises on uneven inputs.
- Works with DDP + `ZeroRedundancyOptimizer` (full worker example: REFERENCE.md Pattern 1).

### DDP + Distributed RPC
- With DDP + RPC framework, always use `torch.distributed.autograd.backward(context_id, [loss])` for gradients and `torch.distributed.optim.DistributedOptimizer` for optimization, inside `dist_autograd.context()`. Full example: REFERENCE.md Pattern 7.

### DDP static_graph
- `static_graph=True` tells DDP the graph is static: used/unused parameter set fixed and no iteration-dependent control flow (`find_unused_parameters` then irrelevant).
- Enables: reentrant backwards, multiple/unused-param activation checkpointing, params outside forward, perf win (skips per-iteration unused-param graph search).
- Check eligibility: `model_DDP._get_ddp_logging_data().get("can_set_static_graph") == True`.

## Working with This Skill
- Beginners: start with getting_started/tutorials reference files.
- Specific features: use the matching category reference file (api, guides, etc.).
- Code examples: REFERENCE.md contains the full extracted patterns.
- `scripts/` — helper scripts; `assets/` — templates/boilerplate (add as needed).

## Notes
- Auto-generated from official docs; reference files preserve source structure and examples.
- To update: re-run the scraper with the same configuration; the skill is rebuilt with the latest docs.
