"""pytest config for the acp_adapter/ subdirectory.

These modules import the optional ``acp`` package directly (e.g.
``from acp.schema import ...``). When ``acp`` is not installed,
collecting them raises ``ModuleNotFoundError`` and aborts the whole
run. Skip the directory cleanly when the dependency is absent rather
than installing it.
"""
import importlib.util

collect_ignore_glob = (
    ["test_*.py"] if importlib.util.find_spec("acp") is None else []
)
