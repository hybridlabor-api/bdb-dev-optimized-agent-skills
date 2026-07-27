# src/server

MCP SDK construction, stdio lifecycle, and tool/resource registration. Keep protocol registration here; tool contracts and action implementations remain under `src/tools/`.

## STRUCTURE
```
server/
|-- server-factory.ts              # SDK server, bridges, metrics, output schemas
|-- stdio-lifecycle.ts             # transport startup and idempotent shutdown
|-- tool-registry.ts               # ListTools/CallTool orchestration
|-- tool-registry-client.ts        # client capability and default-category policy
|-- tool-registry-listing.ts       # filtered, sanitized public tool definitions
|-- tool-registry-manage-tools.ts  # local manage_tools action implementation
|-- tool-registry-elicitation.ts   # missing primitive argument prefill
`-- resource-registry.ts           # resource listing and handler registration
```

## WHERE TO LOOK
| Task | File | Notes |
|------|------|-------|
| Construct the server | `server-factory.ts` | Wire health, metrics, bridge events, schemas, capabilities |
| Change stdio cleanup | `stdio-lifecycle.ts` | Preserve signal, stdin, and process-exit cleanup paths |
| Change `tools/list` routing | `tool-registry.ts` | Coordinates client policy and sanitized listing |
| Change client compatibility | `tool-registry-client.ts` | `listChanged` support controls category filtering |
| Change `tools/list` sanitization | `tool-registry-listing.ts` | Preserve action enum, required fields, and schema flags from canonical definitions |
| Change `manage_tools` | `tool-registry-manage-tools.ts` | Local state only; protected tools stay enabled |
| Change argument elicitation | `tool-registry-elicitation.ts` | Only missing required primitive fields are elicited |
| Change MCP resources | `resource-registry.ts` | Resource handlers stay separate from tool calls |

## REQUEST FLOW
1. `tools/list`: detect client -> select effective categories -> query `dynamicToolManager` -> sanitize schemas.
2. `manage_tools`: execute locally -> emit `notifications/tools/list_changed` only for mutating actions.
3. Other calls: merge action params -> check enabled/connection -> elicit -> consolidated handler -> clean -> validate.
4. `system_control:get_project_settings` may fall back to project INI data without a live bridge.

## CONVENTIONS
- Keep `tool-registry.ts` as orchestration; put isolated listing, capability, control, or elicitation logic in its matching helper.
- Clients without reliable `listChanged` support receive the `all` category for compatibility.
- Keep `cleanObject()` before `responseValidator.wrapResponse()` and derive health success from the wrapped result.
- Preserve tool/action context, `isError`, health timing, and image-payload redaction on every response path.
- Register output schemas during server construction before serving calls.
- Stdio stdout is JSON-RPC-owned; lifecycle/logging changes must not emit ordinary runtime text there.

## VALIDATION
```bash
npm run type-check
npx vitest run tests/unit/server_shutdown_contracts.test.ts src/handlers/resource-handlers.test.ts
```

## ANTI-PATTERNS
- Recombining split helper logic into `tool-registry.ts`.
- Dispatching `manage_tools` to Unreal or bypassing `dynamicToolManager`.
- Returning raw catalog definitions instead of sanitized enabled definitions.
- Mixing resource registration into the tool call path.
