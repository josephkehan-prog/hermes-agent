"""Tests for tools/health_report_tool.py — devops health snapshot aggregator.

No real network: every urllib.request.urlopen call is monkeypatched. System
metrics are exercised both via the system_resource_tool import path and via
the fallback path (simulated by forcing an ImportError)."""

import urllib.error
from unittest.mock import MagicMock

from tools import health_report_tool


def _mock_response(status: int = 200) -> MagicMock:
    """Build a urlopen()-context-manager mock with the given HTTP status."""
    mock_response = MagicMock()
    mock_response.status = status
    mock_response.read.return_value = b'{"models": []}'
    mock_response.__enter__ = lambda s: s
    mock_response.__exit__ = MagicMock(return_value=False)
    return mock_response


class TestCheckModelEndpoint:
    def test_up_on_200(self, monkeypatch):
        monkeypatch.setattr(
            health_report_tool.urllib.request, "urlopen", lambda *a, **kw: _mock_response(200)
        )

        result = health_report_tool._check_model_endpoint("agent1", "http://localhost:11434/api/tags")

        assert result == {"up": True, "detail": "http 200"}

    def test_down_on_connection_error(self, monkeypatch):
        def _raise(*a, **kw):
            raise urllib.error.URLError("connection refused")

        monkeypatch.setattr(health_report_tool.urllib.request, "urlopen", _raise)

        result = health_report_tool._check_model_endpoint("ornith", "http://localhost:1235/v1/models")

        assert result["up"] is False
        assert "connection refused" in result["detail"]

    def test_down_on_http_error(self, monkeypatch):
        def _raise(*a, **kw):
            raise urllib.error.HTTPError("http://x", 500, "boom", {}, None)

        monkeypatch.setattr(health_report_tool.urllib.request, "urlopen", _raise)

        result = health_report_tool._check_model_endpoint("agent1", "http://localhost:11434/api/tags")

        assert result == {"up": False, "detail": "http 500"}


class TestHealthReportOverall:
    """overall.healthy logic: all up -> healthy, any down -> alert."""

    def test_all_models_up_and_no_disk_alert_is_healthy(self, monkeypatch):
        monkeypatch.setattr(
            health_report_tool, "_system_snapshot",
            lambda path: {"ok": True, "disk": {"percent": 10}, "load": {"1m": 0.1}},
        )
        monkeypatch.setattr(
            health_report_tool, "_local_models_snapshot",
            lambda: {
                "agent1": {"up": True, "detail": "http 200"},
                "ornith": {"up": True, "detail": "http 200"},
            },
        )

        result = health_report_tool.health_report(include_models=True)

        assert result["ok"] is True
        assert result["overall"]["healthy"] is True
        assert result["overall"]["alerts"] == []

    def test_one_model_down_produces_alert_and_unhealthy(self, monkeypatch):
        monkeypatch.setattr(
            health_report_tool, "_system_snapshot",
            lambda path: {"ok": True, "disk": {"percent": 10}, "load": {"1m": 0.1}},
        )
        monkeypatch.setattr(
            health_report_tool, "_local_models_snapshot",
            lambda: {
                "agent1": {"up": True, "detail": "http 200"},
                "ornith": {"up": False, "detail": "connection refused"},
            },
        )

        result = health_report_tool.health_report(include_models=True)

        assert result["overall"]["healthy"] is False
        assert len(result["overall"]["alerts"]) == 1
        assert "ornith" in result["overall"]["alerts"][0]

    def test_disk_alert_makes_report_unhealthy(self, monkeypatch):
        monkeypatch.setattr(
            health_report_tool, "_system_snapshot",
            lambda path: {"ok": True, "disk": {"percent": 95}, "load": {"1m": 0.1}},
        )
        monkeypatch.setattr(health_report_tool, "_local_models_snapshot", lambda: {})

        result = health_report_tool.health_report(include_models=False)

        assert result["overall"]["healthy"] is False
        assert "disk usage 95%" in result["overall"]["alerts"][0]


class TestIncludeModelsFalse:
    def test_skips_model_checks_entirely(self, monkeypatch):
        called = []
        monkeypatch.setattr(
            health_report_tool, "_local_models_snapshot",
            lambda: called.append(True) or {},
        )
        monkeypatch.setattr(
            health_report_tool, "_system_snapshot",
            lambda path: {"ok": True, "disk": {"percent": 5}, "load": {"1m": 0.0}},
        )

        result = health_report_tool.health_report(include_models=False)

        assert result["local_models"] == {}
        assert called == []


class TestSystemSnapshotFallback:
    """Graceful degradation when tools.system_resource_tool isn't importable yet."""

    def test_falls_back_when_system_resource_tool_import_fails(self, monkeypatch):
        import builtins

        real_import = builtins.__import__

        def _blocked_import(name, *args, **kwargs):
            if name == "tools.system_resource_tool":
                raise ImportError("simulated: not built yet")
            return real_import(name, *args, **kwargs)

        monkeypatch.setattr(builtins, "__import__", _blocked_import)

        result = health_report_tool._system_snapshot("/")

        assert result["ok"] is True
        assert "note" in result
        assert "fallback" in result["note"]
        assert "disk" in result
        assert "load" in result

    def test_uses_system_resource_tool_when_importable(self, monkeypatch):
        fake_module = MagicMock()
        fake_module.resource_snapshot.return_value = {"ok": True, "disk": {"percent": 42}, "load": {"1m": 1.0}}

        import sys

        monkeypatch.setitem(sys.modules, "tools.system_resource_tool", fake_module)

        result = health_report_tool._system_snapshot("/")

        assert result == {"ok": True, "disk": {"percent": 42}, "load": {"1m": 1.0}}
        fake_module.resource_snapshot.assert_called_once_with(path="/")


class TestFullReportShape:
    def test_full_report_has_expected_top_level_keys(self, monkeypatch):
        monkeypatch.setattr(
            health_report_tool.urllib.request, "urlopen", lambda *a, **kw: _mock_response(200)
        )

        result = health_report_tool.health_report(include_models=True)

        assert set(result.keys()) == {"ok", "timestamp_note", "system", "local_models", "overall"}
        assert set(result["local_models"].keys()) == {"agent1", "ornith"}
