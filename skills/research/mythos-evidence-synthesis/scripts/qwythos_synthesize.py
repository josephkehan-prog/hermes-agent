#!/usr/bin/env python3
"""Run bounded no-tool evidence synthesis through the local Qwythos model."""

from __future__ import annotations

import argparse
import json
import sys
import urllib.error
import urllib.request
from pathlib import Path


MODEL = "hf.co/huihui-ai/Huihui-Qwythos-9B-Claude-Mythos-5-1M-abliterated-GGUF:Q6_K"
ENDPOINT = "http://127.0.0.1:11434/api/chat"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    source = parser.add_mutually_exclusive_group()
    source.add_argument("--packet", help="Bounded evidence packet supplied directly")
    source.add_argument("--packet-file", type=Path, help="UTF-8 evidence packet")
    parser.add_argument(
        "--system",
        default=(
            "Synthesize only the supplied evidence. Separate source claims from inference, "
            "preserve contradictions and uncertainty, and cite the packet's source IDs. Do not "
            "infer statistical significance or generalizability from effect size or sample size "
            "alone. When evidence is insufficient, say so. Do not invent facts, assumptions, "
            "commands, or external evidence."
        ),
    )
    parser.add_argument("--output", type=Path)
    parser.add_argument("--num-ctx", type=int, default=32768)
    parser.add_argument("--num-predict", type=int, default=4096)
    parser.add_argument("--temperature", type=float, default=0.2)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--timeout", type=float, default=900)
    return parser.parse_args()


def load_packet(args: argparse.Namespace) -> str:
    if args.packet_file:
        packet = args.packet_file.read_text(encoding="utf-8")
    elif args.packet is not None:
        packet = args.packet
    elif not sys.stdin.isatty():
        packet = sys.stdin.read()
    else:
        raise ValueError("provide --packet, --packet-file, or piped stdin")
    packet = packet.strip()
    if not packet:
        raise ValueError("evidence packet is empty")
    return packet


def synthesize(args: argparse.Namespace, packet: str) -> str:
    if not 8192 <= args.num_ctx <= 131072:
        raise ValueError("--num-ctx must be between 8192 and 131072")
    if not 1 <= args.num_predict <= 8192:
        raise ValueError("--num-predict must be between 1 and 8192")
    if not 0 <= args.temperature <= 1:
        raise ValueError("--temperature must be between 0 and 1")
    payload = {
        "model": MODEL,
        "messages": [
            {"role": "system", "content": args.system},
            {"role": "user", "content": packet},
        ],
        "stream": False,
        "think": False,
        "options": {
            "num_ctx": args.num_ctx,
            "num_predict": args.num_predict,
            "temperature": args.temperature,
            "seed": args.seed,
        },
    }
    request = urllib.request.Request(
        ENDPOINT,
        data=json.dumps(payload).encode("utf-8"),
        headers={"content-type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=args.timeout) as response:
            result = json.load(response)
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"Ollama returned HTTP {exc.code}: {detail}") from exc
    except urllib.error.URLError as exc:
        raise RuntimeError(f"cannot reach Ollama at {ENDPOINT}: {exc.reason}") from exc
    content = str((result.get("message") or {}).get("content") or "").strip()
    if not content:
        raise RuntimeError("Qwythos returned empty content")
    return content


def main() -> int:
    args = parse_args()
    try:
        content = synthesize(args, load_packet(args))
        if args.output:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(content + "\n", encoding="utf-8")
            print(args.output)
        else:
            print(content)
    except (OSError, RuntimeError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
