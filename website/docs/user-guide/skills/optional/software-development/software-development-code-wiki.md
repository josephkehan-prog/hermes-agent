---
title: "Code Wiki — Generate wiki docs + Mermaid diagrams for any codebase"
sidebar_label: "Code Wiki"
description: "Generate wiki docs + Mermaid diagrams for any codebase"
---

{/* This page is auto-generated from the skill's SKILL.md by website/scripts/generate-skill-docs.py. Edit the source SKILL.md, not this page. */}

# Code Wiki

Generate wiki docs + Mermaid diagrams for any codebase.

## Skill metadata

| | |
|---|---|
| Source | Optional — install with `hermes skills install official/software-development/code-wiki` |
| Path | `optional-skills/software-development/code-wiki` |
| Version | `0.1.0` |
| Author | Teknium (teknium1), Hermes Agent |
| License | MIT |
| Platforms | linux, macos, windows |
| Tags | `Documentation`, `Mermaid`, `Architecture`, `Diagrams`, `Wiki`, `Code-Analysis` |
| Related skills | [`codebase-inspection`](/docs/user-guide/skills/bundled/github/github-codebase-inspection), [`github-repo-management`](/docs/user-guide/skills/bundled/github/github-github-repo-management) |

## Reference: full SKILL.md

:::info
The following is the complete skill definition that Hermes loads when this skill is triggered. This is what the agent sees as instructions when the skill is active.
:::

# Code Wiki Skill

Generate a comprehensive wiki for any codebase — overview, architecture, per-module deep-dives, Mermaid class and sequence diagrams. Inspired by Google CodeWiki, but works on local repos, private repos, and any language. Uses only existing Hermes tools (`terminal`, `read_file`, `search_files`, `write_file`); no Docker, no external services, no extra dependencies.

This skill produces **reference documentation** (what/how). It does not produce strategic narrative (why — that's a different skill).

## When to Use

- User says "document this codebase", "generate a wiki", "make architecture diagrams"
- Onboarding to an unfamiliar repo and wants a structured reference
- User points at a GitHub URL and asks for documentation
- Need a stable artifact (markdown + Mermaid) that renders on GitHub

Do NOT use this for:
- Single-file or single-function documentation — just answer directly
- API reference for one specific endpoint — use `read_file` and answer inline
- Strategic "why does this exist" narrative — different skill, different purpose
- Codebases the user is actively developing in this session — just answer questions as they come

## Prerequisites

- No env vars required.
- `git` on PATH for repo SHA tracking and remote clones.
- Optional: `pygount` for language-breakdown stats (see the `codebase-inspection` skill).

## How to Run

Invoke through the `terminal` tool from the target repo's root, then use `read_file` / `search_files` / `write_file` to produce the wiki. Default output location is `~/.hermes/wikis/<repo-name>/`. Only write into the repo (`docs/wiki/`) when the user explicitly requests it.

## Quick Reference

| Step | Action |
|---|---|
| 1 | Resolve target — local cwd, given path, or `git clone --depth 50 <url>` to a temp dir |
| 2 | Scan structure — `ls`, `find -maxdepth 3`, manifest files, README |
| 3 | Pick 8–10 modules to document |
| 4 | Write `README.md` (overview + module map) |
| 5 | Write `architecture.md` with Mermaid flowchart |
| 6 | Write per-module docs in `modules/` |
| 7 | Write `diagrams/class-diagram.md` (Mermaid classDiagram) |
| 8 | Write `diagrams/sequences.md` (Mermaid sequenceDiagram, 2–4 workflows) |
| 9 | Write `getting-started.md` |
| 10 | Write `api.md` if applicable, else skip |
| 11 | Write `.codewiki-state.json` |
| 12 | Report paths to user |

## Procedure

### 1. Resolve the target

For a GitHub URL:

```bash
WIKI_TMP=$(mktemp -d)
git clone --depth 50 <url> "$WIKI_TMP/repo"
cd "$WIKI_TMP/repo"
REPO_SHA=$(git rev-parse HEAD)
REPO_NAME=$(basename <url> .git)
```

For a local path (or cwd if none given):

```bash
cd <path>
REPO_SHA=$(git rev-parse HEAD 2>/dev/null || echo "uncommitted")
REPO_NAME=$(basename "$PWD")
```

Then set the output dir:

```bash
OUTPUT_DIR="$HOME/.hermes/wikis/$REPO_NAME"
mkdir -p "$OUTPUT_DIR/modules" "$OUTPUT_DIR/diagrams"
```

### 2. Scan repo structure

Use the `terminal` tool for the shell work, `read_file` for manifests:

```bash
# Shallow tree first
ls -la

# Deeper tree, noise filtered
find . -type d \
  -not -path '*/\.*' \
  -not -path '*/node_modules*' \
  -not -path '*/venv*' \
  -not -path '*/__pycache__*' \
  -not -path '*/dist*' \
  -not -path '*/build*' \
  -not -path '*/target*' \
  -maxdepth 3 | sort

# Language breakdown (skip if pygount unavailable)
pygount --format=summary \
  --folders-to-skip=".git,node_modules,venv,.venv,__pycache__,.cache,dist,build,target" \
  . 2>/dev/null || true
```

Then `read_file` the relevant manifests (`package.json`, `pyproject.toml`, `setup.py`, `Cargo.toml`, `go.mod`, `pom.xml`, `build.gradle`) and the project README. Use `search_files target='files'` to find them rather than guessing names.

### 3. Pick modules to document

Cap initial pass at **8–10 modules**. Heuristics by language:

- Python: top-level packages (dirs with `__init__.py`), plus subsystem dirs
- JS/TS: `src/<subdir>`, top-level workspace dirs
- Rust: each crate in a workspace, or top-level `src/<module>` dirs
- Go: each top-level package directory
- Mixed/unfamiliar: top-level directories that contain source code (not config, not tests)

For very large repos, prioritize by:
1. Imported-from count (a module imported by many is core)
2. LOC (bigger modules usually warrant their own doc)
3. Mentions in README / top-level docs

State the module list to the user before generating per-module docs on big repos — gives them a chance to redirect.

### 4–10. Write the wiki files

Write, in order: `README.md` (overview + module map), `architecture.md`
(system shape + Mermaid flowchart), per-module docs in `modules/`,
`diagrams/class-diagram.md` (Mermaid classDiagram), `diagrams/sequences.md`
(Mermaid sequenceDiagram, 2–4 workflows), `getting-started.md`, and `api.md`
(skip if not a library/API server).

**Read `references/templates.md` before writing any of these** — it has the
exact markdown template, section-by-section, for every file above, plus the
Mermaid shape-semantics legend (`[]`=component, `[()]`=storage, `{{}}`=external
service, `(())`=entry point) and node-count caps.

Ground rules that apply across all of them: `read_file` the real source before
writing any claim — never invent a function, class, or call path. For link
targets, use relative paths in local mode and
`https://github.com/<owner>/<repo>/blob/<sha>/<path>` for cloned repos so
links survive future commits. Don't force a class diagram onto a language
without classes (Go, C) — use prose in architecture.md instead.

### 11. Write the state file

```bash
cat > "$OUTPUT_DIR/.codewiki-state.json" <<EOF
{
  "repo_name": "$REPO_NAME",
  "source_path": "$PWD",
  "source_sha": "$REPO_SHA",
  "generated_at": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
  "generator": "hermes-agent code-wiki skill v0.1.0",
  "modules_documented": []
}
EOF
```

### 12. Report to user

State exactly what was generated and where:

```
Generated wiki at ~/.hermes/wikis/<repo-name>/:
  README.md                   project overview, module map
  architecture.md             system architecture + flowchart
  getting-started.md          setup, first run, workflows
  modules/<N files>           per-module deep-dives
  diagrams/architecture.md    Mermaid flowchart
  diagrams/class-diagram.md   Mermaid class diagram
  diagrams/sequences.md       Mermaid sequence diagrams
```

If you cloned to a temp dir, remind the user it can be removed (`rm -rf "$WIKI_TMP"`) after they've reviewed the wiki.

## Scope Control

Generating a full wiki for a 500K-LOC monorepo is wildly token-expensive. Default to bounded scope:

- Initial scan: max depth 3 directories
- Per-module docs: cap at 10 modules unless user expands scope
- Per-file reads: prefer `search_files` for symbols + `read_file` with `offset`/`limit` over full reads
- Skip vendored code (`vendor/`, `third_party/`, generated code, `_pb2.py`, `.min.js`)

If the user says "do the whole thing exhaustively", believe them — but ballpark the cost first: "this repo has ~340 source files, comprehensive coverage will be expensive — confirm?"

## Re-Run / Update

If `.codewiki-state.json` already exists at the target path, read it for the
previous SHA and module list: same SHA → ask whether to regenerate or skip;
different SHA → offer to regenerate only modules with changed files
(`git diff --name-only <old-sha> HEAD`). Full detail and the
future-enhancement note: read `references/troubleshooting.md`.

## Pitfalls (hard rules)

- **Fabricating components.** Every diagram node and claimed function call must be in the source. `read_file` before writing — the single biggest failure mode for auto-generated docs is plausible-sounding fabrication.
- **Generic AI prose / restating code as prose.** Say what the module actually does in domain-specific terms; don't narrate the obvious.
- **Mermaid > 50 nodes** don't render legibly — split them. **Special chars need quotes** (`A["Tool / Agent"]`). **classDiagram generics** render as `~T~`, not `<T>`. No `%%{init: ...}%%` blocks (GitHub strips them).
- **Don't document tests, generated code, or vendored deps** as product code.
- **In-repo output without asking.** Default is `~/.hermes/wikis/`; only write into the repo when explicitly requested.

Full gotcha list (nested-fence handling, etc.): read `references/troubleshooting.md`.

## Verification

After writing, check: Mermaid fences balance (opens × 2 = total per file), all
expected files/dirs exist, module count matches Step 3's commitment, and 2–3
source links resolve to real files. Exact commands for each check: read
`references/troubleshooting.md`.
