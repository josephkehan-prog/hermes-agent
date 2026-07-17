from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from types import SimpleNamespace


SCRIPT = (
    Path(__file__).parents[2]
    / "skills"
    / "autonomous-ai-agents"
    / "war-room-specialist-cascade"
    / "scripts"
    / "specialist_cascade.py"
)


def load_module():
    spec = importlib.util.spec_from_file_location("specialist_cascade", SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_explicit_alias_routes_to_allowlisted_profile():
    route = load_module().route_brief("mixed media", "voiceover")
    assert route.niche == "audiobook"
    assert route.profile == "narrator"
    assert route.lead == "Composer"


def test_each_niche_routes_deterministically():
    module = load_module()
    expected = {
        "Adapt this scene into a screenplay with sluglines": "scriptroom",
        "Render this chapter as an audiobook narration": "narrator",
        "Create SRT captions and a transcript": "caption",
        "Perform invoice JSON structured extraction": "extractor",
        "Build a storyboard and animatic previs": "previs",
    }
    assert {brief: module.route_brief(brief).profile for brief in expected} == expected


def test_tie_requires_clarification():
    route = load_module().route_brief("Create an audiobook narration and SRT captions")
    assert route.status == "needs_clarification"
    assert route.tied_niches == ("audiobook", "transcript-caption")


def test_invocation_uses_argv_without_shell(monkeypatch, tmp_path):
    module = load_module()
    route = module.route_brief("Create screenplay sluglines")
    (tmp_path / ".hermes" / "profiles" / "scriptroom").mkdir(parents=True)
    monkeypatch.setattr(module.Path, "home", classmethod(lambda cls: tmp_path))
    captured = {}

    def fake_run(command, **kwargs):
        captured["command"] = command
        captured["kwargs"] = kwargs
        return SimpleNamespace(returncode=0, stdout="handoff\n", stderr="")

    monkeypatch.setattr(module.subprocess, "run", fake_run)
    assert module.invoke(route, "brief", tmp_path, 10) == "handoff"
    assert captured["command"][:3] == ["hermes", "-p", "scriptroom"]
    assert "screenplay-production" in captured["command"]
    assert "code_execution,clarify" in captured["command"]
    assert "shell" not in captured["kwargs"]
