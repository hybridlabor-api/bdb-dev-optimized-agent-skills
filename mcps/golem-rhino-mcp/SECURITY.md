# Security Policy

## Overview

GOLEM-3DMCP is an **intentionally unrestricted** bridge between AI agents and Rhinoceros 3D. It is designed for **single-user development machines** where the AI agent is trusted. This document explains the security model, trust boundaries, and best practices.

## Architecture

```
AI Agent (Claude Code / Cursor / Windsurf)
    │  stdio (MCP protocol)
    ▼
MCP Server  (golem-3dmcp, Python 3.10+)
    │  TCP, localhost only (127.0.0.1:9876)
    ▼
Rhino Plugin  (Python 3.9, runs inside Rhino 8)
    │  RhinoCommon / rhinoscriptsyntax
    ▼
Rhinoceros 3D Document
```

All communication between the MCP server and Rhino plugin is **localhost-only** (`127.0.0.1`). No traffic leaves the machine.

## Script Execution Model

GOLEM exposes four script execution tools that grant the AI agent **full programmatic access** to Rhino's runtime:

| Tool | Description | Engine |
|------|-------------|--------|
| `execute_python` | Run arbitrary Python code with full RhinoCommon access | `exec()` |
| `execute_rhinoscript` | Run RhinoScript/VBScript commands | `rs.Command()` |
| `evaluate_expression` | Evaluate a single Python expression | `eval()` |
| `run_rhino_command` | Execute Rhino command-line commands | Rhino CLI |

### What executed code can access

Code executed via `execute_python` runs in a namespace containing:

- **`Rhino`** — Full RhinoCommon .NET API
- **`sc` (scriptcontext)** — Active document (`sc.doc`), application state
- **`rs` (rhinoscriptsyntax)** — High-level Rhino scripting functions
- **`System`** — .NET System namespace
- **`__builtins__`** — All Python built-in functions

There is **no sandbox**. Executed code has the same permissions as the Rhino process itself, which typically means full user-level access to the filesystem, network, and other system resources.

### Why this is intentional

GOLEM is a **power tool for professionals**. Sandboxing would cripple the ability to:

- Access custom libraries and plugins
- Read/write files (export models, load references)
- Interact with other applications and services
- Use the full depth of RhinoCommon and .NET

The security boundary is the **AI agent's MCP host** (Claude Code, Cursor, etc.), which mediates what the agent can do via tool-approval prompts.

## Trust Boundaries

| Boundary | Protection |
|----------|------------|
| Network exposure | Localhost-only binding (`127.0.0.1`). No remote connections accepted. |
| Protocol | Length-prefixed JSON with a 64 MB payload limit to prevent memory exhaustion. |
| Threading | All Rhino operations are serialized through the UI thread via `RhinoApp.InvokeOnUiThread`, preventing race conditions. |
| Timeouts | Default 30-second timeout per operation (120 seconds for heavy operations) to prevent hangs. |
| Agent control | MCP hosts (Claude Code, Cursor) prompt users before the agent calls tools, providing a human-in-the-loop check. |

## What GOLEM Does NOT Provide

- **Authentication or authorization** — Any local process that can connect to `127.0.0.1:9876` can send commands.
- **Code sandboxing** — Executed code runs with full process permissions.
- **Input sanitization on scripts** — Code strings are passed directly to `exec()`/`eval()`.
- **Audit logging** — Operations are not logged to a persistent audit trail beyond Rhino's command history.
- **Multi-user isolation** — Designed for single-user machines only.

## Deployment Recommendations

1. **Run on single-user development machines only.** Do not expose GOLEM on shared servers or multi-tenant environments.

2. **Do not change the bind address.** The default `127.0.0.1` binding ensures only local processes can connect. Binding to `0.0.0.0` would expose Rhino to the network.

3. **Review AI-generated scripts.** MCP hosts like Claude Code show tool calls before execution. Review `execute_python` and `run_rhino_command` calls, especially those that access the filesystem or network.

4. **Keep Rhino and GOLEM updated.** Install updates promptly to benefit from upstream security fixes.

5. **Do not run untrusted MCP clients.** Only use GOLEM with MCP hosts you trust (Claude Code, Cursor, Windsurf).

## Supported Versions

| Version | Supported |
|---------|-----------|
| 0.1.x   | Yes       |

## Reporting a Vulnerability

If you discover a security vulnerability in GOLEM-3DMCP, please report it responsibly:

1. **Do not** open a public GitHub issue for security vulnerabilities.
2. **Email** the maintainers directly (see the repository's profile for contact information), or use [GitHub's private vulnerability reporting](https://github.com/TheKingHippopotamus/GOLEM-3DMCP-Rhino-/security/advisories/new).
3. Include a description of the vulnerability, steps to reproduce, and potential impact.
4. Allow reasonable time for a fix before public disclosure.

We aim to acknowledge reports within 48 hours and provide a fix or mitigation within 7 days for critical issues.
