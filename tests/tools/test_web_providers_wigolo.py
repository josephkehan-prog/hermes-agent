"""Tests for the wigolo web search + extract provider.

Covers:
- WigoloWebSearchProvider.is_available() — reflects binary resolvability (cached)
- .search() — happy path, limit slicing, malformed JSON, non-zero exit,
  timeout, missing binary
- .extract() — happy path mapping, per-URL error isolation, timeout
- Result normalization to the legacy web-provider response shape
- Plugin registration/discovery via the web_search_registry

All subprocess calls are mocked — no real network or binary invocation in
these unit tests. Mirrors the ddgs provider test structure.
"""
from __future__ import annotations

import subprocess

import pytest


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _fresh_provider(monkeypatch, *, binary="/usr/bin/wigolo"):
    """Return a provider with the binary cache primed to *binary*.

    Patches ``shutil.which`` so ``_resolve_binary`` returns *binary* without
    touching the real filesystem, and resets the module-level cache so the
    patch takes effect.
    """
    import plugins.web.wigolo.provider as prov

    prov._reset_binary_cache_for_tests()
    if binary is None:
        monkeypatch.setattr(prov.shutil, "which", lambda _name: None)
        monkeypatch.setattr(prov.os.path, "exists", lambda _p: False)
    else:
        monkeypatch.setattr(prov.shutil, "which", lambda _name: binary)
    # Interrupts off by default.
    monkeypatch.setattr("tools.interrupt.is_interrupted", lambda: False, raising=False)
    return prov.WigoloWebSearchProvider()


def _fake_completed(stdout="", returncode=0, stderr=""):
    return subprocess.CompletedProcess(
        args=["wigolo"], returncode=returncode, stdout=stdout, stderr=stderr
    )


# ---------------------------------------------------------------------------
# Basic identity / capability
# ---------------------------------------------------------------------------


class TestWigoloProviderIdentity:
    def test_provider_name(self, monkeypatch):
        p = _fresh_provider(monkeypatch)
        assert p.name == "wigolo"

    def test_display_name_non_empty(self, monkeypatch):
        p = _fresh_provider(monkeypatch)
        assert p.display_name

    def test_supports_both_capabilities(self, monkeypatch):
        p = _fresh_provider(monkeypatch)
        assert p.supports_search() is True
        assert p.supports_extract() is True

    def test_implements_web_search_provider(self):
        from agent.web_search_provider import WebSearchProvider
        from plugins.web.wigolo.provider import WigoloWebSearchProvider

        assert issubclass(WigoloWebSearchProvider, WebSearchProvider)

    def test_extract_is_sync(self, monkeypatch):
        import inspect

        p = _fresh_provider(monkeypatch)
        assert inspect.iscoroutinefunction(p.extract) is False

    def test_setup_schema_shape(self, monkeypatch):
        p = _fresh_provider(monkeypatch)
        schema = p.get_setup_schema()
        assert isinstance(schema, dict)
        assert "name" in schema
        assert "env_vars" in schema
        assert schema["env_vars"] == []  # no API key


# ---------------------------------------------------------------------------
# is_available()
# ---------------------------------------------------------------------------


class TestWigoloIsAvailable:
    def test_available_when_binary_on_path(self, monkeypatch):
        p = _fresh_provider(monkeypatch, binary="/usr/local/bin/wigolo")
        assert p.is_available() is True

    def test_unavailable_when_binary_missing(self, monkeypatch):
        p = _fresh_provider(monkeypatch, binary=None)
        assert p.is_available() is False

    def test_available_via_mise_shim_fallback(self, monkeypatch):
        import plugins.web.wigolo.provider as prov

        prov._reset_binary_cache_for_tests()
        monkeypatch.setattr(prov.shutil, "which", lambda _name: None)
        monkeypatch.setattr(
            prov.os.path, "exists", lambda p: p == prov._MISE_SHIM_PATH
        )
        assert prov.WigoloWebSearchProvider().is_available() is True

    def test_result_is_cached(self, monkeypatch):
        import plugins.web.wigolo.provider as prov

        prov._reset_binary_cache_for_tests()
        calls = {"n": 0}

        def _counting_which(_name):
            calls["n"] += 1
            return "/usr/bin/wigolo"

        monkeypatch.setattr(prov.shutil, "which", _counting_which)
        p = prov.WigoloWebSearchProvider()
        assert p.is_available() is True
        assert p.is_available() is True
        assert calls["n"] == 1  # second call served from cache


# ---------------------------------------------------------------------------
# search()
# ---------------------------------------------------------------------------


class TestWigoloSearch:
    def test_happy_path_normalizes_results(self, monkeypatch):
        p = _fresh_provider(monkeypatch)
        payload = (
            '{"results": ['
            '{"title": "A", "url": "https://a.example.com", "snippet": "desc A", "relevance_score": 1.0},'
            '{"title": "B", "url": "https://b.example.com", "snippet": "desc B", "relevance_score": 0.7}'
            ']}'
        )
        monkeypatch.setattr(
            subprocess, "run", lambda *a, **k: _fake_completed(stdout=payload)
        )

        result = p.search("q", limit=5)

        assert result["success"] is True
        web = result["data"]["web"]
        assert len(web) == 2
        assert web[0] == {
            "title": "A",
            "url": "https://a.example.com",
            "description": "desc A",
            "position": 1,
        }
        assert web[1]["position"] == 2

    def test_limit_flag_and_slicing(self, monkeypatch):
        p = _fresh_provider(monkeypatch)
        captured = {}

        def _capture_run(cmd, *a, **k):
            captured["cmd"] = cmd
            results = ",".join(
                f'{{"title": "R{i}", "url": "https://r{i}.com", "snippet": ""}}'
                for i in range(10)
            )
            return _fake_completed(stdout=f'{{"results": [{results}]}}')

        monkeypatch.setattr(subprocess, "run", _capture_run)

        result = p.search("q", limit=3)

        assert result["success"] is True
        # --limit / --max-results passed to the CLI
        assert "--max-results" in captured["cmd"]
        assert "3" in captured["cmd"]
        # Defensive slice caps at the requested limit even if CLI over-returns.
        assert len(result["data"]["web"]) == 3

    def test_empty_results(self, monkeypatch):
        p = _fresh_provider(monkeypatch)
        monkeypatch.setattr(
            subprocess, "run", lambda *a, **k: _fake_completed(stdout='{"results": []}')
        )
        result = p.search("nothing", limit=5)
        assert result["success"] is True
        assert result["data"]["web"] == []

    def test_missing_results_key_yields_empty(self, monkeypatch):
        p = _fresh_provider(monkeypatch)
        monkeypatch.setattr(
            subprocess, "run", lambda *a, **k: _fake_completed(stdout='{"query": "x"}')
        )
        result = p.search("q", limit=5)
        assert result["success"] is True
        assert result["data"]["web"] == []

    def test_malformed_json_returns_failure(self, monkeypatch):
        p = _fresh_provider(monkeypatch)
        monkeypatch.setattr(
            subprocess, "run", lambda *a, **k: _fake_completed(stdout="not json{{")
        )
        result = p.search("q", limit=5)
        assert result["success"] is False
        assert "failed" in result["error"].lower()

    def test_nonzero_exit_returns_failure(self, monkeypatch):
        p = _fresh_provider(monkeypatch)
        monkeypatch.setattr(
            subprocess,
            "run",
            lambda *a, **k: _fake_completed(returncode=2, stderr="boom"),
        )
        result = p.search("q", limit=5)
        assert result["success"] is False
        assert "boom" in result["error"] or "failed" in result["error"].lower()

    def test_timeout_returns_failure(self, monkeypatch):
        p = _fresh_provider(monkeypatch)

        def _raise_timeout(*a, **k):
            raise subprocess.TimeoutExpired(cmd="wigolo", timeout=30)

        monkeypatch.setattr(subprocess, "run", _raise_timeout)
        result = p.search("q", limit=5)
        assert result["success"] is False
        assert "timed out" in result["error"].lower()

    def test_missing_binary_returns_failure(self, monkeypatch):
        p = _fresh_provider(monkeypatch, binary=None)
        result = p.search("q", limit=5)
        assert result["success"] is False
        assert "not found" in result["error"].lower()

    def test_interrupt_short_circuits(self, monkeypatch):
        p = _fresh_provider(monkeypatch)
        monkeypatch.setattr("tools.interrupt.is_interrupted", lambda: True, raising=False)
        # subprocess.run must never be called when interrupted.
        monkeypatch.setattr(
            subprocess, "run", lambda *a, **k: pytest.fail("should not run")
        )
        result = p.search("q", limit=5)
        assert result["success"] is False
        assert result["error"] == "Interrupted"


# ---------------------------------------------------------------------------
# extract()
# ---------------------------------------------------------------------------


class TestWigoloExtract:
    def test_happy_path_maps_markdown_to_content(self, monkeypatch):
        p = _fresh_provider(monkeypatch)
        payload = (
            '{"url": "https://example.com", "title": "Example", '
            '"markdown": "# Hello\\n\\nbody text", '
            '"metadata": {"language": "en"}, "links": ["https://iana.org"]}'
        )
        monkeypatch.setattr(
            subprocess, "run", lambda *a, **k: _fake_completed(stdout=payload)
        )

        results = p.extract(["https://example.com"])

        assert isinstance(results, list)
        assert len(results) == 1
        r = results[0]
        assert r["url"] == "https://example.com"
        assert r["title"] == "Example"
        assert r["content"] == "# Hello\n\nbody text"
        assert r["raw_content"] == r["content"]
        assert r["metadata"]["sourceURL"] == "https://example.com"
        assert r["metadata"]["title"] == "Example"
        assert r["metadata"]["language"] == "en"
        assert "error" not in r

    def test_multiple_urls_each_fetched(self, monkeypatch):
        p = _fresh_provider(monkeypatch)
        seen = []

        def _run(cmd, *a, **k):
            url = cmd[2]  # [binary, "fetch", url, "--json"]
            seen.append(url)
            return _fake_completed(
                stdout=f'{{"url": "{url}", "title": "T", "markdown": "m"}}'
            )

        monkeypatch.setattr(subprocess, "run", _run)

        results = p.extract(["https://a.com", "https://b.com"])

        assert len(results) == 2
        assert seen == ["https://a.com", "https://b.com"]
        assert all(r["content"] == "m" for r in results)

    def test_per_url_error_does_not_abort_batch(self, monkeypatch):
        p = _fresh_provider(monkeypatch)

        def _run(cmd, *a, **k):
            url = cmd[2]
            if "bad" in url:
                return _fake_completed(returncode=1, stderr="fetch failed")
            return _fake_completed(
                stdout=f'{{"url": "{url}", "title": "OK", "markdown": "ok"}}'
            )

        monkeypatch.setattr(subprocess, "run", _run)

        results = p.extract(["https://good.com", "https://bad.com"])

        assert len(results) == 2
        assert "error" not in results[0]
        assert results[0]["content"] == "ok"
        assert "error" in results[1]
        assert results[1]["url"] == "https://bad.com"

    def test_malformed_json_yields_per_url_error(self, monkeypatch):
        p = _fresh_provider(monkeypatch)
        monkeypatch.setattr(
            subprocess, "run", lambda *a, **k: _fake_completed(stdout="}{not json")
        )
        results = p.extract(["https://example.com"])
        assert len(results) == 1
        assert "error" in results[0]
        assert results[0]["url"] == "https://example.com"

    def test_timeout_yields_per_url_error(self, monkeypatch):
        p = _fresh_provider(monkeypatch)

        def _raise_timeout(*a, **k):
            raise subprocess.TimeoutExpired(cmd="wigolo", timeout=60)

        monkeypatch.setattr(subprocess, "run", _raise_timeout)
        results = p.extract(["https://example.com"])
        assert len(results) == 1
        assert "timed out" in results[0]["error"].lower()

    def test_missing_binary_yields_per_url_error(self, monkeypatch):
        p = _fresh_provider(monkeypatch, binary=None)
        results = p.extract(["https://example.com"])
        assert len(results) == 1
        assert "error" in results[0]
        assert "not found" in results[0]["error"].lower()

    def test_missing_markdown_yields_empty_content(self, monkeypatch):
        p = _fresh_provider(monkeypatch)
        monkeypatch.setattr(
            subprocess,
            "run",
            lambda *a, **k: _fake_completed(
                stdout='{"url": "https://example.com", "title": "T"}'
            ),
        )
        results = p.extract(["https://example.com"])
        assert results[0]["content"] == ""
        assert "error" not in results[0]


# ---------------------------------------------------------------------------
# Plugin registration / discovery
# ---------------------------------------------------------------------------


class TestWigoloRegistration:
    def test_plugin_discovers_and_registers(self):
        from hermes_cli.plugins import _ensure_plugins_discovered

        _ensure_plugins_discovered()
        from agent.web_search_registry import get_provider

        provider = get_provider("wigolo")
        assert provider is not None
        assert provider.name == "wigolo"
        assert provider.supports_search() is True
        assert provider.supports_extract() is True

    def test_register_hook_adds_provider(self):
        from agent import web_search_registry
        from plugins.web.wigolo import register

        class _Ctx:
            def __init__(self):
                self.registered = []

            def register_web_search_provider(self, provider):
                self.registered.append(provider)
                web_search_registry.register_provider(provider)

        ctx = _Ctx()
        register(ctx)
        assert len(ctx.registered) == 1
        assert ctx.registered[0].name == "wigolo"
