"""Tests for the local (on-device) LTX-Video generation provider."""

from plugins.video_gen.local import LocalVideoGenProvider


def test_name_and_display():
    provider = LocalVideoGenProvider()
    assert provider.name == "local"
    assert "LTX" in provider.display_name


def test_capabilities_support_text_and_image():
    caps = LocalVideoGenProvider().capabilities()
    assert "text" in caps["modalities"]
    assert caps["max_reference_images"] >= 1


def test_default_model_is_a_listed_model():
    provider = LocalVideoGenProvider()
    listed = {m["id"] for m in provider.list_models()}
    assert provider.default_model() in listed


def test_setup_schema_has_no_env_vars():
    schema = LocalVideoGenProvider().get_setup_schema()
    assert schema["env_vars"] == []


def test_generate_returns_error_when_unavailable(monkeypatch):
    provider = LocalVideoGenProvider()
    monkeypatch.setattr(provider, "is_available", lambda: False)

    result = provider.generate("a cat walking through a sunlit room")

    assert result["success"] is False
    assert result["provider"] == "local"


def test_generate_ignores_unknown_kwargs(monkeypatch):
    provider = LocalVideoGenProvider()
    monkeypatch.setattr(provider, "is_available", lambda: False)

    # Forward-compat: unknown schema keys must not raise TypeError.
    result = provider.generate("a river", some_future_param=123)

    assert result["success"] is False
