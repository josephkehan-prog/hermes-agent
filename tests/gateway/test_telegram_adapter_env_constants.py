"""Tests for env-overridable module constants in the Telegram adapter.

These constants (send-retry attempt count, polling-conflict retry delay
base/increment) are computed once at import time from ``os.getenv``, so
exercising the override requires reloading the module after the env var is
set — a plain attribute patch wouldn't catch a broken ``os.getenv`` call or
a bad try/except fallback.
"""

import importlib
import sys

from unittest.mock import MagicMock


def _ensure_telegram_mock():
    if "telegram" in sys.modules and hasattr(sys.modules["telegram"], "__file__"):
        return

    telegram_mod = MagicMock()
    telegram_mod.ext.ContextTypes.DEFAULT_TYPE = type(None)
    telegram_mod.constants.ParseMode.MARKDOWN_V2 = "MarkdownV2"
    telegram_mod.constants.ChatType.GROUP = "group"
    telegram_mod.constants.ChatType.SUPERGROUP = "supergroup"
    telegram_mod.constants.ChatType.CHANNEL = "channel"
    telegram_mod.constants.ChatType.PRIVATE = "private"

    for name in ("telegram", "telegram.ext", "telegram.constants", "telegram.request"):
        sys.modules.setdefault(name, telegram_mod)


_ensure_telegram_mock()

import plugins.platforms.telegram.adapter as adapter_module  # noqa: E402


def _reload_adapter():
    return importlib.reload(adapter_module)


def test_send_retry_attempts_default(monkeypatch):
    monkeypatch.delenv("HERMES_TELEGRAM_SEND_RETRY_ATTEMPTS", raising=False)
    mod = _reload_adapter()
    assert mod._SEND_RETRY_ATTEMPTS == 3


def test_send_retry_attempts_honors_env_override(monkeypatch):
    monkeypatch.setenv("HERMES_TELEGRAM_SEND_RETRY_ATTEMPTS", "5")
    try:
        mod = _reload_adapter()
        assert mod._SEND_RETRY_ATTEMPTS == 5
    finally:
        monkeypatch.delenv("HERMES_TELEGRAM_SEND_RETRY_ATTEMPTS", raising=False)
        _reload_adapter()


def test_send_retry_attempts_falls_back_on_invalid_value(monkeypatch):
    monkeypatch.setenv("HERMES_TELEGRAM_SEND_RETRY_ATTEMPTS", "not-a-number")
    try:
        mod = _reload_adapter()
        assert mod._SEND_RETRY_ATTEMPTS == 3
    finally:
        monkeypatch.delenv("HERMES_TELEGRAM_SEND_RETRY_ATTEMPTS", raising=False)
        _reload_adapter()


def test_polling_conflict_base_delay_default(monkeypatch):
    monkeypatch.delenv("HERMES_TELEGRAM_CONFLICT_BASE_DELAY", raising=False)
    mod = _reload_adapter()
    assert mod._POLLING_CONFLICT_BASE_DELAY == 10.0


def test_polling_conflict_base_delay_honors_env_override(monkeypatch):
    monkeypatch.setenv("HERMES_TELEGRAM_CONFLICT_BASE_DELAY", "20")
    try:
        mod = _reload_adapter()
        assert mod._POLLING_CONFLICT_BASE_DELAY == 20.0
    finally:
        monkeypatch.delenv("HERMES_TELEGRAM_CONFLICT_BASE_DELAY", raising=False)
        _reload_adapter()


def test_polling_conflict_delay_increment_honors_env_override(monkeypatch):
    monkeypatch.setenv("HERMES_TELEGRAM_CONFLICT_DELAY_INCREMENT", "15")
    try:
        mod = _reload_adapter()
        assert mod._POLLING_CONFLICT_DELAY_INCREMENT == 15.0
    finally:
        monkeypatch.delenv("HERMES_TELEGRAM_CONFLICT_DELAY_INCREMENT", raising=False)
        _reload_adapter()
