#!/usr/bin/env python3
"""
scripts/start_rhino_server.py
==============================
Convenience script to start (or stop/restart) the GOLEM-3DMCP server inside
a running Rhino instance by invoking the rhinocode CLI.

How it works
------------
1. Locates the rhinocode binary (Rhino 8 ships it at a known path on macOS).
2. Calls ``rhinocode list`` to detect whether a Rhino instance is running.
3. Executes ``rhino_plugin/startup.py`` via ``rhinocode script`` so the GOLEM
   TCP server starts (or restarts) inside Rhino's Python environment.

Flags
-----
    --stop      Send the shutdown command to a running GOLEM server via the
                TCP bridge instead of starting it.
    --restart   Stop and then start the server.
    --port      Override the default TCP port (9876).
    --host      Override the default host (127.0.0.1).
    --dry-run   Print the rhinocode command that would be run, without running it.

Usage
-----
    python scripts/start_rhino_server.py
    python scripts/start_rhino_server.py --restart
    python scripts/start_rhino_server.py --stop
    python scripts/start_rhino_server.py --port 9999
"""

from __future__ import annotations

import argparse
import json
import os
import pathlib
import socket
import struct
import subprocess
import sys
import time
import uuid

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
_STARTUP_PY = _PROJECT_ROOT / "rhino_plugin" / "startup.py"

_RHINOCODE_CANDIDATES = [
    pathlib.Path("/Applications/Rhino 8.app/Contents/Resources/bin/rhinocode"),
    pathlib.Path("/Applications/RhinoWIP.app/Contents/Resources/bin/rhinocode"),
]


# ---------------------------------------------------------------------------
# rhinocode location
# ---------------------------------------------------------------------------
def _find_rhinocode() -> pathlib.Path | None:
    """Return the path to the rhinocode binary, or None if not found."""
    # Check explicit macOS paths first
    for p in _RHINOCODE_CANDIDATES:
        if p.exists() and os.access(p, os.X_OK):
            return p
    # Fall back to PATH (user may have symlinked it)
    import shutil as _shutil
    found = _shutil.which("rhinocode")
    if found:
        return pathlib.Path(found)
    return None


# ---------------------------------------------------------------------------
# Minimal TCP helpers (stop command needs to talk to the running server)
# ---------------------------------------------------------------------------
def _send_raw(sock: socket.socket, data: dict) -> None:
    payload = json.dumps(data, ensure_ascii=False).encode("utf-8")
    sock.sendall(struct.pack("!I", len(payload)) + payload)


def _recv_raw(sock: socket.socket, timeout: float = 5.0) -> dict:
    sock.settimeout(timeout)

    def _read_exactly(n: int) -> bytes:
        buf = b""
        while len(buf) < n:
            chunk = sock.recv(n - len(buf))
            if not chunk:
                raise ConnectionError("Connection closed by peer")
            buf += chunk
        return buf

    (length,) = struct.unpack("!I", _read_exactly(4))
    return json.loads(_read_exactly(length).decode("utf-8"))


def _send_shutdown(host: str, port: int) -> bool:
    """
    Tell a running GOLEM server to shut down via the TCP bridge.

    Returns True if the shutdown was acknowledged (or the connection was
    closed as expected), False on failure.
    """
    try:
        with socket.create_connection((host, port), timeout=5) as sock:
            _send_raw(sock, {
                "id": str(uuid.uuid4()),
                "method": "shutdown",
                "params": {},
            })
            # Best-effort receive — the server may close the socket immediately
            try:
                _recv_raw(sock, timeout=3.0)
            except (ConnectionError, struct.error, OSError):
                pass  # Expected: server closed connection after shutdown
        return True
    except ConnectionRefusedError:
        return False
    except OSError as exc:
        warn(f"Could not connect to {host}:{port} — {exc}")
        return False


def _server_is_running(host: str, port: int) -> bool:
    """Return True if the GOLEM server is currently listening on host:port."""
    try:
        with socket.create_connection((host, port), timeout=2):
            return True
    except OSError:
        return False


# ---------------------------------------------------------------------------
# rhinocode operations
# ---------------------------------------------------------------------------
def _rhinocode_list(rhinocode: pathlib.Path) -> list[str]:
    """
    Run ``rhinocode list`` and return stdout lines.

    Returns an empty list if the command fails or Rhino is not running.
    """
    try:
        result = subprocess.run(
            [str(rhinocode), "list"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        if result.returncode == 0:
            return [line.strip() for line in result.stdout.splitlines() if line.strip()]
        return []
    except (subprocess.TimeoutExpired, OSError):
        return []


def _rhinocode_run_script(
    rhinocode: pathlib.Path,
    script: pathlib.Path,
    dry_run: bool = False,
) -> bool:
    """
    Execute *script* inside the running Rhino instance via rhinocode.

    Returns True on success, False on failure.
    """
    cmd = [str(rhinocode), "script", str(script)]
    if dry_run:
        info(f"[dry-run] Would run: {' '.join(cmd)}")
        return True
    info(f"Running: {' '.join(cmd)}")
    try:
        result = subprocess.run(cmd, timeout=30)
        return result.returncode == 0
    except subprocess.TimeoutExpired:
        error("rhinocode timed out after 30 seconds.")
        return False
    except OSError as exc:
        error(f"Failed to invoke rhinocode: {exc}")
        return False


# ---------------------------------------------------------------------------
# High-level actions
# ---------------------------------------------------------------------------
def do_start(rhinocode: pathlib.Path, host: str, port: int, dry_run: bool) -> int:
    """Start the GOLEM server inside Rhino. Returns exit code."""
    header("Starting GOLEM-3DMCP server in Rhino ...")

    # Check if it is already running
    if _server_is_running(host, port):
        warn(f"GOLEM server is already running on {host}:{port}.")
        warn("Use --restart to stop and restart it.")
        return 0

    instances = _rhinocode_list(rhinocode)
    if not instances:
        warn("No running Rhino instances detected by 'rhinocode list'.")
        warn("Please open Rhinoceros 8, then run this script again.")
        print()
        print("  Alternatively, load the server manually from Rhino:")
        print(f"    rhinocode script \"{_STARTUP_PY}\"")
        print()
        return 1

    info(f"Rhino instance(s) found: {len(instances)}")
    for inst in instances:
        info(f"  {inst}")

    success = _rhinocode_run_script(rhinocode, _STARTUP_PY, dry_run=dry_run)
    if not success:
        error("rhinocode script execution failed.")
        return 1

    if not dry_run:
        # Brief pause to let the server bind the socket
        time.sleep(1.5)
        if _server_is_running(host, port):
            ok(f"GOLEM server is running on {host}:{port}")
        else:
            warn(f"Server not yet reachable on {host}:{port}. It may still be starting.")
            warn(f"Run:  python {_PROJECT_ROOT / 'scripts' / 'test_connection.py'}")

    return 0


def do_stop(host: str, port: int) -> int:
    """Stop the GOLEM server via the TCP bridge. Returns exit code."""
    header("Stopping GOLEM-3DMCP server ...")

    if not _server_is_running(host, port):
        warn(f"No GOLEM server appears to be running on {host}:{port}.")
        return 0

    info(f"Sending shutdown to {host}:{port} ...")
    if _send_shutdown(host, port):
        ok("Shutdown command sent.")
        # Confirm it stopped
        time.sleep(1.0)
        if not _server_is_running(host, port):
            ok("Server stopped successfully.")
        else:
            warn("Server still appears to be running. It may have ignored the shutdown.")
        return 0
    else:
        error(f"Could not connect to {host}:{port} to send shutdown.")
        return 1


def do_restart(rhinocode: pathlib.Path, host: str, port: int, dry_run: bool) -> int:
    """Stop then start the GOLEM server. Returns exit code."""
    header("Restarting GOLEM-3DMCP server ...")
    stop_code = do_stop(host, port)
    if stop_code != 0:
        warn("Stop step had issues — attempting to start anyway.")
    if not dry_run:
        time.sleep(0.5)
    return do_start(rhinocode, host, port, dry_run)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="start_rhino_server",
        description=(
            "Start the GOLEM-3DMCP server inside a running Rhino instance.\n\n"
            "Uses the rhinocode CLI to execute startup.py in Rhino's Python\n"
            "environment."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--stop",
        action="store_true",
        help="Stop the running GOLEM server via the TCP bridge",
    )
    parser.add_argument(
        "--restart",
        action="store_true",
        help="Stop the server (if running) and then start it again",
    )
    parser.add_argument(
        "--host",
        default="127.0.0.1",
        metavar="HOST",
        help="GOLEM server host (default: 127.0.0.1)",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=9876,
        metavar="PORT",
        help="GOLEM server port (default: 9876)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print what would be done without actually doing it",
    )
    return parser.parse_args()


def main() -> None:
    args = _parse_args()

    print()
    print(_c("1", "GOLEM-3DMCP — Rhino Server Launcher"))
    print("=" * 44)

    # -----------------------------------------------------------------------
    # Locate rhinocode
    # -----------------------------------------------------------------------
    rhinocode = _find_rhinocode()
    if rhinocode is None:
        warn("rhinocode CLI not found.")
        print()
        print("  rhinocode ships with Rhino 8. Try adding it to your PATH:")
        print()
        print("    # zsh (default macOS shell):")
        print('    echo \'export PATH="/Applications/Rhino 8.app/Contents/Resources/bin:$PATH"\' >> ~/.zshrc')
        print("    source ~/.zshrc")
        print()
        print("  Or run the startup script directly from Rhino's Python editor:")
        print(f"    {_STARTUP_PY}")
        print()
        if not (args.stop or args.restart):
            sys.exit(1)
    else:
        ok(f"rhinocode found: {rhinocode}")

    # -----------------------------------------------------------------------
    # Dispatch to the appropriate action
    # -----------------------------------------------------------------------
    if args.stop:
        code = do_stop(args.host, args.port)
    elif args.restart:
        if rhinocode is None:
            error("Cannot restart: rhinocode not found (needed for the start step).")
            sys.exit(1)
        code = do_restart(rhinocode, args.host, args.port, args.dry_run)
    else:
        if rhinocode is None:
            sys.exit(1)
        code = do_start(rhinocode, args.host, args.port, args.dry_run)

    print()
    sys.exit(code)


if __name__ == "__main__":
    main()
