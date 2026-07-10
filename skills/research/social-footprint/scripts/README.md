# scripts/

`footprint.py` — username + email footprint recon, stdlib only, keyless.

```bash
python3 footprint.py username octocat                 # curated platform presence check
python3 footprint.py email-permute John Doe example.com   # candidate addresses
python3 footprint.py gravatar test@example.com         # MD5 -> Gravatar existence
python3 footprint.py hibp test@example.com             # STUB, prints why (needs paid key)
```

No network in `email-permute`. See `../SKILL.md` for ethics/legal notes.
