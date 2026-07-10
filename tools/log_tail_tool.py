#!/usr/bin/env python3
"""Tail and grep local log files without reading them into memory whole.

Pure stdlib, no network. Built for devops monitoring (log-tail alerter) so a
skill can pull the last N lines of a multi-gigabyte log — or grep for a
pattern within those last N lines — without paying the cost of a full-file
read.

Two entry points:

* ``tail_lines`` seeks from the end of the file in fixed-size blocks,
  counting newlines as it goes, and stops as soon as it has enough lines.
  It never reads more of the file than necessary to satisfy ``n``.
* ``grep_tail`` calls ``tail_lines`` first, then filters those lines with a
  compiled regex. Invalid patterns are rejected before any work starts.
  Catastrophic-backtracking patterns (e.g. ``(a+)+b``) are bounded by
  running the actual regex scan in a killable child *subprocess* under a
  wall-clock timeout (``GREP_TIMEOUT_SECONDS``); a plain ``except`` cannot
  stop runaway C-level regex backtracking mid-call — only terminating the
  process running it can. If the scan doesn't finish in time,
  ``subprocess.run``'s own timeout handling kills the child and
  ``grep_tail`` returns an error dict instead of hanging. Each line is
  also capped at ``MAX_GREP_LINE_CHARS`` to bound cheap-pattern cost on
  pathologically long lines.

  This uses ``subprocess.run([sys.executable, "-c", ...])`` rather than
  ``multiprocessing.Process`` on purpose. ``multiprocessing``'s "spawn"
  start method re-execs the *parent's* ``__main__`` module in the child
  to reconstruct its state — but grep_tail is invoked from callers whose
  ``__main__`` isn't a real file (``python -c``, a heredoc, the REPL, or
  any embedded/threaded caller), which makes the child fail with
  ``FileNotFoundError: '<stdin>'`` instead of running. Even under a real
  ``__main__`` (this repo's ``run_agent.py``), spawn would re-run that
  module's top-level code in every child, which is slow and can be
  side-effectful. ``fork()`` is not an option either: it's unsafe from
  the daemon thread pools that dispatch this tool (tools/async_delegation.py,
  tools/daemon_pool.py) — forking a multithreaded process can inherit a
  lock (e.g. the logging module's lock) held by another thread that will
  never be released in the child, deadlocking it silently. A plain
  ``python -c <script>`` subprocess imports only stdlib, never re-execs
  any module of ours, and works identically regardless of the parent's
  ``__main__`` or which thread launched it.
"""

import json
import os
import re
import stat
import subprocess
import sys
from typing import Any, Dict, List

from tools.registry import registry

MAX_TAIL_LINES = 10_000
READ_BLOCK_SIZE = 65_536
MAX_GREP_LINE_CHARS = 10_000
DEFAULT_TAIL_LINES = 100
DEFAULT_GREP_TAIL_LINES = 1_000
DEFAULT_MAX_MATCHES = 200
GREP_TIMEOUT_SECONDS = 5

# Self-contained worker script run via `python -c`. Stdlib-only (json, re,
# sys) — it deliberately imports nothing from this package, so there is no
# __main__ to re-exec and no dependency on how/where it was launched from.
# Reads a JSON payload from stdin, writes a JSON result to stdout.
_WORKER_SRC = """
import json, re, sys

payload = json.loads(sys.stdin.read())
compiled = re.compile(payload["pattern"])
max_line_chars = payload["max_line_chars"]
match_cap = payload["max_matches"]

matches = []
for line_no, text in enumerate(payload["lines"], start=1):
    if len(matches) >= match_cap:
        break
    if compiled.search(text[:max_line_chars]):
        matches.append({"line_no": line_no, "text": text})

json.dump({"ok": True, "matches": matches}, sys.stdout)
"""


def _validate_readable_file(path: str) -> str:
    """Return an error message if path isn't a readable regular file, else ''."""
    if not path:
        return "path is required"
    if not os.path.exists(path):
        return f"no such file: {path}"
    if not os.path.isfile(path) or not stat.S_ISREG(os.stat(path).st_mode):
        return f"not a regular file: {path}"
    if not os.access(path, os.R_OK):
        return f"file not readable: {path}"
    return ""


def _clamp_n(n: Any, default: int) -> int:
    """Coerce n to an int within [1, MAX_TAIL_LINES], falling back to default."""
    try:
        n_int = int(n)
    except (TypeError, ValueError):
        n_int = default
    return max(1, min(MAX_TAIL_LINES, n_int))


def _read_tail_blocks(f, n: int) -> List[bytes]:
    """Seek backward from EOF in READ_BLOCK_SIZE blocks until n+1 newlines are
    seen (or the start of the file is reached), returning the raw tail bytes
    split on b'\\n'.
    """
    file_size = f.tell()
    newline_count = 0
    position = file_size
    chunks: List[bytes] = []

    while position > 0 and newline_count <= n:
        block_size = min(READ_BLOCK_SIZE, position)
        position -= block_size
        f.seek(position)
        block = f.read(block_size)
        newline_count += block.count(b"\n")
        chunks.append(block)

    return b"".join(reversed(chunks)).split(b"\n")


def tail_lines(path: str, n: Any = DEFAULT_TAIL_LINES) -> Dict[str, Any]:
    """Return the last n lines of path, reading only the trailing blocks
    needed rather than the whole file. Safe for multi-gigabyte logs.
    """
    error = _validate_readable_file(path)
    if error:
        return {"ok": False, "path": path, "error": error}

    n_clamped = _clamp_n(n, DEFAULT_TAIL_LINES)

    try:
        with open(path, "rb") as f:
            f.seek(0, os.SEEK_END)
            file_size = f.tell()
            raw_lines = _read_tail_blocks(f, n_clamped) if file_size > 0 else [b""]
    except OSError as exc:
        return {"ok": False, "path": path, "error": str(exc)}

    if raw_lines and raw_lines[-1] == b"":
        raw_lines = raw_lines[:-1]

    tail = raw_lines[-n_clamped:]
    lines = [line.decode("utf-8", errors="replace") for line in tail]
    return {
        "ok": True,
        "path": path,
        "lines": lines,
        "truncated": len(raw_lines) > len(tail),
    }


def _run_grep_subprocess(lines: List[str], pattern: str, match_cap: int) -> Dict[str, Any]:
    """Run the regex scan in a killable child subprocess bounded by
    GREP_TIMEOUT_SECONDS. subprocess.run's own timeout kills the child on
    expiry, which actually stops runaway CPU — unlike a thread timeout or
    signal.alarm (which only works on the main thread on POSIX, and tools
    here may run in worker threads). See module docstring for why this is
    a subprocess and not a multiprocessing.Process.
    """
    payload = json.dumps({
        "pattern": pattern,
        "lines": lines,
        "max_matches": match_cap,
        "max_line_chars": MAX_GREP_LINE_CHARS,
    })
    try:
        result = subprocess.run(
            [sys.executable, "-c", _WORKER_SRC],
            input=payload,
            capture_output=True,
            text=True,
            timeout=GREP_TIMEOUT_SECONDS,
        )
    except subprocess.TimeoutExpired:
        return {"ok": False, "error": "pattern evaluation timed out (possible catastrophic backtracking)"}

    if result.returncode != 0:
        return {"ok": False, "error": f"grep worker failed: {result.stderr.strip()[:500]}"}

    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError:
        return {"ok": False, "error": "grep worker returned malformed output"}


def grep_tail(
    path: str,
    pattern: str,
    n: Any = DEFAULT_GREP_TAIL_LINES,
    max_matches: Any = DEFAULT_MAX_MATCHES,
) -> Dict[str, Any]:
    """Tail the last n lines of path, then return lines matching pattern,
    capped at max_matches. Invalid regexes return an error dict, not a
    crash; catastrophic-backtracking patterns time out (see module
    docstring) instead of hanging.
    """
    try:
        re.compile(pattern)
    except re.error as exc:
        return {"ok": False, "path": path, "error": f"invalid pattern: {exc}"}

    tail_result = tail_lines(path, n)
    if not tail_result["ok"]:
        return {"ok": False, "path": path, "error": tail_result["error"]}

    match_cap = _clamp_n(max_matches, DEFAULT_MAX_MATCHES)
    worker_result = _run_grep_subprocess(tail_result["lines"], pattern, match_cap)
    if not worker_result["ok"]:
        return {"ok": False, "path": path, "error": worker_result["error"]}

    matches = worker_result["matches"]
    return {"ok": True, "path": path, "matches": matches, "count": len(matches)}


registry.register(
    name="tail_lines",
    toolset="code_execution",
    schema={
        "name": "tail_lines",
        "description": (
            "Return the last N lines of a local log file. Reads only the "
            "trailing blocks needed via seek-from-end, so it's safe on "
            f"multi-gigabyte files. N is capped at {MAX_TAIL_LINES}. Use "
            "`grep_tail` instead if you need to filter the tail by pattern."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "Path to the local log file."},
                "n": {
                    "type": "integer",
                    "description": f"Number of trailing lines to return (1-{MAX_TAIL_LINES}). Defaults to {DEFAULT_TAIL_LINES}.",
                },
            },
            "required": ["path"],
        },
    },
    handler=lambda args, **kw: json.dumps(
        tail_lines(path=args.get("path", ""), n=args.get("n", DEFAULT_TAIL_LINES)),
        ensure_ascii=False,
    ),
    emoji="📄",
)

registry.register(
    name="grep_tail",
    toolset="code_execution",
    schema={
        "name": "grep_tail",
        "description": (
            "Tail the last N lines of a local log file, then filter them "
            "with a regex pattern, returning up to max_matches hits with "
            "line numbers. Invalid regexes return an error instead of "
            "crashing. Use `tail_lines` instead for unfiltered tailing."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "Path to the local log file."},
                "pattern": {"type": "string", "description": "Regex pattern to search for in each tailed line."},
                "n": {
                    "type": "integer",
                    "description": f"Number of trailing lines to scan (1-{MAX_TAIL_LINES}). Defaults to {DEFAULT_GREP_TAIL_LINES}.",
                },
                "max_matches": {
                    "type": "integer",
                    "description": f"Maximum matches to return. Defaults to {DEFAULT_MAX_MATCHES}.",
                },
            },
            "required": ["path", "pattern"],
        },
    },
    handler=lambda args, **kw: json.dumps(
        grep_tail(
            path=args.get("path", ""),
            pattern=args.get("pattern", ""),
            n=args.get("n", DEFAULT_GREP_TAIL_LINES),
            max_matches=args.get("max_matches", DEFAULT_MAX_MATCHES),
        ),
        ensure_ascii=False,
    ),
    emoji="📄",
)
