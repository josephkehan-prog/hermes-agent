# Grok Build CLI — Workflow Patterns & Pitfalls

Copy-paste patterns for audit notes, PR review, and parallel worktree fixing,
plus the full pitfalls list. Read this when executing one of those workflows
or debugging unexpected Grok behavior.

## Read-Only Audit → Markdown Note Pattern

To have Grok review local artifacts and return a clean markdown note (for
Obsidian or a repo) without mutating anything:

1. Prepare stable input files first with Hermes tools (`read_file`,
   `write_file`). Snapshot only the relevant context into a temp file rather
   than dumping raw paths.
2. Run Grok headless **without** `--always-approve` so it cannot auto-write, and
   demand `markdown only, no preamble`.
3. Save Grok's stdout straight into the destination note with `write_file()`.

```
grok --no-auto-update -p "Read /tmp/current.md and /tmp/inventory.md. Produce markdown only, no preamble. Output a clean note titled 'Cleanup Review'." --output-format plain
```

**Pitfall (same as Claude Code):** for document rewrites, a loose "rewrite this"
prompt may return a change summary instead of the full file. Instead: pipe the
file in, and demand `Return ONLY the full revised markdown document. No intro,
no explanation, no code fences. Start immediately with '# Title'.` Verify the
first lines with `read_file()` before overwriting the destination.

## PR Review Patterns

### Quick Review (Headless)

```
terminal(command="cd /path/to/repo && git diff main...feature-branch | grok --no-auto-update -p 'Review this diff for bugs, security issues, and style problems. Be thorough.'", timeout=120)
```

### Clone-to-temp Review (safe, no repo mutation)

```
terminal(command="REVIEW=$(mktemp -d) && git clone https://github.com/user/repo.git $REVIEW && cd $REVIEW && gh pr checkout 42 && grok --no-auto-update -p 'Review the changes vs origin/main. Check bugs, security, race conditions, missing tests.'", pty=true, timeout=300)
```

### Post the review

```
terminal(command="gh pr comment 42 --body '<review text>'", workdir="/path/to/repo")
```

## Parallel Issue Fixing with Worktrees

```
# Create worktrees
terminal(command="git worktree add -b fix/issue-78 /tmp/issue-78 main", workdir="~/project")
terminal(command="git worktree add -b fix/issue-99 /tmp/issue-99 main", workdir="~/project")

# Launch Grok headless in each (background)
terminal(command="grok --no-auto-update --always-approve -p 'Fix issue #78: <description>. Commit when done.'", workdir="/tmp/issue-78", background=true, notify_on_complete=true)
terminal(command="grok --no-auto-update --always-approve -p 'Fix issue #99: <description>. Commit when done.'", workdir="/tmp/issue-99", background=true, notify_on_complete=true)

# Monitor
process(action="list")

# After completion: push and open PRs
terminal(command="cd /tmp/issue-78 && git push -u origin fix/issue-78")
terminal(command="gh pr create --repo user/repo --head fix/issue-78 --title 'fix: ...' --body '...'")

# Cleanup
terminal(command="git worktree remove /tmp/issue-78", workdir="~/project")
```

## Pitfalls & Gotchas

1. **Auth is subscription-gated.** `grok login` requires a SuperGrok or X
   Premium+ subscription. If login fails or there's no `~/.grok/auth.json`,
   confirm the subscription is active before falling back to `XAI_API_KEY`.
2. **Don't conflate Hermes' xAI auth with the `grok` CLI's auth.** Hermes'
   `x_search` runs on its own xAI OAuth; the standalone `grok` CLI has a
   separate token in `~/.grok/auth.json`. A working `x_search` does NOT mean
   `grok` is logged in.
3. **Always pass `--no-auto-update` in automation** — otherwise Grok phones home
   for update checks (and `x.ai`/`storage.googleapis.com` may be unreachable).
4. **Prefer npm install over the curl installer** — `npm install -g
   @xai-official/grok` avoids the Cloudflare-walled `x.ai` host.
5. **`--always-approve` is the autonomous-build switch.** Without it, headless
   runs may stall waiting on tool-approval prompts. Omit it deliberately for
   read-only review/audit work so Grok can't mutate files.
6. **Headless `-p` skips TUI dialogs**; the TUI needs `pty=true` (+ tmux for
   monitoring), just like Claude Code.
7. **Use `--no-alt-screen`** if you run the TUI inline and the fullscreen
   alt-screen takeover garbles captured output.
8. **No git repo needed**, but for PR/commit workflows you still want one — use
   `mktemp -d && git init` for scratch commit tasks.
9. **Clean up tmux sessions** with `tmux kill-session -t <name>` when done.
