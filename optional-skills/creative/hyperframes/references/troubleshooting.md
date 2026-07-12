# Troubleshooting

## `HeadlessExperimental.beginFrame' wasn't found` (first thing to check)

**Symptom:** `npx hyperframes render` fails with:

```
✗ Render failed
Protocol error (HeadlessExperimental.beginFrame):
'HeadlessExperimental.beginFrame' wasn't found
```

**Cause:** Chromium 147+ removed the `HeadlessExperimental.beginFrame` CDP command. This affected sandbox environments (e.g., OpenClaw, some containerized agent hosts) that ship modern Chromium as the system browser. See [hyperframes#294](https://github.com/heygen-com/hyperframes/issues/294).

**Fix (permanent — preferred):** upgrade.

```bash
npx hyperframes upgrade -y
# or
npm install -g hyperframes@latest
```

`hyperframes >= 0.4.2` auto-detects whether the resolved browser supports `beginFrame` (checks for `chrome-headless-shell` in the binary path) and falls back to screenshot capture mode when it doesn't. Commit [`4c72ba4`](https://github.com/heygen-com/hyperframes/commit/4c72ba4a36ec2bd6733f7b9cb2a9e63f9fb234b9) (March 2026) shipped this auto-detect.

**Fix (escape hatch — if you can't upgrade):**

```bash
export PRODUCER_FORCE_SCREENSHOT=true
npx hyperframes render
```

This forces screenshot mode regardless of the binary. Screenshot mode is slightly slower but visually identical.

**Fix (prevent — recommended):** install `chrome-headless-shell` so the engine can use the fast BeginFrame path:

```bash
npx puppeteer browsers install chrome-headless-shell
# or let the CLI do it
npx hyperframes browser --install
```

`scripts/setup.sh` runs this automatically.

## `npx hyperframes render` hangs for 120s then times out

**Cause:** the resolved browser is system Chrome (e.g., `/usr/bin/google-chrome`) and doesn't support the BeginFrame path, but auto-detect also missed it (older `hyperframes` version).

**Fix:**
1. Check which binary is being used: `npx hyperframes browser --path`
2. If it's system Chrome, either:
   - Install `chrome-headless-shell`: `npx hyperframes browser --install`, OR
   - Set the escape hatch: `export PRODUCER_FORCE_SCREENSHOT=true`, OR
   - Upgrade: `npx hyperframes upgrade -y`

## `ffmpeg: command not found`

Install FFmpeg via your system package manager:

| OS / distro     | Command                             |
| --------------- | ----------------------------------- |
| Ubuntu / Debian | `sudo apt-get install -y ffmpeg`    |
| Fedora / RHEL   | `sudo dnf install -y ffmpeg`        |
| Arch            | `sudo pacman -S ffmpeg`             |
| macOS           | `brew install ffmpeg`               |
| Windows         | `winget install Gyan.FFmpeg`        |

Verify: `ffmpeg -version`.

## `Node version X is not supported`

HyperFrames requires Node.js >= 22. Check with `node --version`.

- **nvm:** `nvm install 22 && nvm use 22`
- **Homebrew (macOS):** `brew install node@22 && brew link --overwrite node@22`
- **apt:** follow [nodesource](https://github.com/nodesource/distributions) for Node 22 LTS.

## `ENOSPC: no space left on device` or OOM kills during render

Renders are memory- and disk-hungry. Minimums:

- **RAM:** 4 GB free (8 GB recommended for 60fps / `--quality high`)
- **Disk:** 2 GB free scratch space — frames are written to `/tmp` during capture

Mitigations:
- Lower quality: `--quality draft`.
- Lower fps: `--fps 24`.
- Lower worker count: `--workers 1`.
- Set `TMPDIR` to a volume with more space: `export TMPDIR=/mnt/scratch`.

## Lint passes but the render is blank / black frames

Check the browser console in `preview` — usually:
- A timeline was registered with the wrong key (`__timelines["typo"]` instead of `__timelines["root"]`).
- The root composition was wrapped in `<template>` (only sub-compositions use `<template>`).
- A script tag failed to load — check Network tab in preview.

Run `npx hyperframes lint --verbose` to see info-level findings.

## Contrast warnings from `hyperframes validate`

```
⚠ WCAG AA contrast warnings (3):
  · .subtitle "secondary text" — 2.67:1 (need 4.5:1, t=5.3s)
```

- **Dark backgrounds:** brighten the failing color until it clears 4.5:1 (normal text) or 3:1 (large text — 24px+ or 19px+ bold).
- **Light backgrounds:** darken it.
- Stay within the palette family — don't invent a new color, adjust the existing one.
- Skip the check temporarily with `--no-contrast` if iterating rapidly, but clear it before delivery.

## `Font family 'X' not supported by compiler`

The compiler embeds a curated set of web-safe + open-source fonts. If a font isn't supported, either:
- Swap to a supported alternative from the warning.
- Register a custom font via `@font-face` pointing to a `.woff2` in the project directory (the compiler embeds referenced `@font-face` files).

## Video plays back muted or with no audio

Check:
- The `<video>` element has `muted playsinline` (required — browser autoplay policy).
- Audio is a **separate** `<audio>` element, not the video element.
- Audio `data-volume` is set (defaults to 1).
- The audio file is at the expected path — compositions load relative to their own directory.

## Docker render fails on Linux with rootless Docker

Add `--privileged` or pass `--cap-add=SYS_ADMIN`:

```bash
npx hyperframes render --docker --docker-args "--cap-add=SYS_ADMIN"
```

The headless browser needs namespace permissions for sandboxing.

## Bug reports

Include `npx hyperframes info` output + the full error log. File at [github.com/heygen-com/hyperframes](https://github.com/heygen-com/hyperframes/issues).

## Composition pitfalls (full detail)

- **`repeat: -1` anywhere** breaks the capture engine. Always compute a finite repeat count: `repeat: Math.ceil(duration / cycleDuration) - 1`.
- **`gsap.set()` on clip elements that enter later** — the element doesn't exist at page load. Use `tl.set(selector, vars, timePosition)` inside the timeline instead, at or after the clip's `data-start`.
- **`<br>` inside content text** — forced breaks don't know the rendered font width, so natural wrap + `<br>` double-breaks. Use `max-width` to let text wrap. Exception: short display titles where each word is deliberately on its own line.
- **Animating `visibility` or `display`** — GSAP can't tween these. Use `autoAlpha` (handles both visibility and opacity).
- **Calling `video.play()` or `audio.play()`** — the framework owns playback. Never call these yourself.
- **Building timelines async** — the capture engine reads `window.__timelines` synchronously after page load. Never wrap timeline construction in `async`, `setTimeout`, or a Promise.
- **Standalone `index.html` wrapped in `<template>`** — hides all content from the browser. Only **sub-compositions** loaded via `data-composition-src` use `<template>`.
- **Using video for audio** — always muted `<video>` + separate `<audio>`.

## Verification checklist (full detail)

Before and after rendering:

1. **Lint + validate + inspect pass:** `npx hyperframes lint --strict && npx hyperframes validate && npx hyperframes inspect` (lint catches structural issues, validate catches contrast, inspect catches visual layout / overflow issues).
2. **Animation choreography** — for new compositions or significant animation changes, run the animation map (copied project-local by `npx hyperframes init`):
   ```bash
   node skills/hyperframes/scripts/animation-map.mjs <composition-dir> \
     --out <composition-dir>/.hyperframes/anim-map
   ```
   Outputs a single `animation-map.json` with per-tween summaries, ASCII Gantt timeline, stagger detection, dead zones (>1s with no animation), element lifecycles, and flags (`offscreen`, `collision`, `invisible`, `paced-fast` <0.2s, `paced-slow` >2s). Scan summaries and flags — fix or justify each. Skip on small edits.
3. **File exists + non-zero:** `ls -lh final.mp4`.
4. **Duration matches `data-duration`:** `ffprobe -v error -show_entries format=duration -of default=nw=1:nk=1 final.mp4`.
5. **Visual check:** extract a mid-composition frame: `ffmpeg -i final.mp4 -ss 00:00:05 -vframes 1 preview.png`.
6. **Audio present if expected:** `ffprobe -v error -show_streams -select_streams a -of default=nw=1:nk=1 final.mp4 | head -1`.

If `hyperframes render` fails, run `npx hyperframes doctor` and attach its output when reporting.
