"""Tests for tools/_regex_guard.py — shared ReDoS-safe regex evaluation."""

import json
import os
import subprocess
import sys
import time

import pytest

from tools import _regex_guard

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestSafeRegexFilter:
    def test_normal_pattern_returns_correct_matches(self):
        lines = [f"line {i}" for i in range(1, 21)] + ["ERROR boom"]

        result = _regex_guard.safe_regex_filter(
            r"ERROR", lines, max_matches=200, max_line_chars=10_000
        )

        assert result["ok"] is True
        assert len(result["matches"]) == 1
        assert result["matches"][0]["text"] == "ERROR boom"
        assert result["matches"][0]["line_no"] == 21

    def test_no_matches_returns_empty_list(self):
        lines = ["nothing here", "still nothing"]

        result = _regex_guard.safe_regex_filter(
            r"NOPE_NOT_PRESENT", lines, max_matches=200, max_line_chars=10_000
        )

        assert result["ok"] is True
        assert result["matches"] == []

    def test_catastrophic_pattern_times_out_instead_of_hanging(self):
        # (a+)+b against a string of 40 'a's followed by a non-matching char
        # is a classic catastrophic-backtracking pattern; a naive engine's
        # backtracking blows up exponentially. Must raise within roughly
        # the timeout, not hang the process.
        lines = ["a" * 40 + "X"]

        started = time.monotonic()
        with pytest.raises(_regex_guard.RegexGuardError, match="timed out"):
            _regex_guard.safe_regex_filter(
                r"(a+)+b",
                lines,
                max_matches=200,
                max_line_chars=10_000,
                timeout=2,
            )
        elapsed = time.monotonic() - started

        assert elapsed < 2 + 5, f"safe_regex_filter took {elapsed:.1f}s, looks hung"

    def test_invalid_regex_raises_clean_error(self):
        with pytest.raises(_regex_guard.RegexGuardError, match="invalid pattern"):
            _regex_guard.safe_regex_filter(
                r"(unclosed", ["a", "b"], max_matches=200, max_line_chars=10_000
            )

    def test_max_matches_caps_returned_matches(self):
        lines = ["ERROR fail"] * 10

        result = _regex_guard.safe_regex_filter(
            r"ERROR", lines, max_matches=3, max_line_chars=10_000
        )

        assert result["ok"] is True
        assert len(result["matches"]) == 3

    def test_max_line_chars_caps_scan_window_per_line(self):
        # The match only appears after char 5000 - if max_line_chars truly
        # bounds the scan window, this must NOT match.
        line = ("x" * 5000) + "ERROR"

        result = _regex_guard.safe_regex_filter(
            r"ERROR", [line], max_matches=200, max_line_chars=100
        )

        assert result["ok"] is True
        assert result["matches"] == []

    def test_works_from_caller_with_no_real_main_file(self):
        # Regression guard: this module must not depend on multiprocessing's
        # "spawn" start method, which re-execs the CALLING process's
        # __main__ module in the child. A `python -c "..."` process has no
        # real __main__ file (spawn would try to re-exec '<stdin>' and
        # fail), so driving safe_regex_filter from exactly that kind of
        # caller is the regression guard for using subprocess.run of a
        # self-contained worker script instead.
        driver = (
            "import json, sys\n"
            "from tools import _regex_guard\n"
            "result = _regex_guard.safe_regex_filter(\n"
            "    r'ERROR', ['line one', 'ERROR boom'],\n"
            "    max_matches=200, max_line_chars=10000,\n"
            ")\n"
            "print(json.dumps(result))\n"
        )
        result = subprocess.run(
            [sys.executable, "-c", driver],
            capture_output=True,
            text=True,
            timeout=30,
            cwd=REPO_ROOT,
        )

        assert result.returncode == 0, result.stderr
        payload = json.loads(result.stdout)
        assert payload["ok"] is True
        assert payload["matches"][0]["text"] == "ERROR boom"


class TestSafeRegexSearch:
    def test_returns_true_on_match(self):
        assert _regex_guard.safe_regex_search(r"ERROR", "boom ERROR here") is True

    def test_returns_false_on_no_match(self):
        assert _regex_guard.safe_regex_search(r"ERROR", "all fine here") is False

    def test_invalid_pattern_raises(self):
        with pytest.raises(_regex_guard.RegexGuardError, match="invalid pattern"):
            _regex_guard.safe_regex_search(r"(unclosed", "text")
