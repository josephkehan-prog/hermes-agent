#!/usr/bin/env python3
"""FLUX.1-dev / FLUX.1-schnell one-shot local image generator.

No ComfyUI server needed — downloads the model on first run, loads it with
diffusers, generates an image directly to disk. Uses MPS on Apple Silicon.

Usage:
    python3 flux_one_shot.py --prompt "..." [--model ...] [--output ./out.png]
    python3 flux_one_shot.py --prompt "..." --count 5 --randomize-seed
    python3 flux_one_shot.py --prompt "watercolor style" --input-image photo.png --strength 0.6

Requires: pip install diffusers accelerate safetensors torch (MPS build)
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path

# ---- Model defaults ----------------------------------------------------------

DEFAULT_MODEL = "black-forest-labs/FLUX.1-dev"
FP8_MODEL     = "Comfy-Org/flux1-dev-fp8.safetensors"
SCHNELL       = "black-forest-labs/FLUX.1-schnell"

# ---- Helpers -----------------------------------------------------------------

def safe_filename(name: str) -> str:
    """Sanitize a filename — no path traversal, no weird chars."""
    return os.path.basename(str(name)) or "output.png"


def resolve_device():
    """Pick the best device. Apple Silicon → MPS, else CPU (slow but works)."""
    import torch
    if torch.backends.mps.is_available() and torch.backends.mps.is_built():
        return torch.device("mps")
    return torch.device("cpu")


def check_deps():
    """Tell the user what's missing before they blame us."""
    missing = []
    try:
        import diffusers; print(f"diffusers {diffusers.__version__}")
    except ImportError:
        missing.append("diffusers (pip install diffusers)")
    try:
        import torch; print(f"torch {torch.__version__}")
    except ImportError:
        missing.append("torch (pip install torch --extra-index-url https://download.pytorch.org/whl/cpu)")

    if missing:
        print(f"\nMissing deps:\n  - " + "\n  - ".join(missing))
        sys.exit(1)


# ---- Generation --------------------------------------------------------------

def generate(prompt: str, model_id: str, output_path: Path,
             steps: int = 50, guidance: float = 3.5, seed=None,
             input_image=None, strength: float = 0.6, fp8: bool = False):
    """Run the diffusion pipeline end-to-end and save the result."""

    device = resolve_device()
    print(f"Device: {device}")
    print(f"Model:  {model_id}")
    if input_image:
        print(f"img2img: {input_image} (strength={strength})")

    t0 = time.time()

    # Lazy imports — first run may take a moment for download.
    import torch
    from diffusers import FluxPipeline, DiffusionPipeline
    from transformers import CLIPTextModel, CLIPTokenizer

    # ---- Build pipeline ----------------------------------------------------
    if model_id == FP8_MODEL or fp8:
        pipe = FluxPipeline.from_pretrained(
            "black-forest-labs/FLUX.1-dev",
            torch_dtype=torch.float16,
            variant="fp8",
        )
    elif model_id == SCHNELL:
        pipe = FluxPipeline.from_pretrained(
            "black-forest-labs/FLUX.1-schnell",
            torch_dtype=torch.bfloat16,
        )
    else:
        # Default dev — full precision
        pipe = FluxPipeline.from_pretrained(
            model_id,
            torch_dtype=torch.float16,
        )

    pipe.to(device)
    pipe.enable_model_cpu_offload()  # saves VRAM on M5 Max — still fast via MPS

    generator = torch.Generator(device=device).manual_seed(seed) if seed is not None else None

    # ---- Generate ----------------------------------------------------------
    if input_image:
        from PIL import Image
        img = Image.open(input_image).convert("RGB")
        result = pipe(
            prompt=prompt,
            image=img,
            strength=strength,
            num_inference_steps=steps,
            guidance_scale=guidance,
            generator=generator,
        ).images[0]
    else:
        result = pipe(
            prompt=prompt,
            num_inference_steps=steps,
            guidance_scale=guidance,
            generator=generator,
        ).images[0]

    # ---- Save --------------------------------------------------------------
    output_path.parent.mkdir(parents=True, exist_ok=True)
    result.save(output_path)
    elapsed = time.time() - t0

    print(f"\nSaved: {output_path}")
    print(f"Time:  {elapsed:.1f}s")

    # ---- JSON summary (for piping into other tools) ------------------------
    info = {
        "status": "success",
        "model": model_id,
        "prompt": prompt,
        "seed": seed if seed is not None else generator.initial_seed() if generator else -1,
        "steps": steps,
        "guidance": guidance,
        "output_files": [str(output_path)],
    }
    print(json.dumps(info))


# ---- Batch wrapper ----------------------------------------------------------

def batch_generate(prompts: list[str], model_id: str, output_dir: Path,
                   count: int = 1, seed_start=None):
    """Generate `count` images per prompt with varying seeds."""
    for i, prompt in enumerate(prompts):
        base = output_dir / f"{i+1:03d}"
        base.mkdir(parents=True, exist_ok=True)
        for j in range(count):
            seed = (seed_start + i * count + j) if seed_start is not None else -1
            out = base / safe_filename(f"gen_{i+1}_{j+1}.png")
            generate(prompt, model_id, out, seed=seed)


# ---- CLI ---------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="FLUX.1 local image generator — one-shot or batch.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument("--prompt", "-p", required=True, help="Text prompt")
    parser.add_argument("--model", "-m", default=DEFAULT_MODEL,
                        help=f"Model ID (default: {DEFAULT_MODEL})")
    parser.add_argument("--output", "-o", default="./flux_output.png",
                        help="Output file path (single run)")
    parser.add_argument("--output-dir", default=None,
                        help="Output directory (batch mode)")
    parser.add_argument("--steps", type=int, default=50,
                        help="Inference steps (default: 50)")
    parser.add_argument("--guidance", type=float, default=3.5,
                        help="Guidance scale (default: 3.5)")
    parser.add_argument("--seed", "-s", type=int or None, default=None,
                        help="Seed (-1 for random)")
    parser.add_argument("--input-image", default=None,
                        help="img2img input image path")
    parser.add_argument("--strength", type=float, default=0.6,
                        help="img2img strength (default: 0.6)")
    parser.add_argument("--count", "-c", type=int, default=1,
                        help="Number of variations (batch mode)")
    parser.add_argument("--randomize-seed", action="store_true",
                        help="Use random seed per variation")
    parser.add_argument("--fp8", action="store_true",
                        help="Use fp8 quantization for speed")
    parser.add_argument("--check-deps", action="store_true",
                        help="Check dependencies and exit")

    args = parser.parse_args()

    if args.check_deps:
        check_deps()
        return

    # Decide single vs batch
    output_path = Path(args.output)
    if args.count > 1 or args.randomize_seed:
        out_dir = Path(args.output_dir) or (output_path.parent / "flux_batch")
        prompts = [args.prompt] * args.count
        seed_start = args.seed
        batch_generate(prompts, args.model, out_dir, count=args.count,
                       seed_start=seed_start)
    else:
        generate(
            prompt=args.prompt,
            model_id=args.model,
            output_path=output_path,
            steps=args.steps,
            guidance=args.guidance,
            seed=args.seed,
            input_image=Path(args.input_image) if args.input_image else None,
            strength=args.strength,
        )


if __name__ == "__main__":
    main()
