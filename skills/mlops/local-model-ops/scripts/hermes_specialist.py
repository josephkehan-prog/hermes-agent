#!/usr/bin/env python3
"""Route bounded no-tool prompts to Hermes local specialist models."""

from __future__ import annotations

import argparse
import base64
import json
import sys
import urllib.error
import urllib.request
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any


OLLAMA_CHAT = "http://127.0.0.1:11434/api/chat"
OLLAMA_TAGS = "http://127.0.0.1:11434/api/tags"
SWAP_CHAT = "http://127.0.0.1:1235/v1/chat/completions"
SWAP_MODELS = "http://127.0.0.1:1235/v1/models"


@dataclass(frozen=True)
class Route:
    endpoint: str
    model: str
    context: int
    system: str
    image: bool = False


ROUTES: dict[str, Route] = {
    "research": Route(
        "ollama",
        "hf.co/huihui-ai/Huihui-Qwythos-9B-Claude-Mythos-5-1M-abliterated-GGUF:Q6_K",
        32768,
        "Synthesize only supplied evidence. Separate claims, confidence, and caveats. "
        "Do not infer statistical significance or generalizability from effect size or sample size alone. "
        "When evidence is insufficient, say so. Do not invent sources or assumptions.",
        True,
    ),
    "vision-fast": Route(
        "ollama",
        "hf.co/prithivMLmods/Qwen3-VL-8B-Instruct-abliterated-v2-GGUF:Q6_K",
        16384,
        "Inspect images precisely. Distinguish visible facts from inference. Be concise.",
        True,
    ),
    "vision-quality": Route(
        "ollama",
        "qwen3-vl:30b-a3b-instruct",
        32768,
        "Inspect images precisely. Distinguish visible facts from inference and uncertainty.",
        True,
    ),
    "writer": Route(
        "ollama",
        "hf.co/mradermacher/Cydonia-24B-v4.3-heretic-v4-i1-GGUF:Q4_K_M",
        32768,
        "Write vivid, specific prose in the requested voice. Preserve constraints and continuity.",
    ),
    "code": Route(
        "swap",
        "ornith-uncensored",
        65536,
        "Solve the coding task precisely. Prefer minimal, testable changes and state assumptions.",
    ),
    "think": Route(
        "swap",
        "qwen3.6-think",
        65536,
        "Reason carefully, then provide a concise final answer.",
    ),
    "controller": Route(
        "swap",
        "agents-a1",
        65536,
        "Plan and coordinate the task. Do not claim tool actions that were not performed.",
    ),
}


def request_json(url: str, payload: dict[str, Any] | None, timeout: int) -> dict[str, Any]:
    body = None if payload is None else json.dumps(payload).encode("utf-8")
    request = urllib.request.Request(url, data=body)
    if body is not None:
        request.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return json.load(response)
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", "replace")
        raise RuntimeError(f"HTTP {exc.code} from {url}: {detail[:500]}") from exc
    except urllib.error.URLError as exc:
        raise RuntimeError(f"Cannot reach {url}: {exc.reason}") from exc


def route_status() -> list[dict[str, Any]]:
    ollama = request_json(OLLAMA_TAGS, None, 5)
    swap = request_json(SWAP_MODELS, None, 5)
    ollama_ids = {item.get("name", "") for item in ollama.get("models", [])}
    swap_ids = {item.get("id", "") for item in swap.get("data", [])}
    rows = []
    for name, route in ROUTES.items():
        available = route.model in (ollama_ids if route.endpoint == "ollama" else swap_ids)
        rows.append({"role": name, **asdict(route), "available": available})
    return rows


def read_prompt(args: argparse.Namespace) -> str:
    if args.prompt_file:
        return Path(args.prompt_file).expanduser().read_text(encoding="utf-8")
    if args.prompt is not None:
        return args.prompt
    if not sys.stdin.isatty():
        return sys.stdin.read()
    raise RuntimeError("Supply --prompt, --prompt-file, or piped stdin")


def encode_image(path: str) -> str:
    image_path = Path(path).expanduser()
    if not image_path.is_file():
        raise RuntimeError(f"Image not found: {image_path}")
    return base64.b64encode(image_path.read_bytes()).decode("ascii")


def run_route(args: argparse.Namespace) -> tuple[str, dict[str, Any]]:
    route = ROUTES[args.role]
    if args.image and not route.image:
        raise RuntimeError(f"Role {args.role!r} does not accept images")
    prompt = read_prompt(args).strip()
    if not prompt:
        raise RuntimeError("Prompt is empty")
    system = args.system or route.system
    context = args.context or route.context
    if not 4096 <= context <= route.context:
        raise RuntimeError(f"Context for {args.role!r} must be between 4096 and {route.context}")
    if not 1 <= args.max_tokens <= 8192:
        raise RuntimeError("--max-tokens must be between 1 and 8192")
    if not 0 <= args.temperature <= 2:
        raise RuntimeError("--temperature must be between 0 and 2")

    if route.endpoint == "ollama":
        message: dict[str, Any] = {"role": "user", "content": prompt}
        if args.image:
            message["images"] = [encode_image(args.image)]
        payload = {
            "model": route.model,
            "stream": False,
            "think": False,
            "keep_alive": args.keep_alive,
            "messages": [{"role": "system", "content": system}, message],
            "options": {
                "num_ctx": context,
                "num_predict": args.max_tokens,
                "temperature": args.temperature,
            },
        }
        response = request_json(OLLAMA_CHAT, payload, args.timeout)
        content = response.get("message", {}).get("content", "")
    else:
        if args.image:
            raise RuntimeError("Image input is supported only on Ollama specialist routes")
        payload = {
            "model": route.model,
            "stream": False,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": prompt},
            ],
            "max_tokens": args.max_tokens,
            "temperature": args.temperature,
        }
        response = request_json(SWAP_CHAT, payload, args.timeout)
        choices = response.get("choices", [])
        content = choices[0].get("message", {}).get("content", "") if choices else ""

    if not content:
        raise RuntimeError(f"Role {args.role!r} returned empty content")
    return content, response


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    list_parser = sub.add_parser("list", help="Show routes without loading models")
    list_parser.add_argument("--json", action="store_true")
    check_parser = sub.add_parser("check", help="Check route availability without generation")
    check_parser.add_argument("--json", action="store_true")
    run_parser = sub.add_parser("run", help="Run one bounded specialist request")
    run_parser.add_argument("role", choices=sorted(ROUTES))
    source = run_parser.add_mutually_exclusive_group()
    source.add_argument("--prompt")
    source.add_argument("--prompt-file")
    run_parser.add_argument("--image")
    run_parser.add_argument("--system")
    run_parser.add_argument("--context", type=int)
    run_parser.add_argument("--max-tokens", type=int, default=768)
    run_parser.add_argument("--temperature", type=float, default=0.2)
    run_parser.add_argument(
        "--keep-alive",
        default="0",
        help="Ollama retention after request (default: 0, unload immediately)",
    )
    run_parser.add_argument("--timeout", type=int, default=180)
    run_parser.add_argument("--output")
    run_parser.add_argument("--raw-json", action="store_true")
    return parser


def print_routes(rows: list[dict[str, Any]], as_json: bool, checked: bool) -> None:
    if as_json:
        print(json.dumps(rows, indent=2))
        return
    header = f"{'ROLE':<15} {'ENDPOINT':<8} {'CTX':>7} {'IMAGE':<5}"
    if checked:
        header += " STATUS"
    print(header + " MODEL")
    for row in rows:
        line = f"{row['role']:<15} {row['endpoint']:<8} {row['context']:>7} {str(row['image']):<5}"
        if checked:
            line += f" {'OK' if row['available'] else 'MISSING':<7}"
        print(f"{line} {row['model']}")


def main() -> int:
    args = build_parser().parse_args()
    try:
        if args.command == "list":
            rows = [{"role": name, **asdict(route)} for name, route in ROUTES.items()]
            print_routes(rows, args.json, checked=False)
            return 0
        if args.command == "check":
            rows = route_status()
            print_routes(rows, args.json, checked=True)
            return 0 if all(row["available"] for row in rows) else 2
        content, response = run_route(args)
        rendered = json.dumps(response, indent=2) if args.raw_json else content
        if args.output:
            output = Path(args.output).expanduser()
            output.parent.mkdir(parents=True, exist_ok=True)
            output.write_text(rendered.rstrip() + "\n", encoding="utf-8")
            print(output)
        else:
            print(rendered)
        return 0
    except (RuntimeError, OSError, ValueError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
