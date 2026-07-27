# -*- coding: utf-8 -*-
"""
rhino_plugin/server.py
======================
Main TCP socket server for GOLEM-3DMCP running inside Rhino 3D.

Architecture overview:
  - A single background thread accepts incoming client connections.
  - Each client is handled sequentially (one active client at a time).
    This is intentional: Rhino's document object model is inherently
    single-threaded, and parallel client sessions would race on shared
    geometry state.
  - Every incoming message is dispatched via ``dispatch(method, params)``,
    imported from rhino_plugin.dispatcher.
  - Rhino document operations MUST run on the UI thread.  The helper
    ``run_on_ui_thread()`` marshals any callable onto Rhino's main thread
    and blocks the calling background thread until the result is available.

Python 3.9 compatibility:
  - No match/case statements.
  - No X | Y union type syntax.
  - Use Optional / Union from typing.
  - All f-strings are allowed (3.6+).

Author: GOLEM-3DMCP
"""

import json
import socket
import threading
import traceback
try:
    from typing import Optional, Callable, Any
except ImportError:
    pass

# Rhino-specific imports.  These are available inside Rhino's IronPython /
# Python 3.9 runtime.  The TYPE_CHECKING guard allows IDEs to resolve the
# symbols without a local Rhino installation.
try:
    import Rhino                       # type: ignore
    import System                      # type: ignore
    _RHINO_AVAILABLE = True
except ImportError:
    # Running outside Rhino (e.g., unit tests).  Provide thin stubs so the
    # rest of the module can be imported and tested.
    _RHINO_AVAILABLE = False

from rhino_plugin.protocol import send_message, recv_message

# ---------------------------------------------------------------------------
# Module-level state
# ---------------------------------------------------------------------------

_server_socket = None          # type: Optional[socket.socket]
_server_thread = None          # type: Optional[threading.Thread]
_running = False               # type: bool
_running_lock = threading.Lock()

# Method registry: maps method name -> callable(params: dict) -> dict
_method_registry = {}          # type: dict


# ---------------------------------------------------------------------------
# UI-thread dispatch helper
# ---------------------------------------------------------------------------

def run_on_ui_thread(func):
    # type: (Callable[[], Any]) -> Any
    """
    Execute *func* on Rhino's UI thread and return its result.

    Rhino's document object model is not thread-safe.  All geometry
    creation, modification, and query operations must happen on the UI
    (main) thread.  This helper:
      1. Wraps *func* in a closure that captures return value / exception.
      2. Posts the closure onto the UI thread via RhinoApp.InvokeOnUiThread.
      3. Blocks the calling background thread on a threading.Event until
         the closure completes (timeout: 30 seconds).
      4. Re-raises any exception that occurred on the UI thread.

    Args:
        func: A zero-argument callable.  Must be safe to run on the UI thread.

    Returns:
        Whatever *func() returns.

    Raises:
        TimeoutError: If the UI thread does not execute the function within
            30 seconds (possible if Rhino is busy or modal dialog is open).
        Exception: Re-raises any exception raised inside *func*.
    """
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

    if _RHINO_AVAILABLE:
        Rhino.RhinoApp.InvokeOnUiThread(System.Action(wrapper))
    else:
        # In test mode, run directly (no UI thread exists).
        wrapper()

    completed = event.wait(timeout=30.0)
    if not completed:
        raise TimeoutError(
            "run_on_ui_thread: UI thread did not respond within 30 seconds. "
            "Rhino may be busy or a modal dialog may be blocking execution."
        )
    if error[0] is not None:
        raise error[0]
    return result[0]


# ---------------------------------------------------------------------------
# Built-in method handlers
# ---------------------------------------------------------------------------

def _handle_ping(params):
    # type: (dict) -> dict
    """Simple liveness check.  Always returns {'alive': True}."""
    return {"alive": True}


def _handle_shutdown(params):
    # type: (dict) -> dict
    """
    Gracefully stop the server from a remote command.

    The actual shutdown is deferred to a daemon thread so this handler can
    return a response before the server socket closes.
    """
    def _deferred():
        # type: () -> None
        import time
        time.sleep(0.1)  # Brief pause so the response is transmitted first.
        stop_server()

    t = threading.Thread(target=_deferred, name="golem-shutdown-deferred", daemon=True)
    t.start()
    return {"shutdown": "initiated"}


def _handle_list_methods(params):
    # type: (dict) -> dict
    """Return a list of all registered method names."""
    return {"methods": sorted(_method_registry.keys())}


# ---------------------------------------------------------------------------
# Method registry
# ---------------------------------------------------------------------------

def register_method(name, func):
    # type: (str, Callable[[dict], dict]) -> None
    """
    Register a handler for a named method.

    Args:
        name: The method name clients will send (e.g., "scene.get_objects").
        func: Callable that accepts a params dict and returns a result dict.
    """
    _method_registry[name] = func


def _register_builtins():
    # type: () -> None
    """Register the three built-in methods."""
    register_method("ping", _handle_ping)
    register_method("shutdown", _handle_shutdown)
    register_method("list_methods", _handle_list_methods)


# ---------------------------------------------------------------------------
# Client handler
# ---------------------------------------------------------------------------

def handle_client(conn, addr):
    # type: (socket.socket, tuple) -> None
    """
    Serve a single connected client until it disconnects or the server stops.

    Message protocol (request):
        {
            "id":     <str|int>,   // Request ID echoed in the response
            "method": <str>,       // Registered method name
            "params": <dict>       // Method parameters (may be empty dict)
        }

    Message protocol (response -- success):
        {
            "id":     <str|int>,
            "result": <dict>,
            "error":  null
        }

    Message protocol (response -- error):
        {
            "id":     <str|int|null>,
            "result": null,
            "error":  {"code": <int>, "message": <str>}
        }

    Args:
        conn: The accepted client socket.
        addr: The (host, port) tuple of the remote client.
    """
    _log("Client connected: {addr}".format(addr=addr))
    conn.settimeout(None)  # Blocking mode; client reads block indefinitely.

    try:
        while _is_running():
            # ------------------------------------------------------------------
            # Read one request message.
            # ------------------------------------------------------------------
            try:
                request = recv_message(conn)
            except ConnectionError:
                _log("Client {addr} disconnected (clean EOF).".format(addr=addr))
                break
            except OSError as exc:
                _log("Client {addr} socket error while reading: {exc}".format(
                    addr=addr, exc=exc))
                break
            except Exception as exc:
                _log("Client {addr} unexpected read error: {exc}".format(
                    addr=addr, exc=exc))
                break

            # ------------------------------------------------------------------
            # Extract request fields.
            # ------------------------------------------------------------------
            request_id = request.get("id", None)
            method = request.get("method", "")
            params = request.get("params", {})

            if not isinstance(params, dict):
                params = {}

            # ------------------------------------------------------------------
            # Dispatch the method.
            # ------------------------------------------------------------------
            try:
                response = _dispatch(method, params, request_id)
            except Exception as exc:
                _log(
                    "Unhandled exception dispatching '{method}' "
                    "for {addr}: {exc}\n{tb}".format(
                        method=method,
                        addr=addr,
                        exc=exc,
                        tb=traceback.format_exc(),
                    )
                )
                response = _error_response(
                    request_id,
                    code=-32603,
                    message="Internal error: {exc}".format(exc=exc),
                )

            # ------------------------------------------------------------------
            # Send the response.
            # ------------------------------------------------------------------
            try:
                send_message(conn, response)
            except OSError as exc:
                _log("Client {addr} socket error while writing: {exc}".format(
                    addr=addr, exc=exc))
                break

    finally:
        try:
            conn.close()
        except OSError:
            pass
        _log("Client {addr} session ended.".format(addr=addr))


def _dispatch(method, params, request_id):
    # type: (str, dict, Any) -> dict
    """
    Look up *method* in the registry, run it (on UI thread if Rhino is
    available), and return a formatted response dict.

    For Rhino document operations the handler is always executed on the UI
    thread via run_on_ui_thread().  For non-document methods (ping, etc.)
    the overhead is negligible, so we use the same path for simplicity and
    to guarantee thread safety.
    """
    if method not in _method_registry:
        # Try the external dispatcher (rhino_plugin.dispatcher) for dynamically
        # registered Rhino-specific commands.
        try:
            from rhino_plugin import dispatcher as _dispatcher  # type: ignore
            # The external dispatcher never raises -- it returns its own full
            # response envelope ({"jsonrpc": "2.0", "id": ..., "result"|"error": ...}).
            # We run it on the UI thread and then normalise its output into our
            # wire envelope format.
            dispatcher_response = run_on_ui_thread(
                lambda: _dispatcher.dispatch(method, params, request_id=request_id)
            )
            # Normalise jsonrpc envelope -> our wire envelope.
            if "error" in dispatcher_response and dispatcher_response["error"] is not None:
                err = dispatcher_response["error"]
                return _error_response(
                    request_id,
                    code=-32000,
                    message=err.get("message", str(err)) if isinstance(err, dict) else str(err),
                )
            return {
                "id": request_id,
                "result": dispatcher_response.get("result") or {},
                "error": None,
            }
        except (ImportError, AttributeError):
            return _error_response(
                request_id,
                code=-32601,
                message="Method not found: {method}".format(method=method),
            )
    else:
        registry_func = _method_registry[method]
        handler_func = lambda: registry_func(params)  # noqa: E731

    # Execute on the UI thread so Rhino document access is safe.
    result = run_on_ui_thread(handler_func)

    return {
        "id": request_id,
        "result": result if result is not None else {},
        "error": None,
    }


def _error_response(request_id, code, message):
    # type: (Any, int, str) -> dict
    """Build a standard error response envelope."""
    return {
        "id": request_id,
        "result": None,
        "error": {
            "code": code,
            "message": message,
        },
    }


# ---------------------------------------------------------------------------
# Server lifecycle
# ---------------------------------------------------------------------------

def start_server(host="127.0.0.1", port=9876):
    # type: (str, int) -> None
    """
    Start the TCP server and begin accepting client connections.

    The server runs in a background daemon thread so it does not block
    Rhino's main UI thread.  Only one server instance can be active at a time;
    calling start_server() while already running is a no-op.

    Args:
        host: IP address to bind (default: localhost only, not exposed on LAN).
        port: TCP port to listen on (default: 9876).
    """
    global _server_socket, _server_thread, _running

    with _running_lock:
        if _running:
            _log("Server is already running on {host}:{port}. Ignoring start_server().".format(
                host=host, port=port))
            return

        # Register built-in methods before accepting connections.
        _register_builtins()

        # Register all domain-specific handler modules (scene, creation,
        # operations, surfaces, manipulation, grasshopper, viewport, files,
        # scripting).  This is idempotent -- calling it multiple times is safe.
        try:
            from rhino_plugin.handlers import register_all_handlers
            handler_count = register_all_handlers()
            _log("GOLEM-3DMCP: Registered {n} handler methods.".format(n=handler_count))
        except Exception as _reg_exc:
            # Non-fatal: the server can still start and serve built-in methods.
            # Individual unregistered domain methods will return NOT_FOUND.
            _log(
                "GOLEM-3DMCP: WARNING -- handler registration failed: {exc}".format(
                    exc=_reg_exc
                )
            )

        # Create the server socket with SO_REUSEADDR so Rhino can restart
        # quickly after a previous run without waiting for TIME_WAIT to expire.
        srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        try:
            srv.bind((host, port))
        except OSError as exc:
            _log("GOLEM-3DMCP: Failed to bind {host}:{port} -- {exc}".format(
                host=host, port=port, exc=exc))
            srv.close()
            raise

        srv.listen(5)
        _server_socket = srv
        _running = True

    _log("GOLEM-3DMCP: Server listening on {host}:{port}".format(host=host, port=port))

    # Accept loop runs in a background thread.
    _server_thread = threading.Thread(
        target=_accept_loop,
        args=(srv,),
        name="golem-accept-loop",
        daemon=True,  # Daemon so it does not prevent Python from exiting.
    )
    _server_thread.start()


def _accept_loop(srv):
    # type: (socket.socket) -> None
    """
    Continuously accept new connections until the server is stopped.

    When a client connects, handle_client() is called synchronously in this
    same thread.  This means only one client can be active at a time.  For the
    GOLEM-3DMCP use case (single Claude Code session connecting to one Rhino
    instance) this is the correct and simplest design.  If multi-client support
    is ever needed, spawn a thread per client here.
    """
    while _is_running():
        # Use a short accept timeout so the loop can check _running promptly
        # after stop_server() is called.
        srv.settimeout(1.0)
        try:
            conn, addr = srv.accept()
        except socket.timeout:
            continue  # No new client; loop back and check _running.
        except OSError:
            # Server socket was closed by stop_server().
            break

        # Service this client (blocking until it disconnects).
        handle_client(conn, addr)

    _log("GOLEM-3DMCP: Accept loop exited.")


def stop_server():
    # type: () -> None
    """
    Stop the TCP server gracefully.

    Sets the running flag to False (which causes the accept loop and any
    active client handler to exit at their next check point) and closes the
    server socket.
    """
    global _running, _server_socket

    with _running_lock:
        if not _running:
            _log("GOLEM-3DMCP: stop_server() called but server is not running.")
            return
        _running = False
        srv = _server_socket
        _server_socket = None

    if srv is not None:
        try:
            srv.close()
        except OSError:
            pass

    _log("GOLEM-3DMCP: Server stopped.")


def _is_running():
    # type: () -> bool
    """Thread-safe check of the running flag."""
    with _running_lock:
        return _running


# ---------------------------------------------------------------------------
# Logging helper
# ---------------------------------------------------------------------------

def _log(message):
    # type: (str) -> None
    """
    Write a log message to the Rhino console (or stdout when outside Rhino).

    Using Rhino.RhinoApp.WriteLine routes the message into the Rhino command
    history window, which is visible to the user in the Rhino UI.  Falling
    back to print() ensures tests and non-Rhino environments still get output.
    """
    if _RHINO_AVAILABLE:
        try:
            Rhino.RhinoApp.WriteLine(message)
        except Exception:
            print(message)
    else:
        print(message)
