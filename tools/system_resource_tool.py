#!/usr/bin/env python3
"""Local system resource snapshots for devops / self-healing health checks.

Pure local, read-only, no network and no shell-out. Disk usage and CPU count
come from the stdlib (``shutil.disk_usage``, ``os.cpu_count``); load average
uses ``os.getloadavg`` (POSIX only — guarded, ``None`` on Windows); memory and
uptime use ``psutil`` (already a pinned dependency — see pyproject.toml —
for exactly this kind of cross-platform process/host introspection). Every
metric is wrapped individually so one platform-specific gap (e.g. no
``getloadavg`` on Windows) never crashes the whole snapshot — it degrades to
``None`` plus a ``note`` explaining why.
"""

import json
import os
import shutil
from typing import Any, Dict, Optional

from tools.registry import registry

_DEFAULT_DISK_PATH = "/"
_PERCENT_ROUND_NDIGITS = 1


def _disk_metrics(path: str) -> Dict[str, Any]:
    """Return disk usage for path via shutil.disk_usage, or None fields + note."""
    try:
        usage = shutil.disk_usage(path)
    except OSError as exc:
        return {"path": path, "total": None, "used": None, "free": None, "percent": None, "note": str(exc)}

    percent = round((usage.used / usage.total) * 100, _PERCENT_ROUND_NDIGITS) if usage.total else None
    return {"path": path, "total": usage.total, "used": usage.used, "free": usage.free, "percent": percent}


def _load_metrics() -> Dict[str, Any]:
    """Return 1/5/15-minute load averages via os.getloadavg, or None + note.

    Not available on Windows (raises AttributeError since the attribute
    doesn't exist there) and can raise OSError on some POSIX systems.
    """
    try:
        one, five, fifteen = os.getloadavg()
        return {"1m": one, "5m": five, "15m": fifteen}
    except (AttributeError, OSError) as exc:
        return {"1m": None, "5m": None, "15m": None, "note": f"unavailable: {exc}"}


def _memory_metrics() -> Dict[str, Any]:
    """Return total/available/used/percent memory via psutil, or None + note."""
    empty = {"total": None, "available": None, "used": None, "percent": None}
    try:
        import psutil
    except ImportError as exc:
        return {**empty, "note": f"unavailable: {exc}"}

    try:
        vm = psutil.virtual_memory()
        return {"total": vm.total, "available": vm.available, "used": vm.used, "percent": vm.percent}
    except (psutil.Error, OSError) as exc:
        return {**empty, "note": f"unavailable: {exc}"}


def _uptime_s() -> Optional[float]:
    """Return host uptime in seconds via psutil.boot_time, or None if unavailable."""
    try:
        import psutil
    except ImportError:
        return None

    try:
        import time

        return time.time() - psutil.boot_time()
    except (psutil.Error, OSError):
        return None


def resource_snapshot(path: str = _DEFAULT_DISK_PATH) -> Dict[str, Any]:
    """Take a read-only local system resource snapshot: disk, load, cpu, memory, uptime.

    Every metric is best-effort — a platform gap degrades that field to None
    (with a "note" explaining why) instead of raising. ``ok`` is always True:
    this function itself never fails, it just reports what it could gather.
    """
    return {
        "ok": True,
        "disk": _disk_metrics(path),
        "load": _load_metrics(),
        "cpu_count": os.cpu_count(),
        "memory": _memory_metrics(),
        "uptime_s": _uptime_s(),
    }


def disk_usage(path: str = _DEFAULT_DISK_PATH) -> Dict[str, Any]:
    """Return disk usage for path: {ok, total, used, free, percent}."""
    if not os.path.exists(path):
        return {"ok": False, "error": f"no such path: {path}"}

    try:
        usage = shutil.disk_usage(path)
    except OSError as exc:
        return {"ok": False, "error": str(exc)}

    percent = round((usage.used / usage.total) * 100, _PERCENT_ROUND_NDIGITS) if usage.total else None
    return {"ok": True, "total": usage.total, "used": usage.used, "free": usage.free, "percent": percent}


def check_thresholds(
    snapshot: Dict[str, Any],
    disk_percent_max: float = 90,
    load1_max: Optional[float] = None,
) -> Dict[str, Any]:
    """Check a resource_snapshot() dict against thresholds; pure logic, no I/O.

    Returns {ok: True, alerts: [...]} — alerts is empty when nothing breaches.
    Metrics that are None (unavailable on this platform) are skipped rather
    than treated as breaches.
    """
    alerts = []

    disk_percent = (snapshot.get("disk") or {}).get("percent")
    if disk_percent is not None and disk_percent > disk_percent_max:
        alerts.append({
            "metric": "disk_percent",
            "value": disk_percent,
            "threshold": disk_percent_max,
            "message": f"disk usage {disk_percent}% exceeds max {disk_percent_max}%",
        })

    load1 = (snapshot.get("load") or {}).get("1m")
    if load1_max is not None and load1 is not None and load1 > load1_max:
        alerts.append({
            "metric": "load1",
            "value": load1,
            "threshold": load1_max,
            "message": f"1m load {load1} exceeds max {load1_max}",
        })

    return {"ok": True, "alerts": alerts}


registry.register(
    name="resource_snapshot",
    toolset="monitoring",
    schema={
        "name": "resource_snapshot",
        "description": (
            "Take a read-only local system resource snapshot: disk usage, load "
            "average, CPU count, memory, and uptime. No network, no shell-out. "
            "Every metric degrades to null with a note instead of failing when "
            "unavailable on the current platform (e.g. load average on Windows). "
            "Use for devops/self-healing health checks."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": f"Filesystem path to report disk usage for. Defaults to {_DEFAULT_DISK_PATH!r}.",
                },
            },
            "required": [],
        },
    },
    handler=lambda args, **kw: json.dumps(
        resource_snapshot(path=args.get("path", _DEFAULT_DISK_PATH)),
        ensure_ascii=False,
    ),
    emoji="🩺",
)

registry.register(
    name="disk_usage",
    toolset="monitoring",
    schema={
        "name": "disk_usage",
        "description": "Return disk usage (total/used/free/percent bytes) for a filesystem path.",
        "parameters": {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": f"Filesystem path to check. Defaults to {_DEFAULT_DISK_PATH!r}.",
                },
            },
            "required": [],
        },
    },
    handler=lambda args, **kw: json.dumps(
        disk_usage(path=args.get("path", _DEFAULT_DISK_PATH)),
        ensure_ascii=False,
    ),
    emoji="🩺",
)

registry.register(
    name="check_thresholds",
    toolset="monitoring",
    schema={
        "name": "check_thresholds",
        "description": (
            "Check a resource_snapshot() result against disk/load thresholds and "
            "return which ones breached. Pure logic, no I/O — pair with "
            "resource_snapshot for self-healing health checks."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "snapshot": {
                    "type": "object",
                    "description": "A resource_snapshot() result dict.",
                },
                "disk_percent_max": {
                    "type": "number",
                    "description": "Max allowed disk usage percent before alerting. Defaults to 90.",
                },
                "load1_max": {
                    "type": "number",
                    "description": "Max allowed 1-minute load average before alerting. Unset by default (no check).",
                },
            },
            "required": ["snapshot"],
        },
    },
    handler=lambda args, **kw: json.dumps(
        check_thresholds(
            snapshot=args.get("snapshot", {}),
            disk_percent_max=args.get("disk_percent_max", 90),
            load1_max=args.get("load1_max"),
        ),
        ensure_ascii=False,
    ),
    emoji="🩺",
)
