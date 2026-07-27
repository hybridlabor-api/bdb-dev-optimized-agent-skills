#!/usr/bin/env python3
"""
GOLEM-3DMCP — Comprehensive Connection & Handler Test
======================================================
Verifies that the Rhino plugin is running and reachable, then exercises one
representative method from each handler category so you know the full stack
is working end-to-end.

Test categories
---------------
  ping        — TCP bridge reachability
  scene       — scene.get_document_info
  creation    — creation.create_point
  manipulation — manipulation.select_objects (no-op list)
  viewport    — viewport.get_view_info
  files       — files.get_document_path
  scripting   — scripting.evaluate_expression (1+1)

Uses the shared mcp_server.protocol framing module for wire-format
correctness; falls back to an inline implementation if the module is absent.

Usage
-----
    python scripts/test_connection.py [--host HOST] [--port PORT]
                                      [--timeout SECS] [--verbose]
                                      [--categories CATEGORY[,CATEGORY,...]]

Environment variables (same as the MCP server uses):
    GOLEM_RHINO_HOST   default: 127.0.0.1
    GOLEM_RHINO_PORT   default: 9876
    GOLEM_TIMEOUT      default: 30

Exit codes
----------
    0 — all selected tests passed
    1 — one or more tests failed
"""

from __future__ import annotations

import argparse
import importlib.util
import pathlib
import socket
import sys
import time
import uuid
from typing import Any

# ---------------------------------------------------------------------------
# Bootstrap: ensure the project root is importable whether or not the package
# has been pip-installed (i.e. .venv may not be activated yet).
# ---------------------------------------------------------------------------
_PROJECT_ROOT = pathlib.Path(__file__).parent.parent.resolve()
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

# ---------------------------------------------------------------------------
# ANSI colour helpers (no external dependencies)
# ---------------------------------------------------------------------------
_IS_TTY = hasattr(sys.stdout, "isatty") and sys.stdout.isatty()


def _c(code: str, text: str) -> str:
    return f"\033[{code}m{text}\033[0m" if _IS_TTY else text


def _green(t: str) -> str:
    return _c("32", t)


def _red(t: str) -> str:
    return _c("31", t)


def _yellow(t: str) -> str:
    return _c("33", t)


def _cyan(t: str) -> str:
    return _c("36", t)


def _bold(t: str) -> str:
    return _c("1", t)


def _dim(t: str) -> str:
    return _c("2", t)


PASS_LABEL = _green("PASS")
FAIL_LABEL = _red("FAIL")
SKIP_LABEL = _yellow("SKIP")


# ---------------------------------------------------------------------------
# Load config and protocol
# ---------------------------------------------------------------------------

def _load_config() -> Any:
    config_path = _PROJECT_ROOT / "mcp_server" / "config.py"
    spec = importlib.util.spec_from_file_location("mcp_server.config", config_path)
    if spec and spec.loader:
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)  # type: ignore[union-attr]
        return mod
    import types
    fb = types.SimpleNamespace()
    fb.RHINO_HOST = "127.0.0.1"
    fb.RHINO_PORT = 9876
    fb.COMMAND_TIMEOUT = 30
    fb.RECONNECT_ATTEMPTS = 3
    fb.RECONNECT_DELAY = 2.0
    return fb


def _load_protocol() -> Any:
    protocol_path = _PROJECT_ROOT / "mcp_server" / "protocol.py"
    spec = importlib.util.spec_from_file_location("mcp_server.protocol", protocol_path)
    if spec and spec.loader:
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)  # type: ignore[union-attr]
        return mod
    return None


_config = _load_config()
_protocol = _load_protocol()

DEFAULT_HOST: str = _config.RHINO_HOST
DEFAULT_PORT: int = _config.RHINO_PORT
DEFAULT_TIMEOUT: int = _config.COMMAND_TIMEOUT
RECONNECT_ATTEMPTS: int = _config.RECONNECT_ATTEMPTS
RECONNECT_DELAY: float = _config.RECONNECT_DELAY

# ---------------------------------------------------------------------------
# Wire-format helpers
# ---------------------------------------------------------------------------

def _send_message(sock: socket.socket, data: dict) -> None:
    if _protocol is not None:
        _protocol.send_message(sock, data)
        return
    import json
    import struct
    payload = json.dumps(data, ensure_ascii=False).encode("utf-8")
    sock.sendall(struct.pack("!I", len(payload)) + payload)


def _recv_message(sock: socket.socket) -> dict:
    if _protocol is not None:
        return _protocol.recv_message(sock)
    import json
    import struct

    def _read(n: int) -> bytes:
        buf = b""
        while len(buf) < n:
            chunk = sock.recv(n - len(buf))
            if not chunk:
                raise ConnectionError("Remote peer closed connection unexpectedly")
            buf += chunk
        return buf

    (length,) = struct.unpack("!I", _read(4))
    return json.loads(_read(length).decode("utf-8"))


# ---------------------------------------------------------------------------
# Single RPC call helper
# ---------------------------------------------------------------------------

class _CallResult:
    __slots__ = ("method", "success", "rtt_ms", "response", "error_msg")

    def __init__(
        self,
        method: str,
        success: bool,
        rtt_ms: float = 0.0,
        response: dict | None = None,
        error_msg: str = "",
    ) -> None:
        self.method = method
        self.success = success
        self.rtt_ms = rtt_ms
        self.response = response or {}
        self.error_msg = error_msg


def _call(
    host: str,
    port: int,
    timeout: int,
    method: str,
    params: dict,
    verbose: bool = False,
) -> _CallResult:
    """
    Open a TCP connection, send one JSON-RPC request, and return the result.

    Each call opens a fresh connection — this matches how the MCP server
    talks to the plugin in production (one command per connection).
    """
    request = {
        "id": str(uuid.uuid4()),
        "method": method,
        "params": params,
    }
    if verbose:
        import json
        print(_dim(f"    --> {json.dumps(request)}"))

    for attempt in range(1, RECONNECT_ATTEMPTS + 1):
        if attempt > 1:
            time.sleep(RECONNECT_DELAY)
        try:
            with socket.create_connection((host, port), timeout=timeout) as sock:
                sock.settimeout(timeout)
                _send_message(sock, request)
                t0 = time.perf_counter()
                response = _recv_message(sock)
                rtt = (time.perf_counter() - t0) * 1000

            if verbose:
                import json
                print(_dim(f"    <-- {json.dumps(response)[:200]}"))

            if not isinstance(response, dict):
                return _CallResult(method, False, rtt, error_msg=f"Unexpected response type: {type(response)}")

            if "error" in response and response["error"] is not None:
                err = response["error"]
                if isinstance(err, dict):
                    msg = f"[{err.get('code', '?')}] {err.get('message', str(err))}"
                else:
                    msg = str(err)
                return _CallResult(method, False, rtt, response, error_msg=msg)

            return _CallResult(method, True, rtt, response)

        except ConnectionRefusedError:
            if attempt == RECONNECT_ATTEMPTS:
                return _CallResult(method, False, error_msg=f"Connection refused on {host}:{port}")
        except socket.timeout:
            if attempt == RECONNECT_ATTEMPTS:
                return _CallResult(method, False, error_msg=f"Timed out after {timeout}s")
        except OSError as exc:
            if attempt == RECONNECT_ATTEMPTS:
                return _CallResult(method, False, error_msg=str(exc))

    return _CallResult(method, False, error_msg="All retry attempts exhausted")


# ---------------------------------------------------------------------------
# Test suite definition
# ---------------------------------------------------------------------------
# Each test is a (category, label, method, params, validator) tuple.
# validator(result) -> (passed: bool, note: str)
# ---------------------------------------------------------------------------

def _always_pass(r: _CallResult) -> tuple[bool, str]:
    return True, ""


def _check_result_key(r: _CallResult) -> tuple[bool, str]:
    if "result" in r.response:
        return True, ""
    return False, f"Missing 'result' key in response: {list(r.response.keys())}"


def _check_ping(r: _CallResult) -> tuple[bool, str]:
    resp = r.response
    # Accept {"status": "ok"} or {"result": {...}}
    if resp.get("status") == "ok":
        return True, "status=ok"
    if "result" in resp:
        result = resp["result"]
        parts = []
        if isinstance(result, dict):
            if "version" in result:
                parts.append(f"version={result['version']}")
            if "rhino_version" in result:
                parts.append(f"rhino={result['rhino_version']}")
        return True, ", ".join(parts) if parts else "result present"
    return False, f"Unexpected response: {resp}"


def _check_doc_info(r: _CallResult) -> tuple[bool, str]:
    result = r.response.get("result", {})
    if not isinstance(result, dict):
        return True, "(non-dict result — server responded)"
    name = result.get("name") or result.get("document_name") or result.get("filename") or "?"
    return True, f"document={name!r}"


def _check_eval_expr(r: _CallResult) -> tuple[bool, str]:
    result = r.response.get("result", {})
    if isinstance(result, dict):
        value = result.get("value") or result.get("result")
        if value is not None:
            return True, f"1+1={value}"
    # If there is any result at all, count it as success
    if "result" in r.response:
        return True, "expression evaluated"
    return False, "No result value returned"


def _check_view_info(r: _CallResult) -> tuple[bool, str]:
    result = r.response.get("result", {})
    if isinstance(result, dict):
        vname = result.get("name") or result.get("viewport") or "?"
        return True, f"viewport={vname!r}"
    if "result" in r.response:
        return True, "view info returned"
    return False, "No result returned"


# (category_id, display_label, method, params_dict, validator)
ALL_TESTS: list[tuple[str, str, str, dict, Any]] = [
    (
        "ping",
        "TCP ping",
        "ping",
        {},
        _check_ping,
    ),
    (
        "scene",
        "scene.get_document_info",
        "scene.get_document_info",
        {},
        _check_doc_info,
    ),
    (
        "creation",
        "creation.create_point",
        "creation.create_point",
        {"x": 0.0, "y": 0.0, "z": 0.0},
        _check_result_key,
    ),
    (
        "manipulation",
        "manipulation.select_objects",
        "manipulation.select_objects",
        {"object_ids": []},
        _check_result_key,
    ),
    (
        "viewport",
        "viewport.get_view_info",
        "viewport.get_view_info",
        {},
        _check_view_info,
    ),
    (
        "files",
        "files.get_document_path",
        "files.get_document_path",
        {},
        _check_result_key,
    ),
    (
        "scripting",
        "scripting.evaluate_expression",
        "scripting.evaluate_expression",
        {"expression": "1 + 1"},
        _check_eval_expr,
    ),
]

ALL_CATEGORY_IDS = [t[0] for t in ALL_TESTS]


# ---------------------------------------------------------------------------
# Pretty printer
# ---------------------------------------------------------------------------

def _print_result_row(
    label: str,
    passed: bool,
    rtt_ms: float,
    note: str,
    verbose: bool,
) -> None:
    status = PASS_LABEL if passed else FAIL_LABEL
    rtt_str = _dim(f"{rtt_ms:6.1f} ms") if passed else _dim("   n/a   ")
    note_str = _dim(f"  {note}") if note else ""
    print(f"  {status}  {label:<40}  {rtt_str}{note_str}")


# ---------------------------------------------------------------------------
# Core runner
# ---------------------------------------------------------------------------

def run_tests(
    host: str,
    port: int,
    timeout: int,
    categories: list[str],
    verbose: bool,
) -> tuple[int, int]:
    """
    Run the selected test categories.

    Returns (passed_count, total_run_count).
    """
    tests_to_run = [t for t in ALL_TESTS if t[0] in categories]
    passed = 0
    skipped = 0
    failures: list[tuple[str, str]] = []

    print()
    print(_bold("GOLEM-3DMCP — Connection & Handler Tests"))
    print("=" * 52)
    print()
    print(f"  Host    : {host}:{port}")
    print(f"  Timeout : {timeout}s per call")
    print(f"  Tests   : {', '.join(categories)}")
    print()

    for category, label, method, params, validator in tests_to_run:
        if verbose:
            print(_dim(f"  Testing {method} ..."))
        result = _call(host, port, timeout, method, params, verbose=verbose)

        if result.success:
            ok_flag, note = validator(result)
            if ok_flag:
                passed += 1
                _print_result_row(label, True, result.rtt_ms, note, verbose)
            else:
                failures.append((label, note))
                _print_result_row(label, False, result.rtt_ms, note, verbose)
        else:
            failures.append((label, result.error_msg))
            _print_result_row(label, False, 0.0, result.error_msg, verbose)

    total_run = len(tests_to_run)
    print()
    print("  " + "-" * 50)

    if failures:
        print(f"  Result  : {FAIL_LABEL}  ({passed}/{total_run} passed)")
        print()
        print(_bold("  Failures:"))
        for label, msg in failures:
            print(f"    {_red('x')} {label}")
            print(f"        {msg}")
        print()
        _print_troubleshooting(host, port)
    else:
        print(f"  Result  : {PASS_LABEL}  ({passed}/{total_run} passed)")
        print()
        print("  All tests passed. The Rhino plugin is responding correctly.")
        print("  Start a Claude Code session — GOLEM-3DMCP tools are ready.")

    print()
    return passed, total_run


# ---------------------------------------------------------------------------
# Troubleshooting guide (shown on failure)
# ---------------------------------------------------------------------------

def _print_troubleshooting(host: str, port: int) -> None:
    print(_bold("  Troubleshooting:"))
    print()
    print("  1. Open Rhinoceros 8 and ensure GOLEM-3DMCP is loaded.")
    print("     In the Rhino command line run:  _GolemStart")
    print("     Or from the terminal:")
    print(f"       python {_PROJECT_ROOT / 'scripts' / 'start_rhino_server.py'}")
    print()
    print("  2. Verify the plugin is listening on the expected port:")
    print(f"       lsof -iTCP:{port} -sTCP:LISTEN")
    print()
    print("  3. Confirm the plugin is installed correctly:")
    print(f"       python {_PROJECT_ROOT / 'scripts' / 'install_plugin.py'}")
    print()
    print("  4. Try a longer timeout if Rhino is slow to respond:")
    print(f"       python {pathlib.Path(__file__).name} --timeout 60")
    print()
    print("  5. Check for macOS firewall rules blocking loopback:")
    print(f"       sudo pfctl -sr | grep {port}")
    print()


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="test_connection",
        description=(
            "Test the TCP bridge between GOLEM-3DMCP and Rhinoceros 3D.\n\n"
            "Sends a ping followed by one representative call per handler\n"
            "category to verify end-to-end connectivity.\n\n"
            "Exits 0 if all selected tests pass, 1 if any fail."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--host",
        default=DEFAULT_HOST,
        metavar="HOST",
        help=f"Rhino plugin TCP host  (default: {DEFAULT_HOST})",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=DEFAULT_PORT,
        metavar="PORT",
        help=f"Rhino plugin TCP port  (default: {DEFAULT_PORT})",
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=DEFAULT_TIMEOUT,
        metavar="SECS",
        help=f"Per-call response timeout in seconds  (default: {DEFAULT_TIMEOUT})",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Print raw request/response JSON for each call",
    )
    parser.add_argument(
        "--categories",
        default=",".join(ALL_CATEGORY_IDS),
        metavar="CAT[,CAT,...]",
        help=(
            f"Comma-separated list of test categories to run.  "
            f"Available: {', '.join(ALL_CATEGORY_IDS)}.  "
            f"Default: all categories."
        ),
    )
    return parser.parse_args()


def main() -> None:
    args = _parse_args()

    # Parse and validate categories
    requested = [c.strip().lower() for c in args.categories.split(",") if c.strip()]
    unknown = [c for c in requested if c not in ALL_CATEGORY_IDS]
    if unknown:
        print(_red(f"Unknown categories: {', '.join(unknown)}"), file=sys.stderr)
        print(f"Available: {', '.join(ALL_CATEGORY_IDS)}", file=sys.stderr)
        sys.exit(1)

    passed, total = run_tests(
        host=args.host,
        port=args.port,
        timeout=args.timeout,
        categories=requested,
        verbose=args.verbose,
    )

    sys.exit(0 if passed == total else 1)


if __name__ == "__main__":
    main()
