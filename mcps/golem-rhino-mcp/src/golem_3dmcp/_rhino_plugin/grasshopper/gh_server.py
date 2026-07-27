# -*- coding: utf-8 -*-
"""
rhino_plugin/grasshopper/gh_server.py
=======================================
Secondary TCP server dedicated to Grasshopper-context operations.

Why a separate server?
----------------------
Some Grasshopper operations must be invoked while Grasshopper's solve loop is
active (e.g. reading parameter data mid-solution, hooking into the ``SolutionEnd``
event).  Running these through the main server on port 9876 is technically
possible but creates awkward threading interactions with the main Rhino event
pump.  This lightweight server on port 9877 provides an isolated channel for
GH-specific traffic while reusing the same length-prefixed JSON wire protocol
defined in ``rhino_plugin.protocol``.

Architecture
------------
* Single background thread -- same philosophy as ``server.py``.
* GH operations are always marshalled onto the Rhino UI thread via
  ``run_on_ui_thread()`` (imported from ``server.py``).
* Shares the global dispatcher from ``rhino_plugin.dispatcher`` -- no separate
  registry needed; all ``grasshopper.*`` methods registered by
  ``handlers/grasshopper.py`` are automatically available here too.
* The server can be started and stopped independently of the main server.

Python 3.9 compatibility
------------------------
* No ``match``/``case``.
* No ``X | Y`` union type syntax.
* No lowercase generic ``dict[...]`` / ``list[...]`` in runtime annotations.
* Only stdlib imports (plus Rhino/Grasshopper available inside Rhino).

Author: GOLEM-3DMCP
"""

import json
import socket
import threading
import traceback
try:
    from typing import Any, Optional
except ImportError:
    pass

from rhino_plugin.protocol import send_message, recv_message

# ---------------------------------------------------------------------------
# Module-level state
# ---------------------------------------------------------------------------

_gh_server_socket = None        # type: Optional[socket.socket]
_gh_server_thread = None        # type: Optional[threading.Thread]
_gh_running = False             # type: bool
_gh_running_lock = threading.Lock()

# Default bind address/port.  Port 9877 keeps GH traffic clearly separate
# from the main server on 9876.
GH_DEFAULT_HOST = "127.0.0.1"
GH_DEFAULT_PORT = 9877


# ---------------------------------------------------------------------------
# Logging helper
# ---------------------------------------------------------------------------

def _log(message):
    # type: (str) -> None
    """Write to the Rhino console if available, otherwise stdout."""
    try:
        import Rhino                         # type: ignore
        try:
            Rhino.RhinoApp.WriteLine(message)
            return
        except Exception:
            pass
    except ImportError:
        pass
    print(message)


# ---------------------------------------------------------------------------
# UI-thread dispatch (reuse logic from server.py without creating a circular
# import -- we import from server at dispatch time inside the handler loop)
# ---------------------------------------------------------------------------

def _run_on_ui_thread(func):
    # type: (Any) -> Any
    """
    Execute *func* on Rhino's UI thread and return its result.

    Identical in behaviour to ``rhino_plugin.server.run_on_ui_thread``.
    Duplicated here to avoid a circular import (``server`` imports
    ``dispatcher`` which imports ``handlers`` which might import us).
    """
    try:
        import Rhino                         # type: ignore
        import System                        # type: ignore
        rhino_available = True
    except ImportError:
        rhino_available = False

    result = [None]
    error = [None]
    event = threading.Event()

    def wrapper():
        # type: () -> None
        try:
            result[0] = func()
        except Exception as exc:
            error[0] = exc
        finally:
            event.set()

    if rhino_available:
        Rhino.RhinoApp.InvokeOnUiThread(System.Action(wrapper))
    else:
        wrapper()

    completed = event.wait(timeout=30.0)
    if not completed:
        raise TimeoutError(
            "GH server: UI thread did not respond within 30 seconds."
        )
    if error[0] is not None:
        raise error[0]
    return result[0]


# ---------------------------------------------------------------------------
# Response format helpers (local copies to avoid circular imports)
# ---------------------------------------------------------------------------

def _success_response(request_id, result):
    # type: (Any, Any) -> dict
    return {
        "id": request_id,
        "result": result if result is not None else {},
        "error": None,
    }


def _error_response(request_id, code, message):
    # type: (Any, int, str) -> dict
    return {
        "id": request_id,
        "result": None,
        "error": {"code": code, "message": message},
    }


# ---------------------------------------------------------------------------
# Method dispatch
# ---------------------------------------------------------------------------

def _dispatch_gh(method, params, request_id):
    # type: (str, dict, Any) -> dict
    """
    Route *method* through the global dispatcher (``rhino_plugin.dispatcher``).

    The dispatcher is imported lazily here to avoid loading handler modules
    before the Grasshopper assemblies are ready.
    """
    try:
        from rhino_plugin import dispatcher as _dispatcher  # type: ignore
    except ImportError as exc:
        return _error_response(
            request_id, -32603,
            "Could not import rhino_plugin.dispatcher: {err}".format(err=exc)
        )

    try:
        response = _run_on_ui_thread(
            lambda: _dispatcher.dispatch(method, params, request_id=request_id)
        )
    except TimeoutError as exc:
        return _error_response(request_id, -32603, str(exc))
    except Exception as exc:
        tb = traceback.format_exc()
        return _error_response(
            request_id, -32603,
            "Unhandled error dispatching '{m}': {err}".format(m=method, err=exc)
        )

    # Normalise the jsonrpc envelope -> wire envelope.
    if isinstance(response, dict):
        err = response.get("error")
        if err is not None:
            msg = err.get("message", str(err)) if isinstance(err, dict) else str(err)
            return _error_response(request_id, -32000, msg)
        return _success_response(request_id, response.get("result"))

    return _success_response(request_id, response)


# ---------------------------------------------------------------------------
# Client handler
# ---------------------------------------------------------------------------

def _handle_gh_client(conn, addr):
    # type: (socket.socket, tuple) -> None
    """
    Serve one connected client until disconnect or server stop.

    Uses the same length-prefixed JSON framing as the main server.
    """
    _log("GH server: client connected {addr}".format(addr=addr))
    conn.settimeout(None)

    try:
        while _gh_is_running():
            try:
                request = recv_message(conn)
            except ConnectionError:
                _log("GH server: client {addr} disconnected.".format(addr=addr))
                break
            except OSError as exc:
                _log("GH server: socket error reading from {addr}: {exc}".format(
                    addr=addr, exc=exc))
                break
            except Exception as exc:
                _log("GH server: unexpected read error from {addr}: {exc}".format(
                    addr=addr, exc=exc))
                break

            request_id = request.get("id", None)
            method = request.get("method", "")
            params = request.get("params", {})
            if not isinstance(params, dict):
                params = {}

            # Intercept the built-in ping/shutdown without hitting the dispatcher.
            if method == "gh.ping":
                response = _success_response(request_id, {"alive": True, "server": "gh"})
            elif method == "gh.shutdown":
                response = _success_response(request_id, {"shutdown": "initiated"})
                try:
                    send_message(conn, response)
                except OSError:
                    pass
                _deferred_stop()
                break
            else:
                try:
                    response = _dispatch_gh(method, params, request_id)
                except Exception as exc:
                    response = _error_response(
                        request_id, -32603,
                        "Internal error: {exc}".format(exc=exc)
                    )

            try:
                send_message(conn, response)
            except OSError as exc:
                _log("GH server: socket error writing to {addr}: {exc}".format(
                    addr=addr, exc=exc))
                break

    finally:
        try:
            conn.close()
        except OSError:
            pass
        _log("GH server: session ended for {addr}".format(addr=addr))


# ---------------------------------------------------------------------------
# Accept loop
# ---------------------------------------------------------------------------

def _accept_loop(srv):
    # type: (socket.socket) -> None
    """Background thread: accept clients until the server is stopped."""
    while _gh_is_running():
        srv.settimeout(1.0)
        try:
            conn, addr = srv.accept()
        except socket.timeout:
            continue
        except OSError:
            break
        _handle_gh_client(conn, addr)
    _log("GH server: accept loop exited.")


# ---------------------------------------------------------------------------
# Deferred stop helper (used by gh.shutdown handler)
# ---------------------------------------------------------------------------

def _deferred_stop():
    # type: () -> None
    """Schedule a stop() call 100 ms from now so the response can be sent."""
    import time

    def _do_stop():
        # type: () -> None
        time.sleep(0.1)
        stop_gh_server()

    t = threading.Thread(target=_do_stop, name="gh-shutdown-deferred", daemon=True)
    t.start()


# ---------------------------------------------------------------------------
# Public lifecycle API
# ---------------------------------------------------------------------------

def start_gh_server(host=GH_DEFAULT_HOST, port=GH_DEFAULT_PORT):
    # type: (str, int) -> None
    """
    Start the Grasshopper-context TCP server.

    The server binds on *host*:*port* (default ``127.0.0.1:9877``) and
    accepts connections in a background daemon thread.  Calling this function
    while the server is already running is a safe no-op.

    Args:
        host: IP address to bind (default: loopback, not exposed on LAN).
        port: TCP port to listen on (default: 9877).
    """
    global _gh_server_socket, _gh_server_thread, _gh_running

    with _gh_running_lock:
        if _gh_running:
            _log(
                "GH server: already running on {h}:{p}. "
                "Ignoring start_gh_server().".format(h=host, p=port)
            )
            return

        srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        try:
            srv.bind((host, port))
        except OSError as exc:
            _log("GH server: failed to bind {h}:{p} -- {exc}".format(
                h=host, p=port, exc=exc))
            srv.close()
            raise

        srv.listen(5)
        _gh_server_socket = srv
        _gh_running = True

    _log("GH server: listening on {h}:{p}".format(h=host, p=port))

    _gh_server_thread = threading.Thread(
        target=_accept_loop,
        args=(srv,),
        name="golem-gh-accept-loop",
        daemon=True,
    )
    _gh_server_thread.start()


def stop_gh_server():
    # type: () -> None
    """
    Stop the Grasshopper-context TCP server gracefully.

    Sets the running flag to False, closes the server socket, and lets the
    background accept loop exit at its next timeout tick.  Calling this
    function when the server is not running is a safe no-op.
    """
    global _gh_running, _gh_server_socket

    with _gh_running_lock:
        if not _gh_running:
            _log("GH server: stop_gh_server() called but server is not running.")
            return
        _gh_running = False
        srv = _gh_server_socket
        _gh_server_socket = None

    if srv is not None:
        try:
            srv.close()
        except OSError:
            pass

    _log("GH server: stopped.")


def is_running():
    # type: () -> bool
    """Return True if the GH server is currently accepting connections."""
    return _gh_is_running()


def _gh_is_running():
    # type: () -> bool
    """Thread-safe read of the running flag."""
    with _gh_running_lock:
        return _gh_running
