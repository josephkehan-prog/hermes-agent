"""Squish memory plugin — MemoryProvider interface.

Wires Hermes's pluggable long-term memory into **Squish**, the machine's
shared-brain memory engine (the same store every agent on this host reads and
writes). Where the built-in note tool and Mem0 keep an isolated per-agent
store, this provider makes Hermes recall from — and contribute to — the one
workspace-wide memory brain.

Backed by the Squish CLI (``squish``), vendored with agent-hub at
``agentic-os/hub/vendor/node_modules/squish-memory/bin/squish.mjs``.

Lifecycle mapping:
  prefetch()        -> ``squish recall``   (semantic recall injected as context)
  sync_turn()       -> ``squish remember`` (persist substantive turns, background)
  on_memory_write() -> ``squish remember`` (mirror built-in memory edits)
  on_pre_compress() -> ``squish remember`` (flush context before it is discarded)
  tools             -> squish_recall / squish_remember / squish_recent

Config via config.yaml:
  memory:
    squish:
      auto_remember: true   # persist turns + mirror memory writes automatically
      recall_limit: 5       # max memories injected per prefetch
"""

from __future__ import annotations

import json
import logging
import os
import shutil
import subprocess
import threading
from pathlib import Path
from typing import Any, Dict, List, Optional

from agent.memory_provider import MemoryProvider
from tools.registry import tool_error

logger = logging.getLogger(__name__)

# Timeouts (seconds)
_RECALL_TIMEOUT = 12   # squish recall — semantic search, should be fast
_REMEMBER_TIMEOUT = 30  # squish remember — may run auto-categorization

# Noise filters
_MIN_QUERY_LEN = 10
_MIN_OUTPUT_LEN = 20

# Vendored squish location (agent-hub monorepo). Used when `squish` is not on PATH.
_VENDOR_SQUISH_MJS = (
    Path.home()
    / "mac/agentic-os/hub/vendor/node_modules/squish-memory/bin/squish.mjs"
)
# mise-managed node used by the live gateway's mcp_servers config.
_MISE_NODE = Path.home() / ".local/share/mise/installs/node/lts/bin/node"

_DEFAULT_RECALL_LIMIT = 5


def _coerce_bool(value: Any, default: bool = False) -> bool:
    if isinstance(value, bool):
        return value
    if value is None:
        return default
    if isinstance(value, (int, float)):
        return bool(value)
    if isinstance(value, str):
        text = value.strip().lower()
        if text in {"1", "true", "yes", "on"}:
            return True
        if text in {"0", "false", "no", "off"}:
            return False
    return default


def _coerce_int(value: Any, default: int) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _format_recall(output: str) -> str:
    """Turn squish recall's JSON into compact bullets; fall back to raw text.

    squish emits ``{"ok":true,"results":[{"content","type",...}]}`` on stdout.
    Bulleting the ``content`` fields keeps injected context readable and small.
    """
    text = output.strip()
    try:
        data = json.loads(text)
    except (ValueError, TypeError):
        return text
    results = data.get("results") if isinstance(data, dict) else None
    if not isinstance(results, list) or not results:
        return ""
    lines: List[str] = []
    for item in results:
        if not isinstance(item, dict):
            continue
        content = str(item.get("content", "")).strip()
        if not content:
            continue
        mtype = str(item.get("type", "")).strip()
        prefix = f"[{mtype}] " if mtype else ""
        lines.append(f"- {prefix}{content}")
    return "\n".join(lines)


def _load_plugin_config() -> Dict[str, Any]:
    """Read Squish's profile-scoped memory config from ``memory.squish``."""
    try:
        from hermes_cli.config import load_config

        config = load_config()
        memory_config = config.get("memory", {})
        if not isinstance(memory_config, dict):
            return {}
        provider_config = memory_config.get("squish", {})
        if isinstance(provider_config, dict) and provider_config:
            return dict(provider_config)
    except Exception:  # noqa: BLE001 — never break the picker on a config read
        pass
    return {}


# ---------------------------------------------------------------------------
# squish command resolution (cached, thread-safe)
# ---------------------------------------------------------------------------

_cmd_lock = threading.Lock()
_cached_prefix: Optional[List[str]] = None  # [] once resolved-to-missing


def _resolve_node() -> Optional[str]:
    node = shutil.which("node")
    if node:
        return node
    if _MISE_NODE.exists():
        return str(_MISE_NODE)
    return None


def _resolve_squish_prefix() -> Optional[List[str]]:
    """Return the argv prefix that invokes squish, or None if unavailable.

    Prefers a ``squish`` binary on PATH; falls back to running the vendored
    ``squish.mjs`` under node. Result is cached (empty list = confirmed missing).
    """
    global _cached_prefix
    with _cmd_lock:
        if _cached_prefix is not None:
            return _cached_prefix or None

    prefix: Optional[List[str]] = None
    on_path = shutil.which("squish")
    if on_path:
        prefix = [on_path]
    elif _VENDOR_SQUISH_MJS.exists():
        node = _resolve_node()
        if node:
            prefix = [node, str(_VENDOR_SQUISH_MJS)]

    with _cmd_lock:
        if _cached_prefix is None:
            _cached_prefix = list(prefix) if prefix else []
    return prefix


def _run_squish(args: List[str], timeout: int = _RECALL_TIMEOUT) -> dict:
    """Run a squish CLI command. Returns {success, output, error}."""
    prefix = _resolve_squish_prefix()
    if not prefix:
        return {"success": False, "error": "squish CLI not found (agent-hub vendor missing)."}

    cmd = list(prefix) + args
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
            stdin=subprocess.DEVNULL,
            encoding="utf-8",
        )
        stdout = (result.stdout or "").strip()
        stderr = (result.stderr or "").strip()
        if result.returncode == 0:
            return {"success": True, "output": stdout}
        return {"success": False, "error": stderr or stdout or f"squish exited {result.returncode}"}
    except subprocess.TimeoutExpired:
        return {"success": False, "error": f"squish timed out after {timeout}s"}
    except FileNotFoundError:
        global _cached_prefix
        with _cmd_lock:
            _cached_prefix = None
        return {"success": False, "error": "squish CLI not found"}
    except Exception as e:  # noqa: BLE001
        return {"success": False, "error": str(e)}


# ---------------------------------------------------------------------------
# Tool schemas
# ---------------------------------------------------------------------------

RECALL_SCHEMA = {
    "name": "squish_recall",
    "description": (
        "Search the shared workspace memory (Squish) for relevant context: "
        "facts, decisions, preferences, and learnings saved by this and other "
        "agents on this machine. Use whenever past context would help."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "query": {"type": "string", "description": "What to search for."},
        },
        "required": ["query"],
    },
}

REMEMBER_SCHEMA = {
    "name": "squish_remember",
    "description": (
        "Store a fact in the shared workspace memory (Squish) so it persists "
        "across sessions and is visible to every agent on this machine. Use for "
        "decisions, user preferences, project facts, and durable learnings."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "content": {"type": "string", "description": "The information to remember."},
        },
        "required": ["content"],
    },
}

RECENT_SCHEMA = {
    "name": "squish_recent",
    "description": "List recent shared-memory entries (today/thisweek/7days/30days).",
    "parameters": {
        "type": "object",
        "properties": {
            "window": {
                "type": "string",
                "description": "Time window.",
                "enum": ["today", "yesterday", "thisweek", "7days", "30days"],
            },
        },
        "required": [],
    },
}


# ---------------------------------------------------------------------------
# MemoryProvider implementation
# ---------------------------------------------------------------------------


class SquishMemoryProvider(MemoryProvider):
    """Shared-brain memory backed by the Squish CLI."""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self._config = dict(config) if config is not None else _load_plugin_config()
        self._auto_remember = _coerce_bool(self._config.get("auto_remember"), True)
        self._recall_limit = _coerce_int(self._config.get("recall_limit"), _DEFAULT_RECALL_LIMIT)
        self._session_id = ""
        self._turn_count = 0
        self._sync_thread: Optional[threading.Thread] = None

    @property
    def name(self) -> str:
        return "squish"

    def is_available(self) -> bool:
        """True when the squish CLI resolves. No network calls."""
        return _resolve_squish_prefix() is not None

    def get_config_schema(self):
        return [
            {
                "key": "auto_remember",
                "description": "Persist substantive turns and mirror built-in memory writes to Squish",
                "default": "true",
                "choices": ["true", "false"],
            },
            {
                "key": "recall_limit",
                "description": "Max memories injected as context per turn",
                "default": str(_DEFAULT_RECALL_LIMIT),
            },
        ]

    def initialize(self, session_id: str, **kwargs) -> None:
        self._session_id = session_id
        self._turn_count = 0

    def system_prompt_block(self) -> str:
        # STATIC only — must stay byte-stable for the conversation's cache prefix.
        if not _resolve_squish_prefix():
            return ""
        return (
            "# Shared Memory (Squish)\n"
            "Active. A workspace-wide memory brain shared by every agent on this "
            "machine. Relevant memories are recalled automatically each turn. Use "
            "squish_recall to search it, squish_remember to store durable facts, "
            "squish_recent to review recent entries."
        )

    def prefetch(self, query: str, *, session_id: str = "") -> str:
        """Semantic recall from the shared brain, injected as turn context."""
        if not query or len(query.strip()) < _MIN_QUERY_LEN:
            return ""
        result = _run_squish(
            ["recall", "--limit", str(self._recall_limit), query.strip()[:5000]],
            timeout=_RECALL_TIMEOUT,
        )
        if result["success"] and result.get("output"):
            formatted = _format_recall(result["output"])
            if len(formatted) > _MIN_OUTPUT_LEN:
                if len(formatted) > 8000:
                    formatted = formatted[:8000] + "\n\n[... truncated]"
                return f"## Shared Memory (Squish)\n{formatted}"
        return ""

    def queue_prefetch(self, query: str, *, session_id: str = "") -> None:
        """No-op: prefetch() runs synchronously at turn start."""
        pass

    def sync_turn(self, user_content: str, assistant_content: str, *, session_id: str = "", **kwargs) -> None:
        """Persist a substantive turn to the shared brain (background)."""
        self._turn_count += 1
        if not self._auto_remember:
            return
        if len(user_content.strip()) < _MIN_QUERY_LEN:
            return

        content = f"User: {user_content[:2000]}\nAssistant: {assistant_content[:2000]}"

        def _store():
            try:
                _run_squish(["remember", content], timeout=_REMEMBER_TIMEOUT)
            except Exception as e:  # noqa: BLE001
                logger.debug("squish sync_turn failed: %s", e)

        if self._sync_thread and self._sync_thread.is_alive():
            self._sync_thread.join(timeout=5.0)
        self._sync_thread = threading.Thread(target=_store, daemon=True, name="squish-sync")
        self._sync_thread.start()

    def on_memory_write(self, action: str, target: str, content: str, metadata: Optional[Dict[str, Any]] = None) -> None:
        """Mirror built-in memory/user-profile edits into the shared brain."""
        if not self._auto_remember:
            return
        if action not in {"add", "replace"} or not content:
            return

        label = "User profile" if target == "user" else "Agent memory"

        def _write():
            try:
                _run_squish(["remember", f"[{label}] {content}"], timeout=_REMEMBER_TIMEOUT)
            except Exception as e:  # noqa: BLE001
                logger.debug("squish memory mirror failed: %s", e)

        threading.Thread(target=_write, daemon=True, name="squish-memwrite").start()

    def on_pre_compress(self, messages: List[Dict[str, Any]]) -> str:
        """Flush recent context into the shared brain before compression drops it."""
        if not self._auto_remember or not messages:
            return ""
        parts = []
        for msg in messages[-10:]:
            role = msg.get("role", "")
            content = msg.get("content", "")
            if isinstance(content, str) and content.strip() and role in {"user", "assistant"}:
                parts.append(f"{role}: {content[:500]}")
        if not parts:
            return ""
        combined = "\n".join(parts)

        def _flush():
            try:
                _run_squish(
                    ["remember", f"[Pre-compression context]\n{combined}"],
                    timeout=_REMEMBER_TIMEOUT,
                )
            except Exception as e:  # noqa: BLE001
                logger.debug("squish pre-compression flush failed: %s", e)

        threading.Thread(target=_flush, daemon=True, name="squish-flush").start()
        return ""

    def get_tool_schemas(self) -> List[Dict[str, Any]]:
        return [RECALL_SCHEMA, REMEMBER_SCHEMA, RECENT_SCHEMA]

    def handle_tool_call(self, tool_name: str, args: dict, **kwargs) -> str:
        if tool_name == "squish_recall":
            return self._tool_recall(args)
        if tool_name == "squish_remember":
            return self._tool_remember(args)
        if tool_name == "squish_recent":
            return self._tool_recent(args)
        return tool_error(f"Unknown tool: {tool_name}")

    def shutdown(self) -> None:
        if self._sync_thread and self._sync_thread.is_alive():
            self._sync_thread.join(timeout=10.0)

    # -- Tool implementations ------------------------------------------------

    def _tool_recall(self, args: dict) -> str:
        query = args.get("query", "")
        if not query:
            return tool_error("query is required")
        result = _run_squish(
            ["recall", "--limit", str(self._recall_limit), query.strip()[:5000]],
            timeout=_RECALL_TIMEOUT,
        )
        if not result["success"]:
            return tool_error(result.get("error", "Recall failed"))
        formatted = _format_recall(result.get("output", ""))
        if not formatted or len(formatted) < _MIN_OUTPUT_LEN:
            return json.dumps({"result": "No relevant memories found."})
        if len(formatted) > 8000:
            formatted = formatted[:8000] + "\n\n[... truncated]"
        return json.dumps({"result": formatted})

    def _tool_remember(self, args: dict) -> str:
        content = args.get("content", "")
        if not content:
            return tool_error("content is required")
        result = _run_squish(["remember", content], timeout=_REMEMBER_TIMEOUT)
        if not result["success"]:
            return tool_error(result.get("error", "Remember failed"))
        return json.dumps({"result": "Stored in shared memory."})

    def _tool_recent(self, args: dict) -> str:
        window = args.get("window", "7days")
        if window not in {"today", "yesterday", "thisweek", "7days", "30days"}:
            window = "7days"
        result = _run_squish(["recent", "--period", window], timeout=_RECALL_TIMEOUT)
        if not result["success"]:
            return tool_error(result.get("error", "Recent failed"))
        return json.dumps({"result": result.get("output", "").strip() or "No recent memories."})


# ---------------------------------------------------------------------------
# Plugin entry point
# ---------------------------------------------------------------------------


def register(ctx) -> None:
    """Register Squish as a memory provider plugin."""
    ctx.register_memory_provider(SquishMemoryProvider())
