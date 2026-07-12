"""Tests for contextual chat actions on Telegram media sends.

While a photo/document/voice/video uploads, Telegram should show the matching
chat action ("sending photo…", "sending file…", "sending voice…", "sending
video…") instead of nothing. Gated by `extra.media_chat_actions` (default on).
"""

import sys
from unittest.mock import AsyncMock, MagicMock

import pytest

from gateway.config import PlatformConfig


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

from plugins.platforms.telegram.adapter import TelegramAdapter  # noqa: E402


def _make_adapter(extra):
    adapter = TelegramAdapter(PlatformConfig(enabled=True, token="***", extra=extra))
    bot = MagicMock()
    bot.send_chat_action = AsyncMock()
    sent_message = MagicMock(message_id=123)
    for method in (
        "send_voice",
        "send_audio",
        "send_document",
        "send_photo",
        "send_video",
        "send_animation",
    ):
        setattr(bot, method, AsyncMock(return_value=sent_message))
    adapter._bot = bot
    return adapter


def _chat_action_of(adapter):
    assert adapter._bot.send_chat_action.await_count >= 1
    return adapter._bot.send_chat_action.await_args.kwargs["action"]


def test_enabled_by_default():
    adapter = _make_adapter(extra={})
    assert adapter._media_chat_actions_enabled is True


def test_disabled_via_extra():
    adapter = _make_adapter(extra={"media_chat_actions": False})
    assert adapter._media_chat_actions_enabled is False


@pytest.mark.asyncio
async def test_send_document_emits_upload_document(tmp_path):
    path = tmp_path / "report.pdf"
    path.write_bytes(b"pdf")
    adapter = _make_adapter(extra={})
    result = await adapter.send_document("123", str(path))
    assert result.success
    assert _chat_action_of(adapter) == "upload_document"


@pytest.mark.asyncio
async def test_send_voice_ogg_emits_upload_voice(tmp_path):
    path = tmp_path / "reply.ogg"
    path.write_bytes(b"ogg")
    adapter = _make_adapter(extra={})
    result = await adapter.send_voice("123", str(path))
    assert result.success
    assert _chat_action_of(adapter) == "upload_voice"


@pytest.mark.asyncio
async def test_send_image_file_emits_upload_photo(tmp_path):
    path = tmp_path / "pic.png"
    path.write_bytes(b"png")
    adapter = _make_adapter(extra={})
    result = await adapter.send_image_file("123", str(path))
    assert result.success
    assert _chat_action_of(adapter) == "upload_photo"


@pytest.mark.asyncio
async def test_send_video_emits_upload_video(tmp_path):
    path = tmp_path / "clip.mp4"
    path.write_bytes(b"mp4")
    adapter = _make_adapter(extra={})
    result = await adapter.send_video("123", str(path))
    assert result.success
    assert _chat_action_of(adapter) == "upload_video"


@pytest.mark.asyncio
async def test_disabled_sends_no_chat_action(tmp_path):
    path = tmp_path / "report.pdf"
    path.write_bytes(b"pdf")
    adapter = _make_adapter(extra={"media_chat_actions": False})
    result = await adapter.send_document("123", str(path))
    assert result.success
    adapter._bot.send_chat_action.assert_not_called()


@pytest.mark.asyncio
async def test_chat_action_failure_is_nonfatal(tmp_path):
    path = tmp_path / "report.pdf"
    path.write_bytes(b"pdf")
    adapter = _make_adapter(extra={})
    adapter._bot.send_chat_action = AsyncMock(side_effect=RuntimeError("boom"))
    result = await adapter.send_document("123", str(path))
    assert result.success
    adapter._bot.send_document.assert_awaited()
