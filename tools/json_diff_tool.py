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
from typing import Any, Dict, List, Optional, Tuple

from tools.registry import registry

_MAX_INPUT_CHARS = 10_000_000


def _is_ignored(path: str, ignore_paths: Tuple[str, ...]) -> bool:
    """True if path equals or is nested under any ignore path.

    Prefix matching is segment-aware: "meta" ignores "meta.ts" but not
    "metadata".
    """
    for ignore in ignore_paths:
        if path == ignore or path.startswith(ignore + "."):
            return True
    return False


def _filter_ignored(changes: Dict[str, Any], ignore_paths: Tuple[str, ...]) -> Dict[str, Any]:
    """Drop change entries whose path is ignored, preserving order."""
    if not ignore_paths:
        return changes
    return {p: v for p, v in changes.items() if not _is_ignored(p, ignore_paths)}


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


def json_diff(old: Any, new: Any, ignore_paths: Optional[List[str]] = None) -> Dict[str, Any]:
    """Recursively diff two JSON-compatible values, reporting differences by dotted path.

    Returns {ok, changed, added, removed, modified, summary}. added/removed are
    {path: value}; modified is {path: {old, new}}. Neither old nor new is mutated.

    ``ignore_paths`` drops changes at the given dotted paths and everything
    nested under them — useful for volatile fields (timestamps, counters) that
    would otherwise mask real changes in a monitoring snapshot. Matching is
    segment-aware: "meta" ignores "meta.ts" but not "metadata".
    """
    try:
        json.dumps(old)
        json.dumps(new)
    except (TypeError, ValueError) as exc:
        return {"ok": False, "error": f"inputs must be JSON-compatible: {exc}"}
    except RecursionError:
        return {"ok": False, "error": "input nesting too deep"}

    if ignore_paths is not None and (
        not isinstance(ignore_paths, list)
        or any(not isinstance(p, str) for p in ignore_paths)
    ):
        return {"ok": False, "error": "ignore_paths must be a list of strings"}
    ignore_tuple: Tuple[str, ...] = tuple(ignore_paths) if ignore_paths else ()

    try:
        added, removed, modified = _diff_values(old, new, "")
    except RecursionError:
        return {"ok": False, "error": "input nesting too deep"}
    added = _filter_ignored(added, ignore_tuple)
    removed = _filter_ignored(removed, ignore_tuple)
    modified = _filter_ignored(modified, ignore_tuple)
    return {
        "ok": True,
        "changed": bool(added or removed or modified),
        "added": added,
        "removed": removed,
        "modified": modified,
        "summary": _build_summary(added, removed, modified),
    }


def json_diff_text(
    old_json_str: str, new_json_str: str, ignore_paths: Optional[List[str]] = None
) -> Dict[str, Any]:
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
    except RecursionError:
        return {"ok": False, "error": "old_json_str nesting too deep"}
    try:
        new = json.loads(new_json_str)
    except json.JSONDecodeError as exc:
        return {"ok": False, "error": f"invalid JSON in new_json_str: {exc}"}
    except RecursionError:
        return {"ok": False, "error": "new_json_str nesting too deep"}

    return json_diff(old, new, ignore_paths=ignore_paths)


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
                "ignore_paths": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": (
                        "Optional dotted paths to exclude from the diff, including anything "
                        "nested under them (e.g. 'meta.timestamp'). Use to ignore volatile "
                        "fields so they don't mask real changes. Segment-aware: 'meta' "
                        "ignores 'meta.ts' but not 'metadata'."
                    ),
                },
            },
            "required": ["old_json", "new_json"],
        },
    },
    handler=lambda args, **kw: json.dumps(
        json_diff_text(
            old_json_str=args.get("old_json", ""),
            new_json_str=args.get("new_json", ""),
            ignore_paths=args.get("ignore_paths"),
        ),
        ensure_ascii=False,
    ),
    emoji="🔀",
)
