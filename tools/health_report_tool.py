#!/usr/bin/env python3
"""Devops health aggregator: one snapshot for self-healing decisions.

Composes ``health_report()`` from three sources:

* **system** — via ``tools.system_resource_tool.resource_snapshot`` when that
  module is importable (built by a sibling worker this same batch); falls
  back to a minimal ``shutil.disk_usage`` + ``os.getloadavg`` snapshot if it
  isn't available yet, so this tool never hard-fails on import order.
* **local_models** — reachability of two fixed local-model endpoints:
  Ollama (``http://localhost:11434/api/tags``) and an OpenAI-compatible
  server nicknamed "ornith" (``http://localhost:1235/v1/models``). These are
  HARDCODED localhost endpoints, not caller-supplied URLs, so this is the
  fixed-endpoint case — no ``_net_guard.reject_private_target`` needed (see
  ``uptime_check_tool.py`` for the caller-supplied-URL/SSRF-guarded case).
  Each check uses a short timeout and reads a capped amount of the body.
* **overall** — pure logic over the two sections above: healthy iff every
  local model is up (when checked) and no system alert fired.

Pure local aside from the two fixed-endpoint reads above. No shell-out, no
destructive actions, deterministic given its inputs.
"""

import json
import os
import shutil
import time
import urllib.error
import urllib.request
from typing import Any, Dict, List, Optional

from tools.registry import registry

_DEFAULT_DISK_PATH = "/"
_MODEL_TIMEOUT_S = 3
_MAX_MODEL_RESPONSE_BYTES = 4096
_DISK_PERCENT_ALERT = 90
_PERCENT_ROUND_NDIGITS = 1
_USER_AGENT = "Hermes-Agent (https://github.com/NousResearch/hermes-agent)"

_LOCAL_MODEL_ENDPOINTS = {
    "agent1": "http://localhost:11434/api/tags",
    "ornith": "http://localhost:1235/v1/models",
}


def _fallback_system_snapshot(path: str) -> Dict[str, Any]:
    """Minimal system snapshot used only when system_resource_tool isn't importable yet."""
    try:
        usage = shutil.disk_usage(path)
        percent = round((usage.used / usage.total) * 100, _PERCENT_ROUND_NDIGITS) if usage.total else None
        disk = {"path": path, "total": usage.total, "used": usage.used, "free": usage.free, "percent": percent}
    except OSError as exc:
        disk = {"path": path, "total": None, "used": None, "free": None, "percent": None, "note": str(exc)}

    try:
        one, five, fifteen = os.getloadavg()
        load = {"1m": one, "5m": five, "15m": fifteen}
    except (AttributeError, OSError) as exc:
        load = {"1m": None, "5m": None, "15m": None, "note": f"unavailable: {exc}"}

    return {"ok": True, "disk": disk, "load": load, "cpu_count": os.cpu_count(), "note": "system_resource_tool unavailable, using fallback"}


def _system_snapshot(path: str) -> Dict[str, Any]:
    """Return a system resource snapshot, preferring system_resource_tool when importable."""
    try:
        from tools.system_resource_tool import resource_snapshot
    except ImportError:
        return _fallback_system_snapshot(path)

    return resource_snapshot(path=path)


def _check_model_endpoint(name: str, url: str) -> Dict[str, Any]:
    """Check one fixed local-model endpoint's reachability. Never raises."""
    request = urllib.request.Request(url, headers={"User-Agent": _USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=_MODEL_TIMEOUT_S) as response:
            response.read(_MAX_MODEL_RESPONSE_BYTES)
            status = response.status
    except urllib.error.HTTPError as exc:
        return {"up": False, "detail": f"http {exc.code}"}
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        return {"up": False, "detail": str(exc)}

    return {"up": status == 200, "detail": f"http {status}"}


def _local_models_snapshot() -> Dict[str, Dict[str, Any]]:
    """Check every fixed local-model endpoint, isolating failures per-endpoint."""
    return {name: _check_model_endpoint(name, url) for name, url in _LOCAL_MODEL_ENDPOINTS.items()}


def _system_alerts(system: Dict[str, Any]) -> List[str]:
    """Return alert strings for system metrics that breach fixed thresholds."""
    alerts = []
    disk_percent = (system.get("disk") or {}).get("percent")
    if disk_percent is not None and disk_percent > _DISK_PERCENT_ALERT:
        alerts.append(f"disk usage {disk_percent}% exceeds {_DISK_PERCENT_ALERT}%")
    return alerts


def _model_alerts(local_models: Dict[str, Dict[str, Any]]) -> List[str]:
    """Return alert strings for any local model endpoint that's down."""
    return [f"{name} is down: {info.get('detail')}" for name, info in local_models.items() if not info.get("up")]


def health_report(include_models: bool = True, path: str = _DEFAULT_DISK_PATH) -> Dict[str, Any]:
    """Compose a single health snapshot: system resources, local models, overall verdict.

    ``include_models`` skips the local-model reachability checks (and their
    network reads) when False. Deterministic given the underlying system
    state and endpoint responses; the only I/O is the two fixed-endpoint
    reads (gated by ``include_models``) and read-only local system calls.
    """
    system = _system_snapshot(path)
    local_models = _local_models_snapshot() if include_models else {}

    alerts = _system_alerts(system) + _model_alerts(local_models)

    return {
        "ok": True,
        "timestamp_note": f"unix epoch seconds at call time: {time.time()}",
        "system": system,
        "local_models": local_models,
        "overall": {"healthy": len(alerts) == 0, "alerts": alerts},
    }


registry.register(
    name="health_report",
    toolset="monitoring",
    schema={
        "name": "health_report",
        "description": (
            "Compose a single devops health snapshot for self-healing decisions: "
            "system resources (disk/load/cpu/memory), local-model endpoint "
            "reachability (Ollama on :11434, ornith on :1235 — fixed localhost "
            "endpoints, short timeout, capped read), and an overall healthy/alerts "
            "verdict. Pure local aside from those two fixed-endpoint checks."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "include_models": {
                    "type": "boolean",
                    "description": "Whether to check local-model endpoint reachability. Defaults to true.",
                },
                "path": {
                    "type": "string",
                    "description": f"Filesystem path to report disk usage for. Defaults to {_DEFAULT_DISK_PATH!r}.",
                },
            },
            "required": [],
        },
    },
    handler=lambda args, **kw: json.dumps(
        health_report(
            include_models=args.get("include_models", True),
            path=args.get("path", _DEFAULT_DISK_PATH),
        ),
        ensure_ascii=False,
    ),
    emoji="🩺",
)
