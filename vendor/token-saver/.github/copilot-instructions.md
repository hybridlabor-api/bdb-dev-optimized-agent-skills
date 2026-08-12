---
name: heimdall-token-saver
description: Instructions for using Heimdall Token Saver to compress terminal output.
---

# Heimdall Token Saver (Context Compression)

You have access to the `token-saver` CLI tool. 
Whenever you execute terminal commands that produce large outputs (e.g., `git diff`, `npm install`, `pytest`, `cargo test`, `kubectl`, `terraform`), you MUST prefix your command with `token-saver run`.

Example:
❌ `git diff`
✅ `token-saver run 'git diff'`

❌ `pytest -v`
✅ `token-saver run 'pytest -v'`

This compresses the terminal output, saving 60-99% of your context window tokens while preserving all critical errors and information. Do not use this for interactive commands like `nano` or `vim`.
