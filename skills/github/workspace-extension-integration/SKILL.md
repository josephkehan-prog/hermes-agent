---
name: workspace-extension-integration
description: Adopt external repos as hermes plugins or tools.
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [GitHub, Repositories, Extensions, Plugins, Tools, Integration]
    related_skills: [github-repo-management]
---

# Workspace Extension Integration

Adopt external tools/repos into the hermes ecosystem as plugins/extensions/tools. Each step shows what to do and why.

## Prerequisites

- Git installed + authenticated (see `github-auth` skill)
- npm or pip available for dep install
- Target extension dir exists: `~/.pi/agent/extensions/`, `~/.hermes/plugins/`, or project-specific

---

## 1. Clone the Repo

```bash
# Standard clone into ~/mac (workspace root)
git clone https://github.com/owner/repo-name.git

# Or shallow clone for faster initial load
git clone --depth 1 https://github.com/owner/repo-name.git

# Clone into specific location under ~/.pi/extensions/ or similar
mkdir -p ~/.pi/agent/extensions && git clone https://github.com/owner/repo-name.git ~/.pi/agent/extensions/pi-webfetch
```

**Verify:** Check README for install instructions, check `package.json`/`pyproject.toml` for dep manager.

---

## 2. Install Dependencies

```bash
cd /path/to/cloned-repo

# For npm-based projects (TypeScript, Node)
npm install

# For Python projects (pip, uv, or venv)
pip install -e .
# OR: uv pip install -e .
# OR: python3 -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt

# Verify deps installed
ls node_modules/@scope/package 2>/dev/null || ls .venv/lib/python*/site-packages/package.py 2>/dev/null
```

**Verify:** Check for `node_modules/.package-lock.json` or `.venv/bin/python3` — if present, deps are in place.

---

## 3. Place in Extension/Plugin Dir

```bash
# For pi coding agent extensions: ~/.pi/agent/extensions/<name>
mv /path/to/cloned-repo ~/.pi/agent/extensions/pi-webfetch

# For hermes plugins: ~/.hermes/plugins/<name>
mv /path/to/cloned-repo ~/.hermes/plugins/hermes-tool-name

# For project-specific extensions (e.g., agentic-os/hub)
cp -r /path/to/cloned-repo ~/mac/agentic-os/hub/extensions/pi-webfetch
```

**Verify:** Confirm the cloned repo is now in the extension/plugin dir. Check README for placement instructions.

---

## 4. Smoke Test (Verify Working State)

```bash
# For Node-based extensions: load directly via entry point
node src/index.ts

# For Python-based tools: run script or import
python3 -c "import package_name; print(package_name.__version__)"

# For pi extensions: use `pi -e` to load in session
pi -e ./src/index.ts

# Or invoke the tool directly:
tool-name --help 2>&1 | head -5
```

**Verify:** Check for errors — if no errors, smoke test passed. If errors appear, note them (setup state, missing config, etc.) and fix accordingly.

---

## Pitfalls

- **Dependencies not installed yet:** `npm install` or `pip install -e .` must run before the tool works.
- **Wrong placement dir:** Each ecosystem has its own convention — check README for where to place extensions/plugins/tools.
- **Smoke test fails due to setup state:** Missing env vars, unconfigured credentials, or post-migration path mismatches are NOT durable rules — user can fix these. Capture the FIX (install command, config step) under an existing skill.
- **Runtime mismatch:** Some tools require specific Node versions (>=24 for ESM), Python versions (3.10+), or system binaries (ffmpeg, sqlite). Verify against README before assuming it works.

---

## Related Skills

- `github-repo-management` — clone/create/fork repos; manage remotes, releases.
- `hermes-agent` — configure hermes workspace, skills, plugins.
