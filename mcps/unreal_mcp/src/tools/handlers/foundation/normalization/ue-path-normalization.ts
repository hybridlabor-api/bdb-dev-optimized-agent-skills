import { getAdditionalPathPrefixes } from '../../../../config.js';

export function normalizePathFields(
  args: Record<string, unknown>,
  pathFields: readonly string[]
): Record<string, unknown> {
  const result = { ...args };
  const rootAliases = [
    'Game',
    'Engine',
    'Script',
    'Temp',
    'Niagara',
    ...getAdditionalPathPrefixes().map(prefix => prefix.replace(/^\//, '').replace(/\/$/, ''))
  ];

  for (const field of pathFields) {
    const value = result[field];
    if (typeof value !== 'string' || value.length === 0) {
      continue;
    }

    let normalized = value.replace(/\\/g, '/');
    if (normalized.startsWith('/Content/')) {
      normalized = '/Game/' + normalized.slice('/Content/'.length);
    } else if (normalized.startsWith('Content/')) {
      normalized = '/Game/' + normalized.slice('Content/'.length);
    } else if (rootAliases.some(root => normalized.startsWith(`${root}/`))) {
      normalized = '/' + normalized;
    }
    if (!normalized.startsWith('/')) {
      normalized = '/Game/' + normalized;
    }
    result[field] = normalized;
  }

  return result;
}
