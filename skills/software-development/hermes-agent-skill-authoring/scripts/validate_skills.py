#!/usr/bin/env python3
"""Validate Hermes skill packages and orchestration-bundle invariants."""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

import yaml


NAME_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
MAX_NAME_LENGTH = 64
MAX_DESCRIPTION_LENGTH = 1024
MAX_CONTENT_LENGTH = 100_000
# Local-model context budget: bodies above FAIL must split into references/;
# bodies above WARN should consider it (~4 chars/token, so 12k ≈ 3k tokens).
MAX_BODY_LENGTH_FAIL = 12_000
BODY_LENGTH_WARN = 8_000


def repository_root() -> Path:
    return Path(__file__).resolve().parents[4]


def parse_skill(path: Path) -> tuple[dict, str]:
    content = path.read_text(encoding="utf-8")
    if not content.startswith("---\n"):
        raise ValueError("frontmatter must start at byte zero")
    end = content.find("\n---\n", 4)
    if end < 0:
        raise ValueError("frontmatter closing delimiter is missing")
    frontmatter = yaml.safe_load(content[4:end])
    if not isinstance(frontmatter, dict):
        raise ValueError("frontmatter must be a YAML mapping")
    body = content[end + 5 :].strip()
    if not body:
        raise ValueError("Markdown body is empty")
    return frontmatter, content


def skill_body(content: str) -> str:
    end = content.find("\n---\n", 4)
    return content[end + 5 :].strip() if end >= 0 else content.strip()


def skill_index(root: Path) -> dict[str, list[Path]]:
    index: dict[str, list[Path]] = {}
    paths = sorted(root.glob("skills/**/SKILL.md")) + sorted(
        root.glob("optional-skills/**/SKILL.md")
    )
    for path in paths:
        try:
            frontmatter, _ = parse_skill(path)
        except (OSError, ValueError, yaml.YAMLError):
            # A malformed unrelated skill must not prevent targeted validation.
            # If it is a requested target, validate() reports its precise error.
            continue
        name = frontmatter.get("name")
        if not isinstance(name, str) or not name:
            continue
        index.setdefault(name, []).append(path)
    return index


def validate(path: Path, index: dict[str, list[Path]]) -> list[str]:
    errors, _ = validate_with_warnings(path, index)
    return errors


def validate_with_warnings(
    path: Path, index: dict[str, list[Path]]
) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []
    try:
        frontmatter, content = parse_skill(path)
    except (OSError, ValueError, yaml.YAMLError) as exc:
        return [str(exc)], warnings

    name = frontmatter.get("name")
    description = frontmatter.get("description")
    if not isinstance(name, str) or not name:
        errors.append("name is required")
    else:
        if len(name) > MAX_NAME_LENGTH or not NAME_RE.fullmatch(name):
            errors.append("name must be <=64 characters of lowercase letters, digits, and hyphens")
        if path.parent.name != name:
            errors.append(f"directory {path.parent.name!r} does not match name {name!r}")
    if not isinstance(description, str) or not description.strip():
        errors.append("description is required")
    elif len(description) > MAX_DESCRIPTION_LENGTH:
        errors.append(f"description exceeds {MAX_DESCRIPTION_LENGTH} characters")
    if len(content) > MAX_CONTENT_LENGTH:
        errors.append(f"content exceeds {MAX_CONTENT_LENGTH} characters")
    body_length = len(skill_body(content))
    if body_length > MAX_BODY_LENGTH_FAIL:
        errors.append(
            f"body exceeds {MAX_BODY_LENGTH_FAIL} characters ({body_length}); "
            "split detail into references/"
        )
    elif body_length > BODY_LENGTH_WARN:
        warnings.append(
            f"body exceeds {BODY_LENGTH_WARN} characters ({body_length}); "
            "consider a references/ split"
        )

    metadata = frontmatter.get("metadata", {})
    if not isinstance(metadata, dict):
        errors.append("metadata must be a mapping")
        return errors, warnings
    hermes = metadata.get("hermes", {})
    if not isinstance(hermes, dict):
        errors.append("metadata.hermes must be a mapping")
        return errors, warnings
    related = hermes.get("related_skills", [])
    if not isinstance(related, list) or any(not isinstance(item, str) for item in related):
        errors.append("metadata.hermes.related_skills must be a list of names")
        related = []
    if len(related) != len(set(related)):
        errors.append("related_skills contains duplicates")
    if name in related:
        errors.append("skill cannot reference itself")

    if hermes.get("bundle") is True:
        domain = hermes.get("domain")
        if not isinstance(domain, str) or not NAME_RE.fullmatch(domain):
            errors.append("bundle skills require a lowercase hyphenated domain")
        if len(related) < 3:
            errors.append("bundle skills require at least three related_skills")
        missing = sorted(member for member in related if member not in index)
        if missing:
            errors.append(f"bundle members do not resolve in-repo: {', '.join(missing)}")
        # A skill shipped in both skills/ and optional-skills/ resolves to the
        # active (skills/) copy, so it is not ambiguous for bundle routing.
        def _active_paths(member: str) -> list[Path]:
            paths = index.get(member, [])
            active = [p for p in paths if "optional-skills" not in p.parts]
            return active or paths

        ambiguous = sorted(member for member in related if len(_active_paths(member)) > 1)
        if ambiguous:
            errors.append(f"bundle members resolve ambiguously in-repo: {', '.join(ambiguous)}")
        required_headings = (
            "## Routing Table",
            "## Orchestration Workflow",
            "## Handoff Record",
            "## Stop Conditions",
            "## Completion Gate",
        )
        for heading in required_headings:
            if heading not in content:
                errors.append(f"bundle is missing required heading: {heading}")
    return errors, warnings


def target_files(arguments: list[str]) -> list[Path]:
    files: list[Path] = []
    for argument in arguments:
        path = Path(argument).resolve()
        files.append(path / "SKILL.md" if path.is_dir() else path)
    return files


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("paths", nargs="+", help="Skill directories or SKILL.md files")
    args = parser.parse_args()
    root = repository_root()
    index = skill_index(root)

    failed = False
    for path in target_files(args.paths):
        errors, warnings = validate_with_warnings(path, index)
        label = path.relative_to(root) if path.is_relative_to(root) else path
        for warning in warnings:
            print(f"{label}: WARN: {warning}", file=sys.stderr)
        if errors:
            failed = True
            for error in errors:
                print(f"{label}: ERROR: {error}", file=sys.stderr)
        else:
            print(f"{label}: OK")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
