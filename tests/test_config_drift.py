"""Tests for hermes_cli.config_drift.

Fully offline and tmp_path-based -- these tests never touch the real
HERMES_HOME. All config/baseline paths are passed explicitly so the module's
defaults (which read ``hermes_constants.get_hermes_home()``) are never
exercised here; the ``tests/conftest.py`` autouse fixture also isolates
HERMES_HOME to a per-test tempdir as a second line of defense.
"""

from pathlib import Path

from hermes_cli.config_drift import check_drift, create_baseline


def _write_config(path: Path, text: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path


def test_check_drift_with_no_baseline_returns_baseline_missing(tmp_path):
    config_path = _write_config(tmp_path / "config.yaml", "model: sonnet\n")
    baseline_file = tmp_path / "state" / "config-baseline" / "config.yaml"

    result = check_drift(config_path=config_path, baseline_file=baseline_file)

    assert result["baseline_exists"] is False
    assert result["drifted"] is False
    assert result["diff"] == []


def test_create_baseline_then_check_drift_reports_no_drift(tmp_path):
    config_path = _write_config(tmp_path / "config.yaml", "model: sonnet\ntemp: 0.5\n")
    baseline_file = tmp_path / "state" / "config-baseline" / "config.yaml"

    returned_path = create_baseline(config_path=config_path, baseline_file=baseline_file)

    assert returned_path == baseline_file
    assert baseline_file.exists()
    assert baseline_file.read_text(encoding="utf-8") == config_path.read_text(encoding="utf-8")

    result = check_drift(config_path=config_path, baseline_file=baseline_file)

    assert result["baseline_exists"] is True
    assert result["drifted"] is False
    assert result["diff"] == []


def test_check_drift_detects_modified_config(tmp_path):
    config_path = _write_config(tmp_path / "config.yaml", "model: sonnet\ntemp: 0.5\n")
    baseline_file = tmp_path / "state" / "config-baseline" / "config.yaml"

    create_baseline(config_path=config_path, baseline_file=baseline_file)

    # Mutate the config after the baseline snapshot was taken.
    _write_config(config_path, "model: opus\ntemp: 0.9\n")

    result = check_drift(config_path=config_path, baseline_file=baseline_file)

    assert result["baseline_exists"] is True
    assert result["drifted"] is True
    assert len(result["diff"]) > 0
    diff_text = "".join(result["diff"])
    assert "model: sonnet" in diff_text
    assert "model: opus" in diff_text

    # check_drift must never write to the live config it reads.
    assert config_path.read_text(encoding="utf-8") == "model: opus\ntemp: 0.9\n"


def test_check_drift_missing_config_after_baseline_is_drift(tmp_path):
    config_path = _write_config(tmp_path / "config.yaml", "model: sonnet\n")
    baseline_file = tmp_path / "state" / "config-baseline" / "config.yaml"

    create_baseline(config_path=config_path, baseline_file=baseline_file)
    config_path.unlink()

    result = check_drift(config_path=config_path, baseline_file=baseline_file)

    assert result["baseline_exists"] is True
    assert result["drifted"] is True
    assert len(result["diff"]) > 0


def test_create_baseline_creates_parent_dirs(tmp_path):
    config_path = _write_config(tmp_path / "config.yaml", "model: sonnet\n")
    # Deeply nested baseline location that does not exist yet.
    baseline_file = tmp_path / "nested" / "state" / "config-baseline" / "config.yaml"

    result_path = create_baseline(config_path=config_path, baseline_file=baseline_file)

    assert result_path.exists()
    assert result_path.parent.is_dir()
