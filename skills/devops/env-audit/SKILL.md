---
name: env-audit
description: Check env vars for missing, unused, or drifted keys.
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    domain: devops
    tags: [env, dotenv, config, audit, secrets]
    related_skills: [dependency-audit, git-hygiene]
---

# Env Audit

## Boundary

Report drift between a project's declared environment variables and what its
code actually uses. Use for finding missing, unused, or undocumented keys. Do
not use to set values, rotate secrets, or deploy config.

## Never Print Values

This skill reads files that hold secrets. Report only KEY NAMES and file
locations — never a value, not even a partial or masked one. If asked to show a
value, refuse and explain that this skill audits names only.

## Inputs

Locate these in the project root (ask if ambiguous):

| File | Role |
|---|---|
| `.env` | Actual local values (secret — names only) |
| `.env.example` / `.env.sample` / `.env.template` | Declared/expected keys |
| Source code | Where keys are read (`os.environ`, `process.env`, `getenv`, etc.) |

## Procedure

1. Parse `.env` and the example file into two SETS of key names. Ignore blank
   lines and `#` comments. A key is the text left of the first `=`.
2. Grep the source for env reads. Cover the project's languages:
   - Python: `os.environ["X"]`, `os.environ.get("X")`, `os.getenv("X")`
   - Node: `process.env.X`, `process.env["X"]`
   - Shell: `$X` / `${X}` in scripts
   Collect the referenced key names into a third set.
3. Compute and report three lists:
   - **Missing**: referenced in code OR listed in the example, but absent from `.env`.
   - **Unused**: present in `.env` but never referenced in code.
   - **Undocumented**: in `.env` but not in the example file.
4. For each finding give the key name and the file:line where the evidence is.

## Rules

1. Names only, always (see "Never Print Values").
2. Do not treat a key as unused solely because a plain grep missed it — note
   dynamic access patterns (`os.environ[var]` with a computed `var`) as
   "cannot verify" rather than "unused".
3. Report counts and the three lists even when a list is empty ("0 missing").
4. Read-only. Never write to `.env` or any file.

## Stop Conditions

- No `.env` and no example file found: say so, list any env reads found in
  code as the expected-key set instead.
- Binary or unparseable `.env`: report it, do not guess.

## Completion Gate

Done when the three lists (missing / unused / undocumented) are reported with
counts and file:line evidence, and no value was printed.
