# Public Records Navigation

When profiling subjects, many data points live behind interactive pages (LinkedIn profiles, The Knot wedding sites, Instagram posts, Facebook timelines). `web_extract` returns metadata snippets — the actual page content may confirm or deny your claims.

## Pattern

```
1. Identify target URL → 2. browser_navigate(url) → 3. browser_snapshot(full=true) → read content directly
```

## Why this matters

Two sessions ago: asserted "The Knot only shows first names + last initial" without navigating — user had to do `/interupt Source`. The page actually contained full ceremony/reception details including location, time, dress code, registry items.

## When to use browser vs web_extract

| Signal | Use browser_navigate |
|--------|---------------------|
| Interactive elements visible in URL structure (clickable links, photo galleries) | Yes — navigate |
| Static markdown/JSON endpoint (.md, .txt, .json, .yaml, raw.githubusercontent.com) | No — web_extract or curl |
| Profile pages behind login walls (LinkedIn full profile, Instagram posts) | Maybe — try snapshot first; if empty elements appear, it's auth-gated |
| Wedding/event sites (The Knot, Zola, WithJoy) | Yes — navigate to see all sections |

## Common interactive surfaces for profiling

- **LinkedIn:** `linkedin.com/in/<name>` → navigate, snapshot, read activity/connections
- **The Knot/Zola/WithJoy:** wedding website URLs → navigate, snapshot, extract ceremony/reception details
- **Instagram:** profile pages behind login walls — may only get metadata via web_search; deep content requires browser with logged-in state (rare)
- **Facebook:** behind login walls — mostly metadata available via web_extract

## Pitfall: refs go stale fast

Each `browser_navigate` refreshes element refs. Clicking the same ref twice will fail ("Unknown ref"). Navigate fresh before each click sequence.
