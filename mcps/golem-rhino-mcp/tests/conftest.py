"""
tests/conftest.py
==================
Shared pytest fixtures for GOLEM-3DMCP tests.

Fixtures
--------
mock_socket
    A MagicMock that mimics socket.socket.  Useful for testing send_message /
    recv_message without a real TCP connection.

mock_connection
    A MagicMock that mimics RhinoConnection.  send_command() records every
    call and returns a configurable response.  Useful for testing MCP tool
    functions without a live Rhino instance.

rhino_connection
    A real RhinoConnection to a live Rhino instance.  Automatically skipped
    when Rhino is not reachable.  Used only by tests marked
    @pytest.mark.integration.
"""

from __future__ import annotations

import json
import socket
import struct
from typing import Any
from unittest.mock import MagicMock

import pytest

from golem_3dmcp.connection import RhinoConnection, RhinoConnectionError

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _encode_message(data: dict) -> bytes:
    """Encode a dict into the wire format (4-byte header + UTF-8 JSON payload)."""
    payload = json.dumps(data, ensure_ascii=False).encode("utf-8")
    header = struct.pack("!I", len(payload))
    return header + payload


# ---------------------------------------------------------------------------
# mock_socket
# ---------------------------------------------------------------------------

@pytest.fixture
def mock_socket():
    """
    A MagicMock configured to look like a connected socket.socket.

    The fixture exposes a helper method ``set_recv_data`` that pre-loads
    bytes into the mock's recv() side effect queue so that callers can
    simulate arbitrary incoming data.

    Example::

        def test_something(mock_socket):
            mock_socket.set_recv_data(_encode_message({"hello": "world"}))
            result = recv_message(mock_socket)
            assert result == {"hello": "world"}
    """
    sock = MagicMock(spec=socket.socket)
    sock.fileno.return_value = 5  # non-negative so socket appears valid

    # Internal byte buffer for simulating recv() reads.
    _buf = bytearray()

    def _recv(n: int) -> bytes:
        chunk = bytes(_buf[:n])
        del _buf[:n]
        return chunk

    sock.recv.side_effect = _recv

    def _set_recv_data(data: bytes) -> None:
        _buf.extend(data)

    sock.set_recv_data = _set_recv_data
    return sock


# ---------------------------------------------------------------------------
# mock_connection
# ---------------------------------------------------------------------------

@pytest.fixture
def mock_connection():
    """
    A MagicMock that behaves like a connected RhinoConnection.

    send_command(method, params) records the call and returns
    mock_connection.default_result (default: empty dict).

    Set mock_connection.default_result to customise the return value for
    a test, or use side_effect for more complex scenarios.

    Example::

        def test_tool(mock_connection, monkeypatch):
            mock_connection.default_result = {"file_path": "/tmp/model.3dm"}
            monkeypatch.setattr("golem_3dmcp.tools.scene.get_connection",
                                lambda: mock_connection)
            result = get_document_info()
            assert result["file_path"] == "/tmp/model.3dm"
    """
    conn = MagicMock(spec=RhinoConnection)
    conn.default_result: dict = {}
    conn.calls: list[dict[str, Any]] = []

    def _send_command(method: str, params: dict, timeout: int = 30) -> dict:
        conn.calls.append({"method": method, "params": params, "timeout": timeout})
        return dict(conn.default_result)

    conn.send_command.side_effect = _send_command
    conn.is_connected.return_value = True
    return conn


# ---------------------------------------------------------------------------
# rhino_connection  (integration tests only)
# ---------------------------------------------------------------------------

@pytest.fixture(scope="session")
def rhino_connection():
    """
    A live RhinoConnection to a running Rhino instance.

    The fixture attempts to connect using default host/port (127.0.0.1:9876).
    If Rhino is not running the fixture yields None and marks the test as
    skipped — integration tests should guard with::

        if connection is None:
            pytest.skip("Rhino not running")

    Or simply rely on the autouse skip marker defined for
    @pytest.mark.integration tests.
    """
    conn = RhinoConnection()
    try:
        conn.connect(host="127.0.0.1", port=9876, timeout=3)
    except RhinoConnectionError:
        yield None
        return

    yield conn
    conn.disconnect()
