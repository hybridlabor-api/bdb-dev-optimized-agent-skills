# src/types

Shared TypeScript contracts for automation responses, handler arguments, environment configuration, and tool parameter/response mappings. Keep this layer compile-time focused; canonical MCP schemas and public tool names remain under `src/tools/definitions/`.

## STRUCTURE
```text
types/
|-- index.ts                         # intended cross-module export surface
|-- automation/automation-responses.ts
|-- config/env.ts                    # Env type plus the runtime loadEnv exception
|-- handlers/
|   |-- handler-types.ts             # handler argument barrel
|   `-- handler-*-types.ts           # domain-specific argument shapes
`-- tools/
    |-- tool-action-types.ts
    |-- tool-consolidated-params.ts
    |-- tool-parameter-types.ts
    |-- tool-response-types.ts
    `-- tool-response-map.ts
```

## WHERE TO LOOK
| Task | Location | Notes |
|------|----------|-------|
| Export a shared type | `index.ts` | Add only contracts intended for broad imports |
| Change bridge response shapes | `automation/automation-responses.ts` | Keep wire-facing fields compatible with response validation |
| Change handler arguments | `handlers/handler-*-types.ts`, `handlers/handler-types.ts` | Split by domain; update the barrel when broadly shared |
| Inspect legacy typed aliases | `tools/tool-consolidated-params.ts`, `tools/tool-parameter-types.ts` | Compatibility-only maps; current parent contracts live in `src/tools/definitions/` |
| Change typed tool responses | `tools/tool-response-types.ts`, `tools/tool-response-map.ts` | The map includes compatibility aliases; it is not the public MCP registry |
| Change environment loading | `config/env.ts` | Runtime parsing belongs here, not in declaration-only files |

## CONVENTIONS
- Use `import type` and `export type` where no runtime value is required.
- Preserve NodeNext `.js` import suffixes in TypeScript source.
- Prefer domain-specific interfaces over adding unrelated optional fields to a shared catch-all type.
- Keep `HandlerArgs` and tool parameter unions aligned with actual handler access patterns.
- Treat external response and argument data as untrusted until narrowed at runtime; types do not replace validation.
- Avoid circular imports between handler and tool contract files. Shared primitives belong in the lowest relevant type module.
- Legacy names in `ToolResponseMap` support internal callers; do not infer new public MCP tools from that map.

## VALIDATION
```bash
npm run type-check
npx vitest run --pool=threads --maxWorkers=1 tests/unit/source_structure.test.ts tests/unit/tools/handler_structure.test.ts
```

## ANTI-PATTERNS
- Adding runtime helpers outside `config/env.ts`.
- Duplicating canonical action enums or JSON schemas in type declarations.
- Exporting every local helper type through `index.ts`.
- Using broad `any` types to silence a contract mismatch.
