#!/usr/bin/env python3
"""
scripts/configure_claude.py
============================
Configure Claude Code to use GOLEM-3DMCP as an MCP server.

Two installation modes
----------------------
global   — Writes to ~/.claude/settings.json.
           Applies to every Claude Code project on this machine.

local    — Writes (or updates) .mcp.json in the GOLEM-3DMCP project root.
           Applies only when Claude Code is opened from that directory.
           This is the recommended default: the file already exists and
           Claude Code loads it automatically.

What gets written
-----------------
    {
      "mcpServers": {
        "golem-3dmcp": {
          "command": "<venv>/bin/python",
          "args": ["-m", "mcp_server.server"],
          "cwd": "<project-root>",
          "env": {
            "GOLEM_RHINO_HOST": "127.0.0.1",
            "GOLEM_RHINO_PORT": "9876",
            "GOLEM_GH_PORT":    "9877",
            "GOLEM_TIMEOUT":    "30"
          },
          "timeout": 60000
        }
      }
    }

Usage
-----
    python scripts/configure_claude.py [--mode global|local|ask]
                                       [--port PORT]
                                       [--gh-port PORT]
                                       [--timeout SECS]
                                       [--dry-run]
                                       [--remove]

Exit codes
----------
    0 — success
    1 — error
"""

from __future__ import annotations

import argparse
import json
import os
import pathlib
import subprocess
import sys
import time

# ---------------------------------------------------------------------------
# ANSI colour helpers (no external dependencies)
# ---------------------------------------------------------------------------
_IS_TTY = hasattr(sys.stdout, "isatty") and sys.stdout.isatty()


def _c(code: str, text: str) -> str:
    return f"\033[{code}m{text}\033[0m" if _IS_TTY else text


def ok(msg: str) -> None:
    print(_c("32", "[OK]   ") + msg)


def info(msg: str) -> None:
    print(_c("36", "[INFO] ") + msg)


def warn(msg: str) -> None:
    print(_c("33", "[WARN] ") + msg)


def error(msg: str) -> None:
    print(_c("31", "[ERR]  ") + msg, file=sys.stderr)


def header(msg: str) -> None:
    print()
    print(_c("1", msg))


# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
_PROJECT_ROOT = pathlib.Path(__file__).parent.parent.resolve()
_VENV_PYTHON = _PROJECT_ROOT / ".venv" / "bin" / "python"

_GLOBAL_SETTINGS = pathlib.Path.home() / ".claude" / "settings.json"
_LOCAL_MCP_JSON = _PROJECT_ROOT / ".mcp.json"

_SERVER_KEY = "golem-3dmcp"


# ---------------------------------------------------------------------------
# MCP server entry block
# ---------------------------------------------------------------------------
def _build_server_entry(
    project_root: pathlib.Path,
    venv_python: pathlib.Path,
    port: int,
    gh_port: int,
    timeout_secs: int,
) -> dict:
    return {
        "command": str(venv_python),
        "args": ["-m", "mcp_server.server"],
        "cwd": str(project_root),
        "env": {
            "GOLEM_RHINO_HOST": "127.0.0.1",
            "GOLEM_RHINO_PORT": str(port),
            "GOLEM_GH_PORT": str(gh_port),
            "GOLEM_TIMEOUT": str(timeout_secs),
        },
        "timeout": 60000,
    }


# ---------------------------------------------------------------------------
# Read / write helpers
# ---------------------------------------------------------------------------
def _read_json(path: pathlib.Path) -> dict:
    """Read a JSON file, returning {} if the file does not exist or is empty."""
    if not path.exists():
        return {}
    try:
        text = path.read_text(encoding="utf-8").strip()
        return json.loads(text) if text else {}
    except json.JSONDecodeError as exc:
        warn(f"Could not parse {path}: {exc}")
        warn("Will treat it as empty and overwrite the mcpServers section.")
        return {}


def _write_json(path: pathlib.Path, data: dict, dry_run: bool = False) -> None:
    text = json.dumps(data, indent=2, ensure_ascii=False) + "\n"
    if dry_run:
        info(f"[dry-run] Would write to {path}:")
        for line in text.splitlines():
            print(f"    {line}")
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    ok(f"Written: {path}")


# ---------------------------------------------------------------------------
# Install / remove logic
# ---------------------------------------------------------------------------
def _install_local(
    project_root: pathlib.Path,
    venv_python: pathlib.Path,
    port: int,
    gh_port: int,
    timeout_secs: int,
    dry_run: bool,
) -> None:
    """Write / update .mcp.json in the project root."""
    data = _read_json(_LOCAL_MCP_JSON)
    data.setdefault("mcpServers", {})[_SERVER_KEY] = _build_server_entry(
        project_root, venv_python, port, gh_port, timeout_secs
    )
    _write_json(_LOCAL_MCP_JSON, data, dry_run=dry_run)


def _install_global(
    project_root: pathlib.Path,
    venv_python: pathlib.Path,
    port: int,
    gh_port: int,
    timeout_secs: int,
    dry_run: bool,
) -> None:
    """Merge the server entry into ~/.claude/settings.json."""
    data = _read_json(_GLOBAL_SETTINGS)
    data.setdefault("mcpServers", {})[_SERVER_KEY] = _build_server_entry(
        project_root, venv_python, port, gh_port, timeout_secs
    )
    _write_json(_GLOBAL_SETTINGS, data, dry_run=dry_run)


def _remove(dry_run: bool) -> None:
    """Remove golem-3dmcp from both local and global config."""
    removed_any = False
    for path in (_LOCAL_MCP_JSON, _GLOBAL_SETTINGS):
        data = _read_json(path)
        servers = data.get("mcpServers", {})
        if _SERVER_KEY in servers:
            del servers[_SERVER_KEY]
            if not servers:
                data.pop("mcpServers", None)
            removed_any = True
            _write_json(path, data, dry_run=dry_run)
            info(f"Removed '{_SERVER_KEY}' from {path}")
    if not removed_any:
        info("GOLEM-3DMCP was not found in any config file — nothing to remove.")


# ---------------------------------------------------------------------------
# Interactive mode picker
# ---------------------------------------------------------------------------
def _ask_mode() -> str:
    """Prompt the user to choose global or local installation."""
    print()
    print("  How would you like to configure Claude Code?")
    print()
    print("    [1] local   — .mcp.json in this project directory (recommended)")
    print("              Claude Code loads this automatically when you open the project.")
    print()
    print("    [2] global  — ~/.claude/settings.json")
    print("              GOLEM-3DMCP will be available in all Claude Code sessions.")
    print()
    while True:
        try:
            choice = input("  Enter 1 or 2 (default: 1): ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            sys.exit(0)
        if choice in ("", "1"):
            return "local"
        if choice == "2":
            return "global"
        print("  Please enter 1 or 2.")


# ---------------------------------------------------------------------------
# Verification: check the MCP server can be invoked
# ---------------------------------------------------------------------------
def _verify_server(venv_python: pathlib.Path) -> bool:
    """
    Attempt to import mcp_server.server via the venv Python to verify the
    package is installed and importable.

    Returns True on success.
    """
    if not venv_python.exists():
        warn(f"venv Python not found: {venv_python}")
        warn("Run ./setup.sh first to create the virtual environment.")
        return False
    try:
        result = subprocess.run(
            [str(venv_python), "-c", "import mcp_server.server; print('ok')"],
            capture_output=True,
            text=True,
            timeout=15,
        )
        if result.returncode == 0 and "ok" in result.stdout:
            ok("MCP server module is importable from the venv.")
            return True
        else:
            warn("MCP server import check failed.")
            if result.stderr:
                warn(result.stderr.strip())
            return False
    except subprocess.TimeoutExpired:
        warn("Import check timed out.")
        return False
    except OSError as exc:
        warn(f"Could not run venv Python: {exc}")
        return False


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="configure_claude",
        description=(
            "Configure Claude Code to use GOLEM-3DMCP as an MCP server.\n\n"
            "Writes the server definition to either the project-local .mcp.json\n"
            "or to the global ~/.claude/settings.json, depending on your choice."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--mode",
        choices=["local", "global", "ask"],
        default="ask",
        help=(
            "Where to write the config: 'local' (.mcp.json in the project), "
            "'global' (~/.claude/settings.json), or 'ask' (interactive prompt). "
            "Default: ask"
        ),
    )
    parser.add_argument(
        "--port",
        type=int,
        default=9876,
        metavar="PORT",
        help="GOLEM Rhino TCP port (default: 9876)",
    )
    parser.add_argument(
        "--gh-port",
        type=int,
        default=9877,
        metavar="PORT",
        help="GOLEM Grasshopper TCP port (default: 9877)",
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=30,
        metavar="SECS",
        help="GOLEM command timeout in seconds (default: 30)",
    )
    parser.add_argument(
        "--remove",
        action="store_true",
        help="Remove the GOLEM-3DMCP server entry from both config files",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview what would be written without touching any files",
    )
    return parser.parse_args()


def main() -> None:
    args = _parse_args()

    print()
    print(_c("1", "GOLEM-3DMCP — Claude Code Configuration"))
    print("=" * 44)

    # -----------------------------------------------------------------------
    # Remove path
    # -----------------------------------------------------------------------
    if args.remove:
        header("Removing GOLEM-3DMCP from Claude Code config ...")
        _remove(dry_run=args.dry_run)
        print()
        return

    # -----------------------------------------------------------------------
    # Resolve venv python
    # -----------------------------------------------------------------------
    venv_python = _VENV_PYTHON
    if not venv_python.exists():
        warn(f"Expected venv Python not found: {venv_python}")
        warn("The config will still be written, but you should run ./setup.sh first.")

    # -----------------------------------------------------------------------
    # Determine mode
    # -----------------------------------------------------------------------
    mode = args.mode
    if mode == "ask":
        mode = _ask_mode()

    # -----------------------------------------------------------------------
    # Show what will be written
    # -----------------------------------------------------------------------
    entry = _build_server_entry(
        _PROJECT_ROOT, venv_python, args.port, args.gh_port, args.timeout
    )
    header(f"Configuration ({mode}) ...")
    print()
    print(_c("2", f"  Key: {_SERVER_KEY}"))
    for line in json.dumps(entry, indent=4).splitlines():
        print(f"  {line}")
    print()

    # -----------------------------------------------------------------------
    # Write the config
    # -----------------------------------------------------------------------
    if mode == "local":
        _install_local(
            _PROJECT_ROOT, venv_python, args.port, args.gh_port, args.timeout,
            dry_run=args.dry_run,
        )
        target_path = _LOCAL_MCP_JSON
    else:
        _install_global(
            _PROJECT_ROOT, venv_python, args.port, args.gh_port, args.timeout,
            dry_run=args.dry_run,
        )
        target_path = _GLOBAL_SETTINGS

    # -----------------------------------------------------------------------
    # Verify the server module is importable
    # -----------------------------------------------------------------------
    header("Verifying MCP server module ...")
    _verify_server(venv_python)

    # -----------------------------------------------------------------------
    # Summary
    # -----------------------------------------------------------------------
    header("Configuration complete.")
    print()
    if mode == "local":
        print(f"  Config written to  : {target_path}")
        print()
        print("  Claude Code will load this automatically when you open the project.")
        print("  If you use the claude CLI, run it from:")
        print(f"    cd {_PROJECT_ROOT}")
        print("    claude")
    else:
        print(f"  Config written to  : {target_path}")
        print()
        print("  GOLEM-3DMCP will be available in all Claude Code sessions.")

    print()
    print("  Next: ensure Rhinoceros 8 is open and the GOLEM plugin is running:")
    print(f"    python {_PROJECT_ROOT / 'scripts' / 'start_rhino_server.py'}")
    print()
    print("  Then verify the connection:")
    print(f"    python {_PROJECT_ROOT / 'scripts' / 'test_connection.py'}")
    print()

    if args.dry_run:
        print(_c("33", "  (dry-run mode — no files were actually written)"))
        print()


if __name__ == "__main__":
    main()
