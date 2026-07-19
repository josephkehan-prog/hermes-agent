#!/usr/bin/env python3
"""Build SKILL_MODEL_INDEX.{json,md} — a grep-based catalog tagging every
skill by the local model / specialist role it invokes (or 'agnostic').

A skill is listed under EVERY model/role it references (a skill can touch
several lanes, e.g. a creative skill using Cydonia as writer + qwen3-coder
as controller). 'agnostic' = calls no local model (external APIs / tooling).
'unspecified-endpoint' = hits a local endpoint but names no model — a hygiene
flag to pin it to a route ID.

Run: python3 skills/scripts/build_skill_model_index.py
Regenerate after adding/removing a model or migrating a skill.
"""
import json, re
from pathlib import Path
from collections import defaultdict

ROOT = Path(__file__).resolve().parents[1]  # skills/
ROUTE_IDS = ["ornith-uncensored", "qwen3-coder", "reranker"]
ROLES = ["code", "controller", "research", "think", "vision-fast", "writer", "extract"]
OLLAMA = {"cydonia": "cydonia", "qwythos": "qwythos", "bge-m3": "bge-m3",
          "nomic-embed": "nomic", "qwen3-embedding": "qwen3-embed",
          "qwen3-reranker": "qwen3-rerank"}

def desc(md):
    try: t = md.read_text(encoding="utf-8", errors="ignore")
    except Exception: return ""
    m = re.search(r'^description:\s*(.+?)\s*$', t, re.M)
    if m: return m.group(1).strip().strip('"\'')
    for ln in t.splitlines():
        ln = ln.strip()
        if ln and not ln.startswith(("#", "---", "name:", "metadata")): return ln[:140]
    return ""

def classify(folder):
    text = ""
    for f in folder.rglob("*"):
        if f.is_file() and f.suffix in (".md", ".py", ".sh", ".json"):
            try: text += f.read_text(encoding="utf-8", errors="ignore")
            except Exception: pass
    tl = text.lower()
    tags = set()
    if "hermes-specialist" in tl:
        for r in ROLES:
            if re.search(rf"\brun {r}\b|\"{r}\"|`{r}`", tl): tags.add(f"role:{r}")
        if not any(t.startswith("role:") for t in tags): tags.add("specialist")
    for rid in ROUTE_IDS:
        if rid in tl: tags.add(f"model:{rid}")
    for name, short in OLLAMA.items():
        if name in tl: tags.add(f"model:{short}")
    # Only flag skills that hit the Hermes llama-swap port (:1235) without
    # naming a model. Generic multi-provider tools and teaching docs that
    # mention :8080 / :11434 / example model names (llama3.2, gpt-4o) are
    # provider-agnostic, not Hermes-stack routers — leave them agnostic.
    if not tags and ("localhost:1235" in tl or "127.0.0.1:1235" in tl):
        tags.add("model:unspecified-endpoint")
    if not tags: tags.add("agnostic")
    return sorted(tags)

skills = []
for md in sorted(ROOT.rglob("SKILL.md")):
    rel = str(md.parent.relative_to(ROOT))
    skills.append({"skill": rel, "tags": classify(md.parent), "what": desc(md)})

json.dump({"skills": skills}, open(ROOT / "SKILL_MODEL_INDEX.json", "w"), indent=1)

by = defaultdict(list); agn = []
for s in skills:
    if s["tags"] == ["agnostic"]: agn.append(s); continue
    for t in s["tags"]:
        if t.startswith(("model:", "role:", "specialist")): by[t].append(s)

LABEL = {
 "model:ornith-uncensored": "BASE — ornith-uncensored (Qwen3.6-35B-A3B huihui, vision, :1235)",
 "model:qwen3-coder": "CODER — qwen3-coder (Qwen3-Coder-30B-A3B huihui, :1235)",
 "model:cydonia": "WRITER — Cydonia-24B (Ollama)", "model:qwythos": "RESEARCH — Qwythos-9B (Ollama)",
 "model:qwen3-embed": "EMBED — Qwen3-Embedding", "model:nomic": "EMBED — nomic-embed-text",
 "model:bge-m3": "EMBED — bge-m3", "model:reranker": "RERANK — Qwen3-Reranker (:1235)",
 "model:qwen3-rerank": "RERANK — Qwen3-Reranker (Ollama)",
 "model:unspecified-endpoint": "⚠ UNSPECIFIED — endpoint but no named model (pin to a route ID)",
}
for r in ROLES: LABEL[f"role:{r}"] = f"specialist role `{r}`"
LABEL["specialist"] = "specialist (role unclear)"

def rowline(s):
    w = s.get("what", "").replace("|", "\\|")
    return f"- `{s['skill']}` — {w}" if w else f"- `{s['skill']}`"

L = ["# Skill → Model Index", "",
     f"_Auto-generated. {len(skills)} skills · {len(agn)} agnostic · {len(skills)-len(agn)} model-touching._", "",
     "Each skill tagged by the local model / specialist role it invokes (or **agnostic**), with what it does. A skill appears under every lane it references. Regenerate: `python3 skills/scripts/build_skill_model_index.py`.", "",
     "## By specialist role (preferred — model-indirect)", ""]
for t in sorted(k for k in LABEL if k.startswith(("role:", "specialist"))):
    if t in by:
        L.append(f"### {LABEL[t]}")
        L += [rowline(s) for s in sorted(by[t], key=lambda x: x["skill"])] + [""]
L += ["## By model / route ID (direct)", ""]
for t in ["model:ornith-uncensored", "model:qwen3-coder", "model:cydonia", "model:qwythos",
          "model:reranker", "model:qwen3-rerank", "model:qwen3-embed", "model:nomic",
          "model:bge-m3", "model:unspecified-endpoint"]:
    if t in by:
        L.append(f"### {LABEL[t]}")
        L += [rowline(s) for s in sorted(by[t], key=lambda x: x["skill"])] + [""]
L += ["## Model-agnostic (no local model)", "",
      f"{len(agn)} skills — external APIs, pure tooling, or docs.", "",
      "<details><summary>list</summary>", ""]
L += [rowline(s) for s in sorted(agn, key=lambda x: x["skill"])]
L += ["", "</details>"]
(ROOT / "SKILL_MODEL_INDEX.md").write_text("\n".join(L), encoding="utf-8")
print(f"wrote SKILL_MODEL_INDEX.md ({len(L)} lines) + .json ({len(skills)} skills)")
