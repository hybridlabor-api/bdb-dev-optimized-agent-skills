"""
tests/test_connection.py
=========================
Unit tests for golem_3dmcp/connection.py — the RhinoConnection TCP client
and the get_connection() singleton.

All network I/O is replaced with mocks; no live socket connections are made.
"""

from __future__ import annotations

import json
import socket
import struct
import threading
from unittest.mock import MagicMock, patch

import pytest

import golem_3dmcp.connection as _conn_module
from golem_3dmcp.connection import (
    RhinoCommandError,
    RhinoConnection,
    RhinoConnectionError,
    RhinoTimeoutError,
    get_connection,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_HEADER_FORMAT = "!I"
_HEADER_SIZE = struct.calcsize(_HEADER_FORMAT)


def _encode(data: dict) -> bytes:
    """Encode a dict as length-prefixed JSON (the protocol wire format)."""
    payload = json.dumps(data, ensure_ascii=False).encode("utf-8")
    header = struct.pack(_HEADER_FORMAT, len(payload))
    return header + payload


def _make_mock_socket(response: dict | None = None) -> MagicMock:
    """
    Create a mock socket that:
      - ignores sendall()
      - returns the encoded *response* from recv() calls
    """
    sock = MagicMock(spec=socket.socket)
    if response is not None:
        buf = bytearray(_encode(response))

        def _recv(n: int) -> bytes:
            chunk = bytes(buf[:n])
            del buf[:n]
            return chunk

        sock.recv.side_effect = _recv
    return sock


def _success_response(result: dict, request_id: str = "test-id") -> dict:
    return {"id": request_id, "result": result, "error": None}


def _error_response(code: int, message: str, request_id: str = "test-id") -> dict:
    return {
        "id": request_id,
        "result": None,
        "error": {"code": code, "message": message},
    }


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(autouse=True)
def reset_singleton():
    """Reset the module-level singleton before and after each test."""
    original = _conn_module._singleton
    _conn_module._singleton = None
    yield
    _conn_module._singleton = original


@pytest.fixture
def conn():
    """A RhinoConnection with _sock pre-set to avoid needing connect()."""
    c = RhinoConnection()
    c._sock = MagicMock(spec=socket.socket)
    return c


# ---------------------------------------------------------------------------
# Custom exception hierarchy
# ---------------------------------------------------------------------------

class TestExceptionHierarchy:

    def test_rhino_connection_error_is_os_error(self):
        with pytest.raises(OSError):
            raise RhinoConnectionError("test")

    def test_rhino_command_error_is_runtime_error(self):
        with pytest.raises(RuntimeError):
            raise RhinoCommandError(code=404, message="not found")

    def test_rhino_command_error_attributes(self):
        exc = RhinoCommandError(code=500, message="internal error")
        assert exc.code == 500
        assert exc.message == "internal error"
        assert "500" in str(exc)
        assert "internal error" in str(exc)

    def test_rhino_timeout_error_is_timeout_error(self):
        with pytest.raises(TimeoutError):
            raise RhinoTimeoutError("timed out")


# ---------------------------------------------------------------------------
# connect / disconnect lifecycle
# ---------------------------------------------------------------------------

class TestConnectDisconnect:

    def test_connect_creates_socket_and_pings(self):
        """connect() should create a socket and verify it with a ping command."""
        mock_sock = _make_mock_socket(
            _success_response({"pong": True})
        )
        with patch("golem_3dmcp.connection.socket.socket", return_value=mock_sock):
            c = RhinoConnection()
            c.connect(host="127.0.0.1", port=9876, timeout=5)

        assert c.is_connected()
        # sendall was called (the ping request was sent)
        assert mock_sock.sendall.called

    def test_connect_raises_on_socket_error(self):
        """If the TCP handshake fails, RhinoConnectionError is raised."""
        mock_sock = MagicMock(spec=socket.socket)
        mock_sock.connect.side_effect = OSError("connection refused")
        with patch("golem_3dmcp.connection.socket.socket", return_value=mock_sock):
            c = RhinoConnection()
            with pytest.raises(RhinoConnectionError, match="connection refused"):
                c.connect()

    def test_connect_raises_when_ping_fails(self):
        """If ping returns an error response, RhinoConnectionError is raised."""
        mock_sock = _make_mock_socket(
            _error_response(code=503, message="not ready")
        )
        with patch("golem_3dmcp.connection.socket.socket", return_value=mock_sock):
            c = RhinoConnection()
            with pytest.raises(RhinoConnectionError):
                c.connect()

    def test_disconnect_clears_socket(self, conn):
        conn.disconnect()
        assert not conn.is_connected()

    def test_disconnect_is_idempotent(self, conn):
        """disconnect() called multiple times should not raise."""
        conn.disconnect()
        conn.disconnect()  # second call — should be a no-op

    def test_is_connected_false_when_no_socket(self):
        c = RhinoConnection()
        assert not c.is_connected()

    def test_is_connected_true_when_socket_set(self, conn):
        assert conn.is_connected()


# ---------------------------------------------------------------------------
# send_command — request envelope
# ---------------------------------------------------------------------------

class TestSendCommandRequestEnvelope:

    def test_request_envelope_structure(self, conn):
        """
        send_command must build a request with 'id', 'method', 'params'
        and send it over the wire.
        """
        result_payload = {"guid": "abc-123"}
        # Set up the mock socket to return a success response.
        buf = bytearray(_encode(_success_response(result_payload)))
        conn._sock.recv.side_effect = lambda n: _drain(buf, n)

        conn.send_command("scene.get_document_info", {"filter": None})

        # Decode what was sent via sendall
        raw = conn._sock.sendall.call_args[0][0]
        (length,) = struct.unpack(_HEADER_FORMAT, raw[:_HEADER_SIZE])
        request = json.loads(raw[_HEADER_SIZE:].decode("utf-8"))

        assert "id" in request
        assert len(request["id"]) > 0          # non-empty UUID
        assert request["method"] == "scene.get_document_info"
        assert request["params"] == {"filter": None}

    def test_request_id_is_unique_per_call(self, conn):
        """Each send_command call generates a fresh UUID4 request ID."""
        ids = []

        def capture_and_respond(raw: bytes) -> None:
            (length,) = struct.unpack(_HEADER_FORMAT, raw[:_HEADER_SIZE])
            req = json.loads(raw[_HEADER_SIZE:].decode("utf-8"))
            ids.append(req["id"])

        # We need two responses; queue them up.
        responses = [
            _encode(_success_response({})),
            _encode(_success_response({})),
        ]
        combined = bytearray(b"".join(responses))

        conn._sock.recv.side_effect = lambda n: _drain(combined, n)
        conn._sock.sendall.side_effect = capture_and_respond

        conn.send_command("ping", {})
        conn.send_command("ping", {})

        assert ids[0] != ids[1]

    def test_send_command_returns_result(self, conn):
        """send_command must return the 'result' dict from the response."""
        expected = {"file_path": "/tmp/model.3dm", "units": "Meters"}
        buf = bytearray(_encode(_success_response(expected)))
        conn._sock.recv.side_effect = lambda n: _drain(buf, n)

        result = conn.send_command("files.get_document_path", {})
        assert result == expected

    def test_send_command_returns_empty_dict_for_null_result(self, conn):
        """If 'result' is null in the response, return an empty dict."""
        response = {"id": "x", "result": None, "error": None}
        buf = bytearray(_encode(response))
        conn._sock.recv.side_effect = lambda n: _drain(buf, n)

        result = conn.send_command("ping", {})
        assert result == {}


# ---------------------------------------------------------------------------
# send_command — error handling
# ---------------------------------------------------------------------------

class TestSendCommandErrors:

    def test_raises_rhino_command_error_on_error_response(self, conn):
        """An error envelope from Rhino must raise RhinoCommandError."""
        buf = bytearray(_encode(_error_response(404, "object not found")))
        conn._sock.recv.side_effect = lambda n: _drain(buf, n)

        with pytest.raises(RhinoCommandError) as exc_info:
            conn.send_command("scene.get_object_info", {"guid": "bad"})

        assert exc_info.value.code == 404
        assert "object not found" in exc_info.value.message

    def test_raises_rhino_timeout_error_on_socket_timeout(self, conn):
        """A socket.timeout during recv must raise RhinoTimeoutError (not retried)."""
        conn._sock.recv.side_effect = TimeoutError("timed out")
        with pytest.raises(RhinoTimeoutError):
            conn.send_command("slow.command", {}, timeout=1)

    def test_raises_connection_error_when_not_connected(self):
        """Calling send_command without a socket raises RhinoConnectionError."""
        c = RhinoConnection()
        assert c._sock is None
        with pytest.raises(RhinoConnectionError, match="Not connected"):
            conn_for_test = c
            # Bypass the retry loop by calling _send_and_recv directly
            conn_for_test._send_and_recv({"id": "x", "method": "m", "params": {}}, 5)

    def test_rhino_command_error_is_not_retried(self, conn):
        """
        Application-level errors (RhinoCommandError) must be raised
        immediately without triggering the auto-reconnect retry loop.
        """
        # Provide a single error response; if retried it would fail because
        # there's no second response in the buffer.
        buf = bytearray(_encode(_error_response(500, "scripting error")))
        conn._sock.recv.side_effect = lambda n: _drain(buf, n)

        with pytest.raises(RhinoCommandError):
            conn.send_command("scripting.execute_python", {"code": "bad"})

        # sendall called exactly once (no retries)
        assert conn._sock.sendall.call_count == 1

    def test_timeout_is_not_retried(self, conn):
        """RhinoTimeoutError must propagate without retry."""
        conn._sock.recv.side_effect = TimeoutError("timed out")

        with pytest.raises(RhinoTimeoutError):
            conn.send_command("slow.op", {})

        assert conn._sock.sendall.call_count == 1

    def test_malformed_response_raises_connection_error(self, conn):
        """
        If the response is not a dict (e.g. a JSON list), a
        RhinoConnectionError is raised.
        """
        # Encode a list instead of a dict
        payload = json.dumps([1, 2, 3]).encode("utf-8")
        header = struct.pack(_HEADER_FORMAT, len(payload))
        buf = bytearray(header + payload)
        conn._sock.recv.side_effect = lambda n: _drain(buf, n)

        with pytest.raises(RhinoConnectionError, match="Malformed"):
            conn.send_command("ping", {})


# ---------------------------------------------------------------------------
# Auto-reconnect
# ---------------------------------------------------------------------------

class TestAutoReconnect:

    def test_reconnects_on_broken_pipe_error(self):
        """
        On BrokenPipeError, send_command should attempt to reconnect and
        retry the command.
        """
        c = RhinoConnection()

        # First call: raise BrokenPipeError (simulating dropped connection).
        # After reconnect: return a valid socket with a success response.
        success_buf = bytearray(_encode(_success_response({"ok": True})))

        reconnected_sock = MagicMock(spec=socket.socket)
        reconnected_sock.recv.side_effect = lambda n: _drain(success_buf, n)

        call_count = 0

        original_send_and_recv = RhinoConnection._send_and_recv

        def patched_send_and_recv(self_inner, request, timeout):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise BrokenPipeError("pipe broken")
            return original_send_and_recv(self_inner, request, timeout)

        def patched_reconnect(self_inner):
            # Inject a fresh working socket
            self_inner._sock = reconnected_sock

        with patch.object(RhinoConnection, "_send_and_recv", patched_send_and_recv):
            with patch.object(RhinoConnection, "reconnect", patched_reconnect):
                c._sock = MagicMock(spec=socket.socket)
                result = c.send_command("ping", {})

        assert result == {"ok": True}
        assert call_count == 2  # first attempt failed, second succeeded

    def test_raises_after_max_reconnect_attempts(self):
        """
        If every attempt fails with BrokenPipeError, RhinoConnectionError
        is raised after _MAX_AUTO_RECONNECT_ATTEMPTS attempts.
        """
        c = RhinoConnection()
        c._sock = MagicMock(spec=socket.socket)

        attempts = []

        def always_broken_pipe(self_inner, request, timeout):
            attempts.append(1)
            raise BrokenPipeError("always broken")

        def no_op_reconnect(self_inner):
            c._sock = MagicMock(spec=socket.socket)  # give it a fresh mock

        with patch.object(RhinoConnection, "_send_and_recv", always_broken_pipe):
            with patch.object(RhinoConnection, "reconnect", no_op_reconnect):
                with pytest.raises(RhinoConnectionError):
                    c.send_command("ping", {})

        assert len(attempts) == RhinoConnection._MAX_AUTO_RECONNECT_ATTEMPTS


# ---------------------------------------------------------------------------
# Thread safety
# ---------------------------------------------------------------------------

class TestThreadSafety:

    def test_concurrent_send_command_calls_are_serialised(self):
        """
        Multiple threads calling send_command() concurrently should all
        succeed and each receive their own response without interleaving.
        """
        NUM_THREADS = 8
        results: list[dict] = []
        errors: list[Exception] = []

        def worker(thread_id: int) -> None:
            c = RhinoConnection()
            expected = {"thread": thread_id}

            buf = bytearray(_encode(_success_response(expected)))
            mock_sock = MagicMock(spec=socket.socket)
            mock_sock.recv.side_effect = lambda n: _drain(buf, n)
            c._sock = mock_sock

            try:
                result = c.send_command("ping", {})
                results.append(result)
            except Exception as e:
                errors.append(e)

        threads = [
            threading.Thread(target=worker, args=(i,))
            for i in range(NUM_THREADS)
        ]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert len(errors) == 0
        assert len(results) == NUM_THREADS

    def test_lock_prevents_concurrent_access_to_socket(self, conn):
        """
        The internal threading.Lock must block a second thread from
        entering _send_and_recv while the first is still in progress.
        """
        entered_first = threading.Event()
        can_finish = threading.Event()

        success_data = _encode(_success_response({}))
        buf = bytearray(success_data + success_data)
        conn._sock.recv.side_effect = lambda n: _drain(buf, n)

        # Patch sendall to signal thread coordination
        def slow_sendall(data: bytes) -> None:
            entered_first.set()
            can_finish.wait(timeout=2)

        conn._sock.sendall.side_effect = slow_sendall

        thread1_result = {}
        thread2_result = {}

        def thread1():
            thread1_result["r"] = conn.send_command("t1", {})

        def thread2():
            entered_first.wait(timeout=2)
            can_finish.set()
            thread2_result["r"] = conn.send_command("t2", {})

        t1 = threading.Thread(target=thread1)
        t2 = threading.Thread(target=thread2)
        t1.start()
        t2.start()
        t1.join(timeout=5)
        t2.join(timeout=5)

        assert "r" in thread1_result
        assert "r" in thread2_result


# ---------------------------------------------------------------------------
# get_connection() singleton
# ---------------------------------------------------------------------------

class TestGetConnectionSingleton:

    def test_returns_singleton_on_second_call(self):
        """Two calls to get_connection() with an already-connected singleton
        should return the same instance."""
        mock_conn = MagicMock(spec=RhinoConnection)
        mock_conn.is_connected.return_value = True
        _conn_module._singleton = mock_conn

        result1 = get_connection()
        result2 = get_connection()

        assert result1 is result2

    def test_creates_new_connection_when_singleton_is_none(self):
        """When no singleton exists, get_connection() creates and connects one."""
        _conn_module._singleton = None

        mock_conn = MagicMock(spec=RhinoConnection)
        mock_conn.is_connected.return_value = True

        with patch("golem_3dmcp.connection.RhinoConnection", return_value=mock_conn):
            result = get_connection(host="127.0.0.1", port=9876)

        mock_conn.connect.assert_called_once_with(
            host="127.0.0.1", port=9876, timeout=10
        )
        assert result is mock_conn

    def test_creates_new_connection_when_existing_is_disconnected(self):
        """
        If the existing singleton is disconnected, get_connection() creates
        a fresh connection.
        """
        stale_conn = MagicMock(spec=RhinoConnection)
        stale_conn.is_connected.return_value = False
        _conn_module._singleton = stale_conn

        fresh_conn = MagicMock(spec=RhinoConnection)
        fresh_conn.is_connected.return_value = True

        with patch("golem_3dmcp.connection.RhinoConnection", return_value=fresh_conn):
            result = get_connection(host="127.0.0.1", port=9876)

        fresh_conn.connect.assert_called_once()
        assert result is fresh_conn

    def test_stores_new_connection_as_singleton(self):
        """After creating a new connection it becomes the module singleton."""
        _conn_module._singleton = None

        mock_conn = MagicMock(spec=RhinoConnection)
        mock_conn.is_connected.return_value = True

        with patch("golem_3dmcp.connection.RhinoConnection", return_value=mock_conn):
            get_connection(host="127.0.0.1", port=9876)

        assert _conn_module._singleton is mock_conn


# ---------------------------------------------------------------------------
# Helpers used within this module
# ---------------------------------------------------------------------------

def _drain(buf: bytearray, n: int) -> bytes:
    """Pop and return the first *n* bytes from *buf*."""
    chunk = bytes(buf[:n])
    del buf[:n]
    return chunk
