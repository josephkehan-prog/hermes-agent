#!/usr/bin/env python3
"""Structured diffing between two JSON-compatible values.

Pure stdlib, no network. Built for the monitoring/alerting domain (watch-notify,
infra-monitor) so a skill can snapshot a JSON payload, take another snapshot
later, and ask "did anything change, and what changed" without hand-rolling a
recursive comparison each time.

Two entry points:

* ``json_diff`` compares two already-parsed JSON-compatible values (dict/list/
  scalar) and reports differences by dotted path (e.g. ``"a.b.0.c"``).
* ``json_diff_text`` parses two raw JSON strings first (validating and capping
  input size), then delegates to ``json_diff``. This is the one exposed as an
  agent tool, since tool-call arguments arrive as strings.
"""

import json
from typing import Any, Dict, Tuple

from tools.registry import registry

_MAX_INPUT_CHARS = 10_000_000


def _join_path(path: str, key: Any) -> str:
    """Append key to a dotted path (dict key or list index)."""
    return f"{path}.{key}" if path else str(key)


def _diff_dicts(old: Dict[str, Any], new: Dict[str, Any], path: str) -> Tuple[Dict, Dict, Dict]:
    """Diff two dicts key by key, in sorted key order for determinism."""
    added: Dict[str, Any] = {}
    removed: Dict[str, Any] = {}
    modified: Dict[str, Any] = {}
    for key in sorted(set(old.keys()) | set(new.keys()), key=str):
        child_path = _join_path(path, key)
        if key not in old:
            added = {**added, child_path: new[key]}
        elif key not in new:
            removed = {**removed, child_path: old[key]}
        else:
            child_added, child_removed, child_modified = _diff_values(old[key], new[key], child_path)
            added, removed, modified = {**added, **child_added}, {**removed, **child_removed}, {**modified, **child_modified}
    return added, removed, modified


def _diff_lists(old: list, new: list, path: str) -> Tuple[Dict, Dict, Dict]:
    """Diff two lists by index, in order, for determinism."""
    added: Dict[str, Any] = {}
    removed: Dict[str, Any] = {}
    modified: Dict[str, Any] = {}
    for index in range(max(len(old), len(new))):
        child_path = _join_path(path, index)
        if index >= len(old):
            added = {**added, child_path: new[index]}
        elif index >= len(new):
            removed = {**removed, child_path: old[index]}
        else:
            child_added, child_removed, child_modified = _diff_values(old[index], new[index], child_path)
            added, removed, modified = {**added, **child_added}, {**removed, **child_removed}, {**modified, **child_modified}
    return added, removed, modified


def _diff_values(old: Any, new: Any, path: str) -> Tuple[Dict, Dict, Dict]:
    """Diff two arbitrary JSON values at path, dispatching on shared container type."""
    if isinstance(old, dict) and isinstance(new, dict):
        return _diff_dicts(old, new, path)
    if isinstance(old, list) and isinstance(new, list):
        return _diff_lists(old, new, path)
    if old != new:
        return {}, {}, {path: {"old": old, "new": new}}
    return {}, {}, {}


def _build_summary(added: Dict, removed: Dict, modified: Dict) -> str:
    """Render a one-line human-readable summary of the diff counts."""
    if not (added or removed or modified):
        return "no changes"
    parts = []
    if added:
        parts.append(f"{len(added)} added")
    if removed:
        parts.append(f"{len(removed)} removed")
    if modified:
        parts.append(f"{len(modified)} modified")
    return ", ".join(parts)


def json_diff(old: Any, new: Any) -> Dict[str, Any]:
    """Recursively diff two JSON-compatible values, reporting differences by dotted path.

    Returns {ok, changed, added, removed, modified, summary}. added/removed are
    {path: value}; modified is {path: {old, new}}. Neither old nor new is mutated.
    """
    try:
        json.dumps(old)
        json.dumps(new)
    except (TypeError, ValueError) as exc:
        return {"ok": False, "error": f"inputs must be JSON-compatible: {exc}"}

    added, removed, modified = _diff_values(old, new, "")
    return {
        "ok": True,
        "changed": bool(added or removed or modified),
        "added": added,
        "removed": removed,
        "modified": modified,
        "summary": _build_summary(added, removed, modified),
    }


def json_diff_text(old_json_str: str, new_json_str: str) -> Dict[str, Any]:
    """Parse two JSON strings and diff them. Returns an error dict on parse failure
    or when either input exceeds the size cap."""
    for label, text in (("old_json_str", old_json_str), ("new_json_str", new_json_str)):
        if not isinstance(text, str):
            return {"ok": False, "error": f"{label} must be a string"}
        if len(text) > _MAX_INPUT_CHARS:
            return {"ok": False, "error": f"{label} exceeds {_MAX_INPUT_CHARS} char limit"}

    try:
        old = json.loads(old_json_str)
    except json.JSONDecodeError as exc:
        return {"ok": False, "error": f"invalid JSON in old_json_str: {exc}"}
    try:
        new = json.loads(new_json_str)
    except json.JSONDecodeError as exc:
        return {"ok": False, "error": f"invalid JSON in new_json_str: {exc}"}

    return json_diff(old, new)


registry.register(
    name="json_diff",
    toolset="code_execution",
    schema={
        "name": "json_diff",
        "description": (
            "Structurally diff two JSON documents and report what changed, by dotted "
            "path (e.g. 'a.b.0.c'). Returns which keys/indices were added, removed, or "
            "modified, plus a changed boolean and one-line summary. Use to decide 'did "
            "anything change since the last snapshot' for monitoring/alerting checks."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "old_json": {"type": "string", "description": "The earlier/baseline JSON document, as a JSON-encoded string."},
                "new_json": {"type": "string", "description": "The current JSON document to compare against old_json, as a JSON-encoded string."},
            },
            "required": ["old_json", "new_json"],
        },
    },
    handler=lambda args, **kw: json.dumps(
        json_diff_text(old_json_str=args.get("old_json", ""), new_json_str=args.get("new_json", "")),
        ensure_ascii=False,
    ),
    emoji="🔀",
)
