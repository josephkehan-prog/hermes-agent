---
title: "Github Repo Management — Clone/create/fork repos; manage remotes, releases"
sidebar_label: "Github Repo Management"
description: "Clone/create/fork repos; manage remotes, releases"
---

{/* This page is auto-generated from the skill's SKILL.md by website/scripts/generate-skill-docs.py. Edit the source SKILL.md, not this page. */}

# Github Repo Management

Clone/create/fork repos; manage remotes, releases.

## Skill metadata

| | |
|---|---|
| Source | Bundled (installed by default) |
| Path | `skills/github/github-repo-management` |
| Version | `1.1.0` |
| Author | Hermes Agent |
| License | MIT |
| Platforms | linux, macos, windows |
| Tags | `GitHub`, `Repositories`, `Git`, `Releases`, `Secrets`, `Configuration` |
| Related skills | [`github-auth`](/docs/user-guide/skills/bundled/github/github-github-auth), [`github-pr-workflow`](/docs/user-guide/skills/bundled/github/github-github-pr-workflow), [`github-issues`](/docs/user-guide/skills/bundled/github/github-github-issues) |

## Reference: full SKILL.md

:::info
The following is the complete skill definition that Hermes loads when this skill is triggered. This is what the agent sees as instructions when the skill is active.
:::

# GitHub Repository Management

Create, clone, fork, configure, and manage GitHub repositories. Each section shows `gh` first, then the `git` + `curl` fallback.

## Prerequisites

- Authenticated with GitHub (see `github-auth` skill)

### Setup

```bash
if command -v gh &>/dev/null && gh auth status &>/dev/null; then
  AUTH="gh"
else
  AUTH="git"
  if [ -z "$GITHUB_TOKEN" ]; then
    if _hermes_env="${HERMES_HOME:-$HOME/.hermes}/.env"; [ -f "$_hermes_env" ] && grep -q "^GITHUB_TOKEN=" "$_hermes_env"; then
      GITHUB_TOKEN=$(grep "^GITHUB_TOKEN=" "$_hermes_env" | head -1 | cut -d= -f2 | tr -d '\n\r')
    elif grep -q "github.com" ~/.git-credentials 2>/dev/null; then
      GITHUB_TOKEN=$(grep "github.com" ~/.git-credentials 2>/dev/null | head -1 | sed 's|https://[^:]*:\([^@]*\)@.*|\1|')
    fi
  fi
fi

# Get your GitHub username (needed for several operations)
if [ "$AUTH" = "gh" ]; then
  GH_USER=$(gh api user --jq '.login')
else
  GH_USER=$(curl -s -H "Authorization: token $GITHUB_TOKEN" https://api.github.com/user | python3 -c "import sys,json; print(json.load(sys.stdin)['login'])")
fi
```

If you're inside a repo already:

```bash
REMOTE_URL=$(git remote get-url origin)
OWNER_REPO=$(echo "$REMOTE_URL" | sed -E 's|.*github\.com[:/]||; s|\.git$||')
OWNER=$(echo "$OWNER_REPO" | cut -d/ -f1)
REPO=$(echo "$OWNER_REPO" | cut -d/ -f2)
```

---

## 1. Cloning Repositories

Cloning is pure `git` — works identically either way:

```bash
# Clone via HTTPS (works with credential helper or token-embedded URL)
git clone https://github.com/owner/repo-name.git

# Clone into a specific directory
git clone https://github.com/owner/repo-name.git ./my-local-dir

# Shallow clone (faster for large repos)
git clone --depth 1 https://github.com/owner/repo-name.git

# Clone a specific branch
git clone --branch develop https://github.com/owner/repo-name.git

# Clone via SSH (if SSH is configured)
git clone git@github.com:owner/repo-name.git
```

**With gh (shorthand):**

```bash
gh repo clone owner/repo-name
gh repo clone owner/repo-name -- --depth 1
```

## 2. Creating Repositories

**With gh:**

```bash
# Create a public repo and clone it
gh repo create my-new-project --public --clone

# Private, with description and license
gh repo create my-new-project --private --description "A useful tool" --license MIT --clone

# Under an organization
gh repo create my-org/my-new-project --public --clone

# From existing local directory
cd /path/to/existing/project
gh repo create my-project --source . --public --push

# From a template
gh repo create my-new-app --template owner/template-repo --public --clone
```

**Without `gh`:** creating a repo, creating under an org, and creating from a
template are all API calls needing `git init`/`git remote add` afterward —
full commands in `references/curl-fallbacks.md#creating-repositories`.

## 3. Forking Repositories

**With gh:**

```bash
gh repo fork owner/repo-name --clone
```

**Without `gh`:** fork via `POST /repos/{owner}/{repo}/forks`, then `git clone`
+ `git remote add upstream` — full commands in
`references/curl-fallbacks.md#forking-repositories`.

### Keeping a Fork in Sync

```bash
# Pure git — works everywhere
git fetch upstream
git checkout main
git merge upstream/main
git push origin main
```

**With gh (shortcut):**

```bash
gh repo sync $GH_USER/repo-name
```

## 4. Repository Information

**With gh:**

```bash
gh repo view owner/repo-name
gh repo list --limit 20
gh search repos "machine learning" --language python --sort stars
```

**Without `gh`:** repo detail/list/search are all `GET` calls piped through a
small `python3 -c` parser — full snippets in
`references/curl-fallbacks.md#repository-information`.

## 5. Repository Settings

**With gh:**

```bash
gh repo edit --description "Updated description" --visibility public
gh repo edit --enable-wiki=false --enable-issues=true
gh repo edit --default-branch main
gh repo edit --add-topic "machine-learning,python"
gh repo edit --enable-auto-merge
```

**Without `gh`:** `PATCH /repos/{owner}/{repo}` for settings, `PUT .../topics`
for topics — full snippets in
`references/curl-fallbacks.md#repository-settings`.

## 6. Branch Protection

No `gh` shorthand for this — always API. View with
`GET /repos/{owner}/{repo}/branches/main/protection`, set with `PUT` on the
same endpoint (`required_status_checks`, `required_pull_request_reviews`,
etc.). Full request bodies: `references/curl-fallbacks.md#branch-protection`.

## 7. Secrets Management (GitHub Actions)

**With gh:**

```bash
gh secret set API_KEY --body "your-secret-value"
gh secret set SSH_KEY < ~/.ssh/id_rsa
gh secret list
gh secret delete API_KEY
```

**Without `gh`:** secrets must be encrypted with the repo's public key
(libsodium sealed box) before `PUT`ting — meaningfully more involved than the
other fallbacks. Full Python encryption snippet:
`references/curl-fallbacks.md#secrets-management-github-actions`. If `gh`
isn't available and secrets are needed, recommend installing it for just this
operation.

## 8. Releases

**With gh:**

```bash
gh release create v1.0.0 --title "v1.0.0" --generate-notes
gh release create v2.0.0-rc1 --draft --prerelease --generate-notes
gh release create v1.0.0 ./dist/binary --title "v1.0.0" --notes "Release notes"
gh release list
gh release download v1.0.0 --dir ./downloads
```

**Without `gh`:** `POST /repos/{owner}/{repo}/releases` to create,
`uploads.github.com/.../assets` to attach binaries — full snippets in
`references/curl-fallbacks.md#releases`.

## 9. GitHub Actions Workflows

**With gh:**

```bash
gh workflow list
gh run list --limit 10
gh run view <RUN_ID>
gh run view <RUN_ID> --log-failed
gh run rerun <RUN_ID>
gh run rerun <RUN_ID> --failed
gh workflow run ci.yml --ref main
gh workflow run deploy.yml -f environment=staging
```

**Without `gh`:** list workflows/runs, download failed logs, rerun, and
`workflow_dispatch` are all separate endpoints — full snippets in
`references/curl-fallbacks.md#github-actions-workflows`.

## 10. Gists

**With gh:**

```bash
gh gist create script.py --public --desc "Useful script"
gh gist list
```

**Without `gh`:** `POST /gists` to create, `GET /gists` to list — full
snippets in `references/curl-fallbacks.md#gists`.

## Quick Reference Table

| Action | gh | git + curl |
|--------|-----|-----------|
| Clone | `gh repo clone o/r` | `git clone https://github.com/o/r.git` |
| Create repo | `gh repo create name --public` | `curl POST /user/repos` |
| Fork | `gh repo fork o/r --clone` | `curl POST /repos/o/r/forks` + `git clone` |
| Repo info | `gh repo view o/r` | `curl GET /repos/o/r` |
| Edit settings | `gh repo edit --...` | `curl PATCH /repos/o/r` |
| Create release | `gh release create v1.0` | `curl POST /repos/o/r/releases` |
| List workflows | `gh workflow list` | `curl GET /repos/o/r/actions/workflows` |
| Rerun CI | `gh run rerun ID` | `curl POST /repos/o/r/actions/runs/ID/rerun` |
| Set secret | `gh secret set KEY` | `curl PUT /repos/o/r/actions/secrets/KEY` (+ encryption) |
