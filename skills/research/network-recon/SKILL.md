---
name: network-recon
description: Keyless DNS and infrastructure reconnaissance.
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [OSINT, Recon, DNS, Certificate Transparency, Infrastructure, Security]
    category: research
    related_skills: [osint-investigation, scrapling, open-databases]
---

# Network Recon

Network / infrastructure reconnaissance for a single domain: DNS records via
DNS-over-HTTPS, subdomain discovery via Certificate Transparency logs,
reverse DNS, WHOIS, and HTTP header / security-header fingerprinting. Every
source is keyless and free — no signup, no API token.

This fills the gap the `osint-investigation` skill deliberately leaves open:
that skill covers public-records OSINT (corporate filings, sanctions,
lobbying, property, courts). It touches WHOIS/DNS only as a one-line
cross-reference. This skill goes deeper on the network/infrastructure side —
subdomain enumeration, full DNS record sets, and HTTP fingerprinting — and is
the one to reach for when the question is "what does this domain's
infrastructure look like," not "who owns this company."

**Authorized/defensive/research use only.** Every source here is public data
(DNS is inherently public; crt.sh mirrors publicly-issued certificates; HTTP
headers are served to any client), but reconnaissance against a domain you
don't control or don't have permission to assess can still violate a target's
terms of service or, in some contexts, the law. Use this for your own
infrastructure, an authorized pentest/bug-bounty scope, or general research —
not for staging an attack against a system you don't have permission to test.

## When to Use

- Enumerating DNS records (A/AAAA/MX/NS/TXT/CNAME/SOA/CAA) for a domain
- Discovering subdomains via public Certificate Transparency logs
- Reverse-resolving an IP to a hostname (PTR)
- Looking up WHOIS registration data
- Auditing a site's HTTP response headers and security-header posture
  (HSTS, CSP, X-Frame-Options, etc.) for a defensive review
- Mapping a target's attack surface as part of an authorized security
  assessment

Not for: public-records/corporate/financial OSINT (use `osint-investigation`),
general page scraping/extraction (use `scrapling`), or academic/open-data
lookups (use `open-databases`).

## Source Catalog

| Source | Base URL | Auth-free limits | Example query URL |
|---|---|---|---|
| Google DoH | `dns.google/resolve` | Generous, no key | `https://dns.google/resolve?name=example.com&type=A` |
| Cloudflare DoH (fallback) | `cloudflare-dns.com/dns-query` | Generous, no key | `https://cloudflare-dns.com/dns-query?name=example.com&type=A` (needs `Accept: application/dns-json`) |
| crt.sh | `crt.sh` | Shared community service; can be slow/rate-limited under load | `https://crt.sh/?q=%25.example.com&output=json` |
| WHOIS | system `whois` command | Registry-dependent | `whois example.com` |
| HTTP fingerprint | target site directly | Whatever the target allows | `curl -sI https://example.com` |

## Workflow

1. **Domain → DNS**: `recon.py dns <domain>` for the standard record set
   (A/AAAA/MX/NS/TXT/CNAME/SOA/CAA). Pass `--types PTR` with an IP address
   to reverse-resolve instead.
2. **DNS → CT subdomains**: `recon.py subdomains <domain>` pulls every
   hostname crt.sh has seen issued for `*.<domain>`, deduped and sorted.
   Feed interesting hits back into step 1 to resolve them.
3. **Subdomains → fingerprint**: `recon.py fingerprint <url>` for each live
   host of interest — server banner, `X-Powered-By`, and a present/missing
   audit against the standard security-header set.
4. **WHOIS** (optional, any point): `recon.py whois <domain>` for
   registration/registrar context. Skipped gracefully if the system has no
   `whois` binary.

```bash
python3 scripts/recon.py dns example.com --types A,MX,NS,TXT,CAA
python3 scripts/recon.py subdomains example.com
python3 scripts/recon.py fingerprint https://example.com
python3 scripts/recon.py whois example.com
python3 scripts/recon.py dns 93.184.216.34 --types PTR
```

See `scripts/README.md`. stdlib only; exits 2 on network/HTTP/parse/validation
errors.

## Model Wiring

| Task | Model | Endpoint | Why |
|------|-------|----------|-----|
| Deterministic record parsing/normalization (e.g. "pull hostname/type/value as JSON from this DNS/crt.sh output") | **agent1** | Ollama `http://localhost:11434/api/chat`, `"options": {"temperature": 0}` | Temperature 0 for repeatable structured output |
| Recon-summary / attack-surface narrative (e.g. "summarize this domain's exposed subdomains and header posture") | **ornith** | llama-swap `http://localhost:1235/v1/chat/completions`, `"chat_template_kwargs": {"enable_thinking": false}` | Reasoning model with thinking disabled for fast, terse synthesis |

```python
import json
import urllib.request

# agent1: deterministic normalization, temperature 0
payload = {
    "model": "hf.co/InternScience/Agents-A1-Q4_K_M-GGUF:latest",
    "messages": [
        {"role": "system", "content": "Extract structured data as JSON only. No prose, no markdown fences."},
        {"role": "user", "content": f"Normalize this DNS/crt.sh output to {{host, type, value}} rows.\n\n{recon_output}"},
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
# ornith: attack-surface narrative, thinking disabled
payload = {
    "model": "ornith-uncensored",
    "messages": [{"role": "user", "content": f"Summarize this domain's attack surface: subdomains, exposed services, missing security headers.\n\n{combined_recon}"}],
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

## Pitfalls

- **crt.sh rate limits**: it's a free community service, not a hardened API
  — it can be slow, occasionally time out, or briefly rate-limit bursty
  callers. `recon.py subdomains` doesn't retry automatically; space out
  repeated calls and treat a timeout as "try again shortly," not "no
  subdomains exist."
- **crt.sh noise**: results include CA test certs (e.g.
  `as207960 test intermediate - ...`), email addresses in the SAN/CN, and
  wildcard entries (`*.example.com`, stripped to `example.com` here). Sanity
  check hostnames before treating them as live infrastructure.
- **DoH truncation**: DNS-over-HTTPS responses can omit or truncate large
  answer sets (e.g. big TXT/SPF chains) under some resolvers.
  `recon.py dns` falls back from `dns.google` to `cloudflare-dns.com` on a
  network/timeout failure, but a truncated-yet-"successful" response from
  either provider won't trigger that fallback — cross-check with a second
  provider or system `dig` if a record set looks incomplete.
- **Wildcard cert noise**: a domain with a wildcard cert (`*.example.com`)
  can make crt.sh subdomain discovery report the apex domain repeatedly
  across many certificate entries — this script dedupes by hostname, but it
  doesn't imply every listed subdomain currently resolves or is in active
  use.
- **PTR unreliability**: not every IP has a PTR record, and where one exists
  it's set by whoever controls the IP's reverse zone (often the hosting
  provider, not the domain owner) — treat a PTR hit as a hint, not proof of
  ownership.
- **WHOIS output is unstructured**: format varies by registry/TLD; this
  script returns raw `whois` output rather than attempting to parse it.
  `recon.py whois` exits 2 with a clear message if no `whois` binary is
  installed, rather than failing silently.
- **Don't reinvent WHOIS/dig from `open-databases`**: that skill already
  covers a single-shot `whois`/`dig` cookbook for ad-hoc lookups; reach for
  *this* skill when you need the fuller DNS-type sweep, CT subdomain
  enumeration, or HTTP fingerprinting that skill doesn't cover.
