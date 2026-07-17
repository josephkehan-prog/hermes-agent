from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from types import SimpleNamespace


SCRIPT = (
    Path(__file__).parents[2]
    / "skills"
    / "mlops"
    / "local-model-ops"
    / "scripts"
    / "hermes_specialist.py"
)


def load_module():
    spec = importlib.util.spec_from_file_location("hermes_specialist", SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def run_args(**overrides):
    values = {
        "role": "research",
        "prompt": "evidence",
        "prompt_file": None,
        "image": None,
        "system": None,
        "context": None,
        "max_tokens": 128,
        "temperature": 0.1,
        "keep_alive": "0",
        "timeout": 10,
    }
    values.update(overrides)
    return SimpleNamespace(**values)


def test_routes_preserve_specialization_and_context_budgets():
    module = load_module()
    assert set(module.ROUTES) == {
        "research",
        "vision-fast",
        "vision-quality",
        "writer",
        "code",
        "think",
        "controller",
    }
    assert "abliterated" in module.ROUTES["research"].model
    assert module.ROUTES["vision-fast"].context == 16384
    assert module.ROUTES["research"].context == 32768
    assert module.ROUTES["writer"].context == 32768
    assert module.ROUTES["controller"].model == "agents-a1"


def test_ollama_payload_is_tool_free_non_thinking_and_unloads(monkeypatch):
    module = load_module()
    captured = {}

    def fake_request(url, payload, timeout):
        captured.update(url=url, payload=payload, timeout=timeout)
        return {"message": {"content": "result"}}

    monkeypatch.setattr(module, "request_json", fake_request)
    content, _response = module.run_route(run_args())
    assert content == "result"
    assert captured["url"] == module.OLLAMA_CHAT
    payload = captured["payload"]
    assert payload["think"] is False
    assert payload["keep_alive"] == "0"
    assert "tools" not in payload
    assert payload["options"]["num_ctx"] == 32768
    assert "statistical significance" in payload["messages"][0]["content"]


def test_swap_payload_selects_code_route_without_tools(monkeypatch):
    module = load_module()
    captured = {}

    def fake_request(url, payload, timeout):
        captured.update(url=url, payload=payload, timeout=timeout)
        return {"choices": [{"message": {"content": "patch"}}]}

    monkeypatch.setattr(module, "request_json", fake_request)
    content, _response = module.run_route(run_args(role="code"))
    assert content == "patch"
    assert captured["url"] == module.SWAP_CHAT
    assert captured["payload"]["model"] == "ornith-uncensored"
    assert "tools" not in captured["payload"]


def test_route_context_cap_cannot_be_overridden(monkeypatch):
    module = load_module()
    args = run_args(role="vision-fast", context=32768)
    try:
        module.run_route(args)
    except RuntimeError as exc:
        assert "must be between 4096 and 16384" in str(exc)
    else:
        raise AssertionError("oversized context was accepted")


def test_route_status_checks_both_endpoint_registries(monkeypatch):
    module = load_module()

    def fake_request(url, _payload, _timeout):
        if url == module.OLLAMA_TAGS:
            return {
                "models": [
                    {"name": route.model}
                    for route in module.ROUTES.values()
                    if route.endpoint == "ollama"
                ]
            }
        return {
            "data": [
                {"id": route.model}
                for route in module.ROUTES.values()
                if route.endpoint == "swap"
            ]
        }

    monkeypatch.setattr(module, "request_json", fake_request)
    rows = module.route_status()
    assert len(rows) == 7
    assert all(row["available"] for row in rows)
