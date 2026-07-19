# Skin/Theme System

> Development deep dive, moved out of `AGENTS.md` (which keeps the
> intent layer, hard rules, pitfalls, and testing policy). On any
> conflict, `AGENTS.md` wins.


The skin engine (`hermes_cli/skin_engine.py`) provides data-driven CLI visual customization. Skins are **pure data** — no code changes needed to add a new skin.

## Architecture

```
hermes_cli/skin_engine.py    # SkinConfig dataclass, built-in skins, YAML loader
~/.hermes/skins/*.yaml       # User-installed custom skins (drop-in)
```

- `init_skin_from_config()` — called at CLI startup, reads `display.skin` from config
- `get_active_skin()` — returns cached `SkinConfig` for the current skin
- `set_active_skin(name)` — switches skin at runtime (used by `/skin` command)
- `load_skin(name)` — loads from user skins first, then built-ins, then falls back to default
- Missing skin values inherit from the `default` skin automatically

## What skins customize

Skin keys → consumers: `colors.banner_{border,title,accent,dim,text}` +
`colors.response_border` (`banner.py`/`cli.py`); `spinner.{waiting_faces,
thinking_faces,thinking_verbs,wings}`, `tool_prefix`, per-tool `tool_emojis`
(`display.py`); `branding.{agent_name,welcome,response_label,prompt_symbol}`
(`banner.py`/`cli.py`).

## Built-in skins

`default` (Hermes gold/kawaii), `ares` (crimson/bronze), `mono` (grayscale),
`slate` (cool blue). Add one via the `_BUILTIN_SKINS` dict in
`hermes_cli/skin_engine.py` (same keys as above + `name`/`description`).

## User skins (YAML)

Drop `~/.hermes/skins/<name>.yaml` with any subset of the keys above:

```yaml
name: cyberpunk
colors: {banner_border: "#FF00FF"}
spinner: {thinking_verbs: ["jacking in", "decrypting"]}
branding: {agent_name: "Cyber Agent"}
```

Activate with `/skin cyberpunk` or `display.skin: cyberpunk` in config.yaml.
