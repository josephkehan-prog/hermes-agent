---
name: hermes-agent-skill-authoring
description: "Use when creating, revising, validating, or bundling Hermes skills in this repository. Covers trigger design, progressive disclosure, umbrella orchestration, member integrity, and repository validation."
version: 2.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [skills, authoring, bundles, umbrellas, validation]
    related_skills: [plan, requesting-code-review]
---

# Author Hermes Skills

## Overview

Create predictable, compact skills under `skills/<category>/<name>/`. Treat a
skill as behavioral instruction for another agent, not as general
documentation. Put only always-needed routing and procedure in `SKILL.md`;
keep detailed knowledge in `references/`, deterministic work in `scripts/`,
and output ingredients in `assets/` or `templates/`.

Hermes supports two useful shapes:

- **Capability skill:** owns one workflow, integration, or knowledge area.
- **Bundle skill:** orchestrates three or more existing skills into an
  end-to-end domain workflow without copying their implementation details.

## Source and Ownership

- In-repo skills live at `skills/<category>/<name>/SKILL.md` and ship with
  Hermes.
- User-local skills live under the active profile's `$HERMES_HOME/skills/`.
- Edit an existing skill in its owning tree. Do not create a user-local copy of
  an in-repo skill.
- Preserve every source skill package when creating a bundle. A bundle routes
  to members; it does not absorb or archive them unless consolidation was
  explicitly requested.

## Required Frontmatter

Start byte zero with `---` and include:

```yaml
---
name: concise-hyphen-name
description: "Use when <trigger>. <distinctive behavior>."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [short, useful, tags]
    related_skills: [existing-skill]
---
```

For a bundle, add `bundle: true` and use `related_skills` as the single
canonical member list:

```yaml
metadata:
  hermes:
    bundle: true
    domain: domain-name
    tags: [bundle, domain-name]
    related_skills: [member-one, member-two, member-three]
```

Give each bundle a stable `domain` identifier. Do not add a second `members`
list. One member inventory prevents metadata drift and also feeds Hermes'
learning graph.

Runtime constraints from `tools/skill_manager_tool.py`:

- name: at most 64 characters, lowercase letters/digits/hyphens
- description: at most 1024 characters
- complete file: at most 100,000 characters
- non-empty Markdown body after valid YAML frontmatter

Local-model context budget enforced by the in-repo validator (the whole body is
injected verbatim on invocation, so it must fit small context windows):

- body over 12,000 characters: validation ERROR — split detail into `references/`
- body over 8,000 characters: validation WARN — consider a `references/` split

## Authoring Workflow

### 1. Verify the premise

Inspect the target category, two or three peers, and any existing skill with a
similar trigger. Decide whether to extend an existing capability, create a new
capability, or create an orchestration bundle.

**Complete when:** the proposed trigger does not duplicate a peer and every
planned member exists in the repository.

### 2. Define concrete requests

Write three representative user requests and one counter-example. Use them to
shape the description because descriptions determine skill activation.

**Complete when:** the description identifies both the domain and the action
class, while the counter-example would not reasonably trigger it.

### 3. Set the degree of freedom

- Use prose and heuristics for judgment-heavy work.
- Use tables or pseudocode where routing should be consistent.
- Add a script only for repeated, deterministic, error-prone operations.

**Complete when:** fragile steps have explicit commands or checks and flexible
steps retain room for context-sensitive judgment.

### 4. Write for progressive disclosure

Keep the core loop in `SKILL.md`. Link directly to optional resources one level
below the skill root. Avoid repeating a rule in the body and a reference.

**Complete when:** the skill can route a normal request without loading any
reference, and every branch-specific resource has a clear read condition.

### 5. Validate behavior and package integrity

Run:

```bash
python skills/software-development/hermes-agent-skill-authoring/scripts/validate_skills.py \
  skills/<category>/<name>
```

For a bundle suite, pass every bundle directory in one invocation. The
validator checks frontmatter, names, ambiguous bundle-member identities,
bundle member count, member resolution, and self-references. Paths are required
so unrelated legacy skills cannot make a focused validation fail.

If the skill includes scripts, execute representative happy-path and failure
cases. If it changes a real integration or resolution chain, add an E2E test
against a temporary `HERMES_HOME`.

**Complete when:** deterministic validation passes and the evidence covers the
actual workflow, not merely file existence.

## Bundle Skill Contract

A bundle is a router and sequencer. It must contain these six elements:

1. **Boundary:** define the end-to-end outcome and explicit exclusions.
2. **Routing table:** map request types to one primary member skill.
3. **Sequence:** order only the members required for the request; never invoke
   every member by default.
4. **Handoff record:** carry inputs, outputs, evidence, decisions, and open
   risks between stages.
5. **Stop conditions:** pause on missing authority, unsafe scope, contradictory
   evidence, or a failed prerequisite.
6. **Completion gate:** prove each requested deliverable and surface-specific
   validation before claiming the bundle outcome.

### Bundle routing rules

- Load this bundle first, then load only the selected member instructions.
- Treat member skills as sources of truth for commands, APIs, and detailed
  procedures.
- Use the smallest member set that completes the request.
- Reuse one artifact/evidence ledger across stages instead of producing
  disconnected outputs.
- Do not silently substitute a related skill when the selected member's
  prerequisite fails; report the failed gate and choose a documented fallback.

### Bundle anti-patterns

- Copying member instructions into the bundle
- Listing related skills without explaining routing or handoffs
- Running all members for every request
- Inventing a new core tool to connect steps already expressible via skills
- Claiming an end-to-end result from one stage's unit-level check
- Referencing optional-only or user-local members from a bundled in-repo skill

## Editing Existing Skills

Prefer replacement over sediment. When adding a stronger rule, remove the old
weaker wording. Preserve scripts, references, templates, assets, and relative
links. For a major rewrite, compare the old and new trigger boundaries before
editing so useful cases are not lost.

## Common Pitfalls

1. **Generic activation text:** describe the actual request classes, not
   merely the topic.
2. **No-op prose:** replace "be careful" with a checkable gate.
3. **Snapshot validation:** assert relationships and invariants rather than a
   fixed global skill count.
4. **Broken package moves:** never move only `SKILL.md` when its resources or
   relative links remain elsewhere.
5. **Phantom members:** every in-repo bundle member must resolve to a current
   in-repo `name:` value.
6. **Current-session cache confusion:** newly installed local skills may need
   `/reload-skills`; direct source validation does not.

## Verification Checklist

- [ ] Trigger and counter-trigger are distinct from peers
- [ ] Frontmatter and directory name agree
- [ ] Description is trigger-focused and within the runtime limit
- [ ] Always-needed procedure stays concise
- [ ] Resources are linked directly and loaded conditionally
- [ ] Scripts were executed on representative cases
- [ ] Bundle has `bundle: true` and at least three resolving members
- [ ] Bundle defines routing, sequence, handoff, stop, and completion gates
- [ ] Source member packages remain intact
- [ ] `validate_skills.py` passes for every created or modified skill
