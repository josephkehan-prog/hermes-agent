#!/usr/bin/env bash
# Driver for the Hermes Agent CLI/library. Headless-safe: no TTY, no network,
# isolated HERMES_HOME. Exercises the three layers a PR here usually touches:
#   1. CLI surface   — `hermes --version`, `hermes doctor`
#   2. direct calls  — import a tool function and call it (most PRs)
#   3. registry path — how the agent actually dispatches a tool
# Run from the repo root: .claude/skills/run-hermes-agent/smoke.sh
set -u
cd "$(dirname "$0")/../../.." || exit 1

# venv probe order matches scripts/run_tests.sh / the runner: .venv, venv, live.
for v in .venv venv "$HOME/.hermes/hermes-agent/venv"; do
  if [ -f "$v/bin/activate" ]; then . "$v/bin/activate"; break; fi
done

# Isolate from the real profile so doctor/config never touch ~/.hermes.
export HERMES_HOME="$(mktemp -d)"
fail=0
step() { printf '\n=== %s ===\n' "$*"; }

step "python + hermes version"
python --version || fail=1
hermes --version || fail=1

step "hermes doctor (health snapshot; exits 0 even with findings)"
hermes doctor >/dev/null 2>&1 && echo "doctor ran (exit 0)" || echo "doctor exit non-zero"

step "direct tool invocation (the path most PRs touch)"
python - <<'PY' || fail=1
import json
from tools.json_diff_tool import json_diff
r = json_diff({"a": 1, "b": {"ts": 1}}, {"a": 2, "b": {"ts": 9}}, ignore_paths=["b.ts"])
assert r["changed"] and r["modified"] == {"a": {"old": 1, "new": 2}}, r
print("json_diff OK:", r["summary"])

from tools.uptime_check_tool import _status_matches
assert _status_matches(204, "2xx") and not _status_matches(301, "2xx")
print("uptime status-class OK")

from tools.notify_tool import _validate_click
assert _validate_click("https://x.com/a")[0] == "https://x.com/a"
assert _validate_click("https://x\r\ny")[1] is not None  # CRLF rejected
print("notify click validation OK")
PY

step "registry dispatch (how the agent invokes a tool)"
python - <<'PY' || fail=1
import json, tools.json_diff_tool  # noqa: F401 — registers 'json_diff'
from tools.registry import registry
entry = registry.get_entry("json_diff")
out = json.loads(entry.handler({"old_json": json.dumps({"n": 1}),
                                "new_json": json.dumps({"n": 2})}))
assert out["ok"] and out["changed"], out
print("registry json_diff OK:", out["summary"])
PY

step "test wrapper (CI-parity, one fast file)"
scripts/run_tests.sh tests/tools/test_json_diff_tool.py 2>&1 | grep -E "=== Summary" || fail=1

step "verdict"
[ "$fail" -eq 0 ] && echo "SMOKE PASS" || echo "SMOKE FAIL"
exit "$fail"
