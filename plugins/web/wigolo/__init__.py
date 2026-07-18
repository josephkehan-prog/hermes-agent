"""wigolo web search + extract plugin — bundled, auto-loaded.

Backed by the local ``wigolo`` CLI binary (shelled out via subprocess). No
API key required — availability reflects whether the binary is resolvable on
PATH (or the mise shim). Both search and extract are sync; the dispatcher in
:mod:`tools.web_tools` handles the async wrap when the caller is async.
"""

from __future__ import annotations

from plugins.web.wigolo.provider import WigoloWebSearchProvider


def register(ctx) -> None:
    """Register the wigolo provider with the plugin context."""
    ctx.register_web_search_provider(WigoloWebSearchProvider())
