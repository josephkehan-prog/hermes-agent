---
name: repo-location-discovery
description: Verify where a project lives before writing files.
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [repo, location, discovery, config, path-verify, git-repo]
    related_skills: [hermes-agent-skill-authoring, github-repo-management]
---

# Repo Location Discovery

Use this skill when you need to write files into a project repo but aren't sure where it actually lives. The most common case: hermes-agent's skills directory — is it under `mac/Hermes/`? Or `.hermes/hermes-agent/`? Both are git repos on different paths.

## Core Method

```
verify path → write file → commit (if desired)
```

### 1. Verify the actual repo location before writing anything

Three methods, in order of preference:

**Method A — `hermes config show`**
```bash
hermes config show | grep Install
# Shows: /Users/josephhan/.hermes/hermes-agent
```
This is the canonical answer for hermes-agent specifically.

**Method B — `find . -name ".git" | grep <project>`**
```bash
find . -maxdepth 4 -name ".git" -type d | grep hermes
# Returns: ./mac/hermes-war-room/.git, ./mac/hermes-skill-factory/.git, ./mac/hermes-agent-self-evolution/.git, ./.hermes/hermes-agent/.git
```
Use when you're in a deep user home and want to see ALL git repos that match.

**Method C — `cd <assumed-path> && git status`**
If the path doesn't exist (or is empty), you know it's wrong immediately. Use this as a sanity check before writing anything.

### 2. Pick the correct location and write

After verifying, use the confirmed path:
```bash
write_file(path="/Users/josephhan/.hermes/hermes-agent/skills/creative/novel-generator/SKILL.md")
```

### 3. Git add + commit (if desired)

```bash
cd /Users/josephhan/.hermes/hermes-agent && git add skills/creative/novel-generator/SKILL.md && git status --short && git commit -m "add: novel-generator skill"
```

## Pitfalls

1. **Assuming `mac/Hermes/` is the same as `.hermes/hermes-agent/`.** They are both hermes-agent, but they live on different paths and git sees them as separate repos. Writing a file to one doesn't make it visible in the other.
2. **Writing files without verifying path.** If you write to wrong path, user has to say "git" or similar to fix it — prevent that by checking first via `hermes config show | grep Install` or a quick `find . -name ".git"`.
3. **Checking only one method.** Use `hermes config show` for hermes-agent; use `find . -name ".git"` when exploring deeper. Don't assume the first check is enough without cross-verifying.

## Verification Checklist

- [ ] Path verified via `hermes config show`, `find . -name ".git"`, or `git status`
- [ ] File written to correct location (not wrong path)
- [ ] Git add + commit completed if desired (or user told not to commit)