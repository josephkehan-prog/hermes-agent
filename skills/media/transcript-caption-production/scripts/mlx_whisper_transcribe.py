#!/usr/bin/env python3
"""Transcribe local media with isolated MLX Whisper and write JSON/SRT."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path


RUNTIME_PYTHON = Path.home() / "mac" / "Hermes" / "runtimes" / "mlx-whisper" / ".venv" / "bin" / "python"
MODEL = "mlx-community/whisper-large-v3-turbo"
MODEL_ROOT = Path.home() / ".cache" / "huggingface" / "hub" / "models--mlx-community--whisper-large-v3-turbo"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def preflight() -> dict[str, object]:
    runtime = RUNTIME_PYTHON.is_file()
    model = any(MODEL_ROOT.glob("snapshots/*/weights.safetensors"))
    import_ok = False
    if runtime:
        result = subprocess.run(
            [str(RUNTIME_PYTHON), "-c", "import mlx_whisper"],
            text=True, capture_output=True, check=False,
        )
        import_ok = result.returncode == 0
    return {
        "runtime_python": runtime,
        "mlx_whisper": import_ok,
        "model": model,
        "model_id": MODEL,
        "ready": runtime and import_ok and model,
    }


def srt_time(seconds: float) -> str:
    milliseconds = max(0, round(float(seconds) * 1000))
    hours, remainder = divmod(milliseconds, 3_600_000)
    minutes, remainder = divmod(remainder, 60_000)
    secs, millis = divmod(remainder, 1000)
    return f"{hours:02}:{minutes:02}:{secs:02},{millis:03}"


def write_srt(segments: list[dict[str, object]], path: Path) -> None:
    cues: list[str] = []
    last_end = 0.0
    for index, segment in enumerate(segments, 1):
        start = max(last_end, float(segment.get("start", 0.0)))
        end = max(start, float(segment.get("end", start)))
        text = " ".join(str(segment.get("text", "")).split())
        if not text:
            continue
        cues.append(f"{index}\n{srt_time(start)} --> {srt_time(end)}\n{text}\n")
        last_end = end
    path.write_text("\n".join(cues), encoding="utf-8")


def worker(args: argparse.Namespace) -> int:
    import mlx_whisper

    kwargs: dict[str, object] = {"path_or_hf_repo": MODEL, "temperature": 0.0}
    if args.language:
        kwargs["language"] = args.language
    result = mlx_whisper.transcribe(str(args.input), **kwargs)
    segments = [
        {"start": float(s.get("start", 0.0)), "end": float(s.get("end", 0.0)), "text": str(s.get("text", ""))}
        for s in result.get("segments", [])
    ]
    payload = {
        "model": MODEL,
        "source": str(args.input),
        "source_sha256": sha256(args.input),
        "language": result.get("language", args.language),
        "text": result.get("text", "").strip(),
        "segments": segments,
    }
    args.output_json.parent.mkdir(parents=True, exist_ok=True)
    args.output_srt.parent.mkdir(parents=True, exist_ok=True)
    args.output_json.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    write_srt(segments, args.output_srt)
    print(json.dumps({
        "ready": True,
        "model": MODEL,
        "source": str(args.input),
        "output_json": str(args.output_json),
        "output_srt": str(args.output_srt),
        "segments": len(segments),
    }, indent=2))
    return 0


def run_transcription(args: argparse.Namespace) -> int:
    checks = preflight()
    if not checks["ready"]:
        raise RuntimeError(f"MLX Whisper preflight failed: {json.dumps(checks, sort_keys=True)}")
    source = args.input.expanduser().resolve()
    if not source.is_file():
        raise ValueError(f"input does not exist: {source}")
    output_json = args.output_json.expanduser().resolve()
    output_srt = args.output_srt.expanduser().resolve()
    for output in (output_json, output_srt):
        if output.exists() and not args.overwrite:
            raise ValueError(f"output exists; pass --overwrite: {output}")
    command = [
        str(RUNTIME_PYTHON), str(Path(__file__).resolve()), "_worker",
        "--input", str(source), "--output-json", str(output_json),
        "--output-srt", str(output_srt),
    ]
    if args.language:
        command.extend(["--language", args.language])
    result = subprocess.run(command, text=True, capture_output=True, check=False, timeout=args.timeout)
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or result.stdout.strip() or "MLX Whisper failed")
    print(result.stdout.strip())
    return 0


def add_transcribe_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output-json", type=Path, required=True)
    parser.add_argument("--output-srt", type=Path, required=True)
    parser.add_argument("--language")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("preflight")
    transcribe = sub.add_parser("transcribe")
    add_transcribe_args(transcribe)
    transcribe.add_argument("--overwrite", action="store_true")
    transcribe.add_argument("--timeout", type=float, default=1800.0)
    worker_parser = sub.add_parser("_worker", help=argparse.SUPPRESS)
    add_transcribe_args(worker_parser)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        if args.command == "preflight":
            payload = preflight()
            print(json.dumps(payload, indent=2))
            return 0 if payload["ready"] else 2
        if args.command == "_worker":
            return worker(args)
        return run_transcription(args)
    except (OSError, RuntimeError, ValueError, subprocess.TimeoutExpired) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
