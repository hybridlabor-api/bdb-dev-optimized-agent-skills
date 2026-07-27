# GOLEM-3DMCP — TCP Protocol Specification

## Overview

The MCP server and the Rhino plugin communicate over a TCP socket using a simple length-prefixed JSON protocol. Both sides implement the same wire format, defined identically in:

- `mcp_server/protocol.py` (Python 3.10+, MCP server side)
- `rhino_plugin/protocol.py` (Python 3.9, Rhino plugin side)

The two files are kept in sync manually. Any change to the wire format must be applied to both.

---

## Wire Format

Every message — request or response — is framed as:

```
+------------------+----------------------+
| 4-byte header    | N-byte payload       |
| big-endian uint32| UTF-8 JSON bytes     |
+------------------+----------------------+
```

**Header:** A 4-byte unsigned 32-bit integer in big-endian byte order (network byte order, `struct` format `!I`). Its value is the exact byte length of the payload that follows.

**Payload:** The UTF-8 encoding of a JSON object. `ensure_ascii=False` is used, so all Unicode characters are preserved as-is rather than escaped.

**Maximum payload size:** 64 MB (67,108,864 bytes). Messages exceeding this limit are rejected with a `ValueError` on both sides to prevent memory exhaustion.

**Minimum payload size:** 0 bytes (empty payload) is technically valid wire-format but will fail JSON parsing.

### Python implementation

```python
# Sending
payload = json.dumps(data, ensure_ascii=False).encode("utf-8")
header = struct.pack("!I", len(payload))
sock.sendall(header + payload)

# Receiving
raw_header = _recv_exactly(sock, 4)
(payload_length,) = struct.unpack("!I", raw_header)
raw_payload = _recv_exactly(sock, payload_length)
data = json.loads(raw_payload.decode("utf-8"))
```

`_recv_exactly(sock, n)` reads exactly `n` bytes, looping across TCP segment boundaries. It raises `ConnectionError` if the remote peer closes the connection before all bytes arrive.

---

## Message Format

### Request (MCP server → Rhino plugin)

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "method": "creation.create_box",
  "params": {
    "corner_x": 0.0,
    "corner_y": 0.0,
    "corner_z": 0.0,
    "width": 100.0,
    "depth": 50.0,
    "height": 30.0
  }
}
```

| Field | Type | Description |
|-------|------|-------------|
| `id` | string | UUID4 request identifier. Echoed in the response for correlation. |
| `method` | string | Dot-namespaced method name, e.g. `"scene.list_objects"`. |
| `params` | object | Key/value parameters for the method. May be an empty object `{}`. |

If `params` is absent or not an object, the Rhino plugin treats it as `{}`.

### Response — Success (Rhino plugin → MCP server)

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "result": {
    "guid": "a1b2c3d4-...",
    "bounding_box": {
      "min": [0.0, 0.0, 0.0],
      "max": [100.0, 50.0, 30.0]
    }
  },
  "error": null
}
```

| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Echoed from the request. |
| `result` | object | The handler's return value. Never absent on success; at minimum `{}`. |
| `error` | null | Explicitly `null` on success. |

### Response — Error (Rhino plugin → MCP server)

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "result": null,
  "error": {
    "code": -32601,
    "message": "Method not found: creation.create_hexagon"
  }
}
```

| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Echoed from the request. May be `null` if the request could not be parsed. |
| `result` | null | Explicitly `null` on error. |
| `error` | object | Error descriptor with `code` (integer) and `message` (string). |

---

## Error Codes

The Rhino plugin uses two sets of error codes:

### JSON-RPC Standard Codes (used by `rhino_plugin/server.py`)

These are returned for transport-level or routing errors before a handler is invoked.

| Code | Meaning |
|------|---------|
| `-32601` | Method not found (not in any registry) |
| `-32603` | Internal server error (unhandled exception in dispatch logic) |
| `-32000` | Application error from external dispatcher |

### GOLEM Domain Codes (used by `rhino_plugin/dispatcher.py`)

These are returned when a registered handler encounters an application-level problem.

| Code | Meaning |
|------|---------|
| `"OK"` | Success (not used in error responses) |
| `"INVALID_PARAMS"` | Missing, wrong-type, or out-of-range parameter |
| `"OBJECT_NOT_FOUND"` | GUID not found in the Rhino document |
| `"OPERATION_FAILED"` | Rhino returned `null` or `false` for a geometry operation |
| `"TIMEOUT"` | UI thread did not execute the handler within 30 seconds |
| `"INTERNAL_ERROR"` | Unhandled Python exception in the handler; `details.traceback` is included |
| `"NOT_FOUND"` | Method name not in the dispatcher registry |
| `"NOT_IMPLEMENTED"` | Handler raises `NotImplementedError` |

GOLEM domain errors may include an optional `details` field:
```json
{
  "code": "INVALID_PARAMS",
  "message": "Required parameter 'guids' is missing.",
  "details": {"method": "operations.boolean_union"}
}
```

On the MCP server side, GOLEM domain codes are translated to `RhinoCommandError(code, message)`. The numeric code passed to `RhinoCommandError` is `-32000` for all GOLEM errors (the string code appears in the message).

---

## Timeout Behaviour

### Connection timeout

`RhinoConnection.connect()` has a `timeout` parameter (default 10 seconds). If the TCP handshake or the initial `ping` command does not complete within this window, `RhinoConnectionError` is raised.

### Command timeout

`RhinoConnection.send_command()` has a `timeout` parameter (default 30 seconds). This is applied via `socket.settimeout()` on the receive phase. If no response arrives within the timeout, `RhinoTimeoutError` is raised. Timeouts are not retried.

The 30-second default covers even slow Grasshopper recomputes. For long-running scripts (`scripting.execute_python`), pass a larger `timeout` value:
```python
conn.send_command("scripting.execute_python", {"code": "..."}, timeout=120)
```

### UI thread timeout

On the Rhino plugin side, `run_on_ui_thread()` waits up to 30 seconds for the UI thread to execute the handler. If the UI thread is busy (modal dialog open, file import in progress, etc.), the handler returns a `TIMEOUT` error.

---

## Ping / Liveness Check

The built-in `ping` method is a liveness check. It is called automatically during `connect()` to verify that the Rhino plugin is alive and responding.

Request:
```json
{"id": "any-id", "method": "ping", "params": {}}
```

Response:
```json
{"id": "any-id", "result": {"alive": true}, "error": null}
```

To perform a manual liveness check from code:
```python
conn = get_connection()
result = conn.send_command("ping", {})
assert result["alive"] is True
```

---

## Built-in Methods

Three methods are always registered, regardless of which handler modules are loaded:

| Method | Description |
|--------|-------------|
| `ping` | Liveness check. Returns `{"alive": true}`. |
| `shutdown` | Gracefully stop the Rhino plugin server. Returns `{"shutdown": "initiated"}` and then closes the socket. |
| `list_methods` | Return all registered method names. Returns `{"methods": ["creation.create_box", ...]}`. |

---

## Reconnection Logic

The MCP server (`mcp_server/connection.py`) handles transient connection failures automatically:

1. On `BrokenPipeError` or `ConnectionResetError` during `send_command()`, the client calls `reconnect()`.
2. `reconnect()` closes the socket and calls `connect()` with the same host/port.
3. This is retried up to `_MAX_AUTO_RECONNECT_ATTEMPTS = 3` times.
4. If all reconnection attempts fail, `RhinoConnectionError` is raised to the caller.

Rhino application-level errors (`RhinoCommandError`) and timeouts (`RhinoTimeoutError`) are not retried — they indicate a problem with the command itself, not the connection.

The singleton `get_connection()` function detects a disconnected socket via `is_connected()` and creates a fresh `RhinoConnection` if needed. Note that `is_connected()` is a lightweight check (the socket object exists and was not explicitly closed); it does not perform a round-trip. Use `send_command("ping", {})` for a hard liveness check.

---

## Grasshopper Sub-Server

The Grasshopper integration uses port 9877 (configurable via `GOLEM_GH_PORT`). The protocol is identical to the main server. The Grasshopper sub-server is an optional component — if it is not running, the `grasshopper.*` tools return `OPERATION_FAILED` errors rather than hanging.

---

## Wire Compatibility Notes

- **Byte order:** Big-endian (network byte order) for the 4-byte header. This is consistent across all platforms.
- **JSON encoding:** UTF-8, `ensure_ascii=False`. Rhino's Python runtime handles UTF-8 correctly.
- **Null values:** JSON `null` is used explicitly for `error: null` on success and `result: null` on error. Do not omit these fields.
- **Number types:** JSON does not distinguish int from float. All numbers arrive as Python `float` unless explicitly cast in handler code. Handler parameters are always validated and cast before use.
- **Large geometry:** The 64 MB payload cap is generous for typical geometry responses. If you need to transfer very large meshes, consider using `files.export_objects` + a local file path instead.
