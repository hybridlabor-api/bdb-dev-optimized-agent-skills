"""
mcp_server/connection.py
========================
TCP client manager for communicating with the GOLEM-3DMCP Rhino plugin server.

Design decisions:
  - Singleton: Only one RhinoConnection instance exists per process.  The MCP
    server is single-process and needs a single, persistent connection to one
    Rhino instance.
  - Thread-safe: A threading.Lock guards every send/receive operation.  The MCP
    framework may call tools from multiple threads concurrently.
  - Auto-reconnect: Transient errors (BrokenPipeError, ConnectionResetError)
    trigger up to 3 automatic reconnect attempts before propagating.
  - Request IDs: Every outbound command gets a UUID4 so in-flight messages are
    uniquely identifiable for debugging/logging purposes.

Author: GOLEM-3DMCP
"""

import socket
import threading
import uuid
from typing import Optional

from mcp_server.protocol import send_message, recv_message

# ---------------------------------------------------------------------------
# Custom exception hierarchy
# ---------------------------------------------------------------------------

class RhinoConnectionError(OSError):
    """
    Raised when a TCP connection to the Rhino plugin server cannot be
    established or is unexpectedly lost.
    """


class RhinoCommandError(RuntimeError):
    """
    Raised when the Rhino plugin returns an error-level response to a command
    (i.e., the 'error' field in the response envelope is non-null).

    Attributes:
        code:    Integer error code from the Rhino plugin.
        message: Human-readable error description from the Rhino plugin.
    """

    def __init__(self, code: int, message: str) -> None:
        super().__init__(f"Rhino error {code}: {message}")
        self.code = code
        self.message = message


class RhinoTimeoutError(TimeoutError):
    """
    Raised when a command sent to Rhino does not receive a response within
    the specified timeout period.
    """


# ---------------------------------------------------------------------------
# RhinoConnection
# ---------------------------------------------------------------------------

class RhinoConnection:
    """
    Manages a persistent TCP connection to the GOLEM-3DMCP Rhino plugin server.

    Usage:
        conn = get_connection()
        result = conn.send_command("scene.get_all_objects", {})

    Thread safety:
        send_command() acquires a lock for the duration of the send+receive
        cycle, so concurrent callers are serialised.  This matches the
        Rhino plugin's single-client-at-a-time server model.
    """

    _MAX_AUTO_RECONNECT_ATTEMPTS = 3

    def __init__(self) -> None:
        self._sock: Optional[socket.socket] = None
        self._lock = threading.Lock()
        self._host: str = "127.0.0.1"
        self._port: int = 9876

    # ------------------------------------------------------------------
    # Connection management
    # ------------------------------------------------------------------

    def connect(
        self,
        host: str = "127.0.0.1",
        port: int = 9876,
        timeout: int = 10,
    ) -> None:
        """
        Establish a TCP connection to the Rhino plugin server and verify it
        is alive by sending a 'ping' command.

        Args:
            host:    Hostname or IP address of the Rhino machine (default:
                     localhost).
            port:    TCP port the Rhino plugin is listening on (default: 9876).
            timeout: Connection timeout in seconds (default: 10).

        Raises:
            RhinoConnectionError: If the TCP connection cannot be established
                or the ping handshake fails.
        """
        with self._lock:
            self._host = host
            self._port = port
            self._sock = self._create_socket(host, port, timeout)

        # Verify the server is alive and responding correctly.
        # send_command() will acquire the lock internally.
        try:
            self.send_command("ping", {}, timeout=timeout)
        except Exception as exc:
            self.disconnect()
            raise RhinoConnectionError(
                f"Connected to {host}:{port} but ping handshake failed: {exc}"
            ) from exc

    def _create_socket(self, host: str, port: int, timeout: int) -> socket.socket:
        """
        Create and connect a TCP socket.  Returns the connected socket.

        Raises:
            RhinoConnectionError: If the TCP handshake fails.
        """
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        try:
            sock.connect((host, port))
        except (OSError, socket.timeout) as exc:
            sock.close()
            raise RhinoConnectionError(
                f"Cannot connect to Rhino plugin at {host}:{port}: {exc}"
            ) from exc
        # Switch to blocking (no timeout) after connection — individual
        # commands specify their own timeout via socket.settimeout().
        sock.settimeout(None)
        return sock

    def disconnect(self) -> None:
        """
        Close the TCP connection cleanly.

        Safe to call even if already disconnected.
        """
        with self._lock:
            if self._sock is not None:
                try:
                    self._sock.shutdown(socket.SHUT_RDWR)
                except OSError:
                    pass
                try:
                    self._sock.close()
                except OSError:
                    pass
                self._sock = None

    def reconnect(self) -> None:
        """
        Close the existing connection and establish a fresh one using the
        same host/port as the most recent connect() call.

        Raises:
            RhinoConnectionError: If the re-connection fails.
        """
        self.disconnect()
        self.connect(host=self._host, port=self._port)

    def is_connected(self) -> bool:
        """
        Check whether the socket is believed to be connected.

        This is a lightweight heuristic — it does not perform a round-trip
        to Rhino.  A socket that has been disconnected by the remote peer
        may still appear connected until the next send/recv.  For a hard
        liveness check, call send_command("ping", {}).

        Returns:
            True if a socket object exists and has not been explicitly closed.
        """
        with self._lock:
            return self._sock is not None

    # ------------------------------------------------------------------
    # Command execution
    # ------------------------------------------------------------------

    def send_command(
        self,
        method: str,
        params: dict,
        timeout: int = 30,
    ) -> dict:
        """
        Send a command to Rhino and wait for the response.

        The request envelope follows the server's expected format:
            {"id": "<uuid4>", "method": "<method>", "params": {...}}

        The response envelope is expected to be:
            {"id": "<uuid4>", "result": {...}, "error": null}
          or
            {"id": "<uuid4>", "result": null,  "error": {"code": N, "message": "..."}}

        Args:
            method:  The Rhino plugin method name (e.g., "scene.get_objects").
            params:  Dictionary of parameters for the method.
            timeout: Seconds to wait for a response before raising
                     RhinoTimeoutError (default: 30).

        Returns:
            The "result" dictionary from the response envelope.

        Raises:
            RhinoConnectionError: If no connection exists or the connection
                is lost mid-command and auto-reconnect fails.
            RhinoCommandError:    If Rhino reports an error for this command.
            RhinoTimeoutError:    If no response arrives within *timeout* seconds.
        """
        request_id = str(uuid.uuid4())
        request = {
            "id": request_id,
            "method": method,
            "params": params,
        }

        last_exc: Optional[Exception] = None
        for attempt in range(1, self._MAX_AUTO_RECONNECT_ATTEMPTS + 1):
            try:
                return self._send_and_recv(request, timeout)
            except (BrokenPipeError, ConnectionResetError) as exc:
                last_exc = exc
                if attempt < self._MAX_AUTO_RECONNECT_ATTEMPTS:
                    # Try to reconnect and retry the command.
                    try:
                        self.reconnect()
                    except RhinoConnectionError:
                        # Reconnect failed; keep trying up to max attempts.
                        pass
            except RhinoTimeoutError:
                raise  # Timeouts are not retried.
            except RhinoCommandError:
                raise  # Application-level errors are not retried.

        raise RhinoConnectionError(
            f"Command '{method}' failed after "
            f"{self._MAX_AUTO_RECONNECT_ATTEMPTS} attempts: {last_exc}"
        ) from last_exc

    def _send_and_recv(self, request: dict, timeout: int) -> dict:
        """
        Internal: acquire the lock, send *request*, receive one response.

        Raises:
            RhinoConnectionError: If not connected.
            RhinoTimeoutError:    If socket times out waiting for a response.
            RhinoCommandError:    If the response contains an error.
            OSError:              On other socket-level failures (callers should
                                  detect BrokenPipeError / ConnectionResetError
                                  and retry).
        """
        with self._lock:
            if self._sock is None:
                raise RhinoConnectionError(
                    "Not connected to Rhino plugin.  Call connect() first."
                )

            # Apply per-command timeout for the receive phase.
            self._sock.settimeout(timeout)
            try:
                send_message(self._sock, request)
                response = recv_message(self._sock)
            except socket.timeout as exc:
                raise RhinoTimeoutError(
                    f"Rhino did not respond to '{request['method']}' "
                    f"within {timeout}s"
                ) from exc
            finally:
                # Reset to blocking (no timeout) after this command.
                if self._sock is not None:
                    self._sock.settimeout(None)

        # ------------------------------------------------------------------
        # Validate and unpack the response.
        # ------------------------------------------------------------------
        if not isinstance(response, dict):
            raise RhinoConnectionError(
                f"Malformed response (expected dict, got {type(response).__name__})"
            )

        error = response.get("error")
        if error is not None:
            code = error.get("code", -1) if isinstance(error, dict) else -1
            message = (
                error.get("message", str(error))
                if isinstance(error, dict)
                else str(error)
            )
            raise RhinoCommandError(code=code, message=message)

        result = response.get("result")
        if result is None:
            result = {}

        return result


# ---------------------------------------------------------------------------
# Module-level singleton
# ---------------------------------------------------------------------------

_singleton: Optional[RhinoConnection] = None
_singleton_lock = threading.Lock()


def get_connection(
    host: Optional[str] = None,
    port: Optional[int] = None,
    timeout: int = 10,
) -> RhinoConnection:
    """
    Return the singleton RhinoConnection, connecting automatically if needed.

    On the first call (or after the singleton was disconnected and garbage-
    collected), a new RhinoConnection is created and connect() is called.
    Subsequent calls return the same instance without reconnecting.

    Host and port default to values from mcp_server.config if not supplied.

    Args:
        host:    Rhino plugin host (defaults to config value).
        port:    Rhino plugin port (defaults to config value).
        timeout: Connection timeout in seconds (default: 10).

    Returns:
        An active RhinoConnection instance.

    Raises:
        RhinoConnectionError: If the connection cannot be established.
    """
    global _singleton

    # Resolve defaults from config.
    if host is None or port is None:
        try:
            from mcp_server import config as _cfg  # type: ignore
            _default_host = getattr(_cfg, "RHINO_HOST", "127.0.0.1")
            _default_port = getattr(_cfg, "RHINO_PORT", 9876)
        except ImportError:
            _default_host = "127.0.0.1"
            _default_port = 9876
        host = host or _default_host
        port = port or _default_port

    with _singleton_lock:
        if _singleton is None or not _singleton.is_connected():
            conn = RhinoConnection()
            conn.connect(host=host, port=port, timeout=timeout)
            _singleton = conn
        return _singleton
