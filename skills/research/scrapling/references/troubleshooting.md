# Scrapling Troubleshooting

Read this when a fetch returns blank/wrong content, gets blocked, or times out.

## Troubleshooting

| Symptom | Likely Cause | What To Do |
|---------|---------------|------------|
| Cloudflare challenge page in output | Turnstile/JS challenge not solved | Use `StealthyFetcher` with `solve_cloudflare=True`; expect +5-15s per fetch |
| Blank/near-empty content from a page that looks fine in a browser | Content is JS-rendered | Switch from `Fetcher` to `DynamicFetcher`, add `network_idle=True` or a `wait_selector` |
| Fetch succeeds but site immediately blocks/redirects on 2nd request | Fingerprinting (TLS/JA3, headers, canvas, WebRTC) flagged the client | Use `StealthyFetcher` with `block_webrtc=True`, `hide_canvas=True`; add `impersonate='chrome'` on `Fetcher`/`FetcherSession` |
| 403/429 responses after a burst of requests | Rate limiting | Add `download_delay` on `Spider`, lower `concurrent_requests`, reuse a `*Session` instead of one-off fetches, rotate `proxy` |
| `DynamicFetcher`/`StealthyFetcher` raises a browser-not-found error | Playwright browsers not installed | Run `scrapling install` after `pip install` |
| Selector returns nothing | Site markup differs from what you inspected (client-rendered, A/B test, geo-gated) | Re-inspect the actual fetched HTML/markdown (`scrapling extract get ... output.md`) rather than the browser DevTools view |
| Everything times out | Fetcher timeout units differ | `Fetcher` timeout is **seconds**; `DynamicFetcher`/`StealthyFetcher` timeout is **milliseconds** |
