# -*- coding: utf-8 -*-
"""
rhino_plugin/protocol.py
========================
Length-prefixed JSON message framing for the GOLEM-3DMCP Rhino plugin.

Wire format:
    [4 bytes big-endian uint32: payload length][N bytes: UTF-8 JSON payload]

This module runs INSIDE Rhino 3D with Python 3.9. It must:
  - Use ONLY Python stdlib (no third-party packages).
  - Be compatible with Python 3.9 (no match/case, no X|Y union syntax).
  - Handle TCP fragmentation correctly -- a single send() can arrive as
    multiple recv() calls, so every read loops until the exact byte count
    is satisfied.

Author: GOLEM-3DMCP
"""

import json
import socket
import struct
try:
    from typing import Dict, Any, Optional
except ImportError:
    pass

# Header is a single big-endian unsigned 32-bit integer (4 bytes).
_HEADER_FORMAT = "!I"
_HEADER_SIZE = struct.calcsize(_HEADER_FORMAT)  # Always 4


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _recv_exactly(sock, num_bytes):
    # type: (socket.socket, int) -> bytes
    """
    Read exactly *num_bytes* from *sock*, blocking until all bytes arrive.

    TCP is a stream protocol -- recv() may return fewer bytes than requested
    if the kernel buffer is not yet full, or if the sender transmitted the
    data in multiple segments.  This helper loops until the full count is
    satisfied or the connection is closed/broken.

    Raises:
        ConnectionError: If the remote peer closes the connection before
            all bytes have been received (i.e. recv returns 0 bytes mid-
            stream, which indicates EOF / graceful shutdown).
        OSError: Propagated from socket.recv() on I/O errors.
    """
    buf = b""
    remaining = num_bytes
    while remaining > 0:
        chunk = sock.recv(remaining)
        if not chunk:
            # recv() returning b"" means the peer closed the connection.
            raise ConnectionError(
                "Connection closed by remote peer after receiving "
                "{received}/{expected} bytes".format(
                    received=num_bytes - remaining,
                    expected=num_bytes,
                )
            )
        buf += chunk
        remaining -= len(chunk)
    return buf


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def send_message(sock, data):
    # type: (socket.socket, Dict[str, Any]) -> None
    """
    Serialize *data* to JSON and send it over *sock* with a 4-byte length
    prefix (big-endian uint32).

    The serialisation intentionally uses UTF-8, which is also what the
    receiving side expects.  The 4-byte header contains the byte-length of
    the encoded payload (not the character count, which differs for non-ASCII
    strings).

    Args:
        sock:  A connected, blocking TCP socket.
        data:  Any JSON-serialisable Python dictionary.

    Raises:
        TypeError:    If *data* is not JSON-serialisable.
        OSError:      On socket write errors (broken pipe, reset, etc.).
        struct.error: If the payload exceeds 2^32 - 1 bytes (4 GB), which
                      would overflow the uint32 length field.
    """
    payload = json.dumps(data, ensure_ascii=False).encode("utf-8")
    if len(payload) > 0xFFFFFFFF:
        raise ValueError(
            "Message payload too large: {size} bytes (max 4294967295)".format(
                size=len(payload)
            )
        )
    header = struct.pack(_HEADER_FORMAT, len(payload))
    # sendall() keeps sending until every byte is transmitted, handling
    # the case where the kernel buffer is temporarily full.
    sock.sendall(header + payload)


def recv_message(sock):
    # type: (socket.socket,) -> Dict[str, Any]
    """
    Receive one length-prefixed JSON message from *sock*.

    Reads the 4-byte header first, then reads exactly that many bytes for
    the payload, then deserialises the JSON.

    Args:
        sock: A connected, blocking TCP socket.

    Returns:
        The deserialised message as a Python dictionary.

    Raises:
        ConnectionError: If the connection is closed mid-stream.
        json.JSONDecodeError: If the payload is not valid JSON.
        OSError: On socket read errors.
    """
    # Step 1: Read the fixed-size 4-byte length header.
    raw_header = _recv_exactly(sock, _HEADER_SIZE)
    (payload_length,) = struct.unpack(_HEADER_FORMAT, raw_header)

    # Guard against absurdly large payloads that could exhaust memory.
    # 64 MB is a generous ceiling for any Rhino command exchange.
    _MAX_PAYLOAD = 64 * 1024 * 1024  # 64 MB
    if payload_length > _MAX_PAYLOAD:
        raise ValueError(
            "Incoming message too large: {size} bytes (max {limit})".format(
                size=payload_length,
                limit=_MAX_PAYLOAD,
            )
        )

    # Step 2: Read exactly payload_length bytes for the JSON body.
    raw_payload = _recv_exactly(sock, payload_length)

    # Step 3: Decode UTF-8 and parse JSON.
    return json.loads(raw_payload.decode("utf-8"))
