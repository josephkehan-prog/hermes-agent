# scripts/

`recon.py` — stdlib-only CLI for keyless DNS / infrastructure recon.

```bash
python3 recon.py dns example.com --types A,MX,NS,TXT,CAA
python3 recon.py dns 93.184.216.34 --types PTR
python3 recon.py subdomains example.com
python3 recon.py fingerprint https://example.com
python3 recon.py whois example.com
```

No deps, no API keys. Domain inputs are validated against a hostname regex
before use; URLs are checked for http(s) scheme; every network read is capped
at 10 MB. Exits 2 on network/HTTP/parse/validation errors.
