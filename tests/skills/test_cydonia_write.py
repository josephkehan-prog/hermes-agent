from __future__ import annotations

import importlib.util
import json
from pathlib import Path
from types import SimpleNamespace


SCRIPT = (
    Path(__file__).parents[2]
    / "skills"
    / "creative"
    / "cydonia-creative-writing"
    / "scripts"
    / "cydonia_write.py"
)


def load_module():
    spec = importlib.util.spec_from_file_location("cydonia_write", SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class FakeResponse:
    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return None

    def read(self):
        return b'{"message":{"content":"draft"}}'


def args(**overrides):
    values = {
        "system": "system",
        "num_ctx": 32768,
        "num_predict": 256,
        "mode": "creative",
        "temperature": None,
        "seed": None,
        "timeout": 10.0,
    }
    values.update(overrides)
    return SimpleNamespace(**values)


def capture_payload(monkeypatch, module, request_args):
    captured = {}

    def fake_urlopen(request, timeout):
        captured["payload"] = json.loads(request.data)
        captured["timeout"] = timeout
        return FakeResponse()

    monkeypatch.setattr(module.urllib.request, "urlopen", fake_urlopen)
    assert module.generate(request_args, "brief") == "draft"
    return captured["payload"]


def test_creative_mode_uses_open_sampling_without_fixed_seed(monkeypatch):
    module = load_module()
    payload = capture_payload(monkeypatch, module, args())

    assert payload["think"] is False
    assert "tools" not in payload
    assert payload["options"]["temperature"] == 0.85
    assert "seed" not in payload["options"]


def test_revision_mode_is_seeded_and_lower_temperature(monkeypatch):
    module = load_module()
    payload = capture_payload(monkeypatch, module, args(mode="revision"))

    assert payload["options"]["temperature"] == 0.35
    assert payload["options"]["seed"] == 42


def test_explicit_sampling_values_override_mode(monkeypatch):
    module = load_module()
    payload = capture_payload(
        monkeypatch,
        module,
        args(mode="revision", temperature=0.6, seed=7),
    )

    assert payload["options"]["temperature"] == 0.6
    assert payload["options"]["seed"] == 7
