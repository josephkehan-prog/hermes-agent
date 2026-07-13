# Hermes Agent Path Verification

When writing files into hermes-agent repo, verify location first. Don't assume `mac/Hermes/` is the same as `.hermes/hermes-agent/`.

## Methods (in order of preference)

### 1. `hermes config show | grep Install`
```bash
hermes config show | grep Install
# Output: /Users/josephhan/.hermes/hermes-agent
```
This is the canonical answer for hermes-agent specifically. Always check this first when writing into hermes repo.

### 2. `find . -name ".git" | grep <project>`
```bash
find . -maxdepth 4 -name ".git" -type d | grep hermes
# Returns multiple repos: ./mac/hermes-war-room/.git, ./mac/hermes-skill-factory/.git, ./.hermes/hermes-agent/.git
```
Use when you're in deep user home and want to see ALL git repos that match.

### 3. `cd <assumed-path> && git status`
If path doesn't exist (or is empty), you know it's wrong immediately. Use as sanity check before writing anything.

## Common mistake

Writing files to `mac/Hermes/hermes-agent/skills/creative/novel-generator/SKILL.md` when hermes-agent actually lives at `.hermes/hermes-agent/skills/creative/novel-generator/SKILL.md`. Git can't see the file in wrong path — must re-write after user says "git" or similar.

## Verification checklist

- [ ] Path verified via `hermes config show`, `find . -name ".git"`, or `git status`
- [ ] File written to correct location (not wrong path)