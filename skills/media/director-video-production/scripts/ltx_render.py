#!/usr/bin/env python3
"""Preflight or render a small video with the isolated LTX-Video MPS runtime."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path


RUNTIME = Path("/Users/josephhan/mac/Hermes/runtimes/ltx-video")
PYTHON = RUNTIME / ".venv/bin/python"
CHECKPOINT = RUNTIME / "checkpoints/ltxv-2b-0.9.6-distilled-04-25.safetensors"
CONFIG = RUNTIME / "configs/hermes-ltxv-2b-0.9.6-distilled.yaml"
DEFAULT_OUTPUT = Path("/Users/josephhan/mac/GPTWorks/Hermes/media/video")


def preflight() -> dict[str, object]:
    checks = {
        "runtime": RUNTIME.is_dir(),
        "python": PYTHON.is_file(),
        "checkpoint": CHECKPOINT.is_file(),
        "config": CONFIG.is_file(),
    }
    if checks["python"]:
        probe = subprocess.run(
            [str(PYTHON), "-c", "import torch; print(torch.__version__, torch.backends.mps.is_available())"],
            cwd=RUNTIME,
            text=True,
            capture_output=True,
            check=False,
        )
        checks["mps"] = probe.returncode == 0 and probe.stdout.rstrip().endswith("True")
        checks["torch"] = probe.stdout.strip()
    else:
        checks["mps"] = False
    checks["ready"] = all(bool(checks[key]) for key in ("runtime", "python", "checkpoint", "config", "mps"))
    return checks


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--preflight", action="store_true")
    parser.add_argument("--prompt")
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--height", type=int, default=256)
    parser.add_argument("--width", type=int, default=384)
    parser.add_argument("--frames", type=int, default=9)
    parser.add_argument("--fps", type=int, default=12)
    parser.add_argument("--seed", type=int, default=171198)
    parser.add_argument("--offload-to-cpu", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    status = preflight()
    if args.preflight:
        print(json.dumps(status, indent=2))
        return 0 if status["ready"] else 1
    if not status["ready"]:
        print(json.dumps(status, indent=2), file=sys.stderr)
        return 1
    if not args.prompt or not args.prompt.strip():
        print("error: --prompt is required for rendering", file=sys.stderr)
        return 2
    if args.height % 32 or args.width % 32:
        print("error: --height and --width must be divisible by 32", file=sys.stderr)
        return 2
    if args.frames < 9 or (args.frames - 1) % 8:
        print("error: --frames must be 9, 17, 25, ...", file=sys.stderr)
        return 2

    args.output_dir.mkdir(parents=True, exist_ok=True)
    before = set(args.output_dir.glob("*.mp4"))
    command = [
        str(PYTHON),
        "inference.py",
        "--prompt", args.prompt.strip(),
        "--output-path", str(args.output_dir.resolve()),
        "--pipeline-config", str(CONFIG),
        "--height", str(args.height),
        "--width", str(args.width),
        "--num-frames", str(args.frames),
        "--frame-rate", str(args.fps),
        "--seed", str(args.seed),
    ]
    if args.offload_to_cpu:
        command.extend(["--offload-to-cpu", "true"])
    env = os.environ.copy()
    env.setdefault("PYTORCH_ENABLE_MPS_FALLBACK", "1")
    env.setdefault("TOKENIZERS_PARALLELISM", "false")
    result = subprocess.run(command, cwd=RUNTIME, env=env, check=False)
    if result.returncode != 0:
        return result.returncode
    created = sorted(set(args.output_dir.glob("*.mp4")) - before, key=lambda p: p.stat().st_mtime)
    if not created:
        print("error: LTX completed without a new MP4", file=sys.stderr)
        return 1
    print(created[-1])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
