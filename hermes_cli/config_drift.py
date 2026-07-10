"""Config drift watcher for Hermes Agent.

Provides a baseline snapshot + diff-over-time mechanism for
``HERMES_HOME/config.yaml`` (see ``hermes_constants.get_config_path()``).

This folds the workspace-only ``hermes-config-drift`` shell script into the
product as a reusable module. ``hermes doctor`` already validates config
*shape* once per run, but nothing previously tracked config *changes* over
time -- that is the gap this module closes.

Pure functions only: no CLI, no argparse. Wiring this into ``hermes doctor``
or a dedicated ``hermes config drift`` subcommand is a later step -- this
module is not registered anywhere yet.

Read-only on the live config: these functions never write to
``config.yaml``. The baseline snapshot is written atomically (temp file +
rename) so a crash or concurrent read never observes a half-written
baseline.
"""

import difflib
import logging
import shutil
import sys
import tempfile
from pathlib import Path
from typing import List, Optional, TypedDict

from hermes_constants import get_config_path, get_hermes_home

logger = logging.getLogger(__name__)


class DriftResult(TypedDict):
    """Structured result of a :func:`check_drift` call."""

    baseline_exists: bool
    drifted: bool
    diff: List[str]


def baseline_path(hermes_home: Optional[Path] = None) -> Path:
    """Return the path where the config baseline snapshot lives.

    Defaults to ``HERMES_HOME/state/config-baseline/config.yaml``. Pass
    ``hermes_home`` explicitly (e.g. from tests) to avoid touching the real
    Hermes home; production callers can omit it and let
    ``hermes_constants.get_hermes_home()`` resolve it.
    """
    home = hermes_home if hermes_home is not None else get_hermes_home()
    return Path(home) / "state" / "config-baseline" / "config.yaml"


def create_baseline(
    config_path: Optional[Path] = None,
    baseline_file: Optional[Path] = None,
) -> Path:
    """Snapshot the current config as the new drift baseline.

    Copies ``config_path`` (default: ``get_config_path()``) to
    ``baseline_file`` (default: ``baseline_path()``) atomically: the copy is
    staged to a temp file in the baseline's own directory, then moved into
    place with a single rename, so readers never see a partially-written
    baseline. Parent directories are created as needed.

    Returns the baseline path.
    """
    src = Path(config_path) if config_path is not None else get_config_path()
    dst = Path(baseline_file) if baseline_file is not None else baseline_path()

    dst.parent.mkdir(parents=True, exist_ok=True)

    with tempfile.NamedTemporaryFile(
        dir=str(dst.parent), prefix=".config-baseline-", suffix=".tmp", delete=False
    ) as tmp:
        tmp_path = Path(tmp.name)

    try:
        shutil.copyfile(src, tmp_path)
        tmp_path.replace(dst)
    except BaseException:
        tmp_path.unlink(missing_ok=True)
        raise

    logger.info("config-drift: baseline created at %s", dst)
    return dst


def check_drift(
    config_path: Optional[Path] = None,
    baseline_file: Optional[Path] = None,
) -> DriftResult:
    """Compare the current config against the stored baseline.

    Read-only: never writes to ``config_path`` (or anywhere else besides
    the return value). If no baseline snapshot exists yet, returns
    ``baseline_exists=False`` -- callers decide whether to call
    :func:`create_baseline` in that case; this function does not create one
    implicitly.

    Returns a :class:`DriftResult` with:
      - ``baseline_exists``: whether a baseline snapshot was found.
      - ``drifted``: ``True`` if the current config differs from baseline.
      - ``diff``: unified diff lines (empty when there is no baseline, no
        current config content, or no drift).
    """
    current = Path(config_path) if config_path is not None else get_config_path()
    baseline = Path(baseline_file) if baseline_file is not None else baseline_path()

    if not baseline.exists():
        return DriftResult(baseline_exists=False, drifted=False, diff=[])

    if not current.exists():
        # The config vanished since the baseline was taken -- that counts
        # as drift rather than an error.
        return DriftResult(
            baseline_exists=True,
            drifted=True,
            diff=[f"--- {baseline}\n", f"+++ {current}\n", "config file missing\n"],
        )

    baseline_lines = baseline.read_text(encoding="utf-8").splitlines(keepends=True)
    current_lines = current.read_text(encoding="utf-8").splitlines(keepends=True)

    diff = list(
        difflib.unified_diff(
            baseline_lines,
            current_lines,
            fromfile=str(baseline),
            tofile=str(current),
        )
    )

    return DriftResult(baseline_exists=True, drifted=bool(diff), diff=diff)


def cmd_config_drift(args) -> None:
    """``hermes config-drift`` -- thin CLI wrapper over this module.

    Default: check the live config against the stored baseline and print
    the result. Exit 0 when there is no baseline yet or no drift, exit 2
    when drift is detected.

    ``--rebaseline``: snapshot the current config as the new baseline and
    exit 0. Does not also run a drift check in the same invocation -- run
    ``hermes config-drift`` again afterward if a report is wanted.

    Read-only on the live config in all cases; ``--rebaseline`` only ever
    writes to the baseline snapshot path (``hermes_cli.config_drift.baseline_path``),
    never to ``config.yaml`` itself.
    """
    if getattr(args, "rebaseline", False):
        path = create_baseline()
        print(f"baseline created: {path}")
        return

    result = check_drift()

    if not result["baseline_exists"]:
        print("no baseline (run 'hermes config-drift --rebaseline' to create one)")
        return

    if not result["drifted"]:
        print("no drift")
        return

    print("drift detected")
    for line in result["diff"]:
        sys.stdout.write(line if line.endswith("\n") else line + "\n")
    sys.exit(2)
