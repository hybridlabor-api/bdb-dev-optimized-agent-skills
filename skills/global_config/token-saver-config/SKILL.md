---
name: token-saver-config
description: Context window output compression engine for CLI commands (60-99% token reduction).
---

# Token-Saver Configuration & Diagnostics

Token-Saver is a drop-in context-window optimizer for AI coding assistants. It compresses the verbose terminal output your agent reads — `git diff`, `pytest`, `npm install`, `terraform plan`, `kubectl`, `docker` — so you spend fewer tokens, stay under your LLM context limit, and get faster, cheaper, more focused responses.

## Key Capabilities & CLI Diagnostics

After installation via `bdb-dev-optimized-agent-skills`, the `token-saver` command is available system-wide:

- **Check Installed Version:**
  ```bash
  token-saver version
  ```

- **View Savings Statistics:**
  ```bash
  token-saver stats
  token-saver stats --json
  ```

- **Benchmark Command Compression:**
  ```bash
  token-saver benchmark 'git diff'
  token-saver benchmark 'pytest' --format json
  token-saver benchmark 'git log -n 20' --dry-run
  ```

- **Check & Apply Updates:**
  ```bash
  token-saver update
  ```

## Compression Engine Rules & Guarantees

1. **Short Outputs:** Commands outputting < 200 characters pass through unchanged.
2. **Zero Information Loss:** All errors, stack traces, test failure details, and actionable diffs survive intact.
3. **Source Code Protection:** Pure source code reads (`cat *.py`, `cat *.ts`) pass through without compression.
4. **Secret Redaction:** Environment files (`.env`) automatically redact secrets before returning to the LLM.
