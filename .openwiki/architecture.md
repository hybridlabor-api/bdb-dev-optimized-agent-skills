# Architecture

This document tracks the technical structure of the skills pack.

## Core Components
- **installer.js**: A Node.js interactive CLI that copies MCP configurations and global skills into `~/.gemini/config/`.
- **OpenWiki Daemon (`openwiki_daemon.py`)**: A Python background process running on a schedule (LaunchAgent / Task Scheduler) that directly queries the Gemma 4 API (via `google-genai` SDK) to update codebase markdown without spinning up new agent instances.
- **memB Core Module**: A required local semantic memory layer utilizing ONNX-quantized models and SQLite to retain agent context safely.

## Directory Structure
- Each skill is contained in a separate subdirectory.
- A `SKILL.md` file defines the prompt, behavior, and capabilities.
- Additional scripts (Python, Bash) reside in the skill's `scripts/` folder.
