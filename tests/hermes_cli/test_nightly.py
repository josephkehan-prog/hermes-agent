"""Tests for ``hermes nightly`` (hermes_cli.nightly).

Fully offline: the ``hermes doctor`` subprocess call is replaced with an
injected ``doctor_runner`` callable (no real subprocess spawned), and
``config_drift.check_drift`` is monkeypatched directly. HERMES_HOME is
isolated per test -- either via the explicit ``hermes_home`` kwarg
(``run_nightly`` tests) or via the repo's autouse HERMES_HOME-isolation
fixture in ``tests/conftest.py`` (the ``cmd_nightly``-level tests, which
call the real default code path).
"""

from argparse import Namespace
from datetime import datetime, timezone
from types import SimpleNamespace

import pytest

import hermes_cli.config_drift as config_drift
import hermes_cli.nightly as nightly


FIXED_NOW = datetime(2026, 7, 10, 3, 0, 0, tzinfo=timezone.utc)


def _healthy_doctor_runner():
    return SimpleNamespace(
        returncode=0,
        stdout="┌ Hermes Doctor ┐\n...\nAll checks passed! 🎉\n",
        stderr="",
    )


def _unhealthy_doctor_runner():
    return SimpleNamespace(
        returncode=0,  # hermes doctor always exits 0 on a normal run
        stdout="┌ Hermes Doctor ┐\nFound 2 issue(s) to address:\n  1. thing\n  2. other\n",
        stderr="",
    )


def _no_drift():
    return {"baseline_exists": True, "drifted": False, "diff": []}


def _drifted():
    return {"baseline_exists": True, "drifted": True, "diff": ["-model: sonnet\n", "+model: opus\n"]}


def _no_baseline():
    return {"baseline_exists": False, "drifted": False, "diff": []}


# ---------------------------------------------------------------------------
# run_doctor_check
# ---------------------------------------------------------------------------

def test_run_doctor_check_healthy_from_marker():
    result = nightly.run_doctor_check(_healthy_doctor_runner)
    assert result.healthy is True
    assert result.exit_code == 0


def test_run_doctor_check_unhealthy_from_issues_marker():
    result = nightly.run_doctor_check(_unhealthy_doctor_runner)
    assert result.healthy is False


def test_run_doctor_check_never_raises_on_runner_exception():
    def _boom():
        raise RuntimeError("subprocess exploded")

    result = nightly.run_doctor_check(_boom)
    assert result.healthy is False
    assert "subprocess exploded" in result.output


# ---------------------------------------------------------------------------
# run_nightly -- digest + latest.log + alerts
# ---------------------------------------------------------------------------

def test_run_nightly_healthy_no_drift_writes_digest_without_alert(tmp_path, monkeypatch):
    monkeypatch.setattr(config_drift, "check_drift", _no_drift)

    summary = nightly.run_nightly(
        hermes_home=tmp_path,
        doctor_runner=_healthy_doctor_runner,
        now=FIXED_NOW,
    )

    assert summary.healthy is True
    assert summary.drifted is False
    assert summary.alerts_path is None

    assert summary.digest_path == tmp_path / "state" / "nightly" / "2026-07-10.log"
    assert summary.digest_path.exists()
    assert summary.latest_path.exists()
    assert summary.digest_path.read_text() == summary.latest_path.read_text()

    text = summary.digest_path.read_text()
    assert "All checks passed!" in text
    assert "no drift" in text
    assert "model-eval: skipped" in text
    assert not (tmp_path / "state" / "nightly" / "ALERTS.log").exists()


def test_run_nightly_unhealthy_appends_alert_line(tmp_path, monkeypatch):
    monkeypatch.setattr(config_drift, "check_drift", _no_drift)

    summary = nightly.run_nightly(
        hermes_home=tmp_path,
        doctor_runner=_unhealthy_doctor_runner,
        now=FIXED_NOW,
    )

    assert summary.healthy is False
    assert summary.alerts_path is not None
    alerts_text = summary.alerts_path.read_text()
    assert "hermes doctor reported issues" in alerts_text
    assert "2026-07-10" in alerts_text


def test_run_nightly_drifted_appends_alert_line(tmp_path, monkeypatch):
    monkeypatch.setattr(config_drift, "check_drift", _drifted)

    summary = nightly.run_nightly(
        hermes_home=tmp_path,
        doctor_runner=_healthy_doctor_runner,
        now=FIXED_NOW,
    )

    assert summary.healthy is True
    assert summary.drifted is True
    assert summary.alerts_path is not None
    alerts_text = summary.alerts_path.read_text()
    assert "config-drift detected changes" in alerts_text
    assert "hermes doctor" not in alerts_text  # only the drift reason listed

    digest_text = summary.digest_path.read_text()
    assert "model: opus" in digest_text


def test_run_nightly_no_baseline_is_not_treated_as_drift(tmp_path, monkeypatch):
    monkeypatch.setattr(config_drift, "check_drift", _no_baseline)

    summary = nightly.run_nightly(
        hermes_home=tmp_path,
        doctor_runner=_healthy_doctor_runner,
        now=FIXED_NOW,
    )

    assert summary.drifted is False
    assert summary.alerts_path is None
    assert "no baseline" in summary.digest_path.read_text()


def test_run_nightly_appends_multiple_reasons_when_both_unhealthy_and_drifted(tmp_path, monkeypatch):
    monkeypatch.setattr(config_drift, "check_drift", _drifted)

    summary = nightly.run_nightly(
        hermes_home=tmp_path,
        doctor_runner=_unhealthy_doctor_runner,
        now=FIXED_NOW,
    )

    alerts_text = summary.alerts_path.read_text()
    assert "hermes doctor reported issues" in alerts_text
    assert "config-drift detected changes" in alerts_text


def test_run_nightly_with_eval_includes_model_eval_section(tmp_path, monkeypatch):
    monkeypatch.setattr(config_drift, "check_drift", _no_drift)

    summary = nightly.run_nightly(
        hermes_home=tmp_path,
        doctor_runner=_healthy_doctor_runner,
        model_eval_runner=lambda: "1   0.10     PASS     OK\nSummary: pass=1/3 manual=0/2 fail=0",
        with_eval=True,
        now=FIXED_NOW,
    )

    text = summary.digest_path.read_text()
    assert "--- model-eval ---" in text
    assert "Summary: pass=1/3" in text


def test_run_nightly_model_eval_failure_does_not_crash(tmp_path, monkeypatch):
    monkeypatch.setattr(config_drift, "check_drift", _no_drift)

    def _boom():
        raise RuntimeError("no local model server")

    summary = nightly.run_nightly(
        hermes_home=tmp_path,
        doctor_runner=_healthy_doctor_runner,
        model_eval_runner=_boom,
        with_eval=True,
        now=FIXED_NOW,
    )

    assert summary.digest_path.exists()
    assert "model-eval failed" in summary.digest_path.read_text()


def test_run_nightly_second_run_same_day_overwrites_digest(tmp_path, monkeypatch):
    monkeypatch.setattr(config_drift, "check_drift", _no_drift)

    nightly.run_nightly(hermes_home=tmp_path, doctor_runner=_healthy_doctor_runner, now=FIXED_NOW)
    summary2 = nightly.run_nightly(
        hermes_home=tmp_path, doctor_runner=_unhealthy_doctor_runner, now=FIXED_NOW
    )

    # Same dated file, now reflecting the second (unhealthy) run.
    assert "Found 2 issue(s)" in summary2.digest_path.read_text()
    assert summary2.latest_path.read_text() == summary2.digest_path.read_text()


# ---------------------------------------------------------------------------
# cmd_nightly -- exit codes via the real default code path
# ---------------------------------------------------------------------------

def test_cmd_nightly_exits_zero_when_healthy_and_no_drift(monkeypatch, capsys):
    monkeypatch.setattr(nightly, "_default_doctor_runner", _healthy_doctor_runner)
    monkeypatch.setattr(config_drift, "check_drift", _no_drift)

    with pytest.raises(SystemExit) as exc_info:
        nightly.cmd_nightly(Namespace(with_eval=False))

    assert exc_info.value.code == 0
    out = capsys.readouterr().out
    assert "digest:" in out
    assert "latest:" in out
    assert "ALERT" not in out


def test_cmd_nightly_exits_nonzero_when_unhealthy(monkeypatch, capsys):
    monkeypatch.setattr(nightly, "_default_doctor_runner", _unhealthy_doctor_runner)
    monkeypatch.setattr(config_drift, "check_drift", _no_drift)

    with pytest.raises(SystemExit) as exc_info:
        nightly.cmd_nightly(Namespace(with_eval=False))

    assert exc_info.value.code == 2
    assert "ALERT appended" in capsys.readouterr().out


def test_cmd_nightly_never_raises_when_doctor_subprocess_itself_fails(monkeypatch, capsys):
    def _boom():
        raise OSError("hermes not found")

    monkeypatch.setattr(nightly, "_default_doctor_runner", _boom)
    monkeypatch.setattr(config_drift, "check_drift", _no_drift)

    with pytest.raises(SystemExit) as exc_info:
        nightly.cmd_nightly(Namespace(with_eval=False))

    assert exc_info.value.code == 2
