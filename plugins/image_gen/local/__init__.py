"""Local (on-device) image generation backend.

Generates images entirely on-device by shelling out to the in-tree
``flux-local`` skill script
(``skills/creative/flux-local/scripts/flux_one_shot.py``), which loads a
FLUX.1 model with diffusers on Apple Silicon (MPS). This lets Hermes image
generation run with **no cloud key** — the trade-off is latency (a multi-GB
model load per cold run) rather than a per-image API cost.

Text-to-image only: the underlying one-shot script is invoked in its
single-output mode, so this provider advertises ``modalities: ["text"]`` and
declines reference images.
"""

from __future__ import annotations

import importlib.util
import logging
import shutil
import subprocess
import tempfile
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional

from agent.image_gen_provider import (
    DEFAULT_ASPECT_RATIO,
    ImageGenProvider,
    error_response,
    resolve_aspect_ratio,
    success_response,
)

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

# flux_one_shot.py lives at <repo>/skills/creative/flux-local/scripts/.
# This file is <repo>/plugins/image_gen/local/__init__.py, so the repo root is
# parents[3] (local -> image_gen -> plugins -> <repo>).
_REPO_ROOT = Path(__file__).resolve().parents[3]
_SCRIPT_PATH = _REPO_ROOT / "skills" / "creative" / "flux-local" / "scripts" / "flux_one_shot.py"


def _local_enabled() -> bool:
    """Whether the user has opted into the local image backend.

    A heavy on-device generator must not silently become the active backend
    just because its script + libs exist. The user opts in via
    ``image_gen.local.enabled: true`` or by selecting ``image_gen.provider:
    local``. Defaults to False and never raises.
    """
    try:
        from hermes_cli.config import load_config

        cfg = load_config()
        ig = cfg.get("image_gen", {})
        if not isinstance(ig, dict):
            return False
        local = ig.get("local", {})
        enabled = isinstance(local, dict) and bool(local.get("enabled"))
        return enabled or ig.get("provider") == "local"
    except Exception:  # noqa: BLE001 — availability probe must never raise
        return False

# Model catalog — ids match the flux-local SKILL.md table.
_MODEL_DEV = "black-forest-labs/FLUX.1-dev"
_MODEL_SCHNELL = "black-forest-labs/FLUX.1-schnell"
_MODEL_FP8 = "Comfy-Org/flux1-dev-fp8.safetensors"
_DEFAULT_MODEL = _MODEL_SCHNELL  # fastest (guidance-distilled, few steps)

# Schnell is guidance-distilled: few steps, no CFG. Dev/fp8 need the full run.
_SCHNELL_STEPS = 4
_DEFAULT_STEPS = 28
_SCHNELL_GUIDANCE = 0.0
_DEFAULT_GUIDANCE = 3.5

# Generous ceiling — a cold run downloads/loads a multi-GB model on MPS.
_GENERATION_TIMEOUT_SECONDS = 600


class LocalImageGenProvider(ImageGenProvider):
    """On-device image generation via the flux-local one-shot script.

    Shells out to ``flux_one_shot.py`` (diffusers + MPS) so image generation
    needs no cloud API key. Text-to-image only.
    """

    @property
    def name(self) -> str:
        return "local"

    @property
    def display_name(self) -> str:
        return "Local (FLUX/MLX)"

    def is_available(self) -> bool:
        # Cheap: no heavy imports, no network. "Available" means the runtime can
        # actually generate — a python3 interpreter, the flux-local script, AND
        # the diffusers backend the script imports. Gating on diffusers (via
        # find_spec, which does not import it) keeps the picker honest: a bare
        # checkout with the script but no image stack is NOT a usable provider.
        if not _local_enabled():
            return False
        if not shutil.which("python3") or not _SCRIPT_PATH.is_file():
            return False
        return importlib.util.find_spec("diffusers") is not None

    def list_models(self) -> List[Dict[str, Any]]:
        return [
            {
                "id": _MODEL_SCHNELL,
                "display": "FLUX.1-schnell",
                "speed": "~fast (4 steps)",
                "strengths": "Fastest local FLUX; guidance-distilled turbo model.",
                "price": "free (local)",
            },
            {
                "id": _MODEL_DEV,
                "display": "FLUX.1-dev",
                "speed": "~slow (28 steps)",
                "strengths": "Highest-quality local FLUX; full guidance.",
                "price": "free (local)",
            },
            {
                "id": _MODEL_FP8,
                "display": "FLUX.1-dev (fp8)",
                "speed": "~medium (28 steps)",
                "strengths": "fp8-quantized dev — less RAM, near-dev quality.",
                "price": "free (local)",
            },
        ]

    def default_model(self) -> Optional[str]:
        return _DEFAULT_MODEL

    def get_setup_schema(self) -> Dict[str, Any]:
        # Local, on-device — no API key to prompt for.
        return {
            "name": self.display_name,
            "badge": "free",
            "tag": "On-device FLUX.1 (diffusers/MPS) — text-to-image, no cloud key",
            "env_vars": [],
        }

    def capabilities(self) -> Dict[str, Any]:
        # The one-shot script is text-to-image only.
        return {"modalities": ["text"], "max_reference_images": 0}

    def generate(
        self,
        prompt: str,
        aspect_ratio: str = DEFAULT_ASPECT_RATIO,
        *,
        image_url: Optional[str] = None,
        reference_image_urls: Optional[List[str]] = None,
        **kwargs: Any,
    ) -> Dict[str, Any]:
        """Generate an image on-device via ``flux_one_shot.py``.

        Never raises: any failure is reshaped into :func:`error_response`.
        """
        aspect = resolve_aspect_ratio(aspect_ratio)
        model = kwargs.get("model") or self.default_model() or _DEFAULT_MODEL

        if not self.is_available():
            return error_response(
                error=(
                    "Local image generation unavailable: python3 or the "
                    f"flux-local script ({_SCRIPT_PATH}) was not found."
                ),
                error_type="provider_unavailable",
                provider=self.name,
                model=model,
                prompt=prompt,
                aspect_ratio=aspect,
            )

        is_schnell = model == _MODEL_SCHNELL
        steps = _SCHNELL_STEPS if is_schnell else _DEFAULT_STEPS
        guidance = _SCHNELL_GUIDANCE if is_schnell else _DEFAULT_GUIDANCE

        try:
            out_dir = self._output_dir()
            out_path = out_dir / f"local_flux_{uuid.uuid4().hex[:8]}.png"

            command = [
                "python3",
                str(_SCRIPT_PATH),
                "--prompt",
                prompt,
                "--model",
                model,
                "--output",
                str(out_path),
                "--steps",
                str(steps),
                "--guidance",
                str(guidance),
            ]

            result = subprocess.run(  # noqa: S603 — fixed script, no shell
                command,
                timeout=_GENERATION_TIMEOUT_SECONDS,
                capture_output=True,
                text=True,
                stdin=subprocess.DEVNULL,
                check=False,
            )

            if result.returncode != 0:
                detail = (result.stderr or result.stdout or "").strip()[-500:]
                return error_response(
                    error=f"flux_one_shot.py exited {result.returncode}: {detail}",
                    error_type="generation_failed",
                    provider=self.name,
                    model=model,
                    prompt=prompt,
                    aspect_ratio=aspect,
                )

            if not out_path.is_file():
                detail = (result.stdout or result.stderr or "").strip()[-500:]
                return error_response(
                    error=f"flux_one_shot.py reported success but wrote no output file. {detail}",
                    error_type="missing_output",
                    provider=self.name,
                    model=model,
                    prompt=prompt,
                    aspect_ratio=aspect,
                )

            return success_response(
                image=str(out_path),
                model=model,
                prompt=prompt,
                aspect_ratio=aspect,
                provider=self.name,
                modality="text",
            )
        except subprocess.TimeoutExpired:
            return error_response(
                error=f"Local image generation timed out after {_GENERATION_TIMEOUT_SECONDS}s.",
                error_type="timeout",
                provider=self.name,
                model=model,
                prompt=prompt,
                aspect_ratio=aspect,
            )
        except Exception as exc:  # noqa: BLE001 — never raise out of generate
            logger.warning("Local image generation raised: %s", exc, exc_info=True)
            return error_response(
                error=f"Local image generation failed: {exc}",
                error_type=type(exc).__name__,
                provider=self.name,
                model=model,
                prompt=prompt,
                aspect_ratio=aspect,
            )

    @staticmethod
    def _output_dir() -> Path:
        """Return a writable directory for the generated PNG.

        Prefers the shared Hermes images cache so outputs land with the other
        providers'; falls back to a fresh temp dir when the cache helper is
        unavailable (e.g. HERMES_HOME not resolvable).
        """
        try:
            from agent.image_gen_provider import _images_cache_dir

            return _images_cache_dir()
        except Exception:  # noqa: BLE001 — defensive; temp dir always works
            return Path(tempfile.mkdtemp(prefix="hermes_local_imggen_"))


# ---------------------------------------------------------------------------
# Plugin entry point
# ---------------------------------------------------------------------------


def register(ctx) -> None:
    """Plugin entry point — wire ``LocalImageGenProvider`` into the registry."""
    ctx.register_image_gen_provider(LocalImageGenProvider())
