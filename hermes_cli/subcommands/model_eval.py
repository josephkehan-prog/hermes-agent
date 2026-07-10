"""``hermes model-eval`` subcommand parser.

Handler injected to avoid importing ``main``, matching the pattern used by
``doctor`` / ``prompt-size``.
"""

from __future__ import annotations

from typing import Callable

DEFAULT_TIMEOUT = 60.0


def build_model_eval_parser(subparsers, *, cmd_model_eval: Callable) -> None:
    """Attach the ``model-eval`` subcommand to ``subparsers``."""
    # =========================================================================
    # model-eval command
    # =========================================================================
    model_eval_parser = subparsers.add_parser(
        "model-eval",
        help="Smoke-test a local model with canned prompts",
        description=(
            "Send a handful of canned single-turn prompts to a local "
            "OpenAI-compatible model endpoint (llama-server at "
            "127.0.0.1:1235 by default) and print a PASS/FAIL/MANUAL table "
            "with latency. Keyless. Exits non-zero if the endpoint is "
            "unreachable or any deterministic check fails."
        ),
    )
    model_eval_parser.add_argument(
        "--ollama",
        metavar="MODEL",
        default=None,
        help=(
            "Target Ollama (127.0.0.1:11434) with this model name instead "
            "of llama-server"
        ),
    )
    model_eval_parser.add_argument(
        "--timeout",
        type=float,
        default=DEFAULT_TIMEOUT,
        help=f"Per-request timeout in seconds (default: {DEFAULT_TIMEOUT:.0f})",
    )
    model_eval_parser.set_defaults(func=cmd_model_eval)
