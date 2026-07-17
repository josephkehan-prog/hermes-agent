from __future__ import annotations

import importlib.util
import sys
from pathlib import Path


ROOT = Path(__file__).parents[2] / "skills" / "media"


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_kokoro_preflight_requires_cached_voice():
    module = load_module(
        "kokoro_narrate",
        ROOT / "audiobook-narration-production" / "scripts" / "kokoro_narrate.py",
    )
    assert module.preflight("missing_voice")["voice"] is False


def test_srt_time_and_monotonic_writer(tmp_path):
    module = load_module(
        "mlx_whisper_transcribe",
        ROOT / "transcript-caption-production" / "scripts" / "mlx_whisper_transcribe.py",
    )
    assert module.srt_time(3661.234) == "01:01:01,234"
    output = tmp_path / "captions.srt"
    module.write_srt(
        [
            {"start": 0.0, "end": 1.0, "text": " first "},
            {"start": 0.5, "end": 2.0, "text": "second"},
        ],
        output,
    )
    text = output.read_text()
    assert "00:00:01,000 --> 00:00:02,000" in text
