# Skill → Model Index

_Auto-generated. 224 skills · 187 agnostic · 37 model-touching._

Each skill tagged by the local model / specialist role it invokes (or **agnostic**), with what it does. A skill appears under every lane it references. Regenerate: `python3 skills/scripts/build_skill_model_index.py`.

## By specialist role (preferred — model-indirect)

### specialist role `code`
- `mlops/local-model-ops` — Operate Hermes local inference on this Mac.
- `mlops/specialist-routing` — Route a task to the right local specialist model.

### specialist role `controller`
- `mlops/local-model-ops` — Operate Hermes local inference on this Mac.
- `mlops/specialist-routing` — Route a task to the right local specialist model.

### specialist role `extract`
- `mlops/specialist-routing` — Route a task to the right local specialist model.

### specialist role `research`
- `mlops/local-model-ops` — Operate Hermes local inference on this Mac.
- `mlops/specialist-routing` — Route a task to the right local specialist model.

### specialist role `think`
- `mlops/local-model-ops` — Operate Hermes local inference on this Mac.
- `mlops/specialist-routing` — Route a task to the right local specialist model.

### specialist role `vision-fast`
- `mlops/local-model-ops` — Operate Hermes local inference on this Mac.
- `mlops/specialist-routing` — Route a task to the right local specialist model.

### specialist role `writer`
- `mlops/local-model-ops` — Operate Hermes local inference on this Mac.
- `mlops/specialist-routing` — Route a task to the right local specialist model.

## By model / route ID (direct)

### BASE — ornith-uncensored (Qwen3.6-35B-A3B huihui, vision, :1235)
- `autonomous-ai-agents/openhands` — Delegate coding to OpenHands CLI (model-agnostic, LiteLLM).
- `devops/log-triage` — Parse and cluster log files for incident triage.
- `devops/self-healing` — Monitor, detect, and remediate local service health.
- `mlops/guidance` — Constrain LLM output with grammars via Guidance.
- `mlops/instructor` — Extract Pydantic-validated data from LLMs with Instructor.
- `mlops/local-model-ops` — Operate Hermes local inference on this Mac.
- `mlops/research/dspy` — DSPy: declarative LM programs, auto-optimize prompts, RAG.
- `mlops/specialist-routing` — Route a task to the right local specialist model.
- `research/crypto-market` — Keyless crypto market data and public wallet lookups.
- `research/darwinian-evolver` — Evolve prompts/regex/SQL/code with Imbue's evolution loop.
- `research/deal-hunting` — Hunt software and hardware deals from free RSS feeds.
- `research/infra-monitor` — Monitor domain infrastructure drift over time.
- `research/market-pulse` — Keyless crypto + prediction-market snapshot dashboard.
- `research/network-recon` — Keyless DNS and infrastructure reconnaissance.
- `research/open-databases` — Query free keyless public research databases.
- `research/polymarket` — Query Polymarket: markets, prices, orderbooks, history.
- `research/portfolio-tracker` — Keyless crypto portfolio valuation from a holdings file.
- `research/scrapling` — Scrapling web scraping with stealth and crawling.
- `research/social-footprint` — Keyless username and email footprint recon.
- `research/watch-notify` — Watch a URL for changes and push an alert.
- `social-media/scrapecreators` — ScrapeCreators API for social profiles (paid key).
- `web-development/page-agent` — Embed alibaba/page-agent in-page GUI agent in a web app.

### CODER — qwen3-coder (Qwen3-Coder-30B-A3B huihui, :1235)
- `autonomous-ai-agents/openhands` — Delegate coding to OpenHands CLI (model-agnostic, LiteLLM).
- `creative/cydonia-creative-writing` — Draft and revise fiction with the local Cydonia model.
- `creative/genre-novel-production` — Write genre novels with Cydonia and continuity checks.
- `creative/quill-story-production` — Draft and revise fiction with Cydonia as Quill.
- `creative/screenplay-production` — Write and revise screenplays with local Cydonia.
- `devops/log-triage` — Parse and cluster log files for incident triage.
- `devops/self-healing` — Monitor, detect, and remediate local service health.
- `finance/prediction-market-analysis` — Find mispriced Polymarket outcomes with local LLMs.
- `mlops/local-model-ops` — Operate Hermes local inference on this Mac.
- `mlops/specialist-routing` — Route a task to the right local specialist model.
- `research/crypto-market` — Keyless crypto market data and public wallet lookups.
- `research/deal-hunting` — Hunt software and hardware deals from free RSS feeds.
- `research/infra-monitor` — Monitor domain infrastructure drift over time.
- `research/market-pulse` — Keyless crypto + prediction-market snapshot dashboard.
- `research/network-recon` — Keyless DNS and infrastructure reconnaissance.
- `research/open-databases` — Query free keyless public research databases.
- `research/polymarket` — Query Polymarket: markets, prices, orderbooks, history.
- `research/portfolio-tracker` — Keyless crypto portfolio valuation from a holdings file.
- `research/prediction-markets-ai` — Find mispriced prediction markets with local LLMs.
- `research/scrapling` — Scrapling web scraping with stealth and crawling.
- `research/social-footprint` — Keyless username and email footprint recon.
- `research/watch-notify` — Watch a URL for changes and push an alert.
- `research/wildcard-triage-routing` — Scope a request and route to a War Room specialist.
- `social-media/scrapecreators` — ScrapeCreators API for social profiles (paid key).

### WRITER — Cydonia-24B (Ollama)
- `creative/cydonia-creative-writing` — Draft and revise fiction with the local Cydonia model.
- `creative/genre-novel-production` — Write genre novels with Cydonia and continuity checks.
- `creative/genre-writer-cascade` — Select the matching standby genre profile for Quill.
- `creative/manuscript-continuity-ledger` — Build and audit manuscript continuity artifacts.
- `creative/quill-story-production` — Draft and revise fiction with Cydonia as Quill.
- `creative/screenplay-production` — Write and revise screenplays with local Cydonia.
- `media/director-video-production` — Produce local video from brief to final artifact.
- `mlops/local-model-ops` — Operate Hermes local inference on this Mac.
- `mlops/specialist-routing` — Route a task to the right local specialist model.

### RESEARCH — Qwythos-9B (Ollama)
- `mlops/local-model-ops` — Operate Hermes local inference on this Mac.
- `mlops/specialist-routing` — Route a task to the right local specialist model.
- `research/mythos-evidence-synthesis` — Reconcile multiple sources into a cited brief.

### RERANK — Qwen3-Reranker (:1235)
- `mlops/rag-retrieval` — Local RAG retrieval with embeddings and reranking.
- `research/last30days` — Research what people say about a topic in 30 days.

### RERANK — Qwen3-Reranker (Ollama)
- `mlops/rag-retrieval` — Local RAG retrieval with embeddings and reranking.

### EMBED — Qwen3-Embedding
- `media/composer-audio-production` — Compose and produce local music and audio assets.
- `mlops/rag-retrieval` — Local RAG retrieval with embeddings and reranking.

### EMBED — nomic-embed-text
- `mlops/rag-retrieval` — Local RAG retrieval with embeddings and reranking.
- `research/workspace-rag` — Local semantic search over Hermes workspace notes.

### EMBED — bge-m3
- `mlops/rag-retrieval` — Local RAG retrieval with embeddings and reranking.

## Model-agnostic (no local model)

187 skills — external APIs, pure tooling, or docs.

<details><summary>list</summary>

- `apple/apple-notes` — Manage Apple Notes via memo CLI: create, search, edit.
- `apple/apple-reminders` — Apple Reminders via remindctl: add, list, complete.
- `apple/findmy` — Track Apple devices/AirTags via FindMy.app on macOS.
- `apple/imessage` — Send and receive iMessages/SMS via the imsg CLI on macOS.
- `apple/signal` — Send and receive Signal messages via signal-cli.
- `autonomous-ai-agents/antigravity-cli` — Operate the Antigravity CLI (agy): plugins, auth, sandbox.
- `autonomous-ai-agents/blackbox` — Delegate coding tasks to the Blackbox AI CLI.
- `autonomous-ai-agents/claude-code` — Delegate coding to Claude Code CLI (features, PRs).
- `autonomous-ai-agents/codex` — Delegate coding to OpenAI Codex CLI (features, PRs).
- `autonomous-ai-agents/grok` — Delegate coding to xAI Grok Build CLI (features, PRs).
- `autonomous-ai-agents/hermes-agent` — Configure, extend, or contribute to Hermes Agent.
- `autonomous-ai-agents/opencode` — Delegate coding to OpenCode CLI (features, PR review).
- `autonomous-ai-agents/war-room-specialist-cascade` — Route War Room requests to hidden niche profiles.
- `blockchain/evm` — Read-only EVM client: wallets, tokens, gas across 8 chains.
- `blockchain/hyperliquid` — Hyperliquid market data, account history, trade review.
- `blockchain/solana` — Query Solana wallets, tokens, NFTs with USD prices.
- `computer-use` — Drive the desktop in the background via computer_use.
- `computer-use/browser-first` — Prefer the browser toolset over computer_use for web.
- `creative/architecture-diagram` — Dark-themed SVG architecture/cloud/infra diagrams as HTML.
- `creative/ascii-art` — ASCII art: pyfiglet, cowsay, boxes, image-to-ascii.
- `creative/ascii-video` — ASCII video: convert video/audio to colored ASCII MP4/GIF.
- `creative/baoyu-infographic` — Infographics: 21 layouts x 21 styles (信息图, 可视化).
- `creative/blender-mcp` — Control Blender via the blender-mcp addon and bpy.
- `creative/canvas-local-visual-production` — Render a visual brief locally and verify the image.
- `creative/claude-design` — Design one-off HTML artifacts (landing, deck, prototype).
- `creative/comfyui` — Generate images, video, audio with ComfyUI workflows.
- `creative/creative-production-bundle` — Route a creative brief across visual media specialists.
- `creative/design-md` — Author/validate/export Google's DESIGN.md token spec files.
- `creative/excalidraw` — Hand-drawn Excalidraw JSON diagrams (arch, flow, seq).
- `creative/flux-local` — Generate images locally with FLUX.1 dev or schnell.
- `creative/humanizer` — Humanize text: strip AI-isms and add real voice.
- `creative/kanban-video-orchestrator` — Run a multi-agent video pipeline on Hermes Kanban.
- `creative/manim-video` — Manim CE animations: 3Blue1Brown math/algo videos.
- `creative/novel-generator` — Generate full novels autonomously via Claude or Codex.
- `creative/p5js` — p5.js sketches: gen art, shaders, interactive, 3D.
- `creative/popular-web-designs` — 54 real design systems (Stripe, Linear, Vercel) as HTML/CSS.
- `creative/pretext` — Build text-as-geometry browser demos with pretext.
- `creative/sketch` — Throwaway HTML mockups: 2-3 design variants to compare.
- `creative/songwriting-and-ai-music` — Songwriting craft and Suno AI music prompts.
- `creative/touchdesigner-mcp` — Control TouchDesigner via twozero MCP for visuals.
- `data-science/jupyter-live-kernel` — Iterative Python via live Jupyter kernel (hamelnb).
- `devops/changelog` — Build a Keep-a-Changelog CHANGELOG.md from git history.
- `devops/cli` — Run 150+ AI apps via the inference.sh CLI (infsh).
- `devops/cron-schedule` — Write, read, fix, or explain cron expressions.
- `devops/dependency-audit` — Audit deps for staleness and CVEs with local scanners.
- `devops/docker-management` — Manage Docker containers, images, and Compose stacks.
- `devops/dockerfile-lint` — Lint a Dockerfile for security, correctness, and size.
- `devops/env-audit` — Check env vars for missing, unused, or drifted keys.
- `devops/git-hygiene` — Keep a repo clean of secrets, big files, bad commits.
- `devops/hermes-s6-container-supervision` — Edit the s6-overlay tree in the Hermes Docker image.
- `devops/pi-webfetch` — Fetch URLs as markdown, text, or HTML for pi.
- `devops/reliability-operations-bundle` — Coordinate a reliability response from signal to fix.
- `devops/sentinel-security-assurance` — Audit a codebase or runtime for security risks.
- `devops/sentry-incident-response` — Diagnose and recover from a runtime incident.
- `devops/watchers` — Poll RSS, JSON APIs, and GitHub with watermark dedup.
- `dogfood` — Exploratory QA of web apps: find bugs, evidence, reports.
- `duckduckgo-search` — Free DuckDuckGo web search, no API key needed.
- `email/agentmail` — Give the agent its own email inbox via AgentMail.
- `email/himalaya` — Himalaya CLI: IMAP/SMTP email from terminal.
- `finance/3-statement-model` — Build integrated 3-statement Excel models.
- `finance/comps-analysis` — Build comparable company analysis in Excel.
- `finance/dcf-model` — Build DCF valuation models in Excel.
- `finance/excel-author` — Build auditable Excel workbooks with openpyxl.
- `finance/lbo-model` — Build leveraged buyout (LBO) models in Excel.
- `finance/merger-model` — Build accretion/dilution merger models in Excel.
- `finance/pptx-author` — Build PowerPoint decks with python-pptx.
- `finance/stocks` — Stock quotes, history, search, compare, crypto via Yahoo.
- `github/codebase-inspection` — Inspect codebases w/ pygount: LOC, languages, ratios.
- `github/forge-github-delivery` — Carry one GitHub change to a merge-ready handoff.
- `github/github-auth` — GitHub auth setup: HTTPS tokens, SSH keys, gh CLI login.
- `github/github-code-review` — Review PRs: diffs, inline comments via gh or REST.
- `github/github-issues` — Create, triage, label, assign GitHub issues via gh or REST.
- `github/github-maintainer-bundle` — Maintain a GitHub repo across the full lifecycle.
- `github/github-pr-workflow` — GitHub PR lifecycle: branch, commit, open, CI, merge.
- `github/github-repo-management` — Clone/create/fork repos; manage remotes, releases.
- `github/workspace-extension-integration` — Adopt external repos as hermes plugins or tools.
- `health/fitness-nutrition` — Plan gym workouts and track nutrition macros.
- `hermes-desktop-plugins` — Write desktop app plugins that add UI panes and commands.
- `mcp/fastmcp` — Build and deploy MCP servers with FastMCP in Python.
- `media/audiobook-narration-production` — Produce local audiobook narration with Kokoro.
- `media/chatterbox-tts` — Local TTS with voice cloning via Chatterbox MLX.
- `media/gif-search` — Search/download GIFs from Tenor via curl + jq.
- `media/hawkeye-visual-evidence` — Inspect UIs and images for visual evidence.
- `media/heartmula` — HeartMuLa: Suno-like song generation from lyrics + tags.
- `media/image-edit` — Edit images locally with sips or ImageMagick.
- `media/media-production-bundle` — Produce a coordinated multi-format media package.
- `media/previsualization-production` — Turn a script into storyboards and animatics.
- `media/songsee` — Audio spectrograms/features (mel, chroma, MFCC) via CLI.
- `media/transcript-caption-production` — Transcribe local audio to timestamped captions.
- `media/youtube-content` — YouTube transcripts to summaries, threads, blogs.
- `meta/skill-factory` — Generate reusable Hermes skills from workflows.
- `migration/openclaw-migration` — Migrate an OpenClaw setup into Hermes Agent.
- `mlops/chroma` — Store and search embeddings with Chroma.
- `mlops/clip` — Zero-shot image classification and search with CLIP.
- `mlops/evaluation/lm-evaluation-harness` — lm-eval-harness: benchmark LLMs (MMLU, GSM8K, etc.).
- `mlops/evaluation/weights-and-biases` — W&B: log ML experiments, sweeps, model registry, dashboards.
- `mlops/huggingface-hub` — HuggingFace hf CLI: search/download/upload models, datasets.
- `mlops/huggingface-tokenizers` — Fast tokenization with HuggingFace Tokenizers.
- `mlops/inference/llama-cpp` — llama.cpp local GGUF inference + HF Hub model discovery.
- `mlops/inference/vllm` — vLLM: high-throughput LLM serving, OpenAI API, quantization.
- `mlops/lambda-labs` — Run ML workloads on Lambda Labs GPU cloud.
- `mlops/llava` — Conversational image understanding with LLaVA.
- `mlops/local-ai-lifecycle-bundle` — Manage the local model lifecycle end to end.
- `mlops/local-model-audit` — Verify whether a project's local ML mode works.
- `mlops/modal` — On-demand serverless GPU cloud for ML workloads.
- `mlops/models/audiocraft` — AudioCraft: MusicGen text-to-music, AudioGen text-to-sound.
- `mlops/models/segment-anything` — SAM: zero-shot image segmentation via points, boxes, masks.
- `mlops/nemo-curator` — GPU-accelerated data curation for LLM training.
- `mlops/pinecone` — Managed vector database for RAG and semantic search.
- `mlops/pytorch-fsdp` — Fully Sharded Data Parallel training with PyTorch.
- `mlops/pytorch-lightning` — High-level PyTorch training with the Trainer class.
- `mlops/saelens` — Train and analyze Sparse Autoencoders with SAELens.
- `mlops/slime` — LLM RL post-training with slime (Megatron+SGLang).
- `note-taking/obsidian` — Read, search, create, and edit notes in the Obsidian vault.
- `orca-cli` — Operate Orca worktrees, terminals, and browser.
- `orchestration` — Multi-agent coordination with messages and DAGs.
- `osint-investigation` — Public-records OSINT investigation framework.
- `payments/mpp-agent` — Pay HTTP 402 APIs via Machine Payments Protocol (MPP).
- `payments/stripe-link-cli` — Agent payments via Stripe Link — cards, SPT, approvals.
- `productivity/airtable` — Airtable REST API via curl. Records CRUD, filters, upserts.
- `productivity/archivist-knowledge-pipeline` — Turn documents into one canonical knowledge artifact.
- `productivity/career-campaign-bundle` — Run an end-to-end job application campaign.
- `productivity/cover-letter` — Draft a 4-paragraph cover letter for a job posting.
- `productivity/csv-insights` — Summarize, filter, and aggregate CSV or TSV files.
- `productivity/google-workspace` — Gmail, Calendar, Drive, Docs, Sheets via gws CLI or Python.
- `productivity/here-now` — Publish static sites and store files on here.now.
- `productivity/ics-calendar` — Create an .ics calendar file or event invite.
- `productivity/interview-prep` — Prep for a teaching-role interview from a posting.
- `productivity/job-search-tracking` — Track job applications and watch listings locally.
- `productivity/knowledge-workflow-bundle` — Capture and transform knowledge across documents.
- `productivity/maps` — Geocode, POIs, routes, timezones via OpenStreetMap/OSRM.
- `productivity/memento-flashcards` — Spaced-repetition flashcards with agent grading.
- `productivity/nano-pdf` — Edit PDF text/typos/titles via nano-pdf CLI (NL prompts).
- `productivity/notion` — Notion API + ntn CLI: pages, databases, markdown, Workers.
- `productivity/ocr-and-documents` — Extract text from PDFs/scans (pymupdf, marker-pdf).
- `productivity/petdex` — Install and select animated petdex mascots for Hermes.
- `productivity/powerpoint` — Create, read, edit .pptx decks, slides, notes, templates.
- `productivity/resume-tailor` — Tailor a resume to a specific job posting.
- `productivity/structured-document-extraction` — Extract JSON fields and tables from documents.
- `productivity/teams-meeting-pipeline` — Operate the Teams meeting summary pipeline.
- `productivity/time-tracking` — Start, stop, and report time in a local ledger.
- `research/agent-reach` — Search the web and 15 platforms via routed backends.
- `research/arxiv` — Search arXiv papers by keyword, author, category, or ID.
- `research/bioinformatics` — Gateway to 400+ bioinformatics skills on demand.
- `research/blogwatcher` — Monitor blogs and RSS/Atom feeds via blogwatcher-cli tool.
- `research/drug-discovery` — Drug discovery assistant for compound analysis.
- `research/ethical-investigation-bundle` — Authorized OSINT investigations with evidence control.
- `research/evidence-research-bundle` — Answer research questions with cited web evidence.
- `research/gitnexus-explorer` — Index a codebase into a GitNexus knowledge graph.
- `research/llm-wiki` — Karpathy's LLM Wiki: build/query interlinked markdown KB.
- `research/multi-source-investigation` — Cross-database investigation with evidence validation.
- `research/osint-reconnaissance` — Digital footprint OSINT via Sherlock and Google Dorks.
- `research/parallel-cli` — Parallel CLI for web search, research, and enrichment.
- `research/platform-scrape-research` — Scrape one platform on a topic into a report.
- `research/quick-summary` — Summarize or extract key points from text.
- `research/research-paper-writing` — Write ML papers for NeurIPS/ICML/ICLR: design→submit.
- `security/1password` — Set up and use the 1Password CLI (op) for secrets.
- `security/credit-card-investigation` — Investigate leaked card data with BIN/IIN lookups.
- `security/dark-web-monitor` — Watch the dark web and export threat-intel feeds.
- `security/dark-web-osint` — Search, fetch, and analyze .onion sites for OSINT.
- `security/maigret` — OSINT username search across networks via Maigret.
- `security/oss-forensics` — Forensic supply-chain investigation of GitHub repos.
- `security/sherlock` — OSINT username search across networks via Sherlock.
- `security/tor-fetch` — Fetch a webpage over Tor, including .onion sites.
- `smart-home/openhue` — Control Philips Hue lights, scenes, rooms via OpenHue CLI.
- `social-media/xurl` — X/Twitter via xurl CLI: post, search, DM, media, v2 API.
- `software-development/code-wiki` — Generate wiki docs + Mermaid diagrams for any codebase.
- `software-development/git-bisect` — Find the commit that introduced a regression.
- `software-development/hermes-agent-skill-authoring` — Create, revise, validate, and bundle Hermes repo skills.
- `software-development/node-inspect-debugger` — Debug Node.js via --inspect + Chrome DevTools Protocol CLI.
- `software-development/plan` — Write an actionable markdown plan, no execution.
- `software-development/python-debugpy` — Debug Python: pdb REPL + debugpy remote (DAP).
- `software-development/regex-craft` — Write, fix, test, or explain a regular expression.
- `software-development/repo-location-discovery` — Verify where a project lives before writing files.
- `software-development/requesting-code-review` — Pre-commit review: security scan, quality gates, auto-fix.
- `software-development/rest-graphql-debug` — Debug REST/GraphQL APIs: status codes, auth, schemas, repro.
- `software-development/simplify-code` — Parallel 3-agent cleanup of recent code changes.
- `software-development/software-delivery-bundle` — Route a software change through each delivery stage.
- `software-development/spike` — Throwaway experiments to validate an idea before build.
- `software-development/sql-review` — Review a SQL statement for correctness and safety.
- `software-development/stacktrace-triage` — Localize where a stack trace or traceback fails.
- `software-development/subagent-driven-development` — Execute plans via delegate_task subagents (2-stage review).
- `software-development/systematic-debugging` — 4-phase root cause debugging: understand bugs before fixing.
- `software-development/test-driven-development` — TDD: enforce RED-GREEN-REFACTOR, tests before code.
- `software-development/vanguard-engineering-ops` — Own multi-step engineering and local-model ops.
- `web-development/cloudflare-temporary-deploy` — Deploy a Worker live, no account, via wrangler --temporary.
- `yuanbao` — Yuanbao (元宝) groups: @mention users, query info/members.

</details>