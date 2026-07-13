---
title: "Telephony — Give Hermes phone capabilities without core tool changes"
sidebar_label: "Telephony"
description: "Give Hermes phone capabilities without core tool changes"
---

{/* This page is auto-generated from the skill's SKILL.md by website/scripts/generate-skill-docs.py. Edit the source SKILL.md, not this page. */}

# Telephony

Give Hermes phone capabilities without core tool changes. Provision and persist a Twilio number, send and receive SMS/MMS, make direct calls, and place AI-driven outbound calls through Bland.ai or Vapi.

## Skill metadata

| | |
|---|---|
| Source | Optional — install with `hermes skills install official/productivity/telephony` |
| Path | `optional-skills/productivity/telephony` |
| Version | `1.0.0` |
| Author | Nous Research |
| License | MIT |
| Platforms | linux, macos, windows |
| Tags | `telephony`, `phone`, `sms`, `mms`, `voice`, `twilio`, `bland.ai`, `vapi`, `calling`, `texting` |
| Related skills | [`maps`](/docs/user-guide/skills/bundled/productivity/productivity-maps), [`google-workspace`](/docs/user-guide/skills/bundled/productivity/productivity-google-workspace), [`agentmail`](/docs/user-guide/skills/optional/email/email-agentmail) |

## Reference: full SKILL.md

:::info
The following is the complete skill definition that Hermes loads when this skill is triggered. This is what the agent sees as instructions when the skill is active.
:::

# Telephony — Numbers, Calls, and Texts without Core Tool Changes

This optional skill gives Hermes practical phone capabilities while keeping telephony out of the core tool list.

It ships with a helper script, `scripts/telephony.py`, that can:
- save provider credentials into `${HERMES_HOME:-~/.hermes}/.env`
- search for and buy a Twilio phone number
- remember that owned number for later sessions
- send SMS / MMS from the owned number
- poll inbound SMS for that number with no webhook server required
- make direct Twilio calls using TwiML `<Say>` or `<Play>`
- import the owned Twilio number into Vapi
- place outbound AI calls through Bland.ai or Vapi

## What this solves

This skill is meant to cover the practical phone tasks users actually want:
- outbound calls
- texting
- owning a reusable agent number
- checking messages that arrive to that number later
- preserving that number and related IDs between sessions
- future-friendly telephony identity for inbound SMS polling and other automations

It does **not** turn Hermes into a real-time inbound phone gateway. Inbound SMS is handled by polling the Twilio REST API. That is enough for many workflows, including notifications and some one-time-code retrieval, without adding core webhook infrastructure.

## Safety rules — mandatory

1. Always confirm before placing a call or sending a text.
2. Never dial emergency numbers.
3. Never use telephony for harassment, spam, impersonation, or anything illegal.
4. Treat third-party phone numbers as sensitive operational data:
   - do not save them to Hermes memory
   - do not include them in skill docs, summaries, or follow-up notes unless the user explicitly wants that
5. It is fine to persist the **agent-owned Twilio number** because that is part of the user's configuration.
6. VoIP numbers are **not guaranteed** to work for all third-party 2FA flows. Use with caution and set user expectations clearly.

## Decision tree — which service to use?

Use this logic instead of hardcoded provider routing:

### 1) "I want Hermes to own a real phone number"
Use **Twilio**.

Why:
- easiest path to buying and keeping a number
- best SMS / MMS support
- simplest inbound SMS polling story
- cleanest future path to inbound webhooks or call handling

Use cases:
- receive texts later
- send deployment alerts / cron notifications
- maintain a reusable phone identity for the agent
- experiment with phone-based auth flows later

### 2) "I only need the easiest outbound AI phone call right now"
Use **Bland.ai**.

Why:
- quickest setup
- one API key
- no need to first buy/import a number yourself

Tradeoff:
- less flexible
- voice quality is decent, but not the best

### 3) "I want the best conversational AI voice quality"
Use **Twilio + Vapi**.

Why:
- Twilio gives you the owned number
- Vapi gives you better conversational AI call quality and more voice/model flexibility

Recommended flow:
1. Buy/save a Twilio number
2. Import it into Vapi
3. Save the returned `VAPI_PHONE_NUMBER_ID`
4. Use `ai-call --provider vapi`

### 4) "I want to call with a custom prerecorded voice message"
Use **Twilio direct call** with a public audio URL.

Why:
- easiest way to play a custom MP3
- pairs well with Hermes `text_to_speech` plus a public file host or tunnel

## Files and persistent state

The skill persists telephony state in two places:

### `${HERMES_HOME:-~/.hermes}/.env`
Used for long-lived provider credentials and owned-number IDs, for example:
- `TWILIO_ACCOUNT_SID`
- `TWILIO_AUTH_TOKEN`
- `TWILIO_PHONE_NUMBER`
- `TWILIO_PHONE_NUMBER_SID`
- `BLAND_API_KEY`
- `VAPI_API_KEY`
- `VAPI_PHONE_NUMBER_ID`
- `PHONE_PROVIDER` (AI call provider: bland or vapi)

### `~/.hermes/telephony_state.json`
Used for skill-only state that should survive across sessions, for example:
- remembered default Twilio number / SID
- remembered Vapi phone number ID
- last inbound message SID/date for inbox polling checkpoints

This means:
- the next time the skill is loaded, `diagnose` can tell you what number is already configured
- `twilio-inbox --since-last --mark-seen` can continue from the previous checkpoint

## Locate the helper script

After installing this skill, locate the script like this:

```bash
SCRIPT="$(find ~/.hermes/skills -path '*/telephony/scripts/telephony.py' -print -quit)"
```

If `SCRIPT` is empty, the skill is not installed yet.

## Install

This is an official optional skill, so install it from the Skills Hub:

```bash
hermes skills search telephony
hermes skills install official/productivity/telephony
```

## Provider setup

### Twilio — owned number, SMS/MMS, direct calls, inbound SMS polling

Sign up at:
- https://www.twilio.com/try-twilio

Then save credentials into Hermes:

```bash
python3 "$SCRIPT" save-twilio ACXXXXXXXXXXXXXXXXXXXXXXXXXXXX your_auth_token_here
```

Search for available numbers:

```bash
python3 "$SCRIPT" twilio-search --country US --area-code 702 --limit 5
```

Buy and remember a number:

```bash
python3 "$SCRIPT" twilio-buy "+17025551234" --save-env
```

List owned numbers:

```bash
python3 "$SCRIPT" twilio-owned
```

Set one of them as the default later:

```bash
python3 "$SCRIPT" twilio-set-default "+17025551234" --save-env
# or
python3 "$SCRIPT" twilio-set-default PNXXXXXXXXXXXXXXXXXXXXXXXXXXXX --save-env
```

### Bland.ai — easiest outbound AI calling

Sign up at:
- https://app.bland.ai

Save config:

```bash
python3 "$SCRIPT" save-bland your_bland_api_key --voice mason
```

### Vapi — better conversational voice quality

Sign up at:
- https://dashboard.vapi.ai

Save the API key first:

```bash
python3 "$SCRIPT" save-vapi your_vapi_api_key
```

Import your owned Twilio number into Vapi and persist the returned phone number ID:

```bash
python3 "$SCRIPT" vapi-import-twilio --save-env
```

If you already know the Vapi phone number ID, save it directly:

```bash
python3 "$SCRIPT" save-vapi your_vapi_api_key --phone-number-id vapi_phone_number_id_here
```

## Diagnose current state

At any time, inspect what the skill already knows:

```bash
python3 "$SCRIPT" diagnose
```

Use this first when resuming work in a later session.

## Common workflows

Full copy-paste command sequences for these tasks — buying/keeping a number,
sending SMS/MMS, polling inbound texts, direct Twilio calls (built-in TTS,
prerecorded audio via Hermes `text_to_speech`, IVR digit navigation), and
outbound AI calls via Bland.ai / Vapi — are in `references/workflows.md`.
Read it before running any of: buy-number, send-sms, poll-inbox,
direct-call, ai-call.

## Suggested agent procedure

When the user asks for a call or text:

1. Determine which path fits the request via the decision tree.
2. Run `diagnose` if configuration state is unclear.
3. Gather the full task details.
4. Confirm with the user before dialing or texting.
5. Use the correct command.
6. Poll for results if needed.
7. Summarize the outcome without persisting third-party numbers to Hermes memory.

## What this skill still does not do

- real-time inbound call answering
- webhook-based live SMS push into the agent loop
- guaranteed support for arbitrary third-party 2FA providers

Those would require more infrastructure than a pure optional skill.

## Pitfalls

- Twilio trial accounts and regional rules can restrict who you can call/text.
- Some services reject VoIP numbers for 2FA.
- `twilio-inbox` polls the REST API; it is not instant push delivery.
- Vapi outbound calling still depends on having a valid imported number.
- Bland is easiest, but not always the best-sounding.
- Do not store arbitrary third-party phone numbers in Hermes memory.

## Verification checklist

After setup, you should be able to do all of the following with just this skill:

1. `diagnose` shows provider readiness and remembered state
2. search and buy a Twilio number
3. persist that number to `${HERMES_HOME:-~/.hermes}/.env`
4. send an SMS from the owned number
5. poll inbound texts for the owned number later
6. place a direct Twilio call
7. place an AI call via Bland or Vapi

## References

- Twilio phone numbers: https://www.twilio.com/docs/phone-numbers/api
- Twilio messaging: https://www.twilio.com/docs/messaging/api/message-resource
- Twilio voice: https://www.twilio.com/docs/voice/api/call-resource
- Vapi docs: https://docs.vapi.ai/
- Bland.ai: https://app.bland.ai/
