"""
golem_3dmcp/protocol.py
======================
Length-prefixed JSON message framing for the GOLEM-3DMCP MCP server side.

Wire format (identical to rhino_plugin/protocol.py — byte-compatible):
    [4 bytes big-endian uint32: payload length][N bytes: UTF-8 JSON payload]

This module runs on the MCP server side (Python 3.10+) and is intentionally
kept in sync with rhino_plugin/protocol.py to guarantee wire compatibility.
The only differences are:
  - Modern Python type annotations (X | Y union syntax).
  - Type hints in function signatures.

Both sides must always agree on:
  1. Header format: big-endian uint32, 4 bytes.
  2. Payload encoding: UTF-8.
  3. Payload format: JSON object (dict).

Author: GOLEM-3DMCP
"""

import json
import socket
import struct
from typing import Any, cast

# Header is a single big-endian unsigned 32-bit integer (4 bytes).
_HEADER_FORMAT = "!I"
_HEADER_SIZE = struct.calcsize(_HEADER_FORMAT)  # Always 4

# Maximum accepted incoming payload.  Same ceiling as the Rhino side.
_MAX_PAYLOAD = 64 * 1024 * 1024  # 64 MB


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _recv_exactly(sock: socket.socket, num_bytes: int) -> bytes:
    """
    Read exactly *num_bytes* from *sock*, blocking until all bytes arrive.

    TCP is a stream protocol.  The kernel may deliver data in segments that
    do not align with application-level message boundaries.  This helper
    loops until the full byte count is satisfied.

    Raises:
        ConnectionError: If the remote peer closes the connection before
            all bytes have been received.
        OSError: Propagated directly from socket.recv() on I/O errors.
    """
    buf = b""
    remaining = num_bytes
    while remaining > 0:
        chunk = sock.recv(remaining)
        if not chunk:
            raise ConnectionError(
                f"Connection closed by remote peer after receiving "
                f"{num_bytes - remaining}/{num_bytes} bytes"
            )
        buf += chunk
        remaining -= len(chunk)
    return buf


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def send_message(sock: socket.socket, data: dict[str, Any]) -> None:
    """
    Serialize *data* to JSON and send it over *sock* with a 4-byte length
    prefix (big-endian uint32).

    This is byte-compatible with rhino_plugin.protocol.send_message.

    Args:
        sock:  A connected, blocking TCP socket.
        data:  Any JSON-serialisable Python dictionary.

    Raises:
        TypeError:    If *data* is not JSON-serialisable.
        ValueError:   If the serialised payload exceeds 2^32 - 1 bytes.
        OSError:      On socket write errors (broken pipe, reset, etc.).
    """
    payload = json.dumps(data, ensure_ascii=False).encode("utf-8")
    if len(payload) > 0xFFFFFFFF:
        raise ValueError(
            f"Message payload too large: {len(payload)} bytes (max 4294967295)"
        )
    header = struct.pack(_HEADER_FORMAT, len(payload))
    # sendall() guarantees all bytes are written, handling partial sends.
    sock.sendall(header + payload)


def recv_message(sock: socket.socket) -> dict[str, Any]:
    """
    Receive one length-prefixed JSON message from *sock*.

    Reads the 4-byte header first, then reads exactly that many bytes for
    the payload, then deserialises the JSON.

    This is byte-compatible with rhino_plugin.protocol.recv_message.

    Args:
        sock: A connected, blocking TCP socket.

    Returns:
        The deserialised message as a Python dictionary.

    Raises:
        ConnectionError:    If the connection is closed mid-stream.
        ValueError:         If the declared payload exceeds the safety cap.
        json.JSONDecodeError: If the payload is not valid JSON.
        OSError:            On socket read errors.
    """
    # Step 1: Read the fixed-size 4-byte length header.
    raw_header = _recv_exactly(sock, _HEADER_SIZE)
    (payload_length,) = struct.unpack(_HEADER_FORMAT, raw_header)

    # Guard against payloads that could exhaust memory.
    if payload_length > _MAX_PAYLOAD:
        raise ValueError(
            f"Incoming message too large: {payload_length} bytes "
            f"(max {_MAX_PAYLOAD})"
        )

    # Step 2: Read exactly payload_length bytes for the JSON body.
    raw_payload = _recv_exactly(sock, payload_length)

    # Step 3: Decode UTF-8 and parse JSON.
    return cast(dict[str, Any], json.loads(raw_payload.decode("utf-8")))
