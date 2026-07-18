---
name: image-edit
description: Edit images locally with sips or ImageMagick.
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [macos]
prerequisites:
  commands: [sips]
metadata:
  hermes:
    tags: [Image, Media, Edit, Resize, Convert, ImageMagick, sips]
---

# Image Edit (local CLI)

Edit images with local command-line tools. All offline, no API keys.

## Routing rules — read first

- There is **no `image_edit` MCP tool** anywhere in the agent-hub registry (verified 2026-07-17). Do not call `tool_call` with invented names like `sqm:image_edit` or `squish-memory:image_edit` — squish-memory is a **memory server only** (remember/recall/pin/forget); a "gateway policy denied" there means the tool does not exist, not a routing problem.
- Do not file `instinct_report` entries mapping image tasks to nonexistent tools.
- Task-to-tool map:
  - **Pixel edits** (resize, crop, convert, strip EXIF) → `sips` or ImageMagick below.
  - **Text-in-image edits** (change embedded text: dates, labels, signs) → OCR text-replacement below (`pytesseract` + PIL).
  - **Generate a new image** → the abliterated Z-Image lane below.
  - **Analyze an image** (OCR, faces, classify, document bounds) → hub `macos-vision › *`.
  - **Search for images online** → hub `brave-search › brave_image_search`.
  - **Model-based semantic edit** (remove/replace objects, restyle) → NOT installed. The Qwen-Image-Edit lane was removed 2026-07-17 (69GB, unquantized). Re-pull only if a real workflow needs it.

## Image generation lane (Apple MLX, local, abliterated — added 2026-07-17)

```bash
# Generation with abliterated prompt encoder (Z-Image-Turbo, ~15s at 512px)
mflux-generate-z-image-turbo --model ~/models/z-image-turbo-abliterated \
  --base-model z-image-turbo --quantize 8 --steps 9 \
  --width 1024 --height 1024 --prompt "…" --output out.png
```

`~/models/z-image-turbo-abliterated` is a symlink mirror (encoder: BennyDaBall
AbliteratedV1). Do not delete the underlying `~/models/z-image-abliterated-encoder`
or the HF cache copy of Z-Image-Turbo — the mirror points into them.

Note: bare `mflux-generate` (FLUX default) no longer works — FLUX weights were
pruned 2026-07-17. Use `mflux-generate-z-image-turbo` for generation.

## Tools available on this machine

- `sips` — built into macOS (`/usr/bin/sips`). Fast for resize/rotate/convert.
- `magick` — ImageMagick via Homebrew (`/opt/homebrew/bin/magick`). Full editing: crop, compose, annotate, filters.
- `ffmpeg` — for video frames and animated formats.

## Common operations

```bash
# Resize to max 1024px on the long side (keeps aspect)
sips -Z 1024 in.png --out out.png

# Convert format
sips -s format jpeg in.png --out out.jpg

# Rotate 90° clockwise
sips -r 90 in.jpg --out out.jpg

# Crop to WxH from center (ImageMagick)
magick in.png -gravity center -crop 800x600+0+0 +repage out.png

# Composite watermark bottom-right
magick base.png wm.png -gravity southeast -geometry +10+10 -composite out.png

# Strip metadata (EXIF/GPS) before sharing
magick in.jpg -strip out.jpg

# Quality/size compression
magick in.jpg -quality 82 out.jpg

# Extract video frame at 5s
ffmpeg -ss 5 -i in.mp4 -frames:v 1 frame.png
```

## OCR-based text replacement (pytesseract + PIL)

For cases where text is embedded in the image (e.g., dates, labels):
- Use `pytesseract` to find character-level bounding boxes via `image_to_data(Output.DICT)`.
- Draw over old text with a white rectangle.
- Draw new text with `ImageDraw.text()` using a suitable font.
- Verify with OCR.
- See [references/ocr-text-replacement.md](references/ocr-text-replacement.md) for full details.

## Rules

- Never edit in place — always write to a new output file; keep the original.
- Strip metadata (`-strip`) before sending any photo off-machine.
- Batch: loop with quoted globs; verify one output before running the full batch.
