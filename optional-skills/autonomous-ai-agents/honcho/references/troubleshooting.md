# Troubleshooting

## "Honcho not configured"
Run `hermes honcho setup`. Ensure `memory.provider: honcho` is in `~/.hermes/config.yaml`.

## Memory not persisting across sessions
Check `hermes honcho status` -- verify `saveMessages: true` and `writeFrequency` isn't `session` (which only writes on exit).

## Profile not getting its own peer
Use `--clone` when creating: `hermes profile create <name> --clone`. For existing profiles: `hermes honcho sync`.

## Observation changes in dashboard not reflected
Observation config is synced from the server on each session init. Start a new session after changing settings in the Honcho UI.

## Messages truncated
Messages over `messageMaxChars` (default 25k) are automatically chunked with `[continued]` markers. If you're hitting this often, check if tool results or skill content is inflating message size.

## Context injection too large
If you see warnings about context budget exceeded, lower `contextTokens` or reduce `dialecticDepth`. The session summary is trimmed first when the budget is tight.

## Session summary missing
Session summary requires at least one prior turn in the current Honcho session. On cold start (new session, no history), the summary is omitted and Honcho uses the cold-start prompt strategy instead.
