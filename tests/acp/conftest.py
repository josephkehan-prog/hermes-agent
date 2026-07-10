"""pytest config for the acp/ subdirectory.

These tests exercise the ACP adapter, whose modules import the optional
``acp`` package at import time (``acp_adapter.server`` does ``import acp``).
When ``acp`` is not installed, collecting these modules raises
``ModuleNotFoundError`` and aborts the whole run. Skip the directory
cleanly when the dependency is absent rather than installing it.
"""
import importlib.util

collect_ignore_glob = (
    ["test_*.py"] if importlib.util.find_spec("acp") is None else []
)
