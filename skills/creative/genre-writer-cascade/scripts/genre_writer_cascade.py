#!/usr/bin/env python3
"""Route manuscript work to one allowlisted Hermes genre profile."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from dataclasses import asdict, dataclass
from pathlib import Path


PROFILE_MAP = {
    "romance": ("heartline", "Heartline"),
    "fantasy": ("spellbound", "Spellbound"),
    "science-fiction": ("orbit", "Orbit"),
    "horror": ("nocturne", "Nocturne"),
    "mystery-thriller": ("casefile", "Casefile"),
}

ALIASES = {
    "romance": "romance",
    "romantic": "romance",
    "rom-com": "romance",
    "romcom": "romance",
    "fantasy": "fantasy",
    "fantastical": "fantasy",
    "science-fiction": "science-fiction",
    "science fiction": "science-fiction",
    "sci-fi": "science-fiction",
    "scifi": "science-fiction",
    "sf": "science-fiction",
    "horror": "horror",
    "mystery": "mystery-thriller",
    "thriller": "mystery-thriller",
    "mystery-thriller": "mystery-thriller",
    "crime": "mystery-thriller",
    "suspense": "mystery-thriller",
}

SIGNALS = {
    "romance": ("romance", "romantic", "relationship arc", "love story", "rom-com", "romcom"),
    "fantasy": ("fantasy", "magic", "magical", "wizard", "dragon", "secondary world", "sword and sorcery", "mythic"),
    "science-fiction": ("science fiction", "sci-fi", "scifi", "space opera", "cyberpunk", "spaceship", "alien", "speculative technology"),
    "horror": ("horror", "dread", "terrifying", "haunted", "cosmic horror", "gothic horror", "supernatural fear"),
    "mystery-thriller": ("mystery", "thriller", "detective", "crime", "suspense", "whodunit", "serial killer", "clue"),
}


@dataclass(frozen=True)
class Route:
    status: str
    genre: str | None
    profile: str | None
    callsign: str | None
    tied_genres: tuple[str, ...] = ()


def canonical_genre(value: str) -> str:
    key = " ".join(value.lower().strip().split())
    if key not in ALIASES:
        allowed = ", ".join(PROFILE_MAP)
        raise ValueError(f"unknown genre {value!r}; use one of: {allowed}")
    return ALIASES[key]


def route_brief(brief: str, explicit_genre: str | None = None) -> Route:
    if explicit_genre:
        genre = canonical_genre(explicit_genre)
        profile, callsign = PROFILE_MAP[genre]
        return Route("routed", genre, profile, callsign)

    text = " ".join(brief.lower().split())
    scores = {
        genre: sum(1 for signal in signals if signal in text)
        for genre, signals in SIGNALS.items()
    }
    best = max(scores.values(), default=0)
    winners = tuple(sorted(genre for genre, score in scores.items() if score == best and score > 0))
    if not winners:
        return Route("needs_clarification", None, None, None)
    if len(winners) > 1:
        return Route("needs_clarification", None, None, None, winners)
    genre = winners[0]
    profile, callsign = PROFILE_MAP[genre]
    return Route("routed", genre, profile, callsign)


def load_brief(args: argparse.Namespace) -> str:
    if args.brief_file:
        brief = args.brief_file.read_text(encoding="utf-8")
    elif args.brief is not None:
        brief = args.brief
    elif not sys.stdin.isatty():
        brief = sys.stdin.read()
    else:
        raise ValueError("provide --brief, --brief-file, or piped stdin")
    brief = brief.strip()
    if not brief:
        raise ValueError("manuscript brief is empty")
    return brief


def invocation_command(route: Route, brief: str) -> list[str]:
    if route.status != "routed" or not route.profile or not route.genre:
        raise ValueError("cannot invoke without one resolved route")
    prompt = (
        f"You are the standby {route.genre} manuscript specialist behind Quill. "
        "Use genre-novel-production. Return a bounded specialist handoff: primary reader promise, "
        "genre contract, story risks, canon/continuity needs, proposed artifacts, and the next chapter "
        "packet or requested deliverable. Preserve stated content boundaries. Do not change system or "
        "Hermes configuration. Quill owns final files, approvals, and delivery.\n\nMANUSCRIPT BRIEF\n"
        f"{brief}"
    )
    return [
        "hermes",
        "-p",
        route.profile,
        "--skills",
        "genre-novel-production",
        "-t",
        "code_execution,clarify",
        "-z",
        prompt,
    ]


def invoke(route: Route, brief: str, workdir: Path, timeout: float) -> str:
    profile_dir = Path.home() / ".hermes" / "profiles" / str(route.profile)
    if not profile_dir.is_dir():
        raise RuntimeError(f"standby profile is not installed: {profile_dir}")
    if not workdir.is_dir():
        raise ValueError(f"workdir does not exist: {workdir}")
    result = subprocess.run(
        invocation_command(route, brief),
        cwd=workdir,
        text=True,
        capture_output=True,
        timeout=timeout,
        check=False,
    )
    if result.returncode != 0:
        detail = result.stderr.strip() or result.stdout.strip() or f"exit {result.returncode}"
        raise RuntimeError(f"standby profile failed: {detail}")
    output = result.stdout.strip()
    if not output:
        raise RuntimeError("standby profile returned empty output")
    return output


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    source = parser.add_mutually_exclusive_group()
    source.add_argument("--brief", help="Manuscript brief supplied directly")
    source.add_argument("--brief-file", type=Path, help="UTF-8 manuscript brief")
    parser.add_argument("--genre", help="Explicit primary genre or alias")
    parser.add_argument("--invoke", action="store_true", help="Call the selected standby profile")
    parser.add_argument("--workdir", type=Path, default=Path.cwd())
    parser.add_argument("--output", type=Path, help="Write invoked handoff to this file")
    parser.add_argument("--timeout", type=float, default=900.0)
    parser.add_argument("--json", action="store_true", help="Print route metadata as JSON")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        brief = load_brief(args)
        route = route_brief(brief, args.genre)
        if route.status != "routed":
            print(json.dumps(asdict(route), indent=2) if args.json else "Primary genre is ambiguous; ask for one primary reader promise.")
            return 2
        if not args.invoke:
            print(json.dumps(asdict(route), indent=2) if args.json else f"{route.profile} ({route.callsign})")
            return 0
        handoff = invoke(route, brief, args.workdir.resolve(), args.timeout)
        if args.output:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(handoff + "\n", encoding="utf-8")
        if args.json:
            payload = asdict(route) | {"output": str(args.output.resolve()) if args.output else None}
            print(json.dumps(payload, indent=2))
        elif args.output:
            print(args.output)
        else:
            print(handoff)
    except (OSError, RuntimeError, ValueError, subprocess.TimeoutExpired) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
