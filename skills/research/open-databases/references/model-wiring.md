# Model Wiring

For research workflows that need to normalize or synthesize across these
sources, two local endpoints are wired (see the `scrapling` skill for the
full pattern; summarized here for this skill's use case):

| Task | Model | Endpoint | Why |
|------|-------|----------|-----|
| Deterministic field extraction/normalization (e.g. "pull DOI/title/year as JSON from this record") | **qwen3-coder** | llama-swap `http://localhost:1235/v1/chat/completions`, `"temperature": 0` | Temperature 0 for repeatable structured output |
| Cross-source synthesis (e.g. "reconcile what OpenAlex, Crossref, and Wikidata say about this entity") | **ornith** | llama-swap `http://localhost:1235/v1/chat/completions`, `"chat_template_kwargs": {"enable_thinking": false}` | Reasoning model with thinking disabled for fast, terse synthesis |

```python
import json
import urllib.request

# qwen3-coder: deterministic normalization, temperature 0
payload = {
    "model": "qwen3-coder",
    "messages": [
        {"role": "system", "content": "Extract structured data as JSON only. No prose, no markdown fences."},
        {"role": "user", "content": f"Normalize this record to {{doi, title, year, source}}.\n\n{record_text}"},
    ],
    "temperature": 0,
    "stream": False,
}
req = urllib.request.Request(
    "http://localhost:1235/v1/chat/completions",
    data=json.dumps(payload).encode(),
    headers={"Content-Type": "application/json"},
)
result = json.loads(urllib.request.urlopen(req, timeout=120).read())["choices"][0]["message"]["content"]
```

```python
# ornith: cross-source synthesis, thinking disabled
payload = {
    "model": "ornith-uncensored",
    "messages": [{"role": "user", "content": f"Reconcile these records from OpenAlex, Crossref, and Wikidata; note any disagreements.\n\n{combined_records}"}],
    "chat_template_kwargs": {"enable_thinking": False},
    "stream": False,
}
req = urllib.request.Request(
    "http://localhost:1235/v1/chat/completions",
    data=json.dumps(payload).encode(),
    headers={"Content-Type": "application/json"},
)
result = json.loads(urllib.request.urlopen(req, timeout=120).read())["choices"][0]["message"]["content"]
```

Verify wiring before relying on it:

```bash
curl -s http://localhost:1235/v1/models | grep -o '"qwen3-coder"'
curl -s http://localhost:1235/v1/models | grep -o '"ornith-uncensored"'
```
