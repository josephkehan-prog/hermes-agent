"""Tests for skills/devops/log-triage/scripts/logtriage.py — no network, local files only."""

from __future__ import annotations

import argparse
import importlib.util
import json
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT = REPO_ROOT / "skills" / "devops" / "log-triage" / "scripts" / "logtriage.py"


def _load_script_module():
    spec = importlib.util.spec_from_file_location("log_triage_logtriage_test_module", SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


logtriage = _load_script_module()


class TestClassifySeverity:
    @pytest.mark.parametrize(
        "line,expected",
        [
            ("2024-01-01 12:00:00 DEBUG loaded config", "DEBUG"),
            ("2024-01-01 12:00:00 INFO service started", "INFO"),
            ("2024-01-01 12:00:00 WARN cache miss", "WARN"),
            ("2024-01-01 12:00:00 WARNING cache miss", "WARN"),
            ("2024-01-01 12:00:00 ERROR failed to connect", "ERROR"),
            ("2024-01-01 12:00:00 ERR failed to connect", "ERROR"),
            ("2024-01-01 12:00:00 FATAL out of memory", "FATAL"),
            ("2024-01-01 12:00:00 CRITICAL disk full", "FATAL"),
            ("2024-01-01 12:00:00 PANIC unrecoverable", "FATAL"),
            ("just a message with no level keyword at all", "UNKNOWN"),
        ],
    )
    def test_classifies_plain_text_lines(self, line, expected):
        assert logtriage.classify_severity(line) == expected

    def test_classifies_json_line_by_level_field(self):
        line = json.dumps({"level": "error", "msg": "boom"})
        assert logtriage.classify_severity(line) == "ERROR"

    def test_classifies_json_line_by_severity_field(self):
        line = json.dumps({"severity": "warning", "msg": "careful"})
        assert logtriage.classify_severity(line) == "WARN"

    def test_json_line_with_unrecognized_level_falls_back_to_unknown(self):
        line = json.dumps({"level": "banana", "msg": "no keyword here"})
        assert logtriage.classify_severity(line) == "UNKNOWN"

    def test_malformed_json_looking_line_falls_back_to_regex(self):
        line = '{not valid json but has ERROR in it'
        assert logtriage.classify_severity(line) == "ERROR"

    def test_fatal_takes_priority_over_error_keyword_in_same_line(self):
        line = "FATAL: previous ERROR escalated to shutdown"
        assert logtriage.classify_severity(line) == "FATAL"


class TestNormalizeTemplate:
    def test_normalizes_numbers_uuids_and_timestamps(self):
        line = (
            "2024-01-01T12:00:05Z ERROR user 123 failed to connect to "
            "db-uuid 550e8400-e29b-41d4-a716-446655440000"
        )
        template = logtriage.normalize_template(line)
        assert template == "<TS> ERROR user <NUM> failed to connect to db-uuid <UUID>"

    def test_normalizes_hex_addresses(self):
        line = "ERROR segfault at address 0xdeadbeef"
        assert logtriage.normalize_template(line) == "ERROR segfault at address <HEX>"


class TestClusterLines:
    def test_three_similar_error_lines_collapse_to_one_template(self):
        lines = [
            "2024-01-01T12:00:05Z ERROR user 123 failed to connect to db-uuid 550e8400-e29b-41d4-a716-446655440000",
            "2024-01-01T12:00:06Z ERROR user 456 failed to connect to db-uuid 6ba7b810-9dad-11d1-80b4-00c04fd430c8",
            "2024-01-01T12:00:07Z ERROR user 789 failed to connect to db-uuid 6ba7b811-9dad-11d1-80b4-00c04fd430c9",
        ]

        clusters = logtriage.cluster_lines(lines)

        assert len(clusters) == 1
        assert clusters[0]["count"] == 3
        assert clusters[0]["template"] == "<TS> ERROR user <NUM> failed to connect to db-uuid <UUID>"
        assert clusters[0]["example"] == lines[0]

    def test_non_error_lines_are_excluded_from_clustering(self):
        lines = [
            "2024-01-01T12:00:00Z INFO service started",
            "2024-01-01T12:00:01Z DEBUG loaded config",
        ]
        assert logtriage.cluster_lines(lines) == []

    def test_top_n_limits_number_of_templates_returned(self):
        kinds = ["timeout", "refused", "reset", "unauthorized", "not-found"]
        lines = [f"ERROR request failed: {kind}" for kind in kinds]
        clusters = logtriage.cluster_lines(lines, top_n=2)
        assert len(clusters) == 2

    def test_most_frequent_template_ranks_first(self):
        lines = [
            "ERROR rare failure",
            "ERROR common failure 1",
            "ERROR common failure 2",
            "ERROR common failure 3",
        ]
        clusters = logtriage.cluster_lines(lines, top_n=5)
        assert clusters[0]["template"] == "ERROR common failure <NUM>"
        assert clusters[0]["count"] == 3


class TestTailLines:
    def test_returns_all_lines_when_under_the_cap(self, tmp_path):
        log_file = tmp_path / "small.log"
        log_file.write_text("line1\nline2\nline3\n")

        lines = logtriage.tail_lines(log_file, max_lines=200)

        assert lines == ["line1", "line2", "line3"]

    def test_large_file_returns_only_last_n_lines(self, tmp_path):
        log_file = tmp_path / "large.log"
        log_file.write_text("\n".join(f"line{i}" for i in range(10_000)) + "\n")

        lines = logtriage.tail_lines(log_file, max_lines=50)

        assert len(lines) == 50
        assert lines[-1] == "line9999"
        assert lines[0] == "line9950"

    def test_byte_cap_bounds_the_read_even_with_a_huge_line_count(self, tmp_path):
        log_file = tmp_path / "huge.log"
        log_file.write_text("\n".join(f"line{i}" for i in range(50_000)) + "\n")

        # Ask for way more lines than the tiny byte cap can hold.
        lines = logtriage.tail_lines(log_file, max_lines=1_000_000, max_bytes=100)

        assert len(lines) < 1_000_000
        assert lines[-1] == "line49999"


class TestExtractTimeSpan:
    def test_finds_first_and_last_iso_timestamps(self):
        lines = [
            "2024-01-01T12:00:00Z INFO start",
            "2024-01-01T12:00:05Z ERROR middle",
            "2024-01-01T12:00:11Z INFO end",
        ]
        assert logtriage.extract_time_span(lines) == {
            "start": "2024-01-01T12:00:00Z",
            "end": "2024-01-01T12:00:11Z",
        }

    def test_returns_none_when_no_timestamps_found(self):
        lines = ["no timestamp here", "still nothing"]
        assert logtriage.extract_time_span(lines) is None


class TestValidateLogPath:
    def test_missing_file_exits_2(self, tmp_path):
        missing = tmp_path / "does-not-exist.log"
        with pytest.raises(SystemExit) as exc_info:
            logtriage.validate_log_path(str(missing))
        assert exc_info.value.code == 2

    def test_directory_path_is_rejected(self, tmp_path):
        with pytest.raises(SystemExit) as exc_info:
            logtriage.validate_log_path(str(tmp_path))
        assert exc_info.value.code == 2

    def test_regular_file_is_accepted(self, tmp_path):
        log_file = tmp_path / "ok.log"
        log_file.write_text("hello\n")
        resolved = logtriage.validate_log_path(str(log_file))
        assert resolved == log_file.resolve()


class TestCmdScan:
    def test_scan_reports_counts_and_matches(self, tmp_path, capsys):
        log_file = tmp_path / "app.log"
        log_file.write_text(
            "2024-01-01T12:00:00Z INFO service started\n"
            "2024-01-01T12:00:01Z ERROR failed to connect\n"
            "2024-01-01T12:00:02Z FATAL out of memory\n"
        )
        args = argparse.Namespace(logfile=str(log_file), since_lines=200, level=None)

        logtriage.cmd_scan(args)

        output = json.loads(capsys.readouterr().out)
        assert output["counts"] == {"INFO": 1, "ERROR": 1, "FATAL": 1}
        assert len(output["matches"]) == 2

    def test_scan_with_level_filter_returns_only_that_level(self, tmp_path, capsys):
        log_file = tmp_path / "app.log"
        log_file.write_text(
            "2024-01-01T12:00:00Z INFO service started\n"
            "2024-01-01T12:00:01Z WARN cache miss\n"
        )
        args = argparse.Namespace(logfile=str(log_file), since_lines=200, level="WARN")

        logtriage.cmd_scan(args)

        output = json.loads(capsys.readouterr().out)
        assert len(output["matches"]) == 1
        assert "WARN" in output["matches"][0]

    def test_scan_rejects_invalid_level(self, tmp_path):
        log_file = tmp_path / "app.log"
        log_file.write_text("INFO hello\n")
        args = argparse.Namespace(logfile=str(log_file), since_lines=200, level="NOTALEVEL")

        with pytest.raises(SystemExit) as exc_info:
            logtriage.cmd_scan(args)
        assert exc_info.value.code == 2


class TestCmdSummary:
    def test_summary_json_structure(self, tmp_path, capsys):
        log_file = tmp_path / "app.log"
        log_file.write_text(
            "2024-01-01T12:00:00Z INFO service started\n"
            "2024-01-01T12:00:05Z ERROR user 1 failed to connect to db-uuid 550e8400-e29b-41d4-a716-446655440000\n"
            "2024-01-01T12:00:06Z ERROR user 2 failed to connect to db-uuid 6ba7b810-9dad-11d1-80b4-00c04fd430c8\n"
        )
        args = argparse.Namespace(logfile=str(log_file), since_lines=200)

        logtriage.cmd_summary(args)

        output = json.loads(capsys.readouterr().out)
        assert set(output.keys()) == {"file", "lines_scanned", "counts", "top_errors", "time_span"}
        assert output["lines_scanned"] == 3
        assert output["top_errors"][0]["count"] == 2
        assert output["time_span"] == {"start": "2024-01-01T12:00:00Z", "end": "2024-01-01T12:00:06Z"}
