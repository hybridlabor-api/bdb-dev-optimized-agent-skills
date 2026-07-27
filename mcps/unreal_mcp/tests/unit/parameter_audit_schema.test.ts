/// <reference types="node" />

import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import { afterEach, describe, expect, it } from 'vitest';

import { allToolDefinitions } from '../../src/tools/definitions/shared/all-tool-definitions.js';

const temporaryDirectories: string[] = [];

function writeFiles(root: string, files: ReadonlyMap<string, string>): void {
  for (const [relativePath, source] of files) {
    const filePath = path.join(root, relativePath);
    fs.mkdirSync(path.dirname(filePath), { recursive: true });
    fs.writeFileSync(filePath, source);
  }
}

function createDefinitionsFixture(): string {
  const root = fs.mkdtempSync(path.join(os.tmpdir(), 'parameter-audit-schema-'));
  temporaryDirectories.push(root);

  const files = new Map<string, string>([
    ['shared/actions.ts', "export const SHARED_ACTIONS = ['shared_action'] as const;\n"],
    [
      'first/properties.ts',
      [
        'export const commonProperties = {',
        "  action: { type: 'string', enum: ['first_action'] },",
        "  firstOnly: { type: 'string' }",
        '};',
        ''
      ].join('\n')
    ],
    [
      'first/schema.ts',
      [
        "import { commonProperties as importedProperties } from './properties.js';",
        'export const inputSchema = {',
        "  type: 'object',",
        '  properties: { ...importedProperties },',
        "  required: ['action', 'firstOnly']",
        '};',
        ''
      ].join('\n')
    ],
    [
      'first/first-tool.ts',
      [
        "import { inputSchema as aliasedSchema } from './schema.js';",
        'export const firstToolDefinition = {',
        "  name: 'first_tool',",
        '  inputSchema: aliasedSchema',
        '};',
        ''
      ].join('\n')
    ],
    [
      'second/properties.ts',
      [
        "import { SHARED_ACTIONS as aliasedActions } from '../shared/actions.js';",
        'export const commonProperties = {',
        "  action: { type: 'string', enum: [...aliasedActions, 'second_action'] },",
        "  secondOnly: { type: 'number' }",
        '};',
        ''
      ].join('\n')
    ],
    [
      'second/schema.ts',
      [
        "import { commonProperties as importedProperties } from './properties.js';",
        'export const inputSchema = {',
        "  type: 'object',",
        '  properties: { ...importedProperties },',
        "  required: ['action']",
        '};',
        ''
      ].join('\n')
    ],
    [
      'second/second-tool.ts',
      [
        "import { inputSchema as aliasedSchema } from './schema.js';",
        'export const secondToolDefinition = {',
        "  name: 'second_tool',",
        '  inputSchema: aliasedSchema',
        '};',
        ''
      ].join('\n')
    ]
  ]);

  writeFiles(root, files);

  return root;
}

function createActionOverrideFixture(): string {
  const root = fs.mkdtempSync(path.join(os.tmpdir(), 'parameter-audit-action-override-'));
  temporaryDirectories.push(root);

  const files = new Map<string, string>([
    [
      'shared/base-properties.ts',
      [
        'export const baseProperties = {',
        "  action: { type: 'string', enum: ['spread_action'] },",
        "  sharedOnly: { type: 'boolean' }",
        '};',
        ''
      ].join('\n')
    ],
    [
      'shared/enumless-properties.ts',
      [
        'export const enumlessProperties = {',
        "  action: { type: 'string', description: 'Replacement without enum' }",
        '};',
        ''
      ].join('\n')
    ],
    [
      'without-enum/without-enum-tool.ts',
      [
        "import { baseProperties } from '../shared/base-properties.js';",
        'export const withoutEnumToolDefinition = {',
        "  name: 'without_enum',",
        '  inputSchema: {',
        '    properties: {',
        '      ...baseProperties,',
        "      action: { type: 'string', description: 'Replacement without enum' }",
        '    },',
        "    required: ['action']",
        '  }',
        '};',
        ''
      ].join('\n')
    ],
    [
      'nested-spread/nested-spread-tool.ts',
      [
        "import { baseProperties } from '../shared/base-properties.js';",
        "import { enumlessProperties } from '../shared/enumless-properties.js';",
        'export const nestedSpreadToolDefinition = {',
        "  name: 'nested_spread',",
        '  inputSchema: {',
        '    properties: {',
        '      ...baseProperties,',
        '      ...enumlessProperties',
        '    },',
        "    required: ['action']",
        '  }',
        '};',
        ''
      ].join('\n')
    ],
    [
      'with-enum/with-enum-tool.ts',
      [
        "import { baseProperties } from '../shared/base-properties.js';",
        'export const withEnumToolDefinition = {',
        "  name: 'with_enum',",
        '  inputSchema: {',
        '    properties: {',
        '      ...baseProperties,',
        "      action: { type: 'string', enum: ['replacement_action'] }",
        '    },',
        "    required: ['action']",
        '  }',
        '};',
        ''
      ].join('\n')
    ]
  ]);

  writeFiles(root, files);

  return root;
}

function stringArray(value: unknown): string[] {
  if (!Array.isArray(value) || !value.every((entry) => typeof entry === 'string')) {
    return [];
  }
  return [...value].sort();
}

function canonicalSchema(tool: (typeof allToolDefinitions)[number]) {
  const properties = tool.inputSchema['properties'];
  const propertyRecord =
    properties && typeof properties === 'object' && !Array.isArray(properties)
      ? properties as Record<string, unknown>
      : {};
  const action = propertyRecord['action'];
  const actionRecord =
    action && typeof action === 'object' && !Array.isArray(action)
      ? action as Record<string, unknown>
      : {};

  return {
    name: tool.name,
    actions: stringArray(actionRecord['enum']),
    properties: Object.keys(propertyRecord).sort(),
    required: stringArray(tool.inputSchema['required'])
  };
}

afterEach(() => {
  for (const directory of temporaryDirectories.splice(0)) {
    fs.rmSync(directory, { recursive: true, force: true });
  }
});

describe('parameter audit schema discovery', () => {
  it('matches every canonical tool schema exactly', async () => {
    const { extractToolSchemas } = await import('../parameter-audit-schema.mjs');
    const schemas = extractToolSchemas();

    expect(schemas).toEqual(
      allToolDefinitions
        .map(canonicalSchema)
        .sort((left, right) => left.name.localeCompare(right.name))
    );
  });

  it('resolves import aliases without conflating same-named helpers in nested modules', async () => {
    const { extractToolSchemas } = await import('../parameter-audit-schema.mjs');
    const definitionsRoot = createDefinitionsFixture();

    expect(extractToolSchemas({ definitionsRoot })).toEqual([
      {
        name: 'first_tool',
        actions: ['first_action'],
        properties: ['action', 'firstOnly'],
        required: ['action', 'firstOnly']
      },
      {
        name: 'second_tool',
        actions: ['second_action', 'shared_action'],
        properties: ['action', 'secondOnly'],
        required: ['action']
      }
    ]);
  });

  it('applies explicit action overrides after spread-provided enums', async () => {
    const { extractToolSchemas } = await import('../parameter-audit-schema.mjs');
    const definitionsRoot = createActionOverrideFixture();

    expect(extractToolSchemas({ definitionsRoot })).toEqual([
      {
        name: 'nested_spread',
        actions: [],
        properties: ['action', 'sharedOnly'],
        required: ['action']
      },
      {
        name: 'with_enum',
        actions: ['replacement_action'],
        properties: ['action', 'sharedOnly'],
        required: ['action']
      },
      {
        name: 'without_enum',
        actions: [],
        properties: ['action', 'sharedOnly'],
        required: ['action']
      }
    ]);
  });
});
