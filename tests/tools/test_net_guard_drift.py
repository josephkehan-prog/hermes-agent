"""Drift guard for the SSRF private-target check.

tools/_net_guard.py's reject_private_target is intentionally duplicated —
not imported — in two standalone skill scripts that can't depend on tools/:
skills/research/network-recon/scripts/recon.py's _reject_private_target and
skills/research/watch-notify/scripts/watch.py's reject_private_target.

That duplication means a future security fix (like the ambiguous-numeric-
host pre-filter) can land in one copy and silently miss the other two. This
test feeds all three implementations the same battery of URLs and asserts
they agree on what to reject and what to allow, so drift between the copies
fails CI instead of shipping an inconsistent guard.
"""

from __future__ import annotations

import importlib.util
import inspect
from pathlib import Path
from unittest.mock import patch

import pytest

from tools import _net_guard

REPO_ROOT = Path(__file__).resolve().parents[2]
RECON_SCRIPT = REPO_ROOT / "skills" / "research" / "network-recon" / "scripts" / "recon.py"
WATCH_SCRIPT = REPO_ROOT / "skills" / "research" / "watch-notify" / "scripts" / "watch.py"


def _load_script_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


recon = _load_script_module(RECON_SCRIPT, "net_guard_drift_recon_module")
watch = _load_script_module(WATCH_SCRIPT, "net_guard_drift_watch_module")

# (label, callable, exception types that mean "rejected"). The library-style
# _net_guard.py raises NetGuardError; the two CLI scripts call sys.exit(2)
# via their own _fail() helper, which raises SystemExit.
IMPLEMENTATIONS = [
    ("tools/_net_guard.py", _net_guard.reject_private_target, (_net_guard.NetGuardError,)),
    ("network-recon/recon.py", recon._reject_private_target, (SystemExit,)),
    ("watch-notify/watch.py", watch.reject_private_target, (SystemExit,)),
]

# Ambiguous numeric forms (the octal/decimal/hex SSRF filter-bypass class)
# plus the private/reserved/loopback/metadata literals the guard has always
# covered.
REJECT_URLS = [
    "http://0177.0.0.1/",  # leading-zero octet, glibc/platform-dependent octal interpretation
    "http://2130706433/",  # bare decimal integer form of 127.0.0.1
    "http://0x7f000001/",  # hex literal form of 127.0.0.1
    "http://127.1/",  # short/partial dotted form (inet_aton-style shorthand)
    "http://127.0.0.1/",  # canonical loopback literal
    "http://169.254.169.254/",  # cloud metadata literal
    "http://[::1]/",  # IPv6 loopback literal
]


def _invoke(func, url):
    """Call func(url); returns True if it rejected the url, False if allowed."""
    try:
        func(url)
    except (_net_guard.NetGuardError, SystemExit):
        return True
    return False


class TestThreeCopiesAgreeOnRejection:
    def test_all_three_are_independent_function_objects(self):
        """Sanity check that we're really exercising 3 separate copies, not
        one shared import — inspect.getsource must succeed for each and the
        function objects must be distinct."""
        sources = [inspect.getsource(func) for _label, func, _exc in IMPLEMENTATIONS]
        assert len(sources) == 3
        assert len({id(func) for _label, func, _exc in IMPLEMENTATIONS}) == 3

    @pytest.mark.parametrize("url", REJECT_URLS)
    def test_all_implementations_reject(self, url):
        results = {label: _invoke(func, url) for label, func, _exc in IMPLEMENTATIONS}
        assert all(results.values()), f"{url!r}: not all copies rejected -> {results}"

    def test_all_implementations_allow_public_host(self):
        with patch("socket.gethostbyname", return_value="93.184.216.34"):
            results = {
                label: _invoke(func, "http://example.com/") for label, func, _exc in IMPLEMENTATIONS
            }
        assert not any(results.values()), f"public host wrongly rejected -> {results}"
