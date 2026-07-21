"""Local (on-device) video generation backend via the LTX-Video runtime.

Generates video entirely on-device with **no cloud key** by shelling out to the
LTX-Video runtime pre-installed at ``~/mac/Hermes/runtimes/ltx-video`` — its own
``uv`` virtualenv plus a 6.3GB 2B-distilled safetensors checkpoint.

Surface (mirrors the ``fal`` provider):

- **Text-to-video** by default: ``video_generate(prompt=...)``.
- **Image-to-video** when ``image_url`` is a *local existing file path* — the
  path is passed to the runtime as a conditioning frame. HTTP(S) URLs are
  ignored (this local runtime only accepts on-disk file paths) and the fact is
  noted in the response ``extra``.

The runtime is invoked as::

    <LTX_ROOT>/.venv/bin/python <LTX_ROOT>/inference.py \\
        --prompt <prompt> \\
        --pipeline_config configs/hermes-ltxv-2b-0.9.8-distilled.yaml \\
        --output_path <fresh temp dir> \\
        --seed <int> --height <int> --width <int> \\
        --num_frames <int> --frame_rate <int> \\
        [--negative_prompt <str>] \\
        [--conditioning_media_paths <path> --conditioning_start_frames 0]

with ``cwd=LTX_ROOT`` so the relative ``pipeline_config`` resolves. After a
successful run we glob the temp output dir recursively for the newest ``*.mp4``
and return its absolute path.
"""

from __future__ import annotations

import logging
import subprocess
import tempfile
from pathlib import Path
from typing import Any, Dict, List, Optional

from agent.video_gen_provider import (
    DEFAULT_ASPECT_RATIO,
    DEFAULT_RESOLUTION,
    VideoGenProvider,
    error_response,
    success_response,
)

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Runtime layout (see module docstring)
# ---------------------------------------------------------------------------

LTX_ROOT: Path = Path.home() / "mac" / "Hermes" / "runtimes" / "ltx-video"
LTX_PYTHON: Path = LTX_ROOT / ".venv" / "bin" / "python"
LTX_ENTRY: Path = LTX_ROOT / "inference.py"
LTX_CHECKPOINT: Path = LTX_ROOT / "checkpoints" / "ltxv-2b-0.9.8-distilled.safetensors"
LTX_PIPELINE_CONFIG: str = "configs/hermes-ltxv-2b-0.9.8-distilled.yaml"

MODEL_ID = "ltxv-2b-0.9.8-distilled"

# ---------------------------------------------------------------------------
# Generation defaults (LTX-friendly, dimensions divisible by 32)
# ---------------------------------------------------------------------------

DEFAULT_WIDTH = 704
DEFAULT_HEIGHT = 480
DEFAULT_FRAME_RATE = 24
DEFAULT_NUM_FRAMES = 121
DEFAULT_SEED = 42

# num_frames must be 8k+1 for the latent temporal stride; clamp to a sane band.
FRAME_STEP = 8
MIN_NUM_FRAMES = 9
MAX_NUM_FRAMES = 257

SUBPROCESS_TIMEOUT_S = 1800
STDERR_TAIL_CHARS = 500


def _parse_resolution(resolution: Optional[str]) -> tuple[int, int]:
    """Parse a ``"WxH"`` string into ``(width, height)``; fall back to defaults.

    Accepts the ``"1280x720"`` shape. Anything else (``"720p"``, ``None``,
    malformed) yields the LTX-friendly default frame size.
    """
    if isinstance(resolution, str) and "x" in resolution.lower():
        parts = resolution.lower().split("x", 1)
        try:
            width = int(parts[0].strip())
            height = int(parts[1].strip())
            if width > 0 and height > 0:
                return width, height
        except (ValueError, IndexError):
            pass
    return DEFAULT_WIDTH, DEFAULT_HEIGHT


def _derive_num_frames(duration: Optional[int], frame_rate: int) -> int:
    """Derive a valid ``num_frames`` (8k+1, clamped) from a duration in seconds."""
    if not duration or duration <= 0:
        return DEFAULT_NUM_FRAMES
    raw = round(duration * frame_rate / FRAME_STEP) * FRAME_STEP + 1
    return min(MAX_NUM_FRAMES, max(MIN_NUM_FRAMES, raw))


def _newest_mp4(directory: Path) -> Optional[Path]:
    """Return the most recently modified ``*.mp4`` under ``directory`` (recursive)."""
    candidates = list(directory.rglob("*.mp4"))
    if not candidates:
        return None
    return max(candidates, key=lambda p: p.stat().st_mtime)


# ---------------------------------------------------------------------------
# Provider
# ---------------------------------------------------------------------------


class LocalVideoGenProvider(VideoGenProvider):
    """On-device text/image-to-video backend driving the local LTX-Video runtime."""

    @property
    def name(self) -> str:
        return "local"

    @property
    def display_name(self) -> str:
        return "Local (LTX-Video)"

    def is_available(self) -> bool:
        """Cheap on-disk check only — no heavy import, no network."""
        try:
            return (
                LTX_PYTHON.is_file()
                and LTX_ENTRY.is_file()
                and LTX_CHECKPOINT.is_file()
            )
        except OSError:  # pragma: no cover — never break the picker
            return False

    def list_models(self) -> List[Dict[str, Any]]:
        return [
            {
                "id": MODEL_ID,
                "display": "LTX-Video 2B distilled (local)",
                "speed": "on-device (MPS)",
                "strengths": "Fully local text-to-video, no cloud key.",
                "price": "free (local)",
                "modalities": ["text", "image"],
            }
        ]

    def default_model(self) -> Optional[str]:
        return MODEL_ID

    def get_setup_schema(self) -> Dict[str, Any]:
        return {
            "name": self.display_name,
            "badge": "free",
            "tag": "On-device LTX-Video (Apple MPS) — no cloud key, no API cost.",
            "env_vars": [],
        }

    def capabilities(self) -> Dict[str, Any]:
        return {
            "modalities": ["text", "image"],
            "max_reference_images": 1,
        }

    def generate(
        self,
        prompt: str,
        *,
        model: Optional[str] = None,
        image_url: Optional[str] = None,
        reference_image_urls: Optional[List[str]] = None,
        duration: Optional[int] = None,
        aspect_ratio: str = DEFAULT_ASPECT_RATIO,
        resolution: str = DEFAULT_RESOLUTION,
        negative_prompt: Optional[str] = None,
        audio: Optional[bool] = None,
        seed: Optional[int] = None,
        **kwargs: Any,
    ) -> Dict[str, Any]:
        prompt = (prompt or "").strip()
        if not prompt:
            return error_response(
                error="prompt is required.",
                error_type="missing_prompt",
                provider="local",
                model=MODEL_ID,
                aspect_ratio=aspect_ratio,
            )

        if not self.is_available():
            return error_response(
                error=(
                    "Local LTX-Video runtime not found. Expected an interpreter, "
                    f"inference.py, and checkpoint under {LTX_ROOT}."
                ),
                error_type="runtime_unavailable",
                provider="local",
                model=MODEL_ID,
                prompt=prompt,
                aspect_ratio=aspect_ratio,
            )

        try:
            width, height = _parse_resolution(resolution)
            frame_rate = DEFAULT_FRAME_RATE
            num_frames = _derive_num_frames(duration, frame_rate)
            seed_value = DEFAULT_SEED if seed is None else int(seed)

            extra: Dict[str, Any] = {
                "width": width,
                "height": height,
                "num_frames": num_frames,
                "frame_rate": frame_rate,
            }
            modality = "text"

            # Build the invocation. ``cwd`` is LTX_ROOT so the relative
            # pipeline_config resolves against the runtime dir.
            with tempfile.TemporaryDirectory(prefix="ltx_out_") as out_dir:
                command: List[str] = [
                    str(LTX_PYTHON),
                    str(LTX_ENTRY),
                    "--prompt", prompt,
                    "--pipeline_config", LTX_PIPELINE_CONFIG,
                    "--output_path", out_dir,
                    "--seed", str(seed_value),
                    "--height", str(height),
                    "--width", str(width),
                    "--num_frames", str(num_frames),
                    "--frame_rate", str(frame_rate),
                ]
                if negative_prompt and negative_prompt.strip():
                    command += ["--negative_prompt", negative_prompt.strip()]

                # Optional single conditioning image — only local file paths.
                conditioning = (image_url or "").strip()
                if conditioning:
                    cond_path = Path(conditioning)
                    if cond_path.is_file():
                        command += [
                            "--conditioning_media_paths", str(cond_path),
                            "--conditioning_start_frames", "0",
                        ]
                        modality = "image"
                    else:
                        # HTTP URL or non-existent path: this local runtime only
                        # takes on-disk paths. Note it and fall back to text.
                        extra["ignored_image_url"] = conditioning

                logger.info(
                    "Local LTX-Video generate: %dx%d, %d frames @ %dfps, seed=%d",
                    width, height, num_frames, frame_rate, seed_value,
                )

                result = subprocess.run(
                    command,
                    cwd=str(LTX_ROOT),
                    timeout=SUBPROCESS_TIMEOUT_S,
                    capture_output=True,
                    text=True,
                    stdin=subprocess.DEVNULL,
                    check=False,
                )

                if result.returncode != 0:
                    stderr_tail = (result.stderr or "")[-STDERR_TAIL_CHARS:]
                    logger.warning(
                        "LTX-Video exited rc=%d: %s", result.returncode, stderr_tail,
                    )
                    return error_response(
                        error=f"Local LTX-Video generation failed: {stderr_tail}",
                        error_type="generation_failed",
                        provider="local",
                        model=MODEL_ID,
                        prompt=prompt,
                        aspect_ratio=aspect_ratio,
                    )

                video_path = _newest_mp4(Path(out_dir))
                if video_path is None:
                    return error_response(
                        error=(
                            "Local LTX-Video reported success but produced no "
                            f"*.mp4 under {out_dir}."
                        ),
                        error_type="missing_output",
                        provider="local",
                        model=MODEL_ID,
                        prompt=prompt,
                        aspect_ratio=aspect_ratio,
                    )

                # Resolve to an absolute path before the temp dir is removed;
                # the mp4 is materialised, so read its bytes out to a durable
                # location is unnecessary here — the caller receives the path
                # while the dir still exists is a risk, so copy out.
                durable = _persist_output(video_path)

            return success_response(
                video=str(durable),
                model=MODEL_ID,
                prompt=prompt,
                modality=modality,
                aspect_ratio=aspect_ratio,
                duration=int(duration or 0),
                provider="local",
                extra=extra,
            )
        except subprocess.TimeoutExpired:
            return error_response(
                error=(
                    f"Local LTX-Video generation timed out after "
                    f"{SUBPROCESS_TIMEOUT_S}s."
                ),
                error_type="timeout",
                provider="local",
                model=MODEL_ID,
                prompt=prompt,
                aspect_ratio=aspect_ratio,
            )
        except Exception as exc:  # noqa: BLE001 — never raise out of a provider
            logger.warning("Local LTX-Video generation error", exc_info=True)
            return error_response(
                error=f"Local LTX-Video generation error: {exc}",
                error_type="provider_error",
                provider="local",
                model=MODEL_ID,
                prompt=prompt,
                aspect_ratio=aspect_ratio,
            )


def _persist_output(video_path: Path) -> Path:
    """Copy the runtime's mp4 out of its temp dir into the durable video cache.

    The subprocess writes into a :class:`tempfile.TemporaryDirectory` that is
    deleted on ``with`` exit, so we materialise the bytes under
    ``$HERMES_HOME/cache/videos/`` and return that absolute path.
    """
    from agent.video_gen_provider import save_bytes_video

    raw = video_path.read_bytes()
    return save_bytes_video(raw, prefix="local")


# ---------------------------------------------------------------------------
# Plugin entry point
# ---------------------------------------------------------------------------


def register(ctx) -> None:
    """Plugin entry point — wire ``LocalVideoGenProvider`` into the registry."""
    ctx.register_video_gen_provider(LocalVideoGenProvider())
