"""Tests for tools/profiler_tool.py — process/script profiling."""

import textwrap

from tools import profiler_tool


class TestProfileScript:
    """profile_script wraps the stdlib cProfile/pstats profiler — no external
    binary required, so this path is always exercisable."""

    def test_profile_script_on_tiny_script(self, tmp_path):
        script = tmp_path / "tiny.py"
        script.write_text(textwrap.dedent(
            """
            def work():
                return sum(range(10000))

            work()
            """
        ))

        result = profiler_tool.profile_script(str(script))

        assert result["ok"] is True
        assert result["tool_used"] == "cProfile"
        assert "cumulative" in result["output"]
        assert "work" in result["output"]

    def test_profile_script_missing_path_is_an_error(self):
        result = profiler_tool.profile_script("/no/such/script.py")

        assert result["ok"] is False
        assert result["tool_used"] == "cProfile"
        assert "no such file" in result["error"]


class TestProfileRunning:
    """profile_running wraps py-spy; must degrade gracefully when it's absent."""

    def test_missing_py_spy_binary_returns_install_hint(self, monkeypatch):
        monkeypatch.setattr(profiler_tool.shutil, "which", lambda name: None)

        result = profiler_tool.profile_running(pid=1234, duration_s=1)

        assert result["ok"] is False
        assert result["tool_used"] == "py-spy"
        assert result["error"] == "py-spy not installed: pip install py-spy"

    def test_invalid_pid_is_rejected_before_touching_py_spy(self, monkeypatch):
        monkeypatch.setattr(profiler_tool.shutil, "which", lambda name: "/usr/local/bin/py-spy")

        result = profiler_tool.profile_running(pid="not-a-pid", duration_s=1)

        assert result["ok"] is False
        assert "invalid pid" in result["error"]
