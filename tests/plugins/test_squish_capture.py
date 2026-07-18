"""Tests for the squish-capture plugin.

Covers the bundled plugin at ``plugins/squish-capture/``:

  * ``register`` wires the three hooks + the slash command against a fake ctx.
  * ``on_session_end`` calls squish exactly once when the per-session counter
    is at/over the activity bar, and zero times when it is under.
  * The subprocess call is always mocked — no real squish write happens.
"""

import importlib.util
import sys
import types
from pathlib import Path

import pytest


def _load_plugin_init():
    """Import the plugin's __init__.py under the PluginManager module name."""
    repo_root = Path(__file__).resolve().parents[2]
    plugin_dir = repo_root / "plugins" / "squish-capture"
    spec = importlib.util.spec_from_file_location(
        "hermes_plugins.squish_capture",
        plugin_dir / "__init__.py",
        submodule_search_locations=[str(plugin_dir)],
    )
    if "hermes_plugins" not in sys.modules:
        ns = types.ModuleType("hermes_plugins")
        ns.__path__ = []
        sys.modules["hermes_plugins"] = ns
    mod = importlib.util.module_from_spec(spec)
    mod.__package__ = "hermes_plugins.squish_capture"
    mod.__path__ = [str(plugin_dir)]
    sys.modules["hermes_plugins.squish_capture"] = mod
    spec.loader.exec_module(mod)
    return mod


class _FakeCtx:
    """Collects register_hook / register_command calls."""

    def __init__(self):
        self.hooks = {}
        self.commands = {}

    def register_hook(self, name, handler):
        self.hooks[name] = handler

    def register_command(self, name, handler, description=""):
        self.commands[name] = {"handler": handler, "description": description}


@pytest.fixture
def plugin():
    mod = _load_plugin_init()
    # Reset the module-level counter between tests for isolation.
    mod._counters.clear()
    return mod


# ---------------------------------------------------------------------------
# Registration
# ---------------------------------------------------------------------------

class TestRegistration:
    def test_registers_hooks_and_command(self, plugin):
        ctx = _FakeCtx()
        plugin.register(ctx)

        assert "on_session_start" in ctx.hooks
        assert "post_tool_call" in ctx.hooks
        assert "on_session_end" in ctx.hooks
        assert "squish-capture" in ctx.commands
        assert callable(ctx.commands["squish-capture"]["handler"])


# ---------------------------------------------------------------------------
# on_session_end save behaviour (subprocess mocked)
# ---------------------------------------------------------------------------

class TestSessionEndSave:
    def _install_spy(self, plugin, monkeypatch):
        """Replace subprocess.run with a spy returning a success CompletedProcess."""
        import subprocess as _sp

        calls = []

        def _fake_run(cmd, **kwargs):
            calls.append(cmd)
            return _sp.CompletedProcess(cmd, 0, stdout="ok", stderr="")

        monkeypatch.setattr(plugin.subprocess, "run", _fake_run)
        return calls

    def test_saves_once_when_over_threshold(self, plugin, monkeypatch):
        calls = self._install_spy(plugin, monkeypatch)

        # Drive the counter well over the min-activity bar.
        for _ in range(plugin.HEAVY_ACTIVITY_THRESHOLD + 1):
            plugin._on_post_tool_call(tool_name="terminal", session_id="s1")

        assert plugin._read_count("s1") == plugin.HEAVY_ACTIVITY_THRESHOLD + 1

        plugin._on_session_end(session_id="s1", completed=True, interrupted=False)

        assert len(calls) == 1, "squish remember must be called exactly once"
        # The command shape: [node, bin, "remember", <text>]
        cmd = calls[0]
        assert cmd[-2] == "remember"
        assert "s1" in cmd[-1]

    def test_no_save_when_under_threshold(self, plugin, monkeypatch):
        calls = self._install_spy(plugin, monkeypatch)

        # Only 2 tool calls — under MIN_ACTIVITY (3).
        assert plugin.MIN_ACTIVITY == 3
        plugin._on_post_tool_call(tool_name="terminal", session_id="s2")
        plugin._on_post_tool_call(tool_name="terminal", session_id="s2")

        plugin._on_session_end(session_id="s2", completed=True, interrupted=False)

        assert len(calls) == 0, "squish must not be called for a light session"

    def test_session_end_never_raises_on_subprocess_error(self, plugin, monkeypatch):
        def _boom(cmd, **kwargs):
            raise OSError("node missing")

        monkeypatch.setattr(plugin.subprocess, "run", _boom)

        for _ in range(plugin.MIN_ACTIVITY):
            plugin._on_post_tool_call(tool_name="terminal", session_id="s3")

        # Must swallow the error, not propagate into the host loop.
        plugin._on_session_end(session_id="s3", completed=True, interrupted=False)


# ---------------------------------------------------------------------------
# Slash command
# ---------------------------------------------------------------------------

class TestSlashCommand:
    def test_help(self, plugin):
        out = plugin._handle_slash("help")
        assert "squish-capture" in out
        assert "status" in out

    def test_status_reports_counter(self, plugin):
        plugin._on_post_tool_call(tool_name="terminal", session_id="s1")
        out = plugin._handle_slash("status")
        assert "total tool calls" in out
        assert "reachable" in out

    def test_unknown_subcommand(self, plugin):
        out = plugin._handle_slash("bogus")
        assert "Unknown subcommand" in out
