# GOLEM-3DMCP — System Architecture

## Overview

GOLEM-3DMCP is a two-part system. One part runs in the standard Python environment managed by Claude Code; the other runs inside Rhino 3D's embedded Python interpreter. They communicate over a local TCP socket using a length-prefixed JSON protocol.

```
+---------------------+         stdio          +---------------------+
|   Claude Code       | <--------------------> |   MCP Server        |
|   (claude.ai/code)  |      MCP protocol      |   mcp_server/       |
+---------------------+                        +---------------------+
                                                         |
                                                         | TCP 127.0.0.1:9876
                                                         | length-prefixed JSON
                                                         v
                                                +---------------------+
                                                |   Rhino Plugin      |
                                                |   rhino_plugin/     |
                                                |   (Python 3.9,      |
                                                |    inside Rhino)    |
                                                +---------------------+
                                                         |
                                               RhinoCommon API calls
                                                         |
                                                         v
                                                +---------------------+
                                                |   Rhinoceros 3D     |
                                                |   UI Thread         |
                                                |   Document Model    |
                                                +---------------------+
                                                         |
                                            Optional GH sub-connection
                                                         |
                                                         v
                                                +---------------------+
                                                |   Grasshopper       |
                                                |   TCP 127.0.0.1:9877|
                                                +---------------------+
```

---

## Part 1 — MCP Server (`mcp_server/`)

The MCP server runs as a subprocess spawned by Claude Code. It speaks the Model Context Protocol over stdio and translates each tool call into a TCP command sent to the Rhino plugin.

### Entry Point

`mcp_server/server.py` creates a single `FastMCP` instance named `GOLEM-3DMCP`. Tool modules are imported inside `main()` rather than at module scope to avoid circular imports — the tool modules import the `mcp` singleton from `server.py`, so they must not be imported until after `mcp` is constructed.

```python
# mcp_server/server.py (simplified)
mcp = FastMCP("GOLEM-3DMCP", description="...")

def main() -> None:
    from mcp_server.tools import scene, creation, operations, ...
    mcp.run(transport="stdio")
```

### TCP Client (`mcp_server/connection.py`)

`RhinoConnection` manages the persistent TCP socket to the Rhino plugin. Key design decisions:

**Singleton pattern.** Only one `RhinoConnection` exists per MCP server process. `get_connection()` creates and connects it on first call; subsequent calls return the same instance. This avoids port exhaustion and matches Rhino's single-client model.

**Thread safety.** A `threading.Lock` serialises every send/receive cycle. The FastMCP framework may call tool functions from multiple threads concurrently; the lock ensures commands are not interleaved on the socket.

**Auto-reconnect.** On `BrokenPipeError` or `ConnectionResetError`, the client automatically attempts up to three reconnections before propagating the error. Timeout errors and application-level errors (`RhinoCommandError`) are not retried.

**Request IDs.** Every outbound message carries a UUID4 as `id`. This enables correlation in logs and debugging, and matches the wire format that Rhino expects.

### Protocol (`mcp_server/protocol.py`)

Wire format: a 4-byte big-endian unsigned 32-bit integer (the payload length in bytes) followed by the UTF-8-encoded JSON payload. Maximum payload: 64 MB.

The same format is implemented identically in `rhino_plugin/protocol.py` for byte-level compatibility. The only difference between the two copies is that the MCP server side uses Python 3.10+ type annotation syntax (`X | Y`) while the Rhino side uses Python 3.9 compatible `Optional[X]`.

### Tool Modules (`mcp_server/tools/`)

Each tool module imports the `mcp` singleton and registers functions with `@mcp.tool()`. The function signatures declare typed parameters and docstrings that become the tool descriptions exposed to Claude Code. The function bodies call `get_connection().send_command(method, params)` and return the result dict.

---

## Part 2 — Rhino Plugin (`rhino_plugin/`)

The plugin runs entirely inside Rhino's embedded Python 3.9 interpreter. It binds a TCP server socket, accepts connections from the MCP server, dispatches commands to handler functions, and executes those functions on Rhino's UI thread.

### TCP Server (`rhino_plugin/server.py`)

The server runs in a background daemon thread (the "accept loop") so it does not block Rhino's main thread. One client is served at a time — the accept loop calls `handle_client()` synchronously for each accepted connection. This is intentional: the Rhino document object model is single-threaded, and parallel client sessions would race on shared geometry state.

**Accept loop:**
```
Background thread:
  while running:
    conn = srv.accept()          # blocks up to 1 second
    handle_client(conn, addr)    # blocks until client disconnects
```

**Client handler:**
```
For each message:
  request  = recv_message(conn)   # blocking read
  response = _dispatch(method, params, id)
  send_message(conn, response)    # blocking write
```

### UI Thread Dispatch (`run_on_ui_thread`)

All Rhino document operations must happen on Rhino's main (UI) thread. The background thread cannot safely call RhinoCommon geometry methods directly.

`run_on_ui_thread(func)` solves this by:

1. Wrapping `func` in a closure that captures return value and any exception.
2. Posting the closure to the UI thread via `Rhino.RhinoApp.InvokeOnUiThread`.
3. Blocking on a `threading.Event` with a 30-second timeout.
4. Re-raising any exception that occurred on the UI thread.

Every handler invocation goes through `run_on_ui_thread`, including built-in methods like `ping`. The overhead is negligible and the safety guarantee is absolute.

### Dispatcher (`rhino_plugin/dispatcher.py`)

The dispatcher maintains a `dict` mapping method name strings to handler callables. Registration uses the `@handler("namespace.method_name")` decorator, which stores the function both in the dict and as a `_handler_name` attribute for bulk discovery.

**Error codes defined in `ErrorCode`:**

| Code | Meaning |
|------|---------|
| `OK` | Success (not used directly in errors) |
| `INVALID_PARAMS` | Missing or wrong-type parameter |
| `OBJECT_NOT_FOUND` | GUID not found in Rhino document |
| `OPERATION_FAILED` | Rhino returned an error or null result |
| `TIMEOUT` | UI thread did not respond in time |
| `INTERNAL_ERROR` | Unhandled exception in handler |
| `NOT_FOUND` | Method name not registered |
| `NOT_IMPLEMENTED` | Handler raises `NotImplementedError` |

`dispatch()` always returns a response dict (never raises), mapping Python exceptions to appropriate error codes.

### Handler Registration

`rhino_plugin/handlers/__init__.py` exports `register_all_handlers()`, which imports each handler module and calls `register_handlers_from_module()` on it. This is called once during `start_server()`. The server registers the three built-in methods (`ping`, `shutdown`, `list_methods`) first, then bulk-registers all domain handlers.

The two-step registration (decorator at import + `register_handlers_from_module` scan) is belt-and-suspenders: decorators fire at import time, but the scan catches any function defined before its decorator ran (which can happen during hot-reload or unusual import orderings).

### Handler Modules

Each handler module is a self-contained unit covering one domain:

| Module | Methods | Domain |
|--------|---------|--------|
| `scene.py` | 10 | Document info, layers, objects, groups, blocks |
| `creation.py` | 12 | Primitive solids, curves, text, points |
| `operations.py` | 19 | Boolean ops, trim/split, offset, fillet, intersect, mesh, rebuild |
| `surfaces.py` | 12 | Loft, sweep1/2, revolve, extrude, patch, unroll, edge_surface |
| `manipulation.py` | 21 | Move, copy, rotate, scale, mirror, arrays, join, group, properties |
| `grasshopper.py` | 9 | Definition control, params, recompute, bake |
| `viewport.py` | 11 | Capture, camera, display mode, named views |
| `files.py` | 7 | Save, open, import, export |
| `scripting.py` | 4 | Python execution, RhinoScript, Rhino commands |

All handlers are Python 3.9 compatible (no `match`/`case`, no `X | Y` union syntax, no lowercase generic annotations at runtime) because they execute in Rhino's embedded interpreter.

### Grasshopper Sub-Server

Grasshopper integration uses a separate internal communication channel on port 9877. The `rhino_plugin/grasshopper/` package contains helpers for serializing Grasshopper components, getting and setting parameter values, and baking geometry. The Grasshopper handlers guard every call with `_GH_AVAILABLE` — if Grasshopper is not loaded in the current Rhino session, the handlers return a clear error rather than crashing.

---

## Connection Lifecycle

```
MCP Server starts
  └─ get_connection() called on first tool use
       └─ RhinoConnection.connect(host, port, timeout=10)
            └─ TCP SYN/ACK (127.0.0.1:9876)
            └─ send_command("ping", {})   ← verify server alive
            └─ returns or raises RhinoConnectionError

Per command:
  └─ send_command(method, params, timeout=30)
       └─ acquire threading.Lock
       └─ send_message(sock, request)     ← 4-byte header + JSON
       └─ recv_message(sock)              ← blocks up to timeout seconds
       └─ release lock
       └─ parse response: result or error

On BrokenPipe / ConnectionReset:
  └─ reconnect() up to 3 times
  └─ if all fail: raise RhinoConnectionError

Claude Code session ends:
  └─ MCP server process exits
  └─ TCP connection closed
  └─ Rhino plugin accept loop continues (ready for next session)
```

---

## Data Flow: A Single Tool Call

Using `create_box` as an example:

```
1. User: "Create a 10x20x30 box at the origin."
   Claude Code → calls MCP tool create_box(width=10, depth=20, height=30)

2. mcp_server/tools/creation.py:create_box()
   → get_connection().send_command("creation.create_box", {
       "corner_x": 0, "corner_y": 0, "corner_z": 0,
       "width": 10, "depth": 20, "height": 30
     })

3. mcp_server/connection.py:send_command()
   → assigns request_id = uuid4()
   → mcp_server/protocol.py:send_message(sock, {
       "id": "abc-123", "method": "creation.create_box", "params": {...}
     })
   → [4 bytes: payload length][JSON bytes] → TCP socket

4. rhino_plugin/server.py:handle_client()
   → rhino_plugin/protocol.py:recv_message(sock)
   → _dispatch("creation.create_box", params, "abc-123")
   → run_on_ui_thread(lambda: handler_func(params))

5. rhino_plugin/handlers/creation.py:create_box()
   → RhinoCommon: Rhino.Geometry.Box(...)
   → sc.doc.Objects.AddBrep(box_brep)
   → returns {"guid": "def-456", "bounding_box": {...}}

6. rhino_plugin/server.py
   → send_message(conn, {
       "id": "abc-123", "result": {"guid": "def-456", ...}, "error": null
     })

7. mcp_server/connection.py:_send_and_recv()
   → receives response, checks error is null
   → returns {"guid": "def-456", "bounding_box": {...}}

8. Claude Code receives the result dict.
   → "I created a box. Its GUID is def-456."
```

---

## Utility Modules

### `rhino_plugin/utils/geometry_serializer.py`

Converts RhinoCommon geometry objects to JSON-serialisable dicts. Functions include:

- `serialize_object(obj)` — general RhinoObject serialiser (type, GUID, name, layer, bounding box)
- `serialize_brep(brep)` — Brep details (face/edge/vertex counts, is_solid, volume, area)
- `serialize_curve(curve)` — Curve details (length, is_closed, domain, start/end points)
- `serialize_mesh(mesh)` — Mesh details (vertex/face counts, is_closed)
- `serialize_surface(srf)` — Surface details (domain, is_closed in U/V)
- `serialize_point3d(pt)` — `{"x": float, "y": float, "z": float}`
- `serialize_bounding_box(bbox)` — min/max corners
- `serialize_any(geom)` — dispatch to the appropriate serialiser by type

### `rhino_plugin/utils/guid_registry.py`

A `GuidRegistry` singleton that tracks GUIDs of objects created by GOLEM-3DMCP. `validate_guid(guid_str)` raises `KeyError` (containing "not found") if the GUID is not registered, which the dispatcher maps to `OBJECT_NOT_FOUND`. This provides fast existence checks without a Rhino document lookup.

### `rhino_plugin/utils/error_handler.py`

`wrap_handler` is a decorator that wraps handler functions in uniform exception handling. It maps:

- `ValueError` / `TypeError` / `KeyError` with "not found" → `INVALID_PARAMS` / `OBJECT_NOT_FOUND`
- `GolemError` → its own error code
- All other exceptions → `INTERNAL_ERROR` with traceback in `details`

`make_error(code, message)` builds an error result dict in the format the dispatcher expects.

### `rhino_plugin/utils/screenshot.py`

`capture_viewport_to_base64(view, width, height, format)` renders the specified Rhino view to a bitmap and encodes it as a base64 string for transmission over the JSON protocol.
