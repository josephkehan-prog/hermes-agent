"""``hermes config-drift`` subcommand parser.

Thin CLI wiring over ``hermes_cli/config_drift.py``'s pure
``create_baseline`` / ``check_drift`` functions. Handler injected to avoid
importing ``main``, matching the pattern used by ``doctor`` / ``prompt-size``.
"""

from __future__ import annotations

from typing import Callable


def build_config_drift_parser(subparsers, *, cmd_config_drift: Callable) -> None:
    """Attach the ``config-drift`` subcommand to ``subparsers``."""
    # =========================================================================
    # config-drift command
    # =========================================================================
    config_drift_parser = subparsers.add_parser(
        "config-drift",
        help="Check config.yaml for drift against the saved baseline",
        description=(
            "Compare the live HERMES_HOME config against a stored baseline "
            "snapshot. Read-only by default: prints 'no drift', 'drift "
            "detected' plus a unified diff, or 'no baseline' -- and exits 2 "
            "when drift is detected. Use --rebaseline to snapshot the "
            "current config as the new baseline."
        ),
    )
    config_drift_parser.add_argument(
        "--rebaseline",
        action="store_true",
        help="Snapshot the current config as the new drift baseline and exit",
    )
    config_drift_parser.set_defaults(func=cmd_config_drift)
