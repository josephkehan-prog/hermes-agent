---
name: infra-monitor
description: Infrastructure drift monitoring for a domain over time — DNS record changes, new/expiring TLS certs via Certificate Transparency logs, IP/ASN changes, and security-header regressions. Composes network-recon's DoH/crt.sh tooling into snapshot-and-diff workflows. Includes scripts/infra_snapshot.py.
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [Monitoring, Infrastructure, DNS, Certificate, Drift-Detection, Security]
    category: research
    related_skills: [network-recon, watch-notify, cert-transparency]
---

# Infra Monitor

Infrastructure drift monitoring for a single domain: has its DNS changed,
has a new TLS certificate been issued (or an existing one gone stale), has
its IP/ASN moved, has its security-header posture regressed? This skill
takes point-in-time snapshots and diffs them against later snapshots to
surface drift, composing `network-recon`'s DoH/crt.sh recon tooling and this
repo's `dns_recon_tool`, `cert_transparency_tool`, and `ip_info_tool`.

This is deliberately narrow: `watch-notify` is generic change detection
(content hashing, arbitrary page/feed watching, notification delivery).
*This* skill is specific to infrastructure signals — DNS record sets, CT
log entries, resolved IPs, security headers — and understands what "no real
change" looks like for each one (DNS TTL flapping, CT-log propagation lag,
CDN IP churn), which a generic hash-diff watcher does not. Reach for
`watch-notify` when the target is a page, feed, or file; reach for this
skill when the target is "a domain's infrastructure."

**Authorized/defensive/research use only.** Every signal here is public
data (DNS is inherently public; CT logs mirror publicly-issued certificates;
security headers are served to any client; IP/ASN registration is public
routing data), but repeated automated monitoring of a domain you don't own
or don't have permission to assess can still violate a target's terms of
service. Use this for your own infrastructure, an authorized
pentest/bug-bounty scope with ongoing monitoring in scope, or general
research — not to build a covert tripwire against a system you don't have
permission to watch.

## When to Use

- Tracking whether a domain's DNS records (A/MX/NS/TXT) have changed since
  the last check
- Watching Certificate Transparency logs for newly issued certs / new
  subdomains appearing under a domain
- Detecting when a domain's resolved IP (and therefore possibly its
  hosting provider/ASN) has moved
- Auditing whether a site's security-header posture has regressed between
  two points in time
- Building a periodic (cron/scheduled-agent) check that alerts on
  infrastructure drift for a domain you're authorized to monitor

Not for: one-off recon with no time dimension (use `network-recon`
directly), generic page/feed/file change watching (use `watch-notify`),
or public-records/corporate OSINT (use `osint-investigation`).

## What It Monitors

| Signal | Source tool | Why it matters |
|---|---|---|
| DNS records (A/MX/NS/TXT) | `scripts/infra_snapshot.py snapshot` (DoH) / `dns_recon_tool` | New/removed A records can mean a migration or a hijack; new MX can mean mail takeover; NS changes mean a new registrar/DNS provider took control |
| New/expiring TLS certs, new subdomains | `scripts/infra_snapshot.py snapshot` (crt.sh) / `cert_transparency_tool` | A newly-issued cert for a subdomain you didn't provision is a classic early signal of shadow infrastructure or a subdomain-takeover setup; an expiring cert with no reissue yet is an outage waiting to happen |
| Resolved IP / ASN / hosting org | `resolved_ip` in the snapshot, cross-checked with `ip_info_tool` | An IP move to a different ASN/org can mean a provider migration (benign) or a compromise redirecting traffic (not benign) — ASN context is what tells them apart |
| Security headers (HSTS, CSP, X-Frame-Options, etc.) | `network-recon`'s `recon.py fingerprint` | A header that was present and is now missing is a regression worth flagging even with no other change |

## Workflow

1. **Snapshot**: `infra_snapshot.py snapshot <domain> --out snap-<date>.json`
   captures DNS (A/MX/NS/TXT via DoH), CT-log subdomains (crt.sh), and the
   primary resolved IP into one timestamped JSON file.
2. **Store**: keep snapshots around (a flat directory of dated JSON files is
   enough) so any two points in time can be diffed later. This skill doesn't
   manage storage/scheduling itself — pair it with a cron entry or the
   `schedule` skill to snapshot on a cadence.
3. **Re-snapshot**: on the next check-in, take a fresh snapshot the same way.
4. **Diff**: `infra_snapshot.py diff <old.json> <new.json>` reports added/
   removed DNS records per type, added/removed CT subdomains, and any IP
   change — human-readable by default, `--json` for the machine-readable
   form. For an ASN check, additionally call `ip_info_tool.ip_info()` on
   `old_ip` and `new_ip` from the diff and compare `asn`/`org`.
5. **Alert**: `diff --fail-on-change` exits 1 when drift is found, for
   wiring into a cron job or `watch-notify`'s delivery side. Before
   alerting, run the triage step below to separate benign churn from
   something worth a human's attention.

```bash
python3 scripts/infra_snapshot.py snapshot example.com --out snap-2026-07-01.json
# ... time passes ...
python3 scripts/infra_snapshot.py snapshot example.com --out snap-2026-07-10.json
python3 scripts/infra_snapshot.py diff snap-2026-07-01.json snap-2026-07-10.json
python3 scripts/infra_snapshot.py diff snap-2026-07-01.json snap-2026-07-10.json --json --fail-on-change
```

See `scripts/README.md`. stdlib only; exits 2 on network/HTTP/parse/
validation errors.

## Model Wiring

| Task | Model | Endpoint | Why |
|------|-------|----------|-----|
| Deterministic snapshot-diffing (e.g. "extract the {added, removed} record set as JSON from this diff output") | **agent1** | Ollama `http://localhost:11434/api/chat`, `"options": {"temperature": 0}` | Temperature 0 for repeatable structured output on a diff that's already structured — use this to reformat/summarize into a downstream schema, not to re-derive the diff itself |
| "Is this drift benign or suspicious" triage narrative (e.g. "a new A record appeared and the old one is gone — is this a migration or a hijack?") | **ornith** | llama-swap `http://localhost:1235/v1/chat/completions`, `"chat_template_kwargs": {"enable_thinking": false}` | Reasoning model with thinking disabled for fast, terse synthesis over the diff + ASN context |

```python
import json
import urllib.request

# agent1: deterministic diff reformatting, temperature 0
payload = {
    "model": "hf.co/InternScience/Agents-A1-Q4_K_M-GGUF:latest",
    "messages": [
        {"role": "system", "content": "Extract structured data as JSON only. No prose, no markdown fences."},
        {"role": "user", "content": f"Reformat this infra diff into {{severity, summary}} rows.\n\n{diff_output}"},
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
# ornith: benign-vs-suspicious drift triage, thinking disabled
payload = {
    "model": "ornith-uncensored",
    "messages": [{
        "role": "user",
        "content": f"This domain's infrastructure changed. Is this drift consistent with a "
                    f"routine migration (CDN churn, provider switch, cert renewal) or does it "
                    f"look suspicious (unexpected NS/MX takeover, subdomain-takeover setup, "
                    f"ASN mismatch)? Diff + ASN context below.\n\n{diff_and_asn_context}",
    }],
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

- **DNS TTL flapping is noise, not drift**: some providers round-robin or
  rotate A records across a small pool of IPs on every TTL expiry. A diff
  that shows one IP swapped for another *within the same pool* on every
  re-snapshot isn't infrastructure change — it's normal load balancing.
  Snapshot on a cadence longer than the domain's TTL, and don't alert on a
  single IP swap without checking whether it recurs/reverts.
- **CT-log lag**: certificate issuance and a cert actually showing up in
  crt.sh's index are not simultaneous — there can be a lag of minutes to
  hours. A `snapshot` taken immediately after a cert was issued may not see
  it yet; don't treat "not in this snapshot" as "not issued."
- **CDN IP churn is benign noise**: domains behind Cloudflare, Fastly,
  CloudFront, etc. can have their resolved A record change routinely as the
  CDN reassigns edge IPs — this is not a hosting migration and rarely
  reflects an ASN change (the CDN's ASN stays the same). Cross-check with
  `ip_info_tool`'s `org`/`asn` field before treating an IP diff as
  meaningful; an IP change with the same ASN/org is almost always CDN
  churn, not drift worth alerting on.
- **crt.sh rate limits / DoH truncation**: both are shared free services —
  see `network-recon`'s Pitfalls section for the same caveats (crt.sh can
  time out under load; DoH responses can truncate large answer sets). This
  skill inherits both; a failed `snapshot` should be retried shortly, not
  treated as "the domain has no records."
- **Wildcard cert / subdomain noise**: a wildcard cert can make the same
  apex domain reappear across many crt.sh entries, and a subdomain
  appearing in CT logs doesn't mean it currently resolves or is in active
  use — see `network-recon`'s wildcard-cert-noise pitfall. Sanity-check a
  "new subdomain" hit before treating it as new live infrastructure.
- **Snapshots are only as good as their cadence**: this skill has no
  built-in scheduler — pair `infra_snapshot.py snapshot` with a cron entry
  or the `schedule` skill. A single snapshot with nothing to diff against
  tells you nothing about drift.
