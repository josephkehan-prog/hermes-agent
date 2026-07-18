"""squish-capture plugin — auto-capture session memory into Squish.

Wires three behaviours, mirroring the disk-cleanup plugin's shape:

1. ``on_session_start`` hook — lightweight; logs at debug that capture is
   active.  Does NOT inject context (the MCP recall path already handles
   that).

2. ``post_tool_call`` hook — maintains an in-process per-session counter of
   tool calls, so ``on_session_end`` can decide whether the session had
   enough activity to be worth remembering.

3. ``on_session_end`` hook — when a session accumulated at least
   :data:`MIN_ACTIVITY` tool calls, shells out to the Squish CLI to save a
   ONE-LINE summary memory.  The subprocess call is hard-timeout-bounded,
   ``shell=False``, and can never raise into the host loop.

4. ``/squish-capture`` slash command — ``status`` (counter + bin reachability)
   and ``save`` (force a save now).

The Squish CLI lives OUTSIDE this repo (in the shared agent-hub vendor tree),
so its path is a module-level constant.  It can be overridden via the
``squish_capture.bin`` key in ``config.yaml`` when the config system is
reachable; otherwise the constant is used.  We never set ``SQUISH_DATA_DIR`` —
Squish writes to the shared per-project ``.squish/squish.db`` by default.
"""

from __future__ import annotations

import logging
import shutil
import subprocess
import threading
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

# Absolute path to the Squish CLI entrypoint.  This lives in the shared
# agent-hub vendor tree, OUTSIDE this repo — hence a hardcoded constant rather
# than a repo-relative path.  Overridable via config.yaml `squish_capture.bin`.
DEFAULT_SQUISH_BIN = (
    "/Users/josephhan/mac/agentic-os/hub/vendor/node_modules/"
    "squish-memory/bin/squish.mjs"
)

# Fallback absolute path to the `node` runtime when it is not on PATH (mise
# installs it here on this machine).  ``shutil.which`` is tried first.
DEFAULT_NODE_BIN = "/Users/josephhan/.local/share/mise/installs/node/24.18.0/bin/node"

# Minimum tool calls before a session is deemed worth remembering.
MIN_ACTIVITY = 3

# Hint threshold for the /status command: at/above this many tool calls the
# session is "heavy" and a save is clearly warranted.  Documented per the task
# spec (THRESHOLD = 15).
HEAVY_ACTIVITY_THRESHOLD = 15

# Hard wall-clock timeout for the squish subprocess (seconds).
SUBPROCESS_TIMEOUT_S = 10


# ---------------------------------------------------------------------------
# State — per-session tool-call counter
# ---------------------------------------------------------------------------

# Keyed by session_id.  Guarded by a lock because post_tool_call can fire
# concurrently across parallel tool calls.
_counters: Dict[str, int] = {}
_lock = threading.Lock()


def _counter_key(session_id: str) -> str:
    return session_id or "default"


def _bump(session_id: str) -> int:
    """Increment and return the tool-call counter for *session_id*."""
    key = _counter_key(session_id)
    with _lock:
        new_val = _counters.get(key, 0) + 1
        _counters[key] = new_val
        return new_val


def _read_count(session_id: str) -> int:
    key = _counter_key(session_id)
    with _lock:
        return _counters.get(key, 0)


def _drain_count(session_id: str) -> int:
    """Pop and return the counter for *session_id* (0 if absent)."""
    key = _counter_key(session_id)
    with _lock:
        return _counters.pop(key, 0)


# ---------------------------------------------------------------------------
# Squish CLI resolution + invocation
# ---------------------------------------------------------------------------

def _resolve_squish_bin() -> str:
    """Resolve the Squish CLI path — config override, else the constant."""
    try:
        from hermes_cli.config import load_config

        cfg = load_config()
    except Exception:
        return DEFAULT_SQUISH_BIN

    if not isinstance(cfg, dict):
        return DEFAULT_SQUISH_BIN
    section = cfg.get("squish_capture")
    if isinstance(section, dict):
        override = section.get("bin")
        if isinstance(override, str) and override.strip():
            return override.strip()
    return DEFAULT_SQUISH_BIN


def _resolve_node_bin() -> str:
    """Resolve the `node` runtime — PATH first, then the mise fallback."""
    found = shutil.which("node")
    return found if found else DEFAULT_NODE_BIN


def _squish_reachable() -> bool:
    """True when both the node runtime and the squish bin exist on disk."""
    import os

    node = _resolve_node_bin()
    bin_path = _resolve_squish_bin()
    return os.path.isfile(node) and os.path.isfile(bin_path)


def _run_squish_remember(text: str) -> bool:
    """Shell out to ``squish remember <text>``.  Never raises.

    Returns True on a zero exit code, False otherwise (including on any
    exception, timeout, or non-zero exit).
    """
    node = _resolve_node_bin()
    bin_path = _resolve_squish_bin()
    cmd = [node, bin_path, "remember", text]
    try:
        proc = subprocess.run(
            cmd,
            shell=False,
            capture_output=True,
            text=True,
            timeout=SUBPROCESS_TIMEOUT_S,
            encoding="utf-8",
        )
    except subprocess.TimeoutExpired:
        logger.debug("squish-capture: remember timed out after %ss", SUBPROCESS_TIMEOUT_S)
        return False
    except Exception as exc:
        logger.debug("squish-capture: remember failed to launch: %s", exc)
        return False

    if proc.returncode != 0:
        logger.debug(
            "squish-capture: remember exited %s; stderr=%s",
            proc.returncode,
            (proc.stderr or "").strip()[:200],
        )
        return False
    return True


def _build_memory_text(session_id: str, count: int) -> str:
    """Build the one-line memory text from session id + activity count."""
    sid = session_id or "unknown"
    return (
        f"Hermes session {sid} completed with {count} tool call(s) "
        f"of activity."
    )


def _maybe_save(session_id: str, count: int, *, force: bool = False) -> bool:
    """Save a summary memory when activity clears the bar (or *force*).

    Returns True when a squish remember call was made and succeeded.
    """
    if not force and count < MIN_ACTIVITY:
        return False
    text = _build_memory_text(session_id, count)
    return _run_squish_remember(text)


# ---------------------------------------------------------------------------
# Hooks
# ---------------------------------------------------------------------------

def _on_session_start(session_id: str = "", **_: Any) -> None:
    """Lightweight — log that capture is active.  No context injection."""
    logger.debug("squish-capture active for session %s", session_id or "?")


def _on_post_tool_call(
    tool_name: str = "",
    args: Optional[Dict[str, Any]] = None,
    result: Any = None,
    task_id: str = "",
    session_id: str = "",
    tool_call_id: str = "",
    **_: Any,
) -> None:
    """Increment the per-session tool-call counter.  Never raises."""
    try:
        _bump(session_id)
    except Exception as exc:  # pragma: no cover - defensive
        logger.debug("squish-capture: counter bump failed: %s", exc)


def _on_session_end(
    session_id: str = "",
    completed: bool = True,
    interrupted: bool = False,
    **_: Any,
) -> None:
    """Save a summary memory if the session had meaningful activity."""
    count = _drain_count(session_id)
    if count < MIN_ACTIVITY:
        return
    try:
        _maybe_save(session_id, count)
    except Exception as exc:  # pragma: no cover - defensive
        logger.debug("squish-capture: session-end save failed: %s", exc)


# ---------------------------------------------------------------------------
# Slash command
# ---------------------------------------------------------------------------

_HELP_TEXT = """\
/squish-capture — auto-capture session memory into Squish

Subcommands:
  status    Show the current session's tool-call counter + bin reachability
  save      Force-save a summary memory for the current session now

Sessions with >= {min} tool calls are auto-saved at session end; >= {heavy}
is treated as heavy activity.
""".format(min=MIN_ACTIVITY, heavy=HEAVY_ACTIVITY_THRESHOLD)


def _handle_slash(raw_args: str) -> Optional[str]:
    argv = raw_args.strip().split()
    if not argv or argv[0] in {"help", "-h", "--help"}:
        return _HELP_TEXT

    sub = argv[0]

    if sub == "status":
        # Best-effort: no session_id in a slash call, so report the aggregate
        # of all live counters plus reachability.
        with _lock:
            total = sum(_counters.values())
            sessions = len(_counters)
        reachable = _squish_reachable()
        return (
            "[squish-capture] status\n"
            f"  live sessions tracked : {sessions}\n"
            f"  total tool calls      : {total}\n"
            f"  min-activity threshold: {MIN_ACTIVITY}\n"
            f"  heavy threshold       : {HEAVY_ACTIVITY_THRESHOLD}\n"
            f"  squish bin            : {_resolve_squish_bin()}\n"
            f"  node bin              : {_resolve_node_bin()}\n"
            f"  reachable             : {'yes' if reachable else 'no'}"
        )

    if sub == "save":
        if not _squish_reachable():
            return (
                "[squish-capture] Cannot save: squish bin or node runtime not "
                f"reachable.\n  squish bin: {_resolve_squish_bin()}\n"
                f"  node bin  : {_resolve_node_bin()}"
            )
        with _lock:
            total = sum(_counters.values()) or MIN_ACTIVITY
        ok = _maybe_save("manual-save", total, force=True)
        return (
            "[squish-capture] Saved summary memory."
            if ok
            else "[squish-capture] Save failed (see debug log)."
        )

    return f"Unknown subcommand: {sub}\n\n{_HELP_TEXT}"


# ---------------------------------------------------------------------------
# Plugin registration
# ---------------------------------------------------------------------------

def register(ctx) -> None:
    ctx.register_hook("on_session_start", _on_session_start)
    ctx.register_hook("post_tool_call", _on_post_tool_call)
    ctx.register_hook("on_session_end", _on_session_end)
    ctx.register_command(
        "squish-capture",
        handler=_handle_slash,
        description="Auto-capture session summaries into Squish memory.",
    )
