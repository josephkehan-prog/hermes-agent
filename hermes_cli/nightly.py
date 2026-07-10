"""``hermes nightly`` -- self-health digest for scheduled/cron runs.

Ports the intent of the workspace ``bin/hermes-nightly`` script into the
product: run ``hermes doctor`` (as a subprocess, so it exercises exactly
the same code path a human invocation would) plus
``config_drift.check_drift()`` (called directly, in-process), write a dated
digest under ``HERMES_HOME/state/nightly/YYYY-MM-DD.log``, refresh a
``latest.log`` copy, and append a one-line summary to
``HERMES_HOME/state/nightly/ALERTS.log`` when unhealthy or drifted.

Designed to never raise: this is meant to run unattended from cron, so
every external call (subprocess, file I/O, the optional model-eval probe)
is wrapped so a single bad probe degrades into a reported failure instead
of an unhandled traceback that kills the scheduler.
"""

from __future__ import annotations

import subprocess
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable, Optional

from hermes_cli import config_drift
from hermes_constants import get_hermes_home

DOCTOR_HEALTHY_MARKER = "All checks passed!"
DOCTOR_ISSUES_MARKER = "issue(s) to address"
DOCTOR_SUBPROCESS_TIMEOUT = 180

DoctorRunner = Callable[[], "subprocess.CompletedProcess"]
ModelEvalRunner = Callable[[], str]


def nightly_dir(hermes_home: Optional[Path] = None) -> Path:
    """Return ``HERMES_HOME/state/nightly`` (or under ``hermes_home`` if given)."""
    home = Path(hermes_home) if hermes_home is not None else get_hermes_home()
    return home / "state" / "nightly"


@dataclass
class DoctorRunResult:
    exit_code: int
    output: str
    healthy: bool


@dataclass
class NightlySummary:
    digest_path: Path
    latest_path: Path
    alerts_path: Optional[Path]
    healthy: bool
    drifted: bool


def _default_doctor_runner() -> subprocess.CompletedProcess:
    """Run ``hermes doctor`` in a subprocess via the current interpreter.

    Uses ``python -m hermes_cli.main doctor`` rather than relying on a
    ``hermes`` console script being on PATH, so this works the same in a
    dev checkout and an installed environment.
    """
    return subprocess.run(
        [sys.executable, "-m", "hermes_cli.main", "doctor"],
        capture_output=True,
        text=True,
        timeout=DOCTOR_SUBPROCESS_TIMEOUT,
    )


def run_doctor_check(doctor_runner: Optional[DoctorRunner] = None) -> DoctorRunResult:
    """Run ``hermes doctor`` and classify its output as healthy or not.

    ``hermes doctor`` always exits 0 on a normal run (its exit code is
    reserved for ``--ack`` failures), so health is determined by scanning
    its printed summary for the "All checks passed!" line rather than the
    process exit code. Any exception running the subprocess itself (missing
    interpreter, timeout, ...) is caught and reported as unhealthy rather
    than propagated -- nightly must never crash the scheduler.
    """
    runner = doctor_runner or _default_doctor_runner
    try:
        proc = runner()
        output = (proc.stdout or "") + (proc.stderr or "")
        healthy = DOCTOR_HEALTHY_MARKER in output and DOCTOR_ISSUES_MARKER not in output
        return DoctorRunResult(exit_code=proc.returncode, output=output, healthy=healthy)
    except Exception as e:
        return DoctorRunResult(
            exit_code=1,
            output=f"hermes doctor failed to run: {type(e).__name__}: {e}",
            healthy=False,
        )


def _default_model_eval_runner() -> str:
    """Run model-eval in-process against the default llama-server target."""
    from hermes_cli.model_eval import render_table, resolve_target, run_eval

    base_url, model_id = resolve_target()
    outcomes = run_eval(base_url=base_url, model_id=model_id)
    return render_table(outcomes, label=f"llama:{model_id}")


def build_digest_text(
    *,
    timestamp: str,
    doctor_result: DoctorRunResult,
    drift_result: config_drift.DriftResult,
    eval_output: Optional[str],
) -> str:
    lines = [f"=== Hermes Nightly Digest ({timestamp}) ===", ""]

    lines.append(f"--- hermes doctor (exit {doctor_result.exit_code}) ---")
    lines.append(doctor_result.output.rstrip("\n") or "(no output)")
    lines.append("")

    lines.append(
        f"--- config-drift (baseline_exists={drift_result['baseline_exists']}, "
        f"drifted={drift_result['drifted']}) ---"
    )
    if drift_result["drifted"]:
        lines.extend(line.rstrip("\n") for line in drift_result["diff"])
    elif drift_result["baseline_exists"]:
        lines.append("no drift")
    else:
        lines.append("no baseline")
    lines.append("")

    if eval_output is not None:
        lines.append("--- model-eval ---")
        lines.append(eval_output.rstrip("\n"))
    else:
        lines.append("--- model-eval: skipped (pass --with-eval to run) ---")
    lines.append("")

    lines.append("=== end digest ===")
    return "\n".join(lines) + "\n"


def run_nightly(
    *,
    with_eval: bool = False,
    hermes_home: Optional[Path] = None,
    doctor_runner: Optional[DoctorRunner] = None,
    model_eval_runner: Optional[ModelEvalRunner] = None,
    now: Optional[datetime] = None,
) -> NightlySummary:
    """Run the nightly checks and write the digest + alerts. Never raises."""
    home = Path(hermes_home) if hermes_home is not None else get_hermes_home()
    out_dir = nightly_dir(home)
    out_dir.mkdir(parents=True, exist_ok=True)

    ts = now or datetime.now(timezone.utc)
    date_stamp = ts.strftime("%Y-%m-%d")
    timestamp_str = ts.strftime("%Y-%m-%d %H:%M:%S %z")
    digest_path = out_dir / f"{date_stamp}.log"
    latest_path = out_dir / "latest.log"
    alerts_path = out_dir / "ALERTS.log"

    doctor_result = run_doctor_check(doctor_runner)

    try:
        drift_result = config_drift.check_drift()
    except Exception as e:
        drift_result = config_drift.DriftResult(
            baseline_exists=False,
            drifted=True,
            diff=[f"config-drift check failed: {type(e).__name__}: {e}"],
        )

    eval_output: Optional[str] = None
    if with_eval:
        try:
            runner = model_eval_runner or _default_model_eval_runner
            eval_output = runner()
        except Exception as e:
            eval_output = f"model-eval failed: {type(e).__name__}: {e}"

    digest_text = build_digest_text(
        timestamp=timestamp_str,
        doctor_result=doctor_result,
        drift_result=drift_result,
        eval_output=eval_output,
    )

    try:
        digest_path.write_text(digest_text, encoding="utf-8")
        latest_path.write_text(digest_text, encoding="utf-8")
    except Exception as e:
        # Digest write failed (disk full, permissions, ...) -- still fall
        # through to the alert logic below rather than raising, since a
        # nightly job that can't write its own log should still surface
        # an alert if possible.
        try:
            with alerts_path.open("a", encoding="utf-8") as f:
                f.write(f"{timestamp_str} failed to write nightly digest: {type(e).__name__}: {e}\n")
        except Exception:
            pass

    unhealthy = not doctor_result.healthy
    drifted = bool(drift_result.get("drifted"))

    alert_written_path: Optional[Path] = None
    if unhealthy or drifted:
        reasons = []
        if unhealthy:
            reasons.append(f"hermes doctor reported issues (exit {doctor_result.exit_code})")
        if drifted:
            reasons.append("config-drift detected changes")
        try:
            with alerts_path.open("a", encoding="utf-8") as f:
                f.write(f"{timestamp_str} {'; '.join(reasons)}\n")
            alert_written_path = alerts_path
        except Exception:
            pass

    return NightlySummary(
        digest_path=digest_path,
        latest_path=latest_path,
        alerts_path=alert_written_path,
        healthy=not unhealthy,
        drifted=drifted,
    )


def cmd_nightly(args) -> None:
    """``hermes nightly`` entry point."""
    with_eval = getattr(args, "with_eval", False)
    summary = run_nightly(with_eval=with_eval)

    print(f"digest: {summary.digest_path}")
    print(f"latest: {summary.latest_path}")
    if summary.alerts_path:
        print(f"ALERT appended to {summary.alerts_path}")

    sys.exit(0 if (summary.healthy and not summary.drifted) else 2)
