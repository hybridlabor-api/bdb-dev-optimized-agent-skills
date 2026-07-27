"""
tests/test_protocol.py
=======================
Unit tests for golem_3dmcp/protocol.py — the length-prefixed JSON message
framing layer.

All tests use mock sockets or raw byte buffers; no real TCP connections are
made.
"""

from __future__ import annotations

import json
import socket
import struct
from unittest.mock import MagicMock

import pytest

from golem_3dmcp.protocol import recv_message, send_message

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_HEADER_FORMAT = "!I"
_HEADER_SIZE = struct.calcsize(_HEADER_FORMAT)  # 4


def _build_wire(data: dict) -> bytes:
    """Encode *data* into the wire format the protocol uses."""
    payload = json.dumps(data, ensure_ascii=False).encode("utf-8")
    header = struct.pack(_HEADER_FORMAT, len(payload))
    return header + payload


def _make_recv_socket(raw_bytes: bytes) -> MagicMock:
    """
    Return a mock socket whose recv() delivers *raw_bytes* in a single chunk
    (or as instructed by the standard TCP stream loop).
    """
    sock = MagicMock(spec=socket.socket)
    buf = bytearray(raw_bytes)

    def _recv(n: int) -> bytes:
        chunk = bytes(buf[:n])
        del buf[:n]
        return chunk

    sock.recv.side_effect = _recv
    return sock


def _make_fragmented_recv_socket(raw_bytes: bytes, chunk_size: int) -> MagicMock:
    """
    Return a mock socket whose recv() delivers at most *chunk_size* bytes
    at a time, simulating TCP fragmentation.
    """
    sock = MagicMock(spec=socket.socket)
    buf = bytearray(raw_bytes)

    def _recv(n: int) -> bytes:
        actual = min(n, chunk_size, len(buf))
        chunk = bytes(buf[:actual])
        del buf[:actual]
        return chunk

    sock.recv.side_effect = _recv
    return sock


# ---------------------------------------------------------------------------
# send_message tests
# ---------------------------------------------------------------------------

class TestSendMessage:

    def test_sends_4_byte_header_followed_by_json(self):
        """sendall() must be called with [header][payload] as a single write."""
        data = {"method": "ping", "params": {}}
        expected_payload = json.dumps(data, ensure_ascii=False).encode("utf-8")
        expected_header = struct.pack(_HEADER_FORMAT, len(expected_payload))

        sock = MagicMock(spec=socket.socket)
        send_message(sock, data)

        sock.sendall.assert_called_once_with(expected_header + expected_payload)

    def test_empty_dict(self):
        """An empty dict is a valid message."""
        sock = MagicMock(spec=socket.socket)
        send_message(sock, {})
        assert sock.sendall.called

        sent = sock.sendall.call_args[0][0]
        (length,) = struct.unpack(_HEADER_FORMAT, sent[:_HEADER_SIZE])
        decoded = json.loads(sent[_HEADER_SIZE:].decode("utf-8"))
        assert decoded == {}

    def test_nested_objects(self):
        """Deeply nested dicts are serialised correctly."""
        data = {"a": {"b": {"c": [1, 2, 3]}}, "x": None}
        sock = MagicMock(spec=socket.socket)
        send_message(sock, data)

        sent = sock.sendall.call_args[0][0]
        (length,) = struct.unpack(_HEADER_FORMAT, sent[:_HEADER_SIZE])
        payload_bytes = sent[_HEADER_SIZE:]
        assert len(payload_bytes) == length
        assert json.loads(payload_bytes.decode("utf-8")) == data

    def test_unicode_payload(self):
        """Non-ASCII characters must be preserved (ensure_ascii=False)."""
        data = {"text": "Привет мир — こんにちは世界 — مرحبا بالعالم"}
        sock = MagicMock(spec=socket.socket)
        send_message(sock, data)

        sent = sock.sendall.call_args[0][0]
        payload = sent[_HEADER_SIZE:].decode("utf-8")
        decoded = json.loads(payload)
        assert decoded["text"] == data["text"]

    def test_large_payload(self):
        """A 1 MB payload should be sent without error."""
        data = {"blob": "x" * (1024 * 1024)}
        sock = MagicMock(spec=socket.socket)
        send_message(sock, data)
        assert sock.sendall.called

    def test_header_encodes_correct_byte_length(self):
        """Header value must be the UTF-8 byte length, not the character count."""
        # The emoji is 4 bytes in UTF-8 but 1 character
        data = {"emoji": "\U0001F600"}
        payload_bytes = json.dumps(data, ensure_ascii=False).encode("utf-8")
        expected_length = len(payload_bytes)

        sock = MagicMock(spec=socket.socket)
        send_message(sock, data)

        sent = sock.sendall.call_args[0][0]
        (actual_length,) = struct.unpack(_HEADER_FORMAT, sent[:_HEADER_SIZE])
        assert actual_length == expected_length

    def test_non_serialisable_raises_type_error(self):
        """Passing a non-JSON-serialisable value must raise TypeError."""
        sock = MagicMock(spec=socket.socket)
        with pytest.raises(TypeError):
            send_message(sock, {"bad": object()})

    def test_propagates_socket_os_error(self):
        """If sendall raises OSError it propagates to the caller."""
        sock = MagicMock(spec=socket.socket)
        sock.sendall.side_effect = OSError("broken pipe")
        with pytest.raises(OSError, match="broken pipe"):
            send_message(sock, {"x": 1})


# ---------------------------------------------------------------------------
# recv_message tests
# ---------------------------------------------------------------------------

class TestRecvMessage:

    def test_receives_simple_dict(self):
        """A well-formed wire message is decoded back to the original dict."""
        data = {"id": "abc", "result": {"x": 42}}
        sock = _make_recv_socket(_build_wire(data))
        result = recv_message(sock)
        assert result == data

    def test_empty_dict_roundtrip(self):
        sock = _make_recv_socket(_build_wire({}))
        assert recv_message(sock) == {}

    def test_nested_objects(self):
        data = {"a": [1, 2, {"b": True, "c": None}]}
        sock = _make_recv_socket(_build_wire(data))
        assert recv_message(sock) == data

    def test_unicode_roundtrip(self):
        data = {"greeting": "日本語テスト — тест — اختبار"}
        sock = _make_recv_socket(_build_wire(data))
        assert recv_message(sock)["greeting"] == data["greeting"]

    def test_large_payload_roundtrip(self):
        """A 2 MB payload should be received correctly."""
        data = {"data": "A" * (2 * 1024 * 1024)}
        sock = _make_recv_socket(_build_wire(data))
        result = recv_message(sock)
        assert result["data"] == data["data"]

    # -- TCP fragmentation --

    def test_partial_reads_header_split(self):
        """Correctly handles receiving the 4-byte header 1 byte at a time."""
        data = {"fragmented": True}
        wire = _build_wire(data)
        sock = _make_fragmented_recv_socket(wire, chunk_size=1)
        result = recv_message(sock)
        assert result == data

    def test_partial_reads_payload_split(self):
        """Correctly handles payload arriving in 3-byte chunks."""
        data = {"key": "value", "number": 12345}
        wire = _build_wire(data)
        sock = _make_fragmented_recv_socket(wire, chunk_size=3)
        result = recv_message(sock)
        assert result == data

    def test_partial_reads_single_byte_chunks(self):
        """Stress test: 1-byte-at-a-time delivery of a non-trivial payload."""
        data = {"list": list(range(50))}
        wire = _build_wire(data)
        sock = _make_fragmented_recv_socket(wire, chunk_size=1)
        result = recv_message(sock)
        assert result == data

    # -- Error conditions --

    def test_oversized_message_rejected(self):
        """Messages with a declared payload > 64 MB must raise ValueError."""
        oversized_length = 64 * 1024 * 1024 + 1  # one byte over the cap
        header = struct.pack(_HEADER_FORMAT, oversized_length)
        sock = _make_recv_socket(header)
        with pytest.raises(ValueError, match="too large"):
            recv_message(sock)

    def test_exactly_at_size_limit_accepted(self):
        """
        A message whose declared size equals the cap (64 MB) should not be
        rejected by the size guard — the guard fires strictly above the cap.

        We do not actually receive 64 MB of data; we only verify that the
        ValueError for size is NOT raised.  The subsequent recv for the payload
        will fail with ConnectionError (empty buffer), which is acceptable.
        """
        limit = 64 * 1024 * 1024
        header = struct.pack(_HEADER_FORMAT, limit)
        # Provide header only — payload will trigger ConnectionError, not ValueError.
        sock = _make_recv_socket(header)
        with pytest.raises(ConnectionError):
            recv_message(sock)

    def test_malformed_json_raises_json_decode_error(self):
        """Non-JSON payload must raise json.JSONDecodeError."""
        payload = b"this is not json!!!"
        header = struct.pack(_HEADER_FORMAT, len(payload))
        sock = _make_recv_socket(header + payload)
        with pytest.raises(json.JSONDecodeError):
            recv_message(sock)

    def test_connection_closed_during_header_read(self):
        """
        If the peer closes the connection before sending the full 4-byte
        header, ConnectionError must be raised.
        """
        # Only 2 bytes of a 4-byte header are available.
        sock = _make_recv_socket(b"\x00\x00")
        with pytest.raises(ConnectionError):
            recv_message(sock)

    def test_connection_closed_during_payload_read(self):
        """
        If the peer closes the connection mid-payload, ConnectionError
        must be raised.
        """
        # Header says 100 bytes but only 10 bytes follow.
        payload_stub = b"x" * 10
        header = struct.pack(_HEADER_FORMAT, 100)
        sock = _make_recv_socket(header + payload_stub)
        with pytest.raises(ConnectionError):
            recv_message(sock)

    def test_connection_closed_immediately(self):
        """An immediately-closed connection raises ConnectionError."""
        sock = _make_recv_socket(b"")
        with pytest.raises(ConnectionError):
            recv_message(sock)


# ---------------------------------------------------------------------------
# Round-trip tests (send → recv)
# ---------------------------------------------------------------------------

class TestRoundTrip:
    """Verify that send_message and recv_message are inverse operations."""

    def _round_trip(self, data: dict) -> dict:
        """Send *data* with send_message, capture the bytes, feed them to recv_message."""
        captured: list[bytes] = []

        send_sock = MagicMock(spec=socket.socket)
        send_sock.sendall.side_effect = lambda b: captured.append(b)

        send_message(send_sock, data)
        wire_bytes = b"".join(captured)

        recv_sock = _make_recv_socket(wire_bytes)
        return recv_message(recv_sock)

    def test_simple_dict(self):
        data = {"method": "scene.get_document_info", "params": {}}
        assert self._round_trip(data) == data

    def test_empty_dict(self):
        assert self._round_trip({}) == {}

    def test_nested_structure(self):
        data = {
            "id": "uuid-1234",
            "result": {
                "objects": [{"guid": "g1", "type": "brep"}, {"guid": "g2"}],
                "count": 2,
                "meta": {"version": 1, "ok": True},
            },
            "error": None,
        }
        assert self._round_trip(data) == data

    def test_unicode(self):
        data = {"name": "Привет — مرحبا — 你好", "emoji": "\U0001F680"}
        result = self._round_trip(data)
        assert result == data

    def test_boolean_and_null_values(self):
        data = {"flag": True, "off": False, "nothing": None}
        assert self._round_trip(data) == data

    def test_integer_and_float_values(self):
        data = {"i": 42, "f": 3.14159265358979, "neg": -100}
        result = self._round_trip(data)
        assert result["i"] == 42
        assert abs(result["f"] - 3.14159265358979) < 1e-12
        assert result["neg"] == -100
