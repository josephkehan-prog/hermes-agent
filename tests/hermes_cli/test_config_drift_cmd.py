"""Tests for the ``hermes config-drift`` CLI wrapper (hermes_cli.config_drift.cmd_config_drift).

Fully offline: the pure ``check_drift`` / ``create_baseline`` functions
already have dedicated coverage in ``tests/test_config_drift.py``. These
tests only exercise the thin CLI layer -- argument handling, printed
output, and exit codes -- by monkeypatching the module-level functions the
handler calls.
"""

from argparse import Namespace
from pathlib import Path

import pytest

import hermes_cli.config_drift as config_drift


def _args(rebaseline: bool = False) -> Namespace:
    return Namespace(rebaseline=rebaseline)


def test_no_baseline_prints_hint_and_exits_zero(monkeypatch, capsys):
    monkeypatch.setattr(
        config_drift,
        "check_drift",
        lambda: {"baseline_exists": False, "drifted": False, "diff": []},
    )

    # Should return normally (no SystemExit) -- exit code 0.
    config_drift.cmd_config_drift(_args())

    out = capsys.readouterr().out
    assert "no baseline" in out
    assert "--rebaseline" in out


def test_no_drift_prints_no_drift_and_exits_zero(monkeypatch, capsys):
    monkeypatch.setattr(
        config_drift,
        "check_drift",
        lambda: {"baseline_exists": True, "drifted": False, "diff": []},
    )

    config_drift.cmd_config_drift(_args())

    out = capsys.readouterr().out
    assert out.strip() == "no drift"


def test_drift_prints_diff_and_exits_two(monkeypatch, capsys):
    diff_lines = ["--- baseline\n", "+++ current\n", "-model: sonnet\n", "+model: opus\n"]
    monkeypatch.setattr(
        config_drift,
        "check_drift",
        lambda: {"baseline_exists": True, "drifted": True, "diff": diff_lines},
    )

    with pytest.raises(SystemExit) as exc_info:
        config_drift.cmd_config_drift(_args())

    assert exc_info.value.code == 2
    out = capsys.readouterr().out
    assert "drift detected" in out
    assert "model: opus" in out


def test_rebaseline_creates_baseline_and_reports_path(monkeypatch, capsys, tmp_path):
    fake_baseline = tmp_path / "state" / "config-baseline" / "config.yaml"
    called = {}

    def _fake_create_baseline():
        called["ran"] = True
        return fake_baseline

    monkeypatch.setattr(config_drift, "create_baseline", _fake_create_baseline)
    # If check_drift were called during --rebaseline, this would raise --
    # asserting rebaseline is a distinct, single-purpose code path.
    monkeypatch.setattr(
        config_drift,
        "check_drift",
        lambda: pytest.fail("check_drift must not run during --rebaseline"),
    )

    config_drift.cmd_config_drift(_args(rebaseline=True))

    assert called["ran"] is True
    out = capsys.readouterr().out
    assert "baseline created" in out
    assert str(fake_baseline) in out


def test_rebaseline_is_read_only_on_live_config(monkeypatch, tmp_path):
    """--rebaseline must only ever write to the baseline snapshot path."""
    from hermes_constants import get_hermes_home

    home = get_hermes_home()
    config_path = home / "config.yaml"
    config_path.write_text("model: sonnet\n", encoding="utf-8")

    config_drift.cmd_config_drift(_args(rebaseline=True))

    # Real config.yaml is untouched; the baseline copy now exists instead.
    assert config_path.read_text(encoding="utf-8") == "model: sonnet\n"
    baseline = config_drift.baseline_path()
    assert baseline.exists()
    assert baseline.read_text(encoding="utf-8") == "model: sonnet\n"
