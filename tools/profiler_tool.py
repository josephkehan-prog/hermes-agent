#!/usr/bin/env python3
"""Profile running Python processes and standalone scripts.

Two capabilities, two backends:

* ``profile_running`` wraps the ``py-spy`` binary
  (https://github.com/benfred/py-spy, MIT License — Copyright (c) Benjamin
  Frederick) to sample a live process's call stacks without requiring any
  code changes or restart. py-spy is not vendored here; this module only
  shells out to the ``py-spy`` binary if the user has it on PATH (``pip
  install py-spy``). When it isn't installed, the tool returns a clear
  install hint instead of attempting to install anything itself.
* ``profile_script`` uses the stdlib ``cProfile``/``pstats`` deterministic
  profiler to run a standalone script and report its top functions by
  cumulative time. No external binary required — this is the always-available
  fallback for one-shot script profiling.
"""

import io
import json
import os
import pstats
import shutil
import subprocess
import sys
import tempfile
from typing import Any, Dict, List, Optional

from tools.registry import registry

_PY_SPY_INSTALL_HINT = "py-spy not installed: pip install py-spy"
_PROFILE_TOP_N = 25
_MIN_DURATION_S = 1
_MAX_DURATION_S = 60
_DEFAULT_DURATION_S = 5
_SUBPROCESS_TIMEOUT_BUFFER_S = 10
_SCRIPT_TIMEOUT_S = 60


def _validate_pid(pid: Any) -> Optional[int]:
    """Return pid as a positive int, or None if invalid."""
    try:
        pid_int = int(pid)
    except (TypeError, ValueError):
        return None
    return pid_int if pid_int > 0 else None


def _validate_duration(duration_s: Any) -> int:
    """Clamp duration_s into [_MIN_DURATION_S, _MAX_DURATION_S]."""
    try:
        duration = int(duration_s)
    except (TypeError, ValueError):
        duration = _DEFAULT_DURATION_S
    return max(_MIN_DURATION_S, min(_MAX_DURATION_S, duration))


def profile_running(pid: Any, duration_s: Any = _DEFAULT_DURATION_S) -> Dict[str, Any]:
    """Sample a running Python process's stacks with py-spy for duration_s seconds.

    Returns {ok, tool_used, output} on success, {ok, tool_used, error} when
    py-spy isn't installed, the pid is invalid, or sampling fails.
    """
    pid_int = _validate_pid(pid)
    if pid_int is None:
        return {"ok": False, "tool_used": "py-spy", "error": f"invalid pid: {pid!r}"}

    py_spy_bin = shutil.which("py-spy")
    if not py_spy_bin:
        return {"ok": False, "tool_used": "py-spy", "error": _PY_SPY_INSTALL_HINT}

    duration = _validate_duration(duration_s)

    with tempfile.NamedTemporaryFile(suffix=".txt", delete=False) as tmp:
        record_path = tmp.name

    try:
        result = subprocess.run(
            [
                py_spy_bin, "record", "--pid", str(pid_int),
                "--duration", str(duration), "--format", "raw",
                "--output", record_path, "--nonblocking",
            ],
            capture_output=True,
            text=True,
            timeout=duration + _SUBPROCESS_TIMEOUT_BUFFER_S,
            check=False,
        )
        if result.returncode != 0:
            error = (result.stderr or result.stdout or "unknown py-spy failure").strip()
            return {"ok": False, "tool_used": "py-spy", "error": f"py-spy exited {result.returncode}: {error[-2000:]}"}

        with open(record_path, "r", encoding="utf-8", errors="replace") as f:
            output = f.read()
        return {"ok": True, "tool_used": "py-spy", "output": output}
    except subprocess.TimeoutExpired:
        return {"ok": False, "tool_used": "py-spy", "error": f"py-spy timed out after {duration}s"}
    except OSError as exc:
        return {"ok": False, "tool_used": "py-spy", "error": str(exc)}
    finally:
        if os.path.exists(record_path):
            os.unlink(record_path)


def profile_script(path: str, args: Optional[List[str]] = None) -> Dict[str, Any]:
    """Run a Python script under cProfile and return its top-25 functions by
    cumulative time as pstats text.

    Runs ``path`` in a subprocess via ``python3 -m cProfile -o <tmp>`` (isolates
    the profiled script's own sys.exit()/globals from this process), then loads
    the resulting stats and renders them with ``pstats.Stats.print_stats``.
    """
    script_path = (path or "").strip()
    if not script_path:
        return {"ok": False, "tool_used": "cProfile", "error": "path is required"}

    script_path = os.path.abspath(os.path.expanduser(script_path))
    if not os.path.isfile(script_path):
        return {"ok": False, "tool_used": "cProfile", "error": f"no such file: {script_path}"}

    script_args = [str(a) for a in (args or [])]

    with tempfile.NamedTemporaryFile(suffix=".pstats", delete=False) as tmp:
        stats_path = tmp.name

    try:
        result = subprocess.run(
            [sys.executable, "-m", "cProfile", "-o", stats_path, script_path, *script_args],
            capture_output=True,
            text=True,
            timeout=_SCRIPT_TIMEOUT_S,
            check=False,
        )
        if result.returncode != 0:
            error = (result.stderr or "unknown script failure").strip()
            return {"ok": False, "tool_used": "cProfile", "error": f"script exited {result.returncode}: {error[-2000:]}"}

        buffer = io.StringIO()
        stats = pstats.Stats(stats_path, stream=buffer)
        stats.sort_stats("cumulative").print_stats(_PROFILE_TOP_N)
        return {"ok": True, "tool_used": "cProfile", "output": buffer.getvalue()}
    except subprocess.TimeoutExpired:
        return {"ok": False, "tool_used": "cProfile", "error": f"script timed out after {_SCRIPT_TIMEOUT_S}s"}
    except OSError as exc:
        return {"ok": False, "tool_used": "cProfile", "error": str(exc)}
    finally:
        if os.path.exists(stats_path):
            os.unlink(stats_path)


registry.register(
    name="profile_running",
    toolset="code_execution",
    schema={
        "name": "profile_running",
        "description": (
            "Sample a running Python process's call stacks with py-spy (no code "
            "changes or restart needed) and return the flame-graph-style raw "
            "output as text. Requires the `py-spy` binary on PATH — if it isn't "
            "installed, returns a clear pip install hint instead of failing "
            "silently. Use `profile_script` instead for one-shot script profiling."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "pid": {"type": "integer", "description": "Process id of the running Python process to sample."},
                "duration_s": {
                    "type": "integer",
                    "description": f"Seconds to sample for ({_MIN_DURATION_S}-{_MAX_DURATION_S}). Defaults to {_DEFAULT_DURATION_S}.",
                },
            },
            "required": ["pid"],
        },
    },
    handler=lambda args, **kw: json.dumps(
        profile_running(pid=args.get("pid"), duration_s=args.get("duration_s", _DEFAULT_DURATION_S)),
        ensure_ascii=False,
    ),
    emoji="🔬",
)

registry.register(
    name="profile_script",
    toolset="code_execution",
    schema={
        "name": "profile_script",
        "description": (
            "Run a Python script under the stdlib cProfile deterministic profiler "
            "and return its top-25 functions by cumulative time as pstats text. "
            "No external tooling required. Use `profile_running` instead to sample "
            "an already-running process."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "Path to the Python script to profile."},
                "args": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Command-line arguments to pass to the script (its sys.argv[1:]).",
                },
            },
            "required": ["path"],
        },
    },
    handler=lambda args, **kw: json.dumps(
        profile_script(path=args.get("path", ""), args=args.get("args")),
        ensure_ascii=False,
    ),
    emoji="🔬",
)
