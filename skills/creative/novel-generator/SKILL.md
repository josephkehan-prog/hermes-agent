---
name: novel-generator
description: "Generate full novels autonomously via Claude Code or Codex — one-shot creative writing agents that plan, draft chapters, and deliver a complete manuscript without human-in-the-loop each turn."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [novel, fiction, creative-writing, autonomous-agent, story-generation, manuscript, chapters]
    related_skills: [claude-code, codex, humanizer, songwriting-and-ai-music]
---

# Novel Generator — Autonomous Manuscript Generation

Use this skill when the user wants to **produce a complete novel** by delegating writing to an autonomous coding/writing agent. The agent plans structure, drafts each chapter, maintains continuity, and delivers a finished manuscript — no per-chapter human approval required.

Load this when the user says things like "write me a novel about X", "generate a full story from this concept", "autonomous novel writing", "build a manuscript end-to-end", or "have Claude/Codex write a book for me".

## When NOT to use this

- User wants a short scene or snippet — keep it small, don't inflate
- User wants collaborative drafting with human feedback each turn (use interactive Claude Code)
- User wants a specific genre they know the agent will miss (e.g., hard sci-fi where the user knows physics details are wrong) — warn them first

## Prerequisites

1. **Claude Code** installed (`npm install -g @anthropic-ai/claude-code`) with auth configured, OR
2. **Codex** available, or another autonomous agent capable of long-form output
3. A working terminal where the writer runs (any project directory)

## Core Method

```
concept → outline → draft chapters → consistency pass → deliver manuscript
```

### 1. Concept Intake

Get from the user: **genre**, **tone**, and a **seed idea**. One question at a time, not all three at once:

1. **"What genre or style?"** — fantasy, sci-fi, literary fiction, thriller, romance, etc.
2. **"What tone should it lean toward?"** — dark, hopeful, satirical, contemplative, fast-paced?
3. **"What's the seed idea or premise?"** — one sentence is enough to start.

Reflect each answer briefly before asking the next. If the user gives all three upfront, skip straight to outline.

### 2. Outline Generation (one-shot)

Have the agent produce a chapter-by-chapter outline as a single file `OUTLINE.md`. Each entry includes:
- Chapter number and title
- POV character(s) per chapter
- Key events / turning point
- Emotional arc for that chapter
- Continuity notes (what happened before, what must happen next)

The agent writes the outline itself — don't hand-hold each chapter. The outline is the contract; chapters are obligations to it.

### 3. Chapter Drafting Loop

Run the writer in **print mode** (`-p`) for each chapter, OR run one long session that produces all chapters sequentially:

```bash
# Option A: One session writes everything
terminal(command="cd /path/to/novel && claude -p 'Read OUTLINE.md and write every chapter. Output each as a separate .md file named chapter-NN.md. Maintain continuity across chapters. The outline is your contract — follow it.' --max-turns 50", timeout=300)

# Option B: Per-chapter loop (more reliable for very long novels)
for i in $(seq 1 $NUM_CHAPTERS); do
  terminal(command="cd /path/to/novel && claude -p 'Read OUTLINE.md. Write chapter-$i.md according to the outline entry for that chapter.' --max-turns 5", timeout=120)
done
```

**Key rules:**
- Each chapter file is standalone `.md` — one chapter per file, named `chapter-NN.md`
- The agent reads previous chapters when writing a new one (continuity check)
- Use `--max-turns` generously for each chapter (5-10 per chapter is typical; 30-50 if doing all at once)
- Set `workdir` to the novel project so files land in the right place

### 4. Consistency Pass

After all chapters are written, run a final pass:

```bash
terminal(command="cd /path/to/novel && claude -p 'Read every chapter file. Check continuity: character names consistent? timelines coherent? plot threads resolved? Fix any issues you find.' --max-turns 10", timeout=180)
```

This is a **read-only review** — the agent reads each chapter and fixes inconsistencies it finds in-place. Don't require human approval of each fix; trust the writer to self-correct.

### 5. Deliver

Combine all chapters into a final manuscript file (e.g., `MANUSCRIPT.md` or `.txt`) and report what was produced:
- Total chapter count
- Approximate word count (`wc -w *.md | tail -1`)
- Any issues the consistency pass caught and fixed

## File Layout

```
novel-project/
├── OUTLINE.md          # Generated plan
├── chapter-01.md       # Each chapter as its own file
├── chapter-02.md
│   ...
└── MANUSCRIPT.md       # Final assembled output (optional)
```

## Tips for Quality

1. **Give a specific seed, not a vague prompt.** "A detective in 1940s Chicago hunting a serial killer who leaves origami cranes at each crime scene" beats "write me a mystery."
2. **If the novel is long (>30 chapters), use per-chapter loop** — one session for all chapters risks context degradation and dropped chapters.
3. **Set `--allowedTools Read,Edit,Bash`** so the writer can read its own output to check continuity.
4. **Use `--output-format json`** if you want structured delivery (each chapter as a JSON object with content field).
5. **Run consistency pass after each chunk of ~10 chapters** for very long novels — catches drift before it deepens.

## Pitfalls

1. **Agent writes every chapter in the same voice.** If output feels flat, run a second pass: "rewrite chapters 3-7 in more varied stylistic voices."
2. **Characters merge or forget names mid-story.** Consistency pass is mandatory — don't skip it.
3. **One session goes too long and hallucinates plot.** For >20 chapters, chunk into groups of 5-10 sessions with a consistency check between each group.
4. **Forgetting to set `workdir`.** Chapters land in the wrong place if you don't point it at the project directory.
5. **Not telling the agent about the outline.** The writer needs to read OUTLINE.md explicitly — otherwise it writes off-the-cuff and ignores the plan.

## Verification Checklist

- [ ] All chapters written as separate numbered `.md` files
- [ ] Outline followed (each chapter matches its outline entry)
- [ ] Consistency pass completed — names, timelines, plot threads coherent
- [ ] Word count reported (`wc -w *.md`)
- [ ] User told what genre/tone was targeted and that they should review for their personal taste

## One-Shot Recipe: Quick Novel from a Prompt

```bash
# 1. Create project dir
mkdir -p ~/tmp/novel && cd ~/tmp/novel

# 2. Have agent plan + write everything in one shot
terminal(command="cd ~/tmp/novel && claude -p 'You are writing a novel about: [SEED IDEA]. Genre: [GENRE]. Tone: [TONE]. Create OUTLINE.md with chapter-by-chapter structure, then write every chapter as chapter-NN.md. Follow the outline exactly.' --allowedTools Read,Edit,Bash --max-turns 50", timeout=300)

# 3. Consistency pass
terminal(command="cd ~/tmp/novel && claude -p 'Read all chapter files. Fix any continuity issues you find.' --max-turns 10", timeout=180)

# 4. Count words
terminal(command="wc -w ~/tmp/novel/chapter-*.md | tail -1")
```
