"""Shared ReDoS-safe regex evaluation for tools taking a caller-supplied pattern.

Consolidates the sandboxing contract originally built for
``tools/log_tail_tool.py``'s ``grep_tail``: catastrophic-backtracking
patterns (e.g. ``(a+)+b``) are bounded by running the actual compile+scan in
a killable child *subprocess* under a wall-clock timeout — a plain
``except`` cannot stop runaway C-level regex backtracking mid-call; only
terminating the process running it can. Any tool that evaluates a
caller-supplied regex against caller-supplied text should import from here
instead of re-implementing this.

This uses ``subprocess.run([sys.executable, "-c", ...])`` rather than
``multiprocessing.Process`` on purpose. ``multiprocessing``'s "spawn" start
method re-execs the *parent's* ``__main__`` module in the child to
reconstruct its state — but callers of this guard may be invoked from a
``__main__`` that isn't a real file (``python -c``, a heredoc, the REPL, or
any embedded/threaded caller), which makes the child fail with
``FileNotFoundError: '<stdin>'`` instead of running. Even under a real
``__main__``, spawn would re-run that module's top-level code in every
child, which is slow and can be side-effectful. ``fork()`` is not an option
either: it's unsafe from the daemon thread pools that dispatch tool handlers
in this repo (``tools/async_delegation.py``, ``tools/daemon_pool.py``) —
forking a multithreaded process can inherit a lock (e.g. the logging
module's lock) held by another thread that will never be released in the
child, deadlocking it silently. A plain ``python -c <script>`` subprocess
imports only stdlib, never re-execs any module of ours, and behaves
identically regardless of the parent's ``__main__`` or which thread called
it — which is what makes this guard safe to call from any of those pools.
"""

import json
import re
import subprocess
import sys
from typing import Any, Dict, List

DEFAULT_REGEX_TIMEOUT = 5

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


class RegexGuardError(Exception):
    """Raised when a caller-supplied regex can't be safely evaluated:
    an invalid pattern (``re.error``), a scan that exceeded its timeout
    (possible catastrophic backtracking), or a worker subprocess failure.
    """


def safe_regex_filter(
    pattern: str,
    lines: List[str],
    *,
    max_matches: int,
    max_line_chars: int,
    timeout: float = DEFAULT_REGEX_TIMEOUT,
) -> Dict[str, Any]:
    """Filter lines by pattern, bounding worst-case regex cost.

    Runs the compile+scan in a killable child subprocess under a wall-clock
    ``timeout`` (see module docstring for why subprocess, not
    multiprocessing). ``subprocess.run``'s own timeout handling kills the
    child on expiry, which actually stops runaway CPU — unlike a thread
    timeout or ``signal.alarm`` (which only works on the main thread on
    POSIX, and tools here may run in worker threads).

    Returns ``{"ok": True, "matches": [{"line_no": int, "text": str}, ...]}``
    on success. Raises ``RegexGuardError`` if ``pattern`` doesn't compile, if
    the scan doesn't finish within ``timeout``, or if the worker subprocess
    fails unexpectedly.

    Each line is capped at ``max_line_chars`` before scanning, to bound
    cheap-pattern cost on pathologically long lines. Collection stops once
    ``max_matches`` matches are found.
    """
    try:
        re.compile(pattern)
    except re.error as exc:
        raise RegexGuardError(f"invalid pattern: {exc}") from exc

    payload = json.dumps({
        "pattern": pattern,
        "lines": lines,
        "max_matches": max_matches,
        "max_line_chars": max_line_chars,
    })
    try:
        result = subprocess.run(
            [sys.executable, "-c", _WORKER_SRC],
            input=payload,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
    except subprocess.TimeoutExpired:
        raise RegexGuardError(
            "pattern evaluation timed out (possible catastrophic backtracking)"
        ) from None

    if result.returncode != 0:
        raise RegexGuardError(f"regex worker failed: {result.stderr.strip()[:500]}")

    try:
        worker_result = json.loads(result.stdout)
    except json.JSONDecodeError:
        raise RegexGuardError("regex worker returned malformed output") from None

    if not worker_result.get("ok"):
        raise RegexGuardError(worker_result.get("error", "regex worker failed"))

    return worker_result


def safe_regex_search(pattern: str, text: str, timeout: float = DEFAULT_REGEX_TIMEOUT) -> bool:
    """Convenience wrapper: True if pattern matches anywhere in text, bounded
    the same way as safe_regex_filter. Raises RegexGuardError under the same
    conditions (invalid pattern, timeout, worker failure).
    """
    result = safe_regex_filter(
        pattern,
        [text],
        max_matches=1,
        max_line_chars=max(len(text), 1),
        timeout=timeout,
    )
    return len(result["matches"]) > 0
