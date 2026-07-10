# scripts/

`extract.py` — fetch a URL (scrapling if installed, else urllib) and optionally
run local-model extraction.

```bash
python3 extract.py 'https://example.com'                              # raw text
python3 extract.py 'https://example.com' --css '.article'              # scoped (needs scrapling)
python3 extract.py 'https://example.com' --model agent1                # structured JSON, temp 0
python3 extract.py 'https://example.com' --model ornith --instruction "Summarize this"
```

stdlib only; scrapling is an optional import. See `../SKILL.md` for the model wiring details.
