# CLI Command & Flag Reference

Full `npx neuroskill <command>` table, global flags, and CLI-level error
troubleshooting. SKILL.md keeps only the handful of commands used in each
numbered workflow section — read this when you need a command or flag not
shown there.

## Commands

All commands support `--json` (raw JSON, pipe-safe) and `--full` (human summary + JSON).

| Command | Description |
|---------|-------------|
| `status` | Full system snapshot: device, scores, bands, ratios, sleep, history |
| `session [N]` | Single session breakdown with first/second half trends (0=most recent) |
| `sessions` | List all recorded sessions across all days |
| `search` | ANN similarity search for neurally similar historical moments |
| `compare` | A/B session comparison with metric deltas and trend analysis |
| `sleep [N]` | Sleep stage classification (Wake/N1/N2/N3/REM) with analysis |
| `label "text"` | Create a timestamped annotation at the current moment |
| `search-labels "query"` | Semantic vector search over past labels |
| `interactive "query"` | Cross-modal 4-layer graph search (text → EXG → labels) |
| `listen` | Real-time event streaming (default 5s, set `--seconds N`) |
| `umap` | 3D UMAP projection of session embeddings |
| `calibrate` | Open calibration window and start a profile |
| `timer` | Launch focus timer (Pomodoro/Deep Work/Short Focus presets) |
| `notify "title" "body"` | Send an OS notification via the NeuroSkill app |
| `raw '{json}'` | Raw JSON passthrough to the server |

## Global Flags

| Flag | Description |
|------|-------------|
| `--json` | Raw JSON output (no ANSI, pipe-safe) |
| `--full` | Human summary + colorized JSON |
| `--port <N>` | Override server port (default: auto-discover, usually 8375) |
| `--ws` | Force WebSocket transport |
| `--http` | Force HTTP transport |
| `--k <N>` | Nearest neighbors count (search, search-labels) |
| `--seconds <N>` | Duration for listen (default: 5) |
| `--trends` | Show per-session metric trends (sessions) |
| `--dot` | Graphviz DOT output (interactive) |

## Error Handling

| Error | Likely Cause | Fix |
|-------|-------------|-----|
| `npx neuroskill status` hangs | NeuroSkill app not running | Open NeuroSkill desktop app |
| `device.state: "disconnected"` | BCI device not connected | Check Bluetooth, device battery |
| All scores return 0 | Poor electrode contact | Reposition headband, moisten electrodes |
| `signal_quality` values < 0.7 | Loose electrodes | Adjust fit, clean electrode contacts |
| SNR < 3 dB | Noisy signal | Minimize head movement, check environment |
| `command not found: npx` | Node.js not installed | Install Node.js 20+ |
