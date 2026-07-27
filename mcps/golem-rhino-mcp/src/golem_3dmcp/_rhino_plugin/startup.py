# -*- coding: utf-8 -*-
"""
rhino_plugin/startup.py
=======================
Bootstrap script for starting the GOLEM-3DMCP TCP server inside Rhino 3D.

HOW TO USE:
  1. Open Rhino 3D.
  2. Run the 'EditPythonScript' command (or open the Python Script Editor).
  3. Open this file and press Run, OR paste its contents into the editor.

Alternatively, add this script to Rhino's startup scripts list:
  Tools > Options > RhinoScript > Add startup script > select this file.

What this script does:
  - Adds the GOLEM-3DMCP project root to sys.path so all package imports work.
  - Calls start_server() to bind a TCP socket on 127.0.0.1:9876.
  - Registers all domain handler modules and reports the method count.
  - The server runs in a background daemon thread and does not block Rhino.

To stop the server:  call stop_server() or run rhino_plugin/shutdown.py
To restart:          call restart_server()
To send a command:   send a 'shutdown' method via the MCP client
"""

import sys
import os

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

_HOST = "127.0.0.1"
_PORT = 9876

# Adjust this path if you have cloned GOLEM-3DMCP to a different location.
project_root = "/Users/kinghippo/Documents/GOLEM-3DMCP"

# ---------------------------------------------------------------------------
# Path setup -- must happen before any rhino_plugin imports
# ---------------------------------------------------------------------------

if project_root not in sys.path:
    sys.path.insert(0, project_root)
    print("GOLEM-3DMCP: Added {path} to sys.path.".format(path=project_root))

# ---------------------------------------------------------------------------
# Import server machinery
# ---------------------------------------------------------------------------

try:
    from rhino_plugin.server import start_server, stop_server, _is_running  # noqa: E402
    from rhino_plugin.dispatcher import get_registered_methods               # noqa: E402
except Exception as _import_exc:
    print(
        "GOLEM-3DMCP: ERROR -- Failed to import server modules.\n"
        "  Ensure '{root}' is the correct project root and all\n"
        "  required packages are present.\n"
        "  Detail: {exc}".format(root=project_root, exc=_import_exc)
    )
    raise

# ---------------------------------------------------------------------------
# Convenience helpers exposed in the Rhino Python console
# ---------------------------------------------------------------------------

def stop_golem():
    # type: () -> None
    """
    Stop the GOLEM-3DMCP TCP server.

    Call this from Rhino's Python console or script editor::

        import rhino_plugin.startup as golem
        golem.stop_golem()
    """
    if not _is_running():
        print("GOLEM-3DMCP: Server is not running.")
        return
    try:
        stop_server()
        print("GOLEM-3DMCP: Server stopped.")
    except Exception as exc:
        print("GOLEM-3DMCP: ERROR while stopping server -- {exc}".format(exc=exc))


def restart_golem(host=_HOST, port=_PORT):
    # type: (str, int) -> None
    """
    Stop and restart the GOLEM-3DMCP TCP server.

    Useful when you have made changes to handler modules and want to reload
    without restarting Rhino.

    Args:
        host: IP address to bind (default: 127.0.0.1).
        port: TCP port to listen on (default: 9876).
    """
    print("GOLEM-3DMCP: Restarting server on {host}:{port}...".format(
        host=host, port=port))
    if _is_running():
        stop_golem()
    _start(host, port)


def _start(host, port):
    # type: (str, int) -> None
    """Internal helper: start the server and print diagnostics."""
    if _is_running():
        print(
            "GOLEM-3DMCP: Server is already running on {host}:{port}. "
            "Call restart_golem() to restart.".format(host=host, port=port)
        )
        return

    print("GOLEM-3DMCP: Starting server on {host}:{port}...".format(
        host=host, port=port))

    try:
        start_server(host, port)
    except OSError as exc:
        print(
            "GOLEM-3DMCP: ERROR -- Could not bind {host}:{port}.\n"
            "  The port may already be in use by another process.\n"
            "  Detail: {exc}\n"
            "  Try: restart_golem() or change _PORT at the top of startup.py.".format(
                host=host, port=port, exc=exc
            )
        )
        return
    except Exception as exc:
        print(
            "GOLEM-3DMCP: ERROR -- Unexpected failure starting server: {exc}".format(
                exc=exc
            )
        )
        return

    # Report registered methods.
    try:
        methods = sorted(get_registered_methods())
        print(
            "GOLEM-3DMCP: Server started successfully on {host}:{port}.".format(
                host=host, port=port
            )
        )
        print("GOLEM-3DMCP: {n} handler methods registered:".format(n=len(methods)))
        for method_name in methods:
            print("    {method}".format(method=method_name))
    except Exception as exc:
        # Diagnostics failure is non-fatal; the server is already running.
        print(
            "GOLEM-3DMCP: Server started, but could not retrieve method list: "
            "{exc}".format(exc=exc)
        )


# ---------------------------------------------------------------------------
# Auto-start when the script is run directly
# ---------------------------------------------------------------------------

_start(_HOST, _PORT)
