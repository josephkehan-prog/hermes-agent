"""Regression tests for the in-repo Hermes skill authoring validator."""

from __future__ import annotations

import importlib.util
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SCRIPT = (
    ROOT
    / "skills"
    / "software-development"
    / "hermes-agent-skill-authoring"
    / "scripts"
    / "validate_skills.py"
)
SPEC = importlib.util.spec_from_file_location("hermes_skill_validator", SCRIPT)
assert SPEC and SPEC.loader
validator = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(validator)


def write_skill(
    path: Path,
    *,
    name: str,
    metadata: str = "{}",
    body: str = "# Test skill",
) -> Path:
    path.mkdir(parents=True)
    skill_md = path / "SKILL.md"
    skill_md.write_text(
        "---\n"
        f"name: {name}\n"
        'description: "Use when testing the validator."\n'
        f"metadata: {metadata}\n"
        "---\n\n"
        f"{body}\n",
        encoding="utf-8",
    )
    return skill_md


def test_non_mapping_metadata_is_reported_instead_of_raising(tmp_path: Path) -> None:
    skill_md = write_skill(tmp_path / "demo", name="demo", metadata="null")

    assert validator.validate(skill_md, {"demo": [skill_md]}) == [
        "metadata must be a mapping"
    ]


def test_skill_index_skips_unrelated_malformed_skill(tmp_path: Path) -> None:
    good = write_skill(tmp_path / "skills" / "category" / "good", name="good")
    bad = tmp_path / "skills" / "category" / "bad" / "SKILL.md"
    bad.parent.mkdir(parents=True)
    bad.write_text("not frontmatter", encoding="utf-8")

    assert validator.skill_index(tmp_path) == {"good": [good]}


def test_bundle_reports_missing_ambiguous_members_and_headings(tmp_path: Path) -> None:
    bundle = write_skill(
        tmp_path / "bundle",
        name="bundle",
        metadata=(
            "{hermes: {bundle: true, domain: demo, "
            "related_skills: [one, duplicate, missing]}}"
        ),
    )
    one = tmp_path / "one" / "SKILL.md"
    duplicate_a = tmp_path / "a" / "SKILL.md"
    duplicate_b = tmp_path / "b" / "SKILL.md"

    errors = validator.validate(
        bundle,
        {"bundle": [bundle], "one": [one], "duplicate": [duplicate_a, duplicate_b]},
    )

    assert "bundle members do not resolve in-repo: missing" in errors
    assert "bundle members resolve ambiguously in-repo: duplicate" in errors
    for heading in (
        "## Routing Table",
        "## Orchestration Workflow",
        "## Handoff Record",
        "## Stop Conditions",
        "## Completion Gate",
    ):
        assert f"bundle is missing required heading: {heading}" in errors


def test_body_over_fail_limit_is_error(tmp_path: Path) -> None:
    skill_md = write_skill(
        tmp_path / "big",
        name="big",
        body="x" * (validator.MAX_BODY_LENGTH_FAIL + 1),
    )

    errors = validator.validate(skill_md, {"big": [skill_md]})

    assert any("body exceeds" in error for error in errors)


def test_body_between_warn_and_fail_warns_but_passes(tmp_path: Path) -> None:
    skill_md = write_skill(
        tmp_path / "mid",
        name="mid",
        body="y" * (validator.BODY_LENGTH_WARN + 1),
    )

    errors, warnings = validator.validate_with_warnings(skill_md, {"mid": [skill_md]})

    assert errors == []
    assert any("body exceeds" in warning for warning in warnings)


def test_body_at_warn_limit_is_silent(tmp_path: Path) -> None:
    skill_md = write_skill(
        tmp_path / "ok",
        name="ok",
        body="z" * validator.BODY_LENGTH_WARN,
    )

    errors, warnings = validator.validate_with_warnings(skill_md, {"ok": [skill_md]})

    assert errors == []
    assert warnings == []


def test_bundle_member_shipped_in_both_trees_is_not_ambiguous(tmp_path: Path) -> None:
    bundle = write_skill(
        tmp_path / "skills" / "cat" / "bundle",
        name="bundle",
        metadata=(
            "{hermes: {bundle: true, domain: demo, "
            "related_skills: [dup, one, two]}}"
        ),
        body="# B\n## Routing Table\n## Orchestration Workflow\n"
        "## Handoff Record\n## Stop Conditions\n## Completion Gate",
    )
    active = tmp_path / "skills" / "cat" / "dup" / "SKILL.md"
    optional = tmp_path / "optional-skills" / "cat" / "dup" / "SKILL.md"
    index = {
        "bundle": [bundle],
        "dup": [active, optional],
        "one": [tmp_path / "skills" / "cat" / "one" / "SKILL.md"],
        "two": [tmp_path / "skills" / "cat" / "two" / "SKILL.md"],
    }

    errors = validator.validate(bundle, index)

    assert not any("ambiguously" in error for error in errors)


def test_skill_index_discovers_optional_skills(tmp_path: Path) -> None:
    core = write_skill(tmp_path / "skills" / "cat" / "core-skill", name="core-skill")
    optional = write_skill(
        tmp_path / "optional-skills" / "cat" / "opt-skill", name="opt-skill"
    )

    index = validator.skill_index(tmp_path)

    assert index == {"core-skill": [core], "opt-skill": [optional]}


BUNDLE_BODY = (
    "# B\n## Routing Table\n## Orchestration Workflow\n"
    "## Handoff Record\n## Stop Conditions\n## Completion Gate"
)


def test_active_bundle_rejects_optional_only_member(tmp_path: Path) -> None:
    bundle = write_skill(
        tmp_path / "skills" / "cat" / "bundle",
        name="bundle",
        metadata=(
            "{hermes: {bundle: true, domain: demo, "
            "related_skills: [opt-only, one, two]}}"
        ),
        body=BUNDLE_BODY,
    )
    index = {
        "bundle": [bundle],
        "opt-only": [tmp_path / "optional-skills" / "cat" / "opt-only" / "SKILL.md"],
        "one": [tmp_path / "skills" / "cat" / "one" / "SKILL.md"],
        "two": [tmp_path / "skills" / "cat" / "two" / "SKILL.md"],
    }

    errors = validator.validate(bundle, index, tmp_path)

    assert "bundle members resolve only under optional-skills: opt-only" in errors


def test_optional_bundle_may_reference_optional_members(tmp_path: Path) -> None:
    bundle = write_skill(
        tmp_path / "optional-skills" / "cat" / "bundle",
        name="bundle",
        metadata=(
            "{hermes: {bundle: true, domain: demo, "
            "related_skills: [opt-a, opt-b, opt-c]}}"
        ),
        body=BUNDLE_BODY,
    )
    index = {"bundle": [bundle]} | {
        f"opt-{s}": [tmp_path / "optional-skills" / "cat" / f"opt-{s}" / "SKILL.md"]
        for s in ("a", "b", "c")
    }

    errors = validator.validate(bundle, index, tmp_path)

    assert errors == []


def test_is_optional_anchors_to_repo_root(tmp_path: Path) -> None:
    root = tmp_path / "optional-skills" / "checkout"
    active = root / "skills" / "cat" / "demo" / "SKILL.md"
    optional = root / "optional-skills" / "cat" / "demo" / "SKILL.md"

    assert validator._is_optional(active, root) is False
    assert validator._is_optional(optional, root) is True


def test_cli_requires_an_explicit_target() -> None:
    result = subprocess.run(
        [sys.executable, str(SCRIPT)],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 2
    assert "the following arguments are required: paths" in result.stderr
