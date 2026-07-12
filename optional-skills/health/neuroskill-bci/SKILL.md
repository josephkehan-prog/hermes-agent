---
name: neuroskill-bci
description: >
  Connect to a running NeuroSkill instance and incorporate the user's real-time
  cognitive and emotional state (focus, relaxation, mood, cognitive load, drowsiness,
  heart rate, HRV, sleep staging, and 40+ derived EXG scores) into responses.
  Requires a BCI wearable (Muse 2/S or OpenBCI) and the NeuroSkill desktop app
  running locally.
platforms: [linux, macos, windows]
version: 1.0.0
author: Hermes Agent + Nous Research
license: MIT
metadata:
  hermes:
    tags: [BCI, neurofeedback, health, focus, EEG, cognitive-state, biometrics, neuroskill]
    category: health
    related_skills: []
---

# NeuroSkill BCI Integration

Connect Hermes to a running [NeuroSkill](https://neuroskill.com/) instance to read
real-time brain and body metrics from a BCI wearable. Use this to give
cognitively-aware responses, suggest interventions, and track mental performance
over time.

> **⚠️ Research Use Only** — NeuroSkill is an open-source research tool. It is
> NOT a medical device and has NOT been cleared by the FDA, CE, or any regulatory
> body. Never use these metrics for clinical diagnosis or treatment.

See `references/metrics.md` for the full metric reference (plus worked interpretation
examples), `references/protocols.md` for intervention protocols, `references/api.md`
for the WebSocket/HTTP API, and `references/cli.md` for the full CLI command/flag
table and error troubleshooting.

---

## Prerequisites

- **Node.js 20+** installed (`node --version`)
- **NeuroSkill desktop app** running with a connected BCI device
- **BCI hardware**: Muse 2, Muse S, or OpenBCI (4-channel EEG + PPG + IMU via BLE)
- `npx neuroskill status` returns data without errors

### Verify Setup
```bash
node --version                    # Must be 20+
npx neuroskill status             # Full system snapshot
npx neuroskill status --json      # Machine-parseable JSON
```

If `npx neuroskill status` returns an error, tell the user:
- Make sure the NeuroSkill desktop app is open
- Ensure the BCI device is powered on and connected via Bluetooth
- Check signal quality — green indicators in NeuroSkill (≥0.7 per electrode)
- If `command not found`, install Node.js 20+

---

## CLI Reference: `npx neuroskill <command>`

All commands support `--json` (raw JSON, pipe-safe) and `--full` (human summary + JSON).
Core commands used below: `status`, `session [N]`, `sessions`, `search`,
`compare`, `sleep [N]`, `label "text"`, `search-labels "query"`,
`interactive "query"`, `listen`, `umap`, `calibrate`, `timer`, `notify`, `raw`.
Full command table, global flags (`--port`, `--ws`, `--k`, `--seconds`, `--trends`, `--dot`, ...),
and CLI error troubleshooting: read `references/cli.md`.

---

## 1. Checking Current State

### Get Live Metrics
```bash
npx neuroskill status --json
```

**Always use `--json`** for reliable parsing. The default output is colorized
human-readable text.

### Key Fields in the Response

The `scores` object contains all live metrics (0–1 scale unless noted):

```jsonc
{
  "scores": {
    "focus": 0.70,           // β / (α + θ) — sustained attention
    "relaxation": 0.40,      // α / (β + θ) — calm wakefulness
    "engagement": 0.60,      // active mental investment
    "meditation": 0.52,      // alpha + stillness + HRV coherence
    "mood": 0.55,            // composite from FAA, TAR, BAR
    "cognitive_load": 0.33,  // frontal θ / temporal α · f(FAA, TBR)
    "drowsiness": 0.10,      // TAR + TBR + falling spectral centroid
    "hr": 68.2,              // heart rate in bpm (from PPG)
    "snr": 14.3,             // signal-to-noise ratio in dB
    "stillness": 0.88,       // 0–1; 1 = perfectly still
    "faa": 0.042,            // Frontal Alpha Asymmetry (+ = approach)
    "tar": 0.56,             // Theta/Alpha Ratio
    "bar": 0.53,             // Beta/Alpha Ratio
    "tbr": 1.06,             // Theta/Beta Ratio (ADHD proxy)
    "apf": 10.1,             // Alpha Peak Frequency in Hz
    "coherence": 0.614,      // inter-hemispheric coherence
    "bands": {
      "rel_delta": 0.28, "rel_theta": 0.18,
      "rel_alpha": 0.32, "rel_beta": 0.17, "rel_gamma": 0.05
    }
  }
}
```

Also includes: `device` (state, battery, firmware), `signal_quality` (per-electrode 0–1),
`session` (duration, epochs), `embeddings`, `labels`, `sleep` summary, and `history`.

### Interpreting the Output

Parse the JSON and translate metrics into natural language — never report raw
numbers alone, always give them meaning (e.g. "focus is solid at 0.70, flow
state territory" not "Focus: 0.70"). Worked DO/DON'T examples and a sample
interactions table: read `references/metrics.md`.

Key interpretation thresholds (full guide: `references/metrics.md`):
- **Focus > 0.70** → flow state territory, protect it
- **Focus < 0.40** → suggest a break or protocol
- **Drowsiness > 0.60** → fatigue warning, micro-sleep risk
- **Relaxation < 0.30** → stress intervention needed
- **Cognitive Load > 0.70 sustained** → mind dump or break
- **TBR > 1.5** → theta-dominant, reduced executive control
- **FAA < 0** → withdrawal/negative affect — consider FAA rebalancing
- **SNR < 3 dB** → unreliable signal, suggest electrode repositioning

---

## 2. Session Analysis

### Single Session Breakdown
```bash
npx neuroskill session --json         # most recent session
npx neuroskill session 1 --json       # previous session
npx neuroskill session 0 --json | jq '{focus: .metrics.focus, trend: .trends.focus}'
```

Returns full metrics with **first-half vs second-half trends** (`"up"`, `"down"`, `"flat"`) — use
this to describe how a session evolved. `npx neuroskill sessions --json` (add `--trends`) lists
all recorded sessions. Worked trend-narration example: `references/metrics.md`.

---

## 3. Historical Search

- **Neural similarity**: `npx neuroskill search --json` (`--k <N>`, `--start`/`--end <UTC>`) finds
  neurally similar historical moments via HNSW over 128-D ZUNA embeddings — use for "when was I
  last in a state like this?" style questions.
- **Semantic label search**: `npx neuroskill search-labels "deep focus" --k 10 --json` searches
  label text via embeddings, returning matching labels with their EXG metrics.
- **Cross-modal graph search**: `npx neuroskill interactive "deep focus" --json` (`--dot` for
  Graphviz output) walks a 4-layer query → labels → EXG points → nearby labels graph.

---

## 4. Session Comparison
```bash
npx neuroskill compare --json                   # auto: last 2 sessions
npx neuroskill compare --a-start <UTC> --a-end <UTC> --b-start <UTC> --b-end <UTC> --json
```

Returns metric deltas (absolute/percent/direction) for ~50 metrics, plus
`insights.improved[]`/`insights.declined[]`, sleep staging for both sessions, and a UMAP job ID.
**Interpret with context — mention trends, not just deltas.** Worked example and the `jq` sort
snippet: `references/metrics.md` and `references/api.md`.

---

## 5. Sleep Data
```bash
npx neuroskill sleep --json                     # last 24 hours
npx neuroskill sleep 0 --json                   # most recent sleep session
```

Epoch-by-epoch sleep staging (5s windows: 0=Wake, 1=N1, 2=N2, 3=N3/deep, 4=REM) with
`efficiency_pct`, `onset_latency_min`, `rem_latency_min`, bout counts. Healthy targets: N3
15–25%, REM 20–25%, efficiency >85%, onset <20 min. Use when the user mentions sleep,
tiredness, or recovery.

---

## 6. Labeling Moments
```bash
npx neuroskill label "breakthrough"
npx neuroskill label --json "focus block start"   # returns label_id
```

Auto-label moments when: the user reports a breakthrough/insight, starts a new task type,
completes a protocol, asks you to mark the moment, or a notable state transition occurs
(entering/leaving flow). Labels are indexed for later retrieval via `search-labels`/`interactive`.

---

## 7. Real-Time Streaming
```bash
npx neuroskill listen --seconds 30 --json
```
Streams live WebSocket events (EXG, PPG, IMU, scores, labels) for the given duration (requires
WebSocket, not available with `--http`). Use for continuous monitoring or observing metric
changes in real time during a protocol.

---

## 8. UMAP Visualization
```bash
npx neuroskill umap --json                      # auto: last 2 sessions
```
GPU-accelerated 3D projection of ZUNA embeddings. `separation_score > 1.5` = neurally distinct
sessions; `< 0.5` = similar brain states.

---

## 9. Proactive State Awareness

### Session Start Check
At the beginning of a session, optionally run a status check if the user mentions
they're wearing their device or asks about their state:
```bash
npx neuroskill status --json
```

Inject a brief state summary in your own words (e.g. "focus is building at
0.62, relaxation is good at 0.55" — see `references/metrics.md` for phrasing).

### When to Proactively Mention State

Mention cognitive state **only** when:
- User explicitly asks ("How am I doing?", "Check my focus")
- User reports difficulty concentrating, stress, or fatigue
- A critical threshold is crossed (drowsiness > 0.70, focus < 0.30 sustained)
- User is about to do something cognitively demanding and asks for readiness

**Do NOT** interrupt flow state to report metrics. If focus > 0.75, protect the
session — silence is the correct response.

---

## 10. Suggesting Protocols

When metrics indicate a need, suggest a protocol from `references/protocols.md`.
Always ask before starting — never interrupt flow state (explain the metric
connection when you suggest one, e.g. "focus has been declining and TBR is
climbing past 1.5 — want me to walk you through a Theta-Beta Neurofeedback
Anchor?").

Key triggers:
- **Focus < 0.40, TBR > 1.5** → Theta-Beta Neurofeedback Anchor or Box Breathing
- **Relaxation < 0.30, stress_index high** → Cardiac Coherence or 4-7-8 Breathing
- **Cognitive Load > 0.70 sustained** → Cognitive Load Offload (mind dump)
- **Drowsiness > 0.60** → Ultradian Reset or Wake Reset
- **FAA < 0 (negative)** → FAA Rebalancing
- **Flow State (focus > 0.75, engagement > 0.70)** → Do NOT interrupt
- **High stillness + headache_index** → Neck Release Sequence
- **Low RMSSD (< 25ms)** → Vagal Toning

---

## 11. Additional Tools

### Focus Timer
```bash
npx neuroskill timer --json
```
Launches the Focus Timer window with Pomodoro (25/5), Deep Work (50/10), or
Short Focus (15/5) presets.

### Calibration
```bash
npx neuroskill calibrate
npx neuroskill calibrate --profile "Eyes Open"
```
Opens the calibration window. Useful when signal quality is poor or the user
wants to establish a personalized baseline.

### OS Notifications
```bash
npx neuroskill notify "Break Time" "Your focus has been declining for 20 minutes"
```

### Raw JSON Passthrough
```bash
npx neuroskill raw '{"command":"status"}' --json
```
For any server command not yet mapped to a CLI subcommand.

Troubleshooting common errors (app not running, device disconnected, poor
signal quality): read `references/cli.md`. Six worked example interactions
(one per common user request): read `references/metrics.md`.

---

## References

- [NeuroSkill Paper — arXiv:2603.03212](https://arxiv.org/abs/2603.03212) (Kosmyna & Hauptmann, MIT Media Lab)
- [NeuroSkill Desktop App](https://github.com/NeuroSkill-com/skill) (GPLv3)
- [NeuroLoop CLI Companion](https://github.com/NeuroSkill-com/neuroloop) (GPLv3)
- [MIT Media Lab Project](https://www.media.mit.edu/projects/neuroskill/overview/)
