from __future__ import annotations

import importlib.util
import json
from pathlib import Path
from types import SimpleNamespace


SCRIPT = (
    Path(__file__).parents[2]
    / "skills"
    / "research"
    / "mythos-evidence-synthesis"
    / "scripts"
    / "qwythos_synthesize.py"
)


def load_module():
    spec = importlib.util.spec_from_file_location("qwythos_synthesize", SCRIPT)
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
        return b'{"message":{"content":"synthesis"}}'


def test_payload_is_bounded_deterministic_and_tool_free(monkeypatch):
    module = load_module()
    assert "abliterated" in module.MODEL
    captured = {}

    def fake_urlopen(request, timeout):
        captured["payload"] = json.loads(request.data)
        captured["timeout"] = timeout
        return FakeResponse()

    monkeypatch.setattr(module.urllib.request, "urlopen", fake_urlopen)
    args = SimpleNamespace(
        system="system",
        num_ctx=65536,
        num_predict=4096,
        temperature=0.2,
        seed=42,
        timeout=10,
    )
    assert module.synthesize(args, "[S1] evidence") == "synthesis"
    payload = captured["payload"]
    assert payload["think"] is False
    assert "tools" not in payload
    assert payload["options"] == {
        "num_ctx": 65536,
        "num_predict": 4096,
        "temperature": 0.2,
        "seed": 42,
    }


def test_default_system_rejects_unsupported_statistical_inference(monkeypatch):
    module = load_module()
    monkeypatch.setattr("sys.argv", [str(SCRIPT)])
    args = module.parse_args()
    assert "statistical significance" in args.system
    assert "When evidence is insufficient" in args.system
