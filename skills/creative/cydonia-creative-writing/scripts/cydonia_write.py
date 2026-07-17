#!/usr/bin/env python3
"""Generate prose with the local Cydonia model through Ollama's native API."""

from __future__ import annotations

import argparse
import json
import sys
import urllib.error
import urllib.request
from pathlib import Path


MODEL = "hf.co/mradermacher/Cydonia-24B-v4.3-heretic-v4-i1-GGUF:Q4_K_M"
ENDPOINT = "http://127.0.0.1:11434/api/chat"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    source = parser.add_mutually_exclusive_group()
    source.add_argument("--prompt", help="Writing brief supplied directly")
    source.add_argument("--prompt-file", type=Path, help="UTF-8 writing brief")
    parser.add_argument(
        "--system",
        default="Write vivid, specific prose that follows the brief exactly.",
        help="System direction for voice and constraints",
    )
    parser.add_argument("--output", type=Path, help="Write prose to this UTF-8 file")
    parser.add_argument("--num-ctx", type=int, default=32768)
    parser.add_argument("--num-predict", type=int, default=2048)
    parser.add_argument(
        "--mode",
        choices=("creative", "revision"),
        default="creative",
        help="Creative sampling for drafts or seeded lower-temperature revision",
    )
    parser.add_argument("--temperature", type=float)
    parser.add_argument("--seed", type=int)
    parser.add_argument("--timeout", type=float, default=600.0)
    return parser.parse_args()


def load_prompt(args: argparse.Namespace) -> str:
    if args.prompt_file:
        prompt = args.prompt_file.read_text(encoding="utf-8")
    elif args.prompt is not None:
        prompt = args.prompt
    elif not sys.stdin.isatty():
        prompt = sys.stdin.read()
    else:
        raise ValueError("provide --prompt, --prompt-file, or piped stdin")
    prompt = prompt.strip()
    if not prompt:
        raise ValueError("writing brief is empty")
    return prompt


def generate(args: argparse.Namespace, prompt: str) -> str:
    if not 4096 <= args.num_ctx <= 65536:
        raise ValueError("--num-ctx must be between 4096 and 65536")
    if not 1 <= args.num_predict <= 8192:
        raise ValueError("--num-predict must be between 1 and 8192")
    temperature = (
        args.temperature
        if args.temperature is not None
        else (0.35 if args.mode == "revision" else 0.85)
    )
    seed = args.seed if args.seed is not None else (42 if args.mode == "revision" else None)
    if not 0.0 <= temperature <= 2.0:
        raise ValueError("--temperature must be between 0 and 2")

    options: dict[str, int | float] = {
        "num_ctx": args.num_ctx,
        "num_predict": args.num_predict,
        "temperature": temperature,
    }
    if seed is not None:
        options["seed"] = seed

    payload = {
        "model": MODEL,
        "messages": [
            {"role": "system", "content": args.system},
            {"role": "user", "content": prompt},
        ],
        "stream": False,
        "think": False,
        "options": options,
    }
    request = urllib.request.Request(
        ENDPOINT,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
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
        raise RuntimeError("Cydonia returned empty content")
    return content


def main() -> int:
    args = parse_args()
    try:
        content = generate(args, load_prompt(args))
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
