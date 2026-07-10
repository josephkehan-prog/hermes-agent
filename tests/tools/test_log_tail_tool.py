"""Tests for tools/log_tail_tool.py — local log tailing and grep."""

import time

from tools import log_tail_tool


def _write_numbered_lines(tmp_path, count):
    path = tmp_path / "app.log"
    lines = [f"line {i}" for i in range(1, count + 1)]
    path.write_text("\n".join(lines) + "\n")
    return str(path)


class TestTailLines:
    def test_returns_last_n_lines_in_order(self, tmp_path):
        path = _write_numbered_lines(tmp_path, 500)

        result = log_tail_tool.tail_lines(path, n=10)

        assert result["ok"] is True
        assert result["lines"] == [f"line {i}" for i in range(491, 501)]
        assert result["truncated"] is True

    def test_seek_from_end_gets_the_correct_last_line(self, tmp_path):
        path = _write_numbered_lines(tmp_path, 500)

        result = log_tail_tool.tail_lines(path, n=5)

        assert result["lines"][-1] == "line 500"

    def test_n_larger_than_file_returns_all_lines_and_not_truncated(self, tmp_path):
        path = _write_numbered_lines(tmp_path, 20)

        result = log_tail_tool.tail_lines(path, n=100)

        assert result["ok"] is True
        assert len(result["lines"]) == 20
        assert result["lines"][0] == "line 1"
        assert result["truncated"] is False

    def test_empty_file_returns_no_lines(self, tmp_path):
        path = tmp_path / "empty.log"
        path.write_text("")

        result = log_tail_tool.tail_lines(str(path), n=10)

        assert result["ok"] is True
        assert result["lines"] == []

    def test_n_is_clamped_to_max_tail_lines(self, tmp_path):
        path = _write_numbered_lines(tmp_path, 20)

        result = log_tail_tool.tail_lines(path, n=999_999_999)

        assert result["ok"] is True
        assert len(result["lines"]) == 20

    def test_missing_file_is_an_error_not_an_exception(self):
        result = log_tail_tool.tail_lines("/no/such/log.log", n=10)

        assert result["ok"] is False
        assert "no such file" in result["error"]

    def test_directory_path_is_an_error(self, tmp_path):
        result = log_tail_tool.tail_lines(str(tmp_path), n=10)

        assert result["ok"] is False
        assert "not a regular file" in result["error"]

    def test_blank_path_is_an_error(self):
        result = log_tail_tool.tail_lines("", n=10)

        assert result["ok"] is False
        assert "path is required" in result["error"]


class TestGrepTail:
    def test_matches_pattern_within_tailed_lines(self, tmp_path):
        path = tmp_path / "app.log"
        path.write_text("\n".join(
            [f"line {i}" for i in range(1, 51)] + ["ERROR boom", "line 52"]
        ) + "\n")

        result = log_tail_tool.grep_tail(str(path), r"ERROR", n=1000)

        assert result["ok"] is True
        assert result["count"] == 1
        assert result["matches"][0]["text"] == "ERROR boom"

    def test_max_matches_caps_returned_matches(self, tmp_path):
        path = tmp_path / "app.log"
        path.write_text("\n".join(["ERROR fail"] * 10) + "\n")

        result = log_tail_tool.grep_tail(str(path), r"ERROR", n=1000, max_matches=3)

        assert result["ok"] is True
        assert result["count"] == 3

    def test_invalid_regex_returns_error_dict_not_crash(self, tmp_path):
        path = _write_numbered_lines(tmp_path, 5)

        result = log_tail_tool.grep_tail(path, r"(unclosed", n=10)

        assert result["ok"] is False
        assert "invalid pattern" in result["error"]

    def test_missing_file_returns_error_dict(self):
        result = log_tail_tool.grep_tail("/no/such/log.log", r"ERROR", n=10)

        assert result["ok"] is False
        assert "no such file" in result["error"]

    def test_no_matches_returns_empty_list(self, tmp_path):
        path = _write_numbered_lines(tmp_path, 5)

        result = log_tail_tool.grep_tail(path, r"NOPE_NOT_PRESENT", n=10)

        assert result["ok"] is True
        assert result["matches"] == []
        assert result["count"] == 0

    def test_catastrophic_backtracking_pattern_times_out_instead_of_hanging(self, tmp_path):
        # (a+)+b is a classic catastrophic-backtracking pattern: against a
        # string of 40 'a's followed by a non-matching char, a naive regex
        # engine's backtracking blows up exponentially. This must return an
        # error dict within a few seconds — not hang the process.
        path = tmp_path / "evil.log"
        path.write_text("a" * 40 + "X" + "\n")

        started = time.monotonic()
        result = log_tail_tool.grep_tail(str(path), r"(a+)+b", n=10)
        elapsed = time.monotonic() - started

        assert elapsed < log_tail_tool.GREP_TIMEOUT_SECONDS + 5, f"grep_tail took {elapsed:.1f}s, looks hung"
        assert result["ok"] is False
        assert "timed out" in result["error"]

    def test_normal_pattern_still_works_after_redos_guard(self, tmp_path):
        # Regression check: the process-bounded worker must not break the
        # common case of a plain pattern matching normally.
        path = tmp_path / "app.log"
        path.write_text("\n".join([f"line {i}" for i in range(1, 21)] + ["ERROR boom"]) + "\n")

        result = log_tail_tool.grep_tail(str(path), r"ERROR", n=1000)

        assert result["ok"] is True
        assert result["count"] == 1
        assert result["matches"][0]["text"] == "ERROR boom"
