"""Tests for the Squish shared-brain memory provider."""

import json

from plugins.memory.squish import SquishMemoryProvider, _format_recall


def test_name_is_squish():
    provider = SquishMemoryProvider({})
    assert provider.name == "squish"


def test_auto_remember_false_skips_sync_turn(monkeypatch):
    calls = []
    provider = SquishMemoryProvider({"auto_remember": False})
    provider.initialize("session-1")
    monkeypatch.setattr(
        "plugins.memory.squish._run_squish",
        lambda *args, **kwargs: calls.append((args, kwargs)),
    )

    provider.sync_turn("please remember this detail", "acknowledged")

    assert calls == []
    assert provider._sync_thread is None


def test_auto_remember_false_skips_memory_write(monkeypatch):
    calls = []
    provider = SquishMemoryProvider({"auto_remember": "false"})
    provider.initialize("session-1")
    monkeypatch.setattr(
        "plugins.memory.squish._run_squish",
        lambda *args, **kwargs: calls.append((args, kwargs)),
    )

    provider.on_memory_write("add", "user", "User prefers concise responses")

    assert calls == []


def test_short_user_turn_is_not_persisted(monkeypatch):
    calls = []
    provider = SquishMemoryProvider({"auto_remember": True})
    provider.initialize("session-1")
    monkeypatch.setattr(
        "plugins.memory.squish._run_squish",
        lambda *args, **kwargs: calls.append((args, kwargs)),
    )

    provider.sync_turn("hi", "hello there")

    assert calls == []


def test_prefetch_ignores_short_queries(monkeypatch):
    provider = SquishMemoryProvider({})
    provider.initialize("session-1")
    monkeypatch.setattr(
        "plugins.memory.squish._run_squish",
        lambda *args, **kwargs: {"success": True, "output": '{"results": []}'},
    )

    assert provider.prefetch("hi") == ""


def test_prefetch_formats_recall_results(monkeypatch):
    payload = json.dumps(
        {"ok": True, "results": [{"type": "decision", "content": "use squish for shared memory"}]}
    )
    provider = SquishMemoryProvider({"recall_limit": 3})
    provider.initialize("session-1")
    monkeypatch.setattr(
        "plugins.memory.squish._run_squish",
        lambda *args, **kwargs: {"success": True, "output": payload},
    )

    block = provider.prefetch("what memory backend should hermes use")

    assert "Shared Memory (Squish)" in block
    assert "use squish for shared memory" in block


def test_handle_unknown_tool_returns_error():
    provider = SquishMemoryProvider({})
    result = provider.handle_tool_call("not_a_tool", {})
    assert "error" in result.lower()


def test_recall_tool_returns_no_memories_on_empty(monkeypatch):
    provider = SquishMemoryProvider({})
    provider.initialize("session-1")
    monkeypatch.setattr(
        "plugins.memory.squish._run_squish",
        lambda *args, **kwargs: {"success": True, "output": '{"results": []}'},
    )

    out = json.loads(provider.handle_tool_call("squish_recall", {"query": "anything relevant"}))

    assert out["result"] == "No relevant memories found."


def test_tool_schemas_expose_recall_remember_recent():
    provider = SquishMemoryProvider({})
    names = {s["name"] for s in provider.get_tool_schemas()}
    assert names == {"squish_recall", "squish_remember", "squish_recent"}


def test_format_recall_bullets_content():
    payload = json.dumps(
        {"results": [{"type": "fact", "content": "A"}, {"type": "", "content": "B"}]}
    )
    assert _format_recall(payload) == "- [fact] A\n- B"


def test_format_recall_falls_back_to_raw_on_non_json():
    assert _format_recall("plain text output") == "plain text output"


def test_format_recall_empty_results_is_empty():
    assert _format_recall('{"results": []}') == ""
