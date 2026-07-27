# NATIVE MCP

Direct plugin MCP implementation for Streamable HTTP/SSE at `/mcp`. This subtree owns protocol metadata, sessions, dynamic tool visibility, and translation into the bridge subsystem; it does not own editor action implementations.

## STRUCTURE
| Area | Responsibility |
|------|----------------|
| `DynamicTools/` | Enabled state, categories, protected tools, list-changed notification |
| `Protocol/` | JSON-RPC parse/build helpers and MCP tool-result envelopes |
| `Registry/` | Canonical-name gate, static definitions, cached schemas |
| `Routing/` | Consolidated parent-tool action routing helpers |
| `Tools/<Category>/` | Self-describing name, description, category, schema, dispatch metadata |
| `Transport/` | Bind/listen, HTTP parsing, sessions, SSE, pending requests, shutdown |

## CANONICAL SURFACE
`FMcpToolRegistry::Register()` accepts exactly these 23 names:

```text
manage_tools, manage_asset, manage_blueprint, control_actor, control_editor, manage_level
build_environment, animation_physics, system_control, manage_sequence, inspect
manage_audio, manage_geometry, manage_effect, manage_gas, manage_character, manage_combat
manage_ai, manage_inventory, manage_interaction, manage_networking, manage_level_structure, manage_pcg
```

- `MCP_REGISTER_TOOL` only attempts static registration. The source tree may contain more registrars; non-canonical names are silently filtered and duplicate names are ignored.
- Do not infer the exposed native surface from the number of `McpTool_*.cpp` files. `Registry/McpToolRegistry.cpp` is authoritative.
- Adding a registrar alone cannot expose a new parent tool. Update the canonical gate deliberately, keep TS/native parity, and justify context growth.
- `tools/list` filters accepted registry entries by dynamic enabled state; `tools/call` enforces the same state before dispatch.

## TOOL DEFINITIONS
- Tool definitions are metadata only. Build schemas with `McpSchemaBuilder`; do not hand-assemble repetitive schema JSON.
- Pattern A returns the parent tool name from `GetDispatchAction()` and lets the handler read the sub-action.
- Pattern B returns an empty dispatch action; transport extracts `GetActionFieldName()` from arguments and dispatches that value.
- Transport mirrors `action` into `subAction` for handlers that still require the older payload field. Do not spread additional alias normalization.
- Keep definition names, action enums, required fields, routing helpers, TS schemas, and handler payload expectations aligned.
- `manage_tools` is intercepted locally and returns a one-shot response; other tool calls queue through `UMcpAutomationBridgeSubsystem` and complete over SSE.

## DYNAMIC TOOLS
- Startup enables all accepted tools when `bLoadAllToolsOnStart` is true; otherwise it enables the `core` category.
- `manage_tools` and `inspect` are protected tools. The `core` category cannot be disabled.
- State changes must emit `notifications/tools/list_changed`; preserve locking around tool/category state and cached registry schemas.

## TRANSPORT LIFECYCLE
- `POST /mcp` handles JSON-RPC; `GET /mcp` opens the persistent notification SSE stream; `DELETE /mcp` terminates a session and its streams.
- `initialize` must carry an id and returns `Mcp-Session-Id`. All later requests and notification streams require a valid session header.
- Client notifications receive HTTP 202 after validation. `tools/call` owns its socket until the streamed result completes.
- Return JSON-RPC errors through `McpJsonRpc` and tool outcomes through MCP `content[]` plus `isError`; never leak raw handler JSON as the top-level response.
- Do not block socket threads on Unreal work. Shutdown intentionally pumps game-thread tasks while draining active connections and async writes.

## SECURITY
- Empty/`localhost` listen hosts normalize to loopback. A disallowed non-loopback host falls back to `127.0.0.1`.
- When capability auth is enabled, require `X-MCP-Capability-Token` before method dispatch.
- Browser Origin/CORS access is allowed only under capability-token protection; preserve origin rejection and preflight behavior.
- Keep request-size limits, session expiry, method/path checks, write serialization, and socket ownership accounting intact.

## VALIDATION
```bash
npm run test:native-parity
npm run test:params
```

- Parity verifies canonical TS/native parent tools; the strict parameter audit catches schema and action mismatches.
