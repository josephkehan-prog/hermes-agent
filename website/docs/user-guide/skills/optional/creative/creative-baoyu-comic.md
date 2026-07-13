---
title: "Baoyu Comic — Knowledge comics (知识漫画): educational, biography, tutorial"
sidebar_label: "Baoyu Comic"
description: "Knowledge comics (知识漫画): educational, biography, tutorial"
---

{/* This page is auto-generated from the skill's SKILL.md by website/scripts/generate-skill-docs.py. Edit the source SKILL.md, not this page. */}

# Baoyu Comic

Knowledge comics (知识漫画): educational, biography, tutorial.

## Skill metadata

| | |
|---|---|
| Source | Optional — install with `hermes skills install official/creative/baoyu-comic` |
| Path | `optional-skills/creative/baoyu-comic` |
| Version | `1.56.1` |
| Author | 宝玉 (JimLiu) |
| License | MIT |
| Platforms | linux, macos, windows |
| Tags | `comic`, `knowledge-comic`, `creative`, `image-generation` |

## Reference: full SKILL.md

:::info
The following is the complete skill definition that Hermes loads when this skill is triggered. This is what the agent sees as instructions when the skill is active.
:::

# Knowledge Comic Creator

Adapted from [baoyu-comic](https://github.com/JimLiu/baoyu-skills) for Hermes Agent's tool ecosystem.

Create original knowledge comics with flexible art style × tone combinations.

## When to Use

Trigger this skill when the user asks to create a knowledge/educational comic, biography comic, tutorial comic, or uses terms like "知识漫画", "教育漫画", or "Logicomix-style". The user provides content (text, file path, URL, or topic) and optionally specifies art style, tone, layout, aspect ratio, or language.

## Reference Images

Hermes' `image_generate` tool is **prompt-only** — it does **NOT** accept reference images. When the user supplies one, extract its traits **in text** (style / palette / scene) and embed them in the relevant page prompt(s); record the source in that page's prompt frontmatter. Character consistency instead comes from text descriptions in `characters/characters.md`, embedded inline in every page prompt.

Intake rules, the usage-mode table (`style`/`palette`/`scene`), and the frontmatter recording format: read `references/reference-images.md` when the user provides a reference image.

## Options

### Visual Dimensions

| Option | Values | Description |
|--------|--------|-------------|
| Art | ligne-claire (default), manga, realistic, ink-brush, chalk, minimalist | Art style / rendering technique |
| Tone | neutral (default), warm, dramatic, romantic, energetic, vintage, action | Mood / atmosphere |
| Layout | standard (default), cinematic, dense, splash, mixed, webtoon, four-panel | Panel arrangement |
| Aspect | 3:4 (default, portrait), 4:3 (landscape), 16:9 (widescreen) | Page aspect ratio |
| Language | auto (default), zh, en, ja, etc. | Output language |
| Refs | File paths | Reference images used for style / palette trait extraction (not passed to the image model). See [Reference Images](#reference-images) above. |

### Partial Workflow Options

| Option | Description |
|--------|-------------|
| Storyboard only | Generate storyboard only, skip prompts and images |
| Prompts only | Generate storyboard + prompts, skip images |
| Images only | Generate images from existing prompts directory |
| Regenerate N | Regenerate specific page(s) only (e.g., `3` or `2,5,8`) |

Details: [references/partial-workflows.md](https://github.com/NousResearch/hermes-agent/blob/main/optional-skills/creative/baoyu-comic/references/partial-workflows.md)

### Art, Tone & Preset Catalogue

- **Art styles** (6): `ligne-claire`, `manga`, `realistic`, `ink-brush`, `chalk`, `minimalist`. Full definitions at `references/art-styles/<style>.md`.
- **Tones** (7): `neutral`, `warm`, `dramatic`, `romantic`, `energetic`, `vintage`, `action`. Full definitions at `references/tones/<tone>.md`.
- **Presets** (5) with special rules beyond plain art+tone:

  | Preset | Equivalent | Hook |
  |--------|-----------|------|
  | `ohmsha` | manga + neutral | Visual metaphors, no talking heads, gadget reveals |
  | `wuxia` | ink-brush + action | Qi effects, combat visuals, atmospheric |
  | `shoujo` | manga + romantic | Decorative elements, eye details, romantic beats |
  | `concept-story` | manga + warm | Visual symbol system, growth arc, dialogue+action balance |
  | `four-panel` | minimalist + neutral + four-panel layout | 起承转合 structure, B&W + spot color, stick-figure characters |

  Full rules at `references/presets/<preset>.md` — load the file when a preset is picked.

- **Compatibility matrix** and **content-signal → preset** table live in [references/auto-selection.md](https://github.com/NousResearch/hermes-agent/blob/main/optional-skills/creative/baoyu-comic/references/auto-selection.md). Read it before recommending combinations in Step 2.

## File Structure

Output directory: `comic/{topic-slug}/`
- Slug: 2-4 words kebab-case from topic (e.g., `alan-turing-bio`)
- Conflict: append timestamp (e.g., `turing-story-20260118-143052`)

**Contents**:
| File | Description |
|------|-------------|
| `source-{slug}.md` | Saved source content (kebab-case slug matches the output directory) |
| `analysis.md` | Content analysis |
| `storyboard.md` | Storyboard with panel breakdown |
| `characters/characters.md` | Character definitions |
| `characters/characters.png` | Character reference sheet (downloaded from `image_generate`) |
| `prompts/NN-{cover\|page}-[slug].md` | Generation prompts |
| `NN-{cover\|page}-[slug].png` | Generated images (downloaded from `image_generate`) |
| `refs/NN-ref-{slug}.{ext}` | User-supplied reference images (optional, for provenance) |

## Language Handling

**Detection Priority**:
1. User-specified language (explicit option)
2. User's conversation language
3. Source content language

**Rule**: Use user's input language for ALL interactions:
- Storyboard outlines and scene descriptions
- Image generation prompts
- User selection options and confirmations
- Progress updates, questions, errors, summaries

Technical terms remain in English.

## Workflow

### Progress Checklist

```
Comic Progress:
- [ ] Step 1: Setup & Analyze
  - [ ] 1.1 Analyze content
  - [ ] 1.2 Check existing directory
- [ ] Step 2: Confirmation - Style & options ⚠️ REQUIRED
- [ ] Step 3: Generate storyboard + characters
- [ ] Step 4: Review outline (conditional)
- [ ] Step 5: Generate prompts
- [ ] Step 6: Review prompts (conditional)
- [ ] Step 7: Generate images
  - [ ] 7.1 Generate character sheet (if needed) → characters/characters.png
  - [ ] 7.2 Generate pages (with character descriptions embedded in prompt)
- [ ] Step 8: Completion report
```

### Flow

```
Input → Analyze → [Check Existing?] → [Confirm: Style + Reviews] → Storyboard → [Review?] → Prompts → [Review?] → Images → Complete
```

### Step Summary

| Step | Action | Key Output |
|------|--------|------------|
| 1.1 | Analyze content | `analysis.md`, `source-{slug}.md` |
| 1.2 | Check existing directory | Handle conflicts |
| 2 | Confirm style, focus, audience, reviews | User preferences |
| 3 | Generate storyboard + characters | `storyboard.md`, `characters/` |
| 4 | Review outline (if requested) | User approval |
| 5 | Generate prompts | `prompts/*.md` |
| 6 | Review prompts (if requested) | User approval |
| 7.1 | Generate character sheet (if needed) | `characters/characters.png` |
| 7.2 | Generate pages | `*.png` files |
| 8 | Completion report | Summary |

### User Questions

Use the `clarify` tool to confirm options. Since `clarify` handles one question at a time, ask the most important question first and proceed sequentially. See [references/workflow.md](https://github.com/NousResearch/hermes-agent/blob/main/optional-skills/creative/baoyu-comic/references/workflow.md) for the full Step 2 question set.

**Timeout handling (CRITICAL)**: `clarify` can return `"The user did not provide a response within the time limit. Use your best judgement to make the choice and proceed."` — this is NOT user consent to default everything.

- Treat it as a default **for that one question only**. Continue asking the remaining Step 2 questions in sequence; each question is an independent consent point.
- **Surface the default to the user visibly** in your next message so they have a chance to correct it: e.g. `"Style: defaulted to ohmsha preset (clarify timed out). Say the word to switch."` — an unreported default is indistinguishable from never having asked.
- Do NOT collapse Step 2 into a single "use all defaults" pass after one timeout. If the user is genuinely absent, they will be equally absent for all five questions — but they can correct visible defaults when they return, and cannot correct invisible ones.

### Step 7: Image Generation

Use Hermes' built-in `image_generate` tool for all image rendering. Its schema accepts only `prompt` and `aspect_ratio` (`landscape` | `portrait` | `square`); it **returns a URL**, not a local file. Every generated page or character sheet must therefore be downloaded to the output directory.

**Prompt file requirement (hard)**: write each image's full, final prompt to a standalone file under `prompts/` (naming: `NN-{type}-[slug].md`) BEFORE calling `image_generate`. The prompt file is the reproducibility record.

**Never rely on shell CWD persistence for `-o` paths (hard rule).** The terminal tool's persistent-shell CWD can change between batches (session expiry, `TERMINAL_LIFETIME_SECONDS`, a failed `cd` that leaves you in the wrong directory). `curl -o relative/path.png` is a silent footgun: if CWD has drifted, the file lands somewhere else with no error. **Always pass a fully-qualified absolute path to `-o`**, or pass `workdir=<abs path>` to the terminal tool. Incident Apr 2026: pages 06-09 of a 10-page comic landed at the repo root instead of `comic/<slug>/` because batch 3 inherited a stale CWD from batch 2. The agent then spent several turns claiming the files existed where they didn't.

**Backup rule**: existing `prompts/…md` and `…png` files → rename with `-backup-YYYYMMDD-HHMMSS` suffix before regenerating.

Aspect-ratio mapping, the full download procedure, and the 7.1 character-sheet vs 7.2 pages split (character sheet is a human-facing review artifact only — page prompts already embed character text from Step 5, and `image_generate` never takes image input): read `references/workflow.md` § Step 7 before generating images.

Full step-by-step workflow (analysis, storyboard, review gates, regeneration variants): [references/workflow.md](https://github.com/NousResearch/hermes-agent/blob/main/optional-skills/creative/baoyu-comic/references/workflow.md).

## References

**Core Templates**:
- [analysis-framework.md](https://github.com/NousResearch/hermes-agent/blob/main/optional-skills/creative/baoyu-comic/references/analysis-framework.md) - Deep content analysis
- [character-template.md](https://github.com/NousResearch/hermes-agent/blob/main/optional-skills/creative/baoyu-comic/references/character-template.md) - Character definition format
- [storyboard-template.md](https://github.com/NousResearch/hermes-agent/blob/main/optional-skills/creative/baoyu-comic/references/storyboard-template.md) - Storyboard structure
- [ohmsha-guide.md](https://github.com/NousResearch/hermes-agent/blob/main/optional-skills/creative/baoyu-comic/references/ohmsha-guide.md) - Ohmsha manga specifics

**Style Definitions**:
- `references/art-styles/` - Art styles (ligne-claire, manga, realistic, ink-brush, chalk, minimalist)
- `references/tones/` - Tones (neutral, warm, dramatic, romantic, energetic, vintage, action)
- `references/presets/` - Presets with special rules (ohmsha, wuxia, shoujo, concept-story, four-panel)
- `references/layouts/` - Layouts (standard, cinematic, dense, splash, mixed, webtoon, four-panel)

**Workflow**:
- [workflow.md](https://github.com/NousResearch/hermes-agent/blob/main/optional-skills/creative/baoyu-comic/references/workflow.md) - Full workflow details
- [auto-selection.md](https://github.com/NousResearch/hermes-agent/blob/main/optional-skills/creative/baoyu-comic/references/auto-selection.md) - Content signal analysis
- [partial-workflows.md](https://github.com/NousResearch/hermes-agent/blob/main/optional-skills/creative/baoyu-comic/references/partial-workflows.md) - Partial workflow options

## Page Modification

| Action | Steps |
|--------|-------|
| **Edit** | **Update prompt file FIRST** → regenerate image → download new PNG |
| **Add** | Create prompt at position → generate with character descriptions embedded → renumber subsequent → update storyboard |
| **Delete** | Remove files → renumber subsequent → update storyboard |

**IMPORTANT**: When updating pages, ALWAYS update the prompt file (`prompts/NN-{cover|page}-[slug].md`) FIRST before regenerating. This ensures changes are documented and reproducible.

## Pitfalls

- Image generation: 10-30 seconds per page; auto-retry once on failure
- **Always download** the URL returned by `image_generate` to a local PNG — downstream tooling (and the user's review) expects files in the output directory, not ephemeral URLs
- **Use absolute paths for `curl -o`** — never rely on persistent-shell CWD across batches. Silent footgun: files land in the wrong directory and subsequent `ls` on the intended path shows nothing. See Step 7 "Download step".
- Use stylized alternatives for sensitive public figures
- **Step 2 confirmation required** - do not skip
- **Steps 4/6 conditional** - only if user requested in Step 2
- **Step 7.1 character sheet** - recommended for multi-page comics, optional for simple presets. The PNG is a review/regeneration aid; page prompts (written in Step 5) use the text descriptions in `characters/characters.md`, not the PNG. `image_generate` does not accept images as visual input
- **Strip secrets** — scan source content for API keys, tokens, or credentials before writing any output file
