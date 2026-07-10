"""``hermes nightly`` subcommand parser.

Handler injected to avoid importing ``main``, matching the pattern used by
``doctor`` / ``prompt-size``.
"""

from __future__ import annotations

from typing import Callable


def build_nightly_parser(subparsers, *, cmd_nightly: Callable) -> None:
    """Attach the ``nightly`` subcommand to ``subparsers``."""
    # =========================================================================
    # nightly command
    # =========================================================================
    nightly_parser = subparsers.add_parser(
        "nightly",
        help="Write a dated self-health digest (doctor + config-drift)",
        description=(
            "Run 'hermes doctor' and config-drift, write a dated digest "
            "under HERMES_HOME/state/nightly/YYYY-MM-DD.log, refresh "
            "latest.log, and append a line to ALERTS.log when unhealthy or "
            "drifted. Safe to run unattended from cron -- never raises."
        ),
    )
    nightly_parser.add_argument(
        "--with-eval",
        action="store_true",
        dest="with_eval",
        help=(
            "Also run model-eval (loads the local model onto the server; "
            "opt-in, heavier than the default checks)"
        ),
    )
    nightly_parser.set_defaults(func=cmd_nightly)
