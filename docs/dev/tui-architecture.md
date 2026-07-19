# TUI Architecture (ui-tui + tui_gateway)

> Development deep dive, moved out of `AGENTS.md` (which keeps the
> intent layer, hard rules, pitfalls, and testing policy). On any
> conflict, `AGENTS.md` wins.


The TUI is a full replacement for the classic (prompt_toolkit) CLI, activated via `hermes --tui` or `HERMES_TUI=1`.

## Process Model

```
hermes --tui
  └─ Node (Ink)  ──stdio JSON-RPC──  Python (tui_gateway)
       │                                  └─ AIAgent + tools + sessions
       └─ renders transcript, composer, prompts, activity
```

TypeScript owns the screen. Python owns sessions, tools, model calls, and slash command logic.

## Transport

Newline-delimited JSON-RPC over stdio. Requests from Ink, events from Python. See `tui_gateway/server.py` for the full method/event catalog.

## Key Surfaces

| Surface | Ink component | Gateway method |
|---------|---------------|----------------|
| Chat streaming | `app.tsx` + `messageLine.tsx` | `prompt.submit` → `message.delta/complete` |
| Tool activity | `thinking.tsx` | `tool.start/progress/complete` |
| Approvals | `prompts.tsx` | `approval.respond` ← `approval.request` |
| Clarify/sudo/secret | `prompts.tsx`, `maskedPrompt.tsx` | `clarify/sudo/secret.respond` |
| Session picker | `sessionPicker.tsx` | `session.list/resume` |
| Slash commands | Local handler + fallthrough | `slash.exec` → `_SlashWorker`, `command.dispatch` |
| Completions | `useCompletion` hook | `complete.slash`, `complete.path` |
| Theming | `theme.ts` + `branding.tsx` | `gateway.ready` with skin data |

## Slash Command Flow

1. Built-in client commands (`/help`, `/quit`, `/clear`, `/resume`, `/copy`, `/paste`, etc.) handled locally in `app.tsx`
2. Everything else → `slash.exec` (runs in persistent `_SlashWorker` subprocess) → `command.dispatch` fallback

## Dev Commands

```bash
cd ui-tui
npm install       # first time
npm run dev       # watch mode (rebuilds hermes-ink + tsx --watch)
npm start         # production
npm run build     # full build (hermes-ink + tsc)
npm run typecheck # typecheck only (tsc --noEmit)
npm run lint      # eslint
npm run fmt       # prettier
npm test          # vitest
```

## TUI in the Dashboard (`hermes dashboard` → `/chat`)

The dashboard embeds the real `hermes --tui` — **not** a rewrite. See
`hermes_cli/pty_bridge.py` + the `/api/pty` WebSocket in
`hermes_cli/web_server.py`: browser mounts xterm.js (`ChatPage.tsx`), auth via
ephemeral `_SESSION_TOKEN` query param, server spawns the TUI through
`ptyprocess` (POSIX only), raw PTY bytes both ways, resize via
`\x1b[RESIZE:<cols>;<rows>]` → `TIOCSWINSZ`.

**Do not re-implement the primary chat experience in React.** Transcript,
composer/input flow, and PTY-backed terminal belong to the embedded
`hermes --tui` — new Ink features show up in the dashboard automatically.
Structured React UI *around* the TUI is allowed when it is not a second chat
surface (sidebars, inspectors, status panels like `ChatSidebar`,
`ModelPickerDialog`): keep their state independent of the PTY child's session
and fail non-destructively so the terminal pane keeps working.

## Electron Desktop Chat App (`apps/desktop/`)

A **separate** chat surface (Electron + React + nanostores,
`@assistant-ui/react`) talking JSON-RPC to a `tui_gateway` backend. Transport
lives in framework-agnostic `apps/shared` (`@hermes/shared` —
`JsonRpcGatewayClient`), also used by `web/`; desktop has **no dependency on
the dashboard frontend**. It spawns a headless `hermes serve` backend
(`headless_backend=True` skips `_build_web_ui`; `HERMES_SERVE_HEADLESS=1`
disables the SPA — only the JSON-RPC/WS/API surface is reachable). `dashboard`
and `serve` share `cmd_dashboard`/`start_server` but are independent surfaces.
Backward-compat fallback: the desktop spawn (`electron/backend-command.ts`,
`backendSupportsServe()`) rewrites argv to legacy `dashboard --no-open` when
the resolved runtime doesn't register `serve` — removing it would brick
mid-upgrade users. Desktop does NOT embed `hermes --tui`. Full desktop rules:
`apps/desktop/AGENTS.md`.

**Desktop slash commands — curated client-side, dispatched to backend:**

- Backend provides everything: `tui_gateway/server.py` `commands.catalog` +
  `complete.slash` include built-ins, `quick_commands`, and skill commands.
- Curation lives in `apps/desktop/src/lib/desktop-slash-commands.ts`
  (load-bearing): `isDesktopSlashCommand` gates execution (extensions always
  run); `isDesktopSlashSuggestion` gates discovery in both completion paths of
  `use-slash-completions.ts`; `isDesktopSlashExtensionCommand` lets
  skill/quick commands through both suggestion and catalog-filter paths.
- Dispatch: `use-prompt-actions/slash.ts` (`runSlash`) — desktop-owned
  built-ins handled locally; everything else `slash.exec` →
  `command.dispatch` fallback; a skill command resolves to
  `{type: "skill", message}` submitted as a normal prompt.

**Rule:** curation hides noise (terminal-/messaging-only built-ins), NEVER
user-activated extensions — skill and quick commands belong in completions.
Tests: from `apps/desktop`, `npx vitest run src/lib/desktop-slash-commands.test.ts`.
