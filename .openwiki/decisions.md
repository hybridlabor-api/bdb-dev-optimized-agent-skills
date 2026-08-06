# Architectural Decision Records (ADRs)

This document records the foundational architectural decisions, rationale, and constraints across the **BDB Agent OS Ecosystem**.

---

## ADR-001: Strict Privacy & Zero PII Leakage
- **Status:** Accepted
- **Context:** Agent skill configurations and documentation are distributed to multiple developer environments and open/private repositories.
- **Decision:** Enforce a mandatory ban on hardcoded local usernames, absolute user home directory paths, raw tokens, and connection credentials across all code, documentation, and agent prompts. Use `~` or dynamic environment variables (`$HOME`, `%USERPROFILE%`).
- **Consequences:** Ensures universal portability across macOS, Linux, and Windows without risking personal information exposure.

---

## ADR-002: Direct API Execution for OpenWiki Daemon
- **Status:** Accepted
- **Context:** Earlier versions spawned sub-instances of the `agy` CLI client to update documentation via prompt loops.
- **Decision:** Replace recursive agent process invocation with direct API calls against fast, lightweight LLM endpoints.
- **Consequences:** Eliminates recursive agent loops, process deadlocks, and excessive token burn while accelerating wiki update cycles to sub-minute latencies.

---

## ADR-003: Core Mandatory memB Semantic Memory Layer
- **Status:** Accepted
- **Context:** AI agents frequently lose long-term context across session restarts, leading to repeated questioning and forgotten design decisions.
- **Decision:** Mandate `memB` as a non-toggleable core dependency bundled with a local 30MB ONNX embedding model (`all-MiniLM-L6-v2`) and local SQLite database (`~/.MemBDB/memb.db`).
- **Consequences:** Provides zero-latency, private, local semantic recall across all agent interactions without dependency on cloud vector services.

---

## ADR-004: Multi-Provider LLM Flexibility for OpenWiki
- **Status:** Accepted
- **Context:** Different deployment environments (air-gapped workstations, high-throughput cloud runners, or rate-limited free tiers) require different LLM backends. Relying exclusively on one API provider limits flexibility.
- **Decision:** Implement a dual-engine architecture in `openwiki_daemon.py`: a native Google GenAI adapter (`google-genai` SDK) and a universal OpenAI-compatible REST protocol adapter. Expose provider switching via `OPENWIKI_PROVIDER`, `OPENWIKI_MODEL`, and `OPENWIKI_BASE_URL` supporting Google (Gemma 4), Groq, Grok/xAI, Nvidia NIM, OpenRouter, OpenAI, and local runners (Ollama, LM Studio).
- **Consequences:** Allows instant fallback, local offline execution, and provider agility with zero modifications to codebase scanning logic.

---

## ADR-005: Git-Only Deterministic Code Health Analytics (Zero-Token Engine)
- **Status:** Accepted
- **Context:** Calculating codebase hotspot velocity, author churn, single-contributor bus factor, and file modification frequencies via LLMs is slow, costly, and prone to hallucinations.
- **Decision:** Implement RepoGraph analytics purely via local Git commit history analysis (e.g. `git log`, `git shortlog`) with zero external LLM token consumption. Generate both structured Markdown reports (`.openwiki/code_health.md`) and an interactive 6-panel SVG dashboard (`.openwiki/code_health_dashboard.html`).
- **Consequences:** Sub-second execution, zero API token cost, mathematical accuracy on code churn, and real-time 60-second dashboard auto-refresh.

---

## ADR-006: Modular Extension Decoupling (Creator Suite vs. Core Skills)
- **Status:** Accepted
- **Context:** Heavy generative 3D pipelines (TRELLIS, TripoSR), automated cinema video suites (OpenMontage, Remotion Video-Shotcraft, Palmier Pro NLE MCP), and local ComfyUI model weights add tens of gigabytes of dependencies and complex CUDA/toolchain requirements.
- **Decision:** Decouple these heavy creative engines into an independent companion repository (`bdb-dev-creator-extension`). Maintain `bdb-dev-optimized-agent-skills` as a lean, ultra-fast universal core skills backbone with optional add-on links during installation.
- **Consequences:** Keeps the primary agent skills pack fast to install and lightweight to clone (<25MB), while providing deep creative generative pipelines for specialized workstations via the extension repo.
