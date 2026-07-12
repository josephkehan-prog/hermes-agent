# Setup: Optional Upgrades

`unbroker` works zero-config (stdlib-only Python). `$PDD setup --auto` turns
on every upgrade it detects, reading credentials from the shell env **and
from `$HERMES_HOME/.env`** so keys Hermes already loads for its own tools
are picked up without re-exporting. Each upgrade converts a class of human
tasks into agent actions. Read this when configuring email/browser modes or
diagnosing why an upgrade isn't engaging.

## Cloud browser (recommended default): `BROWSERBASE_API_KEY`

`setup --auto` selects it whenever the key is present, and it is the
intended baseline: a real residential-IP cloud browser **clears soft/managed
CAPTCHAs (Cloudflare Turnstile, hCaptcha/reCAPTCHA checkbox) as normal
operation**, so those brokers stay automated (T1) instead of becoming human
tasks. This is not CAPTCHA "solving" — no solver service, no fingerprint
spoofing; only interactive/behavioral ("hard") challenges the browser
genuinely cannot pass fall back to a human task. Without the key, the plain
agent browser is used and soft-CAPTCHA brokers drop to T2 (human).

## Email automation — two credential-free-or-not options

**Browser mode (no password): `setup --email-mode browser`.** The agent
sends opt-out/CCPA emails and opens verification links through the
operator's **logged-in webmail** using `browser_*` tools. Nothing is stored.
This requires Hermes to be pointed at the operator's own logged-in browser,
**NOT** a cloud browser: a headless cloud browser (Browserbase) holds no
webmail session and is itself Cloudflare/DataDome-gated on webmail and on
session-bound broker gates (e.g. PeopleConnect guided-mode). Drive the
operator's real Chrome over CDP — launch `chrome --remote-debugging-port=9222
--user-data-dir="$HOME/.hermes/chrome-debug"` (a dedicated debug profile
signed into the webmail once, not the Default profile) and connect the
browser tools to `127.0.0.1:9222`. **`$PDD cdp` launches this for you**
(finds Chrome/Chromium/Brave/Edge, starts it detached on the dedicated
profile, prints the CDP endpoint; `--check` to test, `--print` for the
command). See `references/methods.md` → "Browser backends: scan vs execute".
Falls back to drafts for an email if the inbox isn't reachable.

**SMTP/IMAP (stored creds): `EMAIL_ADDRESS` + `EMAIL_PASSWORD`** (+
`EMAIL_SMTP_HOST` / `EMAIL_IMAP_HOST` for non-mainstream providers;
gmail/outlook/yahoo/icloud/fastmail inferred). The CLI sends via
`send-email` and reads verify links via `poll-verification`. The `agentmail`
skill (per-broker aliases) also counts.

## Other upgrades

- **Google Sheets tracker**: the `google-workspace` skill.
- **Stealth/Cloudflare-protected pages**: the `scrapling` skill.
