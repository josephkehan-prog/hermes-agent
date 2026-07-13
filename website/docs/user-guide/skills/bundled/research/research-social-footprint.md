---
title: "Social Footprint"
sidebar_label: "Social Footprint"
description: "Username + email footprint reconnaissance — curated keyless platform-presence checks, email permutation generation, and Gravatar lookup"
---

{/* This page is auto-generated from the skill's SKILL.md by website/scripts/generate-skill-docs.py. Edit the source SKILL.md, not this page. */}

# Social Footprint

Username + email footprint reconnaissance — curated keyless platform-presence checks, email permutation generation, and Gravatar lookup. Authorized/defensive/research use only. Includes scripts/footprint.py.

## Skill metadata

| | |
|---|---|
| Source | Bundled (installed by default) |
| Path | `skills/research/social-footprint` |
| Version | `1.0.0` |
| Author | Hermes Agent |
| License | MIT |
| Platforms | linux, macos, windows |
| Tags | `OSINT`, `Footprint`, `Username`, `Email`, `Social`, `Recon` |
| Related skills | [`osint-investigation`](/docs/user-guide/skills/bundled/osint-investigation/osint-investigation-osint-investigation), [`network-recon`](/docs/user-guide/skills/bundled/research/research-network-recon) |

## Reference: full SKILL.md

:::info
The following is the complete skill definition that Hermes loads when this skill is triggered. This is what the agent sees as instructions when the skill is active.
:::

# Social Footprint

Username + email footprint reconnaissance: check whether a handle is
registered across a curated set of public platforms, generate plausible
email addresses from a name and domain, and check Gravatar registration —
all with stdlib-only, keyless HTTP requests. No scraping of profile
content, no scripted logins, no bypassing of access controls.

## Ethics note — read before running

This skill is for **authorized, consented, or clearly defensive** use only:
penetration-test engagements with signed scope, your own accounts/handles,
security research, journalism/due-diligence with a legitimate public-interest
basis, or checking your own organization's exposure. It is NOT for stalking,
harassment, doxxing, or any unauthorized profiling of a private individual.

- Every check here is a **status-code presence probe** against a public
  profile URL — not scraping, not authentication, not bypassing any access
  control. It answers "does this URL 404 or not," nothing more.
- A "present" result is a lead, not proof of identity — usernames collide
  across unrelated people constantly. Never present a hit as confirmed
  identity without independent corroboration.
- Respect each platform's Terms of Service and `robots.txt`. Heavy automated
  querying can violate ToS even when technically keyless; this skill's
  default concurrency (8 workers) is tuned for occasional lookups, not bulk
  scanning of many usernames.
- If the target is a specific named private individual and the engagement
  is not clearly authorized, stop and ask before proceeding.

## When to Use

- Verifying whether a handle you've been given is actually registered on a
  given platform (pentest recon, security research, due diligence)
- Building a candidate list of likely work email addresses from a name and
  a known company domain (authorized recon, e.g. phishing-simulation setup
  with client sign-off)
- Checking if an email address has a Gravatar (a cheap, keyless "is this a
  real, actively-used address" signal)
- A lightweight, dependency-free alternative to `sherlock`/`maigret` when
  those aren't installed, for a handful of high-signal platforms

Do NOT use this skill for:

- Full public-records investigation (SEC filings, court records, property,
  sanctions, corporate registries) — that's `osint-investigation`, which
  also has its own `footprint.py`/`dorkpack.py` helpers scoped to its
  evidence-chain workflow. This skill is the standalone, minimal entry
  point when all you need is a quick username/email check without pulling
  in the rest of that skill's CSV/entity-resolution machinery.
- General network/domain recon (WHOIS, DNS, port state) — that's
  `network-recon`.
- Breach-data lookups — the `hibp` subcommand here is an intentional STUB;
  see [Pitfalls](#pitfalls).

## Platform Catalog

Curated, keyless subset (technique inspired by
[sherlock-project/sherlock](https://github.com/sherlock-project/sherlock),
MIT — no code vendored, just the status-code-presence idea):

| Platform | Profile URL pattern | Notes |
|---|---|---|
| GitHub | `github.com/{u}` | clean 404 for missing users |
| GitLab | `gitlab.com/{u}` | clean 404 |
| Reddit | `reddit.com/user/{u}/about.json` | JSON API, clean error on missing |
| Keybase | `keybase.io/{u}` | clean 404 |
| Dev.to | `dev.to/{u}` | clean 404 |
| Hacker News | `news.ycombinator.com/user?id={u}` | 200 always; classified via control diff |
| Docker Hub | `hub.docker.com/u/{u}` | clean 404 |
| SoundCloud | `soundcloud.com/{u}` | mixed; classified via control diff |

For 500+ site coverage, escalate to `sherlock <username>` (separate install,
not bundled here).

## Workflow

1. **Username check** — run `footprint.py username <name>` to see presence
   across the catalog above. Each site is checked against a
   near-certainly-nonexistent control username first, so a soft-404 site
   (one that returns HTTP 200 for both real and fake profiles) is
   classified by comparing response bodies to the control rather than
   trusting the status code blindly. Results are `present` / `absent` /
   `manual` (ambiguous — open the URL yourself) / `unknown` / `error`.
2. **Email permutation** — if you have a name and a company/domain but not
   an address, run `footprint.py email-permute <first> <last> <domain>` to
   get the standard candidate list (`first.last@`, `flast@`, etc.). This is
   a pure string generator — no network call, so it's safe to run freely.
3. **Gravatar check** — `footprint.py gravatar <email>` MD5-hashes the
   address and checks `gravatar.com/avatar/<hash>?d=404` for a 200 (exists)
   vs 404 (no Gravatar). Useful as a cheap secondary signal that an address
   is real and actively used somewhere.
4. **Collate and narrate** — for a run that touches several usernames/
   permutations, use the model wiring below: agent1 to collate the raw
   JSON results deterministically, ornith to write the human-readable
   footprint narrative.

```bash
python3 SKILL_DIR/scripts/footprint.py username octocat --json
python3 SKILL_DIR/scripts/footprint.py email-permute John Doe example.com
python3 SKILL_DIR/scripts/footprint.py gravatar test@example.com
```

## Model Wiring

| Task | Model | Endpoint | Why |
|------|-------|----------|-----|
| Deterministic result collation (merge username/email/gravatar JSON into one structured record) | **agent1** | Ollama `http://localhost:11434/api/chat`, `"options": {"temperature": 0}` | Temperature 0 for repeatable structured output |
| Footprint narrative (turn collated results into a readable summary for the user) | **ornith** | llama-swap `http://localhost:1235/v1/chat/completions`, `"chat_template_kwargs": {"enable_thinking": false}` | Reasoning model with thinking disabled for fast, terse narrative |

```python
import json
import urllib.request

# agent1: deterministic collation, temperature 0
payload = {
    "model": "hf.co/InternScience/Agents-A1-Q4_K_M-GGUF:latest",
    "messages": [
        {"role": "system", "content": "Merge these footprint results into one JSON record. No prose, no markdown fences."},
        {"role": "user", "content": f"Combine username, email-permute, and gravatar results:\n\n{raw_results_json}"},
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
# ornith: footprint narrative, thinking disabled
payload = {
    "model": "ornith-uncensored",
    "messages": [{"role": "user", "content": f"Summarize this footprint recon as a short narrative, flagging manual/unknown hits as unconfirmed:\n\n{collated_json}"}],
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

- **False positives on soft-404s**: several platforms return HTTP 200 for
  every username (JS-rendered or a generic landing page instead of a real
  404). `footprint.py` mitigates this with the control-username diff, but
  any `manual` result must be opened and eyeballed before you report it as
  a hit — never upgrade `manual` to `present` because it "seems likely."
- **Rate limits / ToS**: default concurrency is 8 workers with a single
  request per platform per run. Running this against many usernames in a
  loop can trip rate limiting or violate a platform's ToS on automated
  querying — space out bulk runs.
- **Username collisions are not identity**: a hit on a platform confirms
  the *string* is registered, not that it belongs to your target. Cross-
  reference with other evidence (bio text, avatar, linked accounts) before
  treating it as confirmed.
- **HIBP is a stub, on purpose**: `footprint.py hibp <email>` does not call
  the Have I Been Pwned API — it requires a paid key
  (haveibeenpwned.com/API/Key) that this skill deliberately does not wire.
  The subcommand exists as a documented placeholder; it prints a
  `[NEEDS-REVIEW]` message and exits. If a user supplies their own key,
  wire it via an env var, never hardcode it.
- **Gravatar false negatives**: an address can be real and heavily used
  without ever having a Gravatar account — absence is weak evidence at
  best, not proof the address is unused.
- **Email permutations are guesses**: `email-permute` produces plausible
  candidates from common corporate naming conventions; it does not verify
  deliverability. Don't represent the output as confirmed addresses.

## Legal / Ethics

All checks in this skill query public, unauthenticated URLs — the same
requests a browser makes when you visit a profile page. That said:

- Confirm you have authorization (engagement scope, consent, or a clear
  defensive/research purpose) before running username or email checks
  against a named individual who hasn't agreed to be looked up.
- Do not use results to harass, dox, impersonate, or otherwise harm anyone.
- Automated querying at scale can still violate a platform's Terms of
  Service even without authentication — this is a legal risk independent of
  the technical "no login required" framing.
- Breach-data lookups (HIBP) require the target's own opt-in or a
  legitimate security-research/incident-response basis under HIBP's terms;
  this skill does not attempt to work around that by omitting the key.
