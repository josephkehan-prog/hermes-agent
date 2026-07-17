#!/usr/bin/env python3
"""Route a narrow production request to one allowlisted hidden profile."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from dataclasses import asdict, dataclass
from pathlib import Path


PROFILE_MAP = {
    "screenplay": ("scriptroom", "Scriptroom", "Quill", "screenplay-production"),
    "audiobook": ("narrator", "Narrator", "Composer", "audiobook-narration-production"),
    "transcript-caption": ("caption", "Caption", "Director", "transcript-caption-production"),
    "structured-document": ("extractor", "Extractor", "Archivist", "structured-document-extraction"),
    "previsualization": ("previs", "Previs", "Director", "previsualization-production"),
}

ALIASES = {
    "screenplay": "screenplay",
    "script": "screenplay",
    "screenwriting": "screenplay",
    "teleplay": "screenplay",
    "audiobook": "audiobook",
    "narration": "audiobook",
    "tts": "audiobook",
    "voiceover": "audiobook",
    "transcript": "transcript-caption",
    "transcription": "transcript-caption",
    "caption": "transcript-caption",
    "captions": "transcript-caption",
    "subtitle": "transcript-caption",
    "subtitles": "transcript-caption",
    "structured-document": "structured-document",
    "document-extraction": "structured-document",
    "extractor": "structured-document",
    "ocr-json": "structured-document",
    "previsualization": "previsualization",
    "previs": "previsualization",
    "storyboard": "previsualization",
    "animatic": "previsualization",
}

SIGNALS = {
    "screenplay": (
        "screenplay", "screenwriting", "teleplay", "stage script",
        "scripted podcast", "slugline", "beat sheet", "script adaptation",
    ),
    "audiobook": (
        "audiobook", "narration", "narrated", "voiceover", "voice-over",
        "text to speech", "text-to-speech", "tts", "spoken word",
    ),
    "transcript-caption": (
        "transcript", "transcription", "captions", "captioning", "subtitles",
        "subtitle", "srt", "vtt", "speech to text", "speech-to-text",
    ),
    "structured-document": (
        "extract fields", "structured extraction", "invoice json", "receipt json",
        "form to json", "schema to json", "table extraction", "document extraction",
    ),
    "previsualization": (
        "previsualization", "previs", "storyboard", "animatic", "shot proof",
        "camera blocking", "concept trailer", "image to video proof",
    ),
}

ARTIFACT_CONTRACTS = {
    "screenplay": "Use BEAT-SHEET.md, SCENE-LEDGER.md, and SCRIPT.fountain or SCRIPT.md; never invent a code converter unless explicitly requested.",
    "audiobook": "Use source text, VOICE-LEDGER.md, audition/final WAV files, and an ffprobe/listening QA record.",
    "transcript-caption": "Use raw timed JSON, corrected transcript, SRT/VTT, correction ledger, and playback QA.",
    "structured-document": "Use declared schema, validated JSON, field-to-page evidence map, and rejected-field ledger.",
    "previsualization": "Use SHOT-LEDGER.md, board/contact-sheet paths, optional fixed-seed motion proof, and inspection notes.",
}


@dataclass(frozen=True)
class Route:
    status: str
    niche: str | None
    profile: str | None
    callsign: str | None
    lead: str | None
    skill: str | None
    tied_niches: tuple[str, ...] = ()


def canonical_niche(value: str) -> str:
    key = " ".join(value.lower().strip().split())
    if key not in ALIASES:
        raise ValueError(f"unknown niche {value!r}; use one of: {', '.join(PROFILE_MAP)}")
    return ALIASES[key]


def _resolved(niche: str) -> Route:
    profile, callsign, lead, skill = PROFILE_MAP[niche]
    return Route("routed", niche, profile, callsign, lead, skill)


def route_brief(brief: str, explicit_niche: str | None = None) -> Route:
    if explicit_niche:
        return _resolved(canonical_niche(explicit_niche))
    text = " ".join(brief.lower().split())
    scores = {
        niche: sum(1 for signal in signals if signal in text)
        for niche, signals in SIGNALS.items()
    }
    best = max(scores.values(), default=0)
    winners = tuple(sorted(niche for niche, score in scores.items() if score == best and score > 0))
    if not winners:
        return Route("needs_clarification", None, None, None, None, None)
    if len(winners) > 1:
        return Route("needs_clarification", None, None, None, None, None, winners)
    return _resolved(winners[0])


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
        raise ValueError("brief is empty")
    return brief


def invocation_command(route: Route, brief: str) -> list[str]:
    if route.status != "routed" or not all((route.profile, route.niche, route.skill, route.lead)):
        raise ValueError("cannot invoke without one resolved route")
    prompt = (
        f"You are the hidden {route.niche} specialist behind {route.lead}. "
        f"Load {route.skill}. Execute only the bounded niche stage requested by the brief. "
        "Return a compact handoff containing inputs, decisions, runtime/model preflight, artifacts or "
        "planned artifacts, validation evidence, limitations, and the next action for the visible lead. "
        "Never claim a runtime/model preflight unless you executed its documented command and can name the evidence; otherwise report not_run. "
        "When required source input is absent, return blocked-input with the exact missing input and do not invent implementation artifacts. "
        f"Artifact contract: {ARTIFACT_CONTRACTS[str(route.niche)]} "
        "Do not activate profiles, change Hermes configuration, download models, or widen scope.\n\n"
        f"SPECIALIST BRIEF\n{brief}"
    )
    return [
        "hermes", "-p", str(route.profile), "--skills", str(route.skill),
        "-t", "code_execution,clarify", "-z", prompt,
    ]


def invoke(route: Route, brief: str, workdir: Path, timeout: float) -> str:
    profile_dir = Path.home() / ".hermes" / "profiles" / str(route.profile)
    if not profile_dir.is_dir():
        raise RuntimeError(f"hidden profile is not installed: {profile_dir}")
    if not workdir.is_dir():
        raise ValueError(f"workdir does not exist: {workdir}")
    result = subprocess.run(
        invocation_command(route, brief), cwd=workdir, text=True,
        capture_output=True, timeout=timeout, check=False,
    )
    if result.returncode != 0:
        detail = result.stderr.strip() or result.stdout.strip() or f"exit {result.returncode}"
        raise RuntimeError(f"hidden profile failed: {detail}")
    output = result.stdout.strip()
    if not output:
        raise RuntimeError("hidden profile returned empty output")
    return output


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    source = parser.add_mutually_exclusive_group()
    source.add_argument("--brief")
    source.add_argument("--brief-file", type=Path)
    parser.add_argument("--niche")
    parser.add_argument("--invoke", action="store_true")
    parser.add_argument("--workdir", type=Path, default=Path.cwd())
    parser.add_argument("--output", type=Path)
    parser.add_argument("--timeout", type=float, default=900.0)
    parser.add_argument("--json", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        brief = load_brief(args)
        route = route_brief(brief, args.niche)
        if route.status != "routed":
            message = "Primary niche is ambiguous; ask for one primary deliverable."
            print(json.dumps(asdict(route), indent=2) if args.json else message)
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
