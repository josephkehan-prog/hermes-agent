#!/usr/bin/env python3
"""Preflight or render local Kokoro narration with artifact verification."""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
import sys
from pathlib import Path


MODEL_ROOT = Path.home() / ".cache" / "huggingface" / "hub" / "models--hexgrad--Kokoro-82M"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def cached_voice(voice: str) -> Path | None:
    return next(iter(MODEL_ROOT.glob(f"snapshots/*/voices/{voice}.pt")), None)


def cached_model() -> Path | None:
    return next(iter(MODEL_ROOT.glob("snapshots/*/kokoro-v1_0.pth")), None)


def preflight(voice: str) -> dict[str, object]:
    checks = {
        "kokoro_cli": bool(shutil.which("kokoro")),
        "ffprobe": bool(shutil.which("ffprobe")),
        "model": bool(cached_model()),
        "voice": bool(cached_voice(voice)),
        "voice_id": voice,
    }
    checks["ready"] = all(checks[key] for key in ("kokoro_cli", "ffprobe", "model", "voice"))
    return checks


def load_text(args: argparse.Namespace) -> str:
    if args.text_file:
        text = args.text_file.read_text(encoding="utf-8")
    elif args.text is not None:
        text = args.text
    else:
        raise ValueError("provide --text or --text-file")
    text = text.strip()
    if not text:
        raise ValueError("narration text is empty")
    if len(text) > 50_000:
        raise ValueError("text exceeds 50,000 characters; render chapter sections separately")
    return text


def probe(path: Path) -> dict[str, object]:
    result = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "stream=codec_name,sample_rate,channels",
         "-show_entries", "format=duration,size", "-of", "json", str(path)],
        text=True, capture_output=True, check=False,
    )
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or "ffprobe failed")
    return json.loads(result.stdout)


def render(args: argparse.Namespace) -> dict[str, object]:
    checks = preflight(args.voice)
    if not checks["ready"]:
        raise RuntimeError(f"Kokoro preflight failed: {json.dumps(checks, sort_keys=True)}")
    if not 0.5 <= args.speed <= 2.0:
        raise ValueError("--speed must be between 0.5 and 2.0")
    output = args.output.expanduser().resolve()
    if output.suffix.lower() != ".wav":
        raise ValueError("--output must end in .wav")
    if output.exists() and not args.overwrite:
        raise ValueError(f"output exists; pass --overwrite: {output}")
    output.parent.mkdir(parents=True, exist_ok=True)
    text = load_text(args)
    command = [
        str(shutil.which("kokoro")), "--text", text, "--voice", args.voice,
        "--language", args.language or args.voice[0], "--speed", str(args.speed),
        "--output-file", str(output),
    ]
    result = subprocess.run(command, text=True, capture_output=True, check=False, timeout=args.timeout)
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or result.stdout.strip() or "Kokoro failed")
    if not output.is_file() or output.stat().st_size == 0:
        raise RuntimeError("Kokoro produced no audio")
    return {
        "ready": True,
        "model": "hexgrad/Kokoro-82M",
        "voice": args.voice,
        "language": args.language or args.voice[0],
        "speed": args.speed,
        "source_sha256": hashlib.sha256(text.encode("utf-8")).hexdigest(),
        "output": str(output),
        "output_sha256": sha256(output),
        "probe": probe(output),
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    check = sub.add_parser("preflight")
    check.add_argument("--voice", default="af_heart")
    make = sub.add_parser("render")
    source = make.add_mutually_exclusive_group(required=True)
    source.add_argument("--text")
    source.add_argument("--text-file", type=Path)
    make.add_argument("--voice", default="af_heart")
    make.add_argument("--language", choices=list("abhefipjz"))
    make.add_argument("--speed", type=float, default=1.0)
    make.add_argument("--output", type=Path, required=True)
    make.add_argument("--overwrite", action="store_true")
    make.add_argument("--timeout", type=float, default=1800.0)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        payload = preflight(args.voice) if args.command == "preflight" else render(args)
        print(json.dumps(payload, indent=2))
        return 0 if payload.get("ready") else 2
    except (OSError, RuntimeError, ValueError, subprocess.TimeoutExpired) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
