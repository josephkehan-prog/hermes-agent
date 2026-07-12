"""Skill retriever must degrade gracefully when jieba is not installed.

The live install log-spammed 'No module named jieba' because the retriever
imported jieba unconditionally on every tokenization call. jieba only powers
CJK word segmentation; Latin text tokenizes fine on word boundaries, so a
missing jieba should disable CJK segmentation, not break retrieval.
"""
import importlib
import sys

import pytest


@pytest.fixture
def retriever_mod_no_jieba(monkeypatch):
    """Import agent.skill_retriever with jieba forced absent."""
    # Ensure a real import of jieba fails inside the module.
    monkeypatch.setitem(sys.modules, "jieba", None)
    monkeypatch.delitem(sys.modules, "agent.skill_retriever", raising=False)
    mod = importlib.import_module("agent.skill_retriever")
    importlib.reload(mod)
    yield mod
    # Restore a clean module state for other tests.
    monkeypatch.delitem(sys.modules, "agent.skill_retriever", raising=False)


def test_module_imports_without_jieba(retriever_mod_no_jieba):
    assert retriever_mod_no_jieba is not None
    assert retriever_mod_no_jieba._JIEBA_AVAILABLE is False


def test_tokenize_latin_text_without_jieba(retriever_mod_no_jieba):
    tokens = retriever_mod_no_jieba._tokenize("deploy the kubernetes cluster")
    assert "deploy" in tokens
    assert "kubernetes" in tokens
    assert "cluster" in tokens


def test_tokenize_never_raises_on_cjk_without_jieba(retriever_mod_no_jieba):
    # Without segmentation the whole CJK run may be one token — acceptable
    # degradation, but it must not raise.
    tokens = retriever_mod_no_jieba._tokenize("部署集群")
    assert isinstance(tokens, list)


def test_tokenize_empty_string(retriever_mod_no_jieba):
    assert retriever_mod_no_jieba._tokenize("") == []


def test_tokenize_uses_jieba_when_available():
    """When jieba IS importable, _tokenize routes through it."""
    jieba = pytest.importorskip("jieba")
    import importlib

    sys.modules.pop("agent.skill_retriever", None)
    mod = importlib.import_module("agent.skill_retriever")
    importlib.reload(mod)
    assert mod._JIEBA_AVAILABLE is True
    # jieba.cut on Latin text returns the word plus spaces; tokens present.
    tokens = mod._tokenize("hello world")
    assert any("hello" in t for t in tokens)
