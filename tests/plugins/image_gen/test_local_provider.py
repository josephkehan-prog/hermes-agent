"""Tests for the local (on-device) FLUX image-generation provider."""

from plugins.image_gen.local import LocalImageGenProvider


def test_name_and_display():
    provider = LocalImageGenProvider()
    assert provider.name == "local"
    assert "Local" in provider.display_name


def test_capabilities_are_text_only():
    caps = LocalImageGenProvider().capabilities()
    assert caps["modalities"] == ["text"]
    assert caps["max_reference_images"] == 0


def test_default_model_is_a_listed_model():
    provider = LocalImageGenProvider()
    listed = {m["id"] for m in provider.list_models()}
    assert provider.default_model() in listed


def test_setup_schema_has_no_env_vars():
    schema = LocalImageGenProvider().get_setup_schema()
    assert schema["env_vars"] == []


def test_generate_returns_error_when_unavailable(monkeypatch):
    provider = LocalImageGenProvider()
    monkeypatch.setattr(provider, "is_available", lambda: False)

    result = provider.generate("a cat in a sunlit room")

    assert result["success"] is False
    assert result["provider"] == "local"
