# Release Notes

## v2.3.0 (Ecosystem Phase 4)
- **Agentic Ingestion**: Discarded dumb crawling. `memb_ingest.py` is now explicitly driven by LLMs via `--project` and `--category` flags, ensuring highly semantic, intelligent physical categorization.
- **Auto-Pruning Vault**: The AI-first Vault (`God_Mode.md`) is now perfectly self-pruning and strictly sanitizes filenames for Obsidian WikiLink compatibility.
- **Loose Coupling Fusion (memB + OpenWiki)**: Implemented cross-skill synergistic triggers. OpenWiki can now autonomously trigger memB ingestion via silent background CLI handoffs.
- **Global AI-First Directives**: Deployed strict navigation directives to `memb-skill`, forcing all agents (Antigravity, Cursor, Claude) to read `God_Mode.md` instead of blindly scanning files.

## v2.2.1
- **memB Core Architecture Update**: `memb_ingest.py` now natively generates an AI-first flat-file markdown vault (Top-Down Radial God Mode Topology) to allow native zero-compute context navigation for local 30MB SLMs.
- Replaced `_CLAUDE.md` with a universal `agent.md` operating manual for the vector engine in the vault.

## v2.2.0
- Relicensed project under Apache 2.0 Licensing.
- Added **memB Deep Ingestion Tool** (`memb_ingest.py`) and new `/memb-ingest` skill.
- Created native **Obsidian Vault Plugin** for memB synchronization and removed static obsidian scripts.
- Added Obsidian Vault exporter and Mermaid knowledge graph visualizer tool (with radial mindmap layout).
- Implemented a non-blocking auto-update checker for npm releases.
- Added new `/bdbmediastorm` skill and updated `/bdbrainstorm` scaffolding rules.
- Added new `github-repo` skill for repository standards.
- Added trilingual README support (English, German, Portuguese) with 1:1 complete section parity.
- Synced latest BDB MCP token-saver processors.
- Fixed grandMA3 MCP architecture configuration to avoid OSC port conflicts.

## v2.1.0
- Split package into `-pro` (with OpenWiki and memB background daemons) and `@legacy` tags on NPM.
- Rewrote the OpenWiki daemon to use direct Gemma 4 API calls, fixing infinite recursion bugs and `agy` agent spawning issues.
- Updated the CLI installer with an interactive colored menu for MCP selection.
- Automated daemon deployment and `.env` credentials storage via the installer.

## v2.0.0
- Refined skill selection down to 143 highly optimized skills.
- Integrated OpenWiki documentation support.
- Cleaned up PII and added strict privacy guidelines.
