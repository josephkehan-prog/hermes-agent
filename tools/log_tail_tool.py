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
  ``tools/_regex_guard.py``, which runs the actual regex scan in a killable
  child subprocess under a wall-clock timeout (``GREP_TIMEOUT_SECONDS``); a
  plain ``except`` cannot stop runaway C-level regex backtracking mid-call
  — only terminating the process running it can. If the scan doesn't finish
  in time, ``grep_tail`` returns an error dict instead of hanging. Each
  line is also capped at ``MAX_GREP_LINE_CHARS`` to bound cheap-pattern
  cost on pathologically long lines. See ``tools/_regex_guard.py`` for why
  this is a ``subprocess.run`` and not a ``multiprocessing.Process``.
"""

import json
import os
import re
import stat
from typing import Any, Dict, List

from tools import _regex_guard
from tools.registry import registry

MAX_TAIL_LINES = 10_000
READ_BLOCK_SIZE = 65_536
MAX_GREP_LINE_CHARS = 10_000
DEFAULT_TAIL_LINES = 100
DEFAULT_GREP_TAIL_LINES = 1_000
DEFAULT_MAX_MATCHES = 200
GREP_TIMEOUT_SECONDS = _regex_guard.DEFAULT_REGEX_TIMEOUT


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


def grep_tail(
    path: str,
    pattern: str,
    n: Any = DEFAULT_GREP_TAIL_LINES,
    max_matches: Any = DEFAULT_MAX_MATCHES,
    case_insensitive: bool = False,
) -> Dict[str, Any]:
    """Tail the last n lines of path, then return lines matching pattern,
    capped at max_matches. Invalid regexes return an error dict, not a
    crash; catastrophic-backtracking patterns time out (see module
    docstring) instead of hanging.

    ``case_insensitive`` applies the regex with the ignore-case flag.
    """
    try:
        re.compile(pattern)
    except re.error as exc:
        return {"ok": False, "path": path, "error": f"invalid pattern: {exc}"}

    if case_insensitive:
        # Inline flag at the very start of the pattern — the guard worker
        # compiles the pattern text directly, so this is the portable way to
        # request ignore-case without changing the worker payload.
        pattern = f"(?i){pattern}"

    tail_result = tail_lines(path, n)
    if not tail_result["ok"]:
        return {"ok": False, "path": path, "error": tail_result["error"]}

    match_cap = _clamp_n(max_matches, DEFAULT_MAX_MATCHES)
    try:
        guard_result = _regex_guard.safe_regex_filter(
            pattern,
            tail_result["lines"],
            max_matches=match_cap,
            max_line_chars=MAX_GREP_LINE_CHARS,
            timeout=GREP_TIMEOUT_SECONDS,
        )
    except _regex_guard.RegexGuardError as exc:
        return {"ok": False, "path": path, "error": str(exc)}

    matches = guard_result["matches"]
    return {"ok": True, "path": path, "matches": matches, "count": len(matches)}


registry.register(
    name="tail_lines",
    toolset="monitoring",
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
    toolset="monitoring",
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
                "case_insensitive": {
                    "type": "boolean",
                    "description": "Match the pattern case-insensitively. Defaults to false.",
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
            case_insensitive=bool(args.get("case_insensitive", False)),
        ),
        ensure_ascii=False,
    ),
    emoji="📄",
)
