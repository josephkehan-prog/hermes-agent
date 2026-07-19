# Kanban (multi-agent work queue)

> Development deep dive, moved out of `AGENTS.md` (which keeps the
> intent layer, hard rules, pitfalls, and testing policy). On any
> conflict, `AGENTS.md` wins.


Durable SQLite-backed board that lets multiple profiles / workers
collaborate on shared tasks. Users drive it via `hermes kanban <verb>`;
workers spawned by the dispatcher drive it via a dedicated `kanban_*`
toolset so their schema footprint is zero when they're not inside a
kanban task.

- **CLI:** `hermes_cli/kanban.py` wires `hermes kanban` (verbs: `init`,
  `create`, `list`/`ls`, `show`, `assign`, `link`, `comment`, `attach`,
  `complete`, `block`, `archive`, `tail`, `dispatch`, `daemon`, `gc`, …
  — see `hermes kanban -h`).
- **Worker/orchestrator toolset:** `tools/kanban_tools.py` exposes
  `kanban_*` tools (show/complete/block/heartbeat/comment/create/link/
  attach…); profiles that explicitly enable the `kanban` toolset outside
  a dispatcher-spawned task also get `kanban_list` + `kanban_unblock`.
- **Dispatcher:** long-lived loop that (default every 60s) reclaims
  stale claims, promotes ready tasks, atomically claims, and spawns
  assigned profiles. Runs **inside the gateway** by default via
  `kanban.dispatch_in_gateway: true`.
- **Plugin assets:** `plugins/kanban/dashboard/` (web UI) +
  `plugins/kanban/systemd/` (`hermes-kanban-dispatcher.service` for
  standalone dispatcher deployment).

Isolation model:
- **Board** is the hard boundary — workers are spawned with
  `HERMES_KANBAN_BOARD` pinned in their env so they can't see other
  boards.
- **Tenant** is a soft namespace *within* a board — one specialist
  fleet can serve multiple businesses with workspace-path + memory-key
  isolation.
- After `kanban.failure_limit` consecutive non-success attempts on the
  same task (default: 2), the dispatcher auto-blocks it to prevent spin
  loops.

Full user-facing docs: `website/docs/user-guide/features/kanban.md`.
