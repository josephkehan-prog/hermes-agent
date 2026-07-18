---
name: dockerfile-lint
description: Lint a Dockerfile for security, correctness, and size.
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    domain: devops
    tags: [docker, dockerfile, security, lint, containers]
    related_skills: [dependency-audit, git-hygiene]
---

# Dockerfile Lint

## Boundary

Review a Dockerfile and report concrete issues with the line each is on. Use to
audit a Dockerfile, not to build or run the image. Do not invent findings for a
clean file — report "no issues" when there are none.

## Checklist

Read the Dockerfile top to bottom and check each item. Report the line number
and the exact instruction for every finding.

### Security (report as HIGH)

| Check | Problem |
|---|---|
| `USER` directive present | No `USER` → container runs as root; add a non-root user |
| Secrets in `ENV`/`ARG` | API keys, passwords, tokens baked into layers are recoverable |
| `ADD` with a URL | Use `curl`+checksum or `COPY`; `ADD` from URL is unverified |
| `curl … \| sh` | Piping remote scripts to a shell runs unverified code |
| `--privileged`/cap hints | Note any privilege escalation the file assumes |

### Correctness & reproducibility (report as MEDIUM)

| Check | Problem |
|---|---|
| Base image tag | `FROM x:latest` or no tag → non-reproducible; pin a version/digest |
| `apt-get install` without `--no-install-recommends` and cleanup | Bloats image; and update+install must be one `RUN` (cache poisoning) |
| Package manager cache left | `rm -rf /var/lib/apt/lists/*` (apt) / `--no-cache` (apk) missing |
| `COPY . .` before dependency install | Busts the dependency cache on every source change |
| Missing `WORKDIR` | Relative paths become ambiguous |

### Image size (report as LOW)

| Check | Problem |
|---|---|
| Multi-stage opportunity | Build tools shipped in the final image |
| Many `RUN` layers | Consecutive `RUN`s that could be a single layer |

## Procedure

1. Read the file. Identify the base image and its tag.
2. Walk each instruction; match against the checklist.
3. For each finding: line number, the instruction text, the problem, and the
   one-line fix.
4. Group findings by severity (HIGH → MEDIUM → LOW). Report counts.

## Rules

1. Cite the exact line number and instruction for every finding — no vague
   "somewhere you should...".
2. Do not flag a practice the file already follows (e.g. don't say "pin the
   base" when it is pinned).
3. Never claim to have built or scanned the image; this is static review only.

## Stop Conditions

- Input is not a Dockerfile (no `FROM`): say so, do not guess.
- Multi-stage file: review each stage; attribute findings to their stage.

## Completion Gate

Done when every finding has line + instruction + fix, findings are grouped by
severity with counts, and a clean file is reported as "no issues" rather than
padded with speculative ones.
