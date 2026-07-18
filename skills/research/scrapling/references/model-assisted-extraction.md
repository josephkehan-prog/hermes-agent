# Model-Assisted Extraction

Read this when wiring local-model extraction (agent1/ornith) into a scraping workflow instead of hand-writing selectors.

## Model-Assisted Extraction

For research/profiling workflows, pipe fetched text into a local model instead of hand-writing selectors for every field, or to summarize/analyze what you scraped. Two local endpoints are wired for this, split by task:

| Task | Model | Endpoint | Why |
|------|-------|----------|-----|
| Deterministic structured extraction (e.g. "pull name/title/date/price as JSON") | **agent1** (`hf.co/InternScience/Agents-A1-Q4_K_M-GGUF:latest`) | Ollama, `http://localhost:11434/api/chat` | Temperature 0 for repeatable output |
| Analytical/summarization passes (e.g. "what's the sentiment", "summarize this profile") | **ornith** (`ornith-uncensored`) | llama-swap, `http://localhost:1235/v1/chat/completions` | Reasoning model; disable thinking with `chat_template_kwargs: {"enable_thinking": false}` for fast, terse output |

Both are called by `scripts/extract.py` — see [scripts/README.md](scripts/README.md). To wire them up manually:

```python
import json
import urllib.request

# agent1: deterministic structured JSON, temperature 0
payload = {
    "model": "hf.co/InternScience/Agents-A1-Q4_K_M-GGUF:latest",
    "messages": [
        {"role": "system", "content": "Extract structured data as JSON only. No prose, no markdown fences."},
        {"role": "user", "content": f"Extract name, title, date as JSON.\n\n{page_text}"},
    ],
    "options": {"temperature": 0},
    "stream": False,
}
req = urllib.request.Request(
    "http://localhost:11434/api/chat",
    data=json.dumps(payload).encode(),
    headers={"Content-Type": "application/json"},
)
result = json.loads(urllib.request.urlopen(req, timeout=120).read())["message"]["content"]
```

```python
# ornith: analysis/summarization, thinking disabled
payload = {
    "model": "ornith-uncensored",
    "messages": [{"role": "user", "content": f"Summarize this page in 3 bullets.\n\n{page_text}"}],
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
curl -s http://localhost:11434/api/tags | grep -o '"hf.co/InternScience/Agents-A1[^"]*"'
curl -s http://localhost:1235/v1/models | grep -o '"ornith-uncensored"'
```

If either curl returns nothing, the corresponding local server is down or the model isn't loaded — `extract.py` will fail fast with `connection refused` (exit 2) rather than hang.
