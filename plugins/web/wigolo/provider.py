"""wigolo web search + content extraction — plugin form.

Subclasses :class:`agent.web_search_provider.WebSearchProvider`. Unlike the
SDK-backed providers (exa, tavily) this backend shells out to the local
``wigolo`` CLI binary, so it needs no API key — only the binary on ``PATH``
(or the mise shim). wigolo is a local-first web intelligence tool: it caches
fetches, reranks results, and emits machine-readable JSON via ``--json``.

Config keys this provider responds to::

    web:
      search_backend: "wigolo"     # explicit per-capability
      extract_backend: "wigolo"    # explicit per-capability
      backend: "wigolo"            # shared fallback for both

No env var required. Availability is a cheap ``shutil.which`` (cached).

Both capabilities are sync — the CLI is invoked via :mod:`subprocess`. The
``web_extract_tool`` dispatcher wraps sync extracts via ``asyncio.to_thread``
when it needs to keep the event loop responsive.

CLI contracts (as of wigolo v1)::

    wigolo search <query> --json --max-results N
      -> {"results": [{"title", "url", "snippet", "relevance_score"}, ...]}

    wigolo fetch <url> --json
      -> {"url", "title", "markdown", "metadata", "links", ...}
"""

from __future__ import annotations

import json
import logging
import os
import shutil
import subprocess
from typing import Any, Dict, List, Optional

from agent.web_search_provider import WebSearchProvider

logger = logging.getLogger(__name__)

# Fallback binary location when ``wigolo`` isn't on PATH — mise installs a
# shim here. Checked only if ``shutil.which`` misses.
_MISE_SHIM_PATH = os.path.expanduser("~/.local/share/mise/shims/wigolo")

# Subprocess wall-clock caps. Search is snappier (cache + rerank); fetch may
# render JS-heavy pages, so it gets a longer budget. On timeout the child is
# killed and a typed failure is surfaced rather than hanging the shared agent
# loop (mirrors the ddgs #36776 fix, but subprocess gives us native kill).
_SEARCH_TIMEOUT_SECS = 30
_FETCH_TIMEOUT_SECS = 60

# Cached resolved binary path. ``None`` means "not yet resolved"; the sentinel
# lets us distinguish "unresolved" from "resolved to absent" (empty string).
_binary_path: Optional[str] = None
_binary_resolved = False


def _resolve_binary() -> str:
    """Return the absolute path to the ``wigolo`` binary, or ``""`` if absent.

    Resolution order: ``shutil.which("wigolo")`` (respects PATH), then the
    mise shim fallback. Result is cached so repeated ``is_available()`` calls
    (fired on every ``hermes tools`` paint) don't re-probe the filesystem.
    """
    global _binary_path, _binary_resolved
    if _binary_resolved:
        return _binary_path or ""

    found = shutil.which("wigolo")
    if not found and os.path.exists(_MISE_SHIM_PATH):
        found = _MISE_SHIM_PATH

    _binary_path = found or ""
    _binary_resolved = True
    return _binary_path


def _reset_binary_cache_for_tests() -> None:
    """Drop the cached binary path so tests can re-resolve cleanly."""
    global _binary_path, _binary_resolved
    _binary_path = None
    _binary_resolved = False


def _run_wigolo(args: List[str], *, timeout: int) -> Dict[str, Any]:
    """Invoke ``wigolo`` with *args* and parse its ``--json`` stdout.

    Returns the parsed JSON dict on success. Raises:

    * ``FileNotFoundError`` — binary not resolvable.
    * ``subprocess.TimeoutExpired`` — exceeded *timeout* (child is killed).
    * ``RuntimeError`` — non-zero exit (stderr surfaced in the message).
    * ``ValueError`` — stdout was not valid JSON.
    """
    binary = _resolve_binary()
    if not binary:
        raise FileNotFoundError(
            "wigolo binary not found on PATH or at the mise shim path "
            f"({_MISE_SHIM_PATH})"
        )

    proc = subprocess.run(  # noqa: S603 — args are constructed, not shell
        [binary, *args, "--json"],
        capture_output=True,
        text=True,
        timeout=timeout,
        check=False,
    )
    if proc.returncode != 0:
        stderr = (proc.stderr or "").strip()
        raise RuntimeError(
            f"wigolo exited {proc.returncode}"
            + (f": {stderr}" if stderr else "")
        )

    stdout = (proc.stdout or "").strip()
    if not stdout:
        raise ValueError("wigolo returned empty output")
    try:
        parsed = json.loads(stdout)
    except json.JSONDecodeError as exc:
        raise ValueError(f"wigolo returned malformed JSON: {exc}") from exc
    if not isinstance(parsed, dict):
        raise ValueError(
            f"wigolo returned unexpected JSON type: {type(parsed).__name__}"
        )
    return parsed


class WigoloWebSearchProvider(WebSearchProvider):
    """wigolo CLI search + extract provider.

    Both methods are sync (subprocess). No API key required; availability is
    a cheap cached binary lookup. Errors (missing binary, non-zero exit, bad
    JSON, timeout) are surfaced as ``{"success": False, "error": ...}`` for
    search and per-URL ``{"error": ...}`` entries for extract, never raised
    to the caller — matching the exa/ddgs contract.
    """

    @property
    def name(self) -> str:
        return "wigolo"

    @property
    def display_name(self) -> str:
        return "wigolo (local CLI)"

    def is_available(self) -> bool:
        """Return True when the ``wigolo`` binary is resolvable.

        Cheap and cached — no subprocess health call. Must not do network
        I/O; runs at tool-registration time and on every ``hermes tools``
        paint.
        """
        return bool(_resolve_binary())

    def supports_search(self) -> bool:
        return True

    def supports_extract(self) -> bool:
        return True

    def search(self, query: str, limit: int = 5) -> Dict[str, Any]:
        """Execute a wigolo search via ``wigolo search <query> --json``.

        Returns ``{"success": True, "data": {"web": [{...}, ...]}}`` on
        success, ``{"success": False, "error": str}`` on failure (missing
        binary, timeout, non-zero exit, malformed JSON).
        """
        try:
            from tools.interrupt import is_interrupted

            if is_interrupted():
                return {"success": False, "error": "Interrupted"}

            safe_limit = max(1, int(limit))
            logger.info("wigolo search: '%s' (limit=%d)", query, safe_limit)

            payload = _run_wigolo(
                ["search", query, "--max-results", str(safe_limit)],
                timeout=_SEARCH_TIMEOUT_SECS,
            )

            raw_results = payload.get("results") or []
            web_results: List[Dict[str, Any]] = []
            for i, item in enumerate(raw_results):
                if i >= safe_limit:
                    break
                if not isinstance(item, dict):
                    continue
                web_results.append(
                    {
                        "url": str(item.get("url") or ""),
                        "title": str(item.get("title") or ""),
                        "description": str(item.get("snippet") or ""),
                        "position": i + 1,
                    }
                )

            logger.info(
                "wigolo search '%s': %d results (limit %d)",
                query, len(web_results), safe_limit,
            )
            return {"success": True, "data": {"web": web_results}}
        except FileNotFoundError as exc:
            return {"success": False, "error": str(exc)}
        except subprocess.TimeoutExpired:
            logger.warning(
                "wigolo search timed out after %ds for query: %r",
                _SEARCH_TIMEOUT_SECS, query,
            )
            return {
                "success": False,
                "error": (
                    f"wigolo search timed out after {_SEARCH_TIMEOUT_SECS}s. "
                    "Try again or switch to a different search provider."
                ),
            }
        except (RuntimeError, ValueError) as exc:
            logger.warning("wigolo search error: %s", exc)
            return {"success": False, "error": f"wigolo search failed: {exc}"}
        except Exception as exc:  # noqa: BLE001 — surface as failure
            logger.warning("wigolo search error: %s", exc)
            return {"success": False, "error": f"wigolo search failed: {exc}"}

    def extract(self, urls: List[str], **kwargs: Any) -> List[Dict[str, Any]]:
        """Extract content from one or more URLs via ``wigolo fetch``.

        Returns a list of result dicts shaped for the legacy LLM
        post-processing pipeline. Each URL is fetched independently; a
        per-URL failure yields an ``error`` field on that entry rather than
        aborting the batch. ``kwargs`` (format, include_raw, max_chars, …)
        are accepted for forward-compat and ignored.
        """
        try:
            from tools.interrupt import is_interrupted

            interrupt_check = is_interrupted
        except Exception:  # noqa: BLE001 — interrupt module optional
            interrupt_check = lambda: False  # noqa: E731

        results: List[Dict[str, Any]] = []
        for url in urls:
            if interrupt_check():
                results.append({"url": url, "title": "", "content": "", "error": "Interrupted"})
                continue
            results.append(self._extract_one(url))
        return results

    def _extract_one(self, url: str) -> Dict[str, Any]:
        """Fetch a single URL and map to the ABC extract-result shape."""
        try:
            logger.info("wigolo fetch: %s", url)
            payload = _run_wigolo(
                ["fetch", url],
                timeout=_FETCH_TIMEOUT_SECS,
            )

            content = str(payload.get("markdown") or "")
            title = str(payload.get("title") or "")
            # wigolo echoes the (possibly-normalized) URL; prefer it, fall
            # back to the requested URL.
            result_url = str(payload.get("url") or url)
            metadata = payload.get("metadata")
            if not isinstance(metadata, dict):
                metadata = {}
            # Ensure the legacy pipeline's expected keys are present.
            metadata = {
                "sourceURL": result_url,
                "title": title,
                **metadata,
            }

            return {
                "url": result_url,
                "title": title,
                "content": content,
                "raw_content": content,
                "metadata": metadata,
            }
        except FileNotFoundError as exc:
            return {"url": url, "title": "", "content": "", "error": str(exc)}
        except subprocess.TimeoutExpired:
            logger.warning(
                "wigolo fetch timed out after %ds for URL: %r",
                _FETCH_TIMEOUT_SECS, url,
            )
            return {
                "url": url,
                "title": "",
                "content": "",
                "error": f"wigolo fetch timed out after {_FETCH_TIMEOUT_SECS}s",
            }
        except (RuntimeError, ValueError) as exc:
            logger.warning("wigolo fetch error for %s: %s", url, exc)
            return {
                "url": url,
                "title": "",
                "content": "",
                "error": f"wigolo fetch failed: {exc}",
            }
        except Exception as exc:  # noqa: BLE001
            logger.warning("wigolo fetch error for %s: %s", url, exc)
            return {
                "url": url,
                "title": "",
                "content": "",
                "error": f"wigolo fetch failed: {exc}",
            }

    def get_setup_schema(self) -> Dict[str, Any]:
        return {
            "name": "wigolo (local CLI)",
            "badge": "free · no key · local",
            "tag": (
                "Local-first web search + fetch via the wigolo CLI — no API "
                "key, cached and reranked. Requires the wigolo binary on PATH."
            ),
            "env_vars": [],
        }
