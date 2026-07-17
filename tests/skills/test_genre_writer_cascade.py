from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from types import SimpleNamespace


SCRIPT = (
    Path(__file__).parents[2]
    / "skills"
    / "creative"
    / "genre-writer-cascade"
    / "scripts"
    / "genre_writer_cascade.py"
)


def load_module():
    spec = importlib.util.spec_from_file_location("genre_writer_cascade", SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_explicit_alias_routes_to_allowlisted_profile():
    module = load_module()
    route = module.route_brief("a blended manuscript", "sci-fi")
    assert route.genre == "science-fiction"
    assert route.profile == "orbit"


def test_each_primary_genre_routes_deterministically():
    module = load_module()
    expected = {
        "A romance novel about a relationship arc": "heartline",
        "An epic fantasy novel with costly magic": "spellbound",
        "A science fiction space opera": "orbit",
        "A horror novel built around dread": "nocturne",
        "A detective mystery with a clue ledger": "casefile",
    }
    assert {brief: module.route_brief(brief).profile for brief in expected} == expected


def test_blended_tie_requires_clarification():
    module = load_module()
    route = module.route_brief("A fantasy romance novel")
    assert route.status == "needs_clarification"
    assert route.tied_genres == ("fantasy", "romance")


def test_invocation_uses_argv_without_shell_and_allowlisted_tools(monkeypatch, tmp_path):
    module = load_module()
    route = module.route_brief("A horror manuscript")
    profile_dir = tmp_path / ".hermes" / "profiles" / "nocturne"
    profile_dir.mkdir(parents=True)
    monkeypatch.setattr(module.Path, "home", classmethod(lambda cls: tmp_path))
    captured = {}

    def fake_run(command, **kwargs):
        captured["command"] = command
        captured["kwargs"] = kwargs
        return SimpleNamespace(returncode=0, stdout="handoff\n", stderr="")

    monkeypatch.setattr(module.subprocess, "run", fake_run)
    assert module.invoke(route, "brief", tmp_path, 10) == "handoff"
    assert captured["command"][:3] == ["hermes", "-p", "nocturne"]
    assert "code_execution,clarify" in captured["command"]
    assert captured["kwargs"]["cwd"] == tmp_path
    assert "shell" not in captured["kwargs"]
