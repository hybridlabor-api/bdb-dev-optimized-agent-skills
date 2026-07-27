import { getAdditionalPathPrefixes } from '../../../../config.js';
import type { HandlerArgs } from '../../../../types/handlers/handler-types.js';

function hasParentDirectorySegment(value: string): boolean {
  return value.replace(/\\/g, '/').split('/').some(segment => segment === '..');
}

export function ensureArgsPresent(args: unknown): asserts args is Record<string, unknown> {
  if (args === null || args === undefined) {
    throw new Error('Invalid arguments: null or undefined');
  }
}

export function validateSecurityPatterns(args: Record<string, unknown>): string | undefined {
  const blockedPathPatterns = [
    '/etc/',
    '\\Windows\\',
    '\\Program Files',
  ];

  for (const [key, value] of Object.entries(args)) {
    if (typeof value !== 'string') {
      continue;
    }

    const lowerValue = value.toLowerCase();
    if (hasParentDirectorySegment(value)) {
      return `Security violation: '${key}' contains blocked path pattern. Path traversal is not allowed.`;
    }

    for (const pattern of blockedPathPatterns) {
      if (value.includes(pattern) || lowerValue.includes(pattern.toLowerCase())) {
        return `Security violation: '${key}' contains blocked path pattern. Path traversal is not allowed.`;
      }
    }

    if (key.toLowerCase().includes('path') && value.startsWith('/')) {
      const additional = getAdditionalPathPrefixes();
      const action = typeof args.action === 'string' ? args.action.toLowerCase() : '';
      const normalizedKey = key.toLowerCase();
      const isSnapshotPath =
        (normalizedKey === 'path' || normalizedKey === 'outputpath') &&
        (action === 'export_snapshot' || action === 'import_snapshot');
      const allowedRoots = ['/game', '/engine', '/script', '/temp', '/niagara',
        ...(isSnapshotPath ? ['/saved'] : []),
        ...additional.map(prefix => prefix.replace(/\/$/, '').toLowerCase())];
      const isAllowed = allowedRoots.some(root =>
        lowerValue === root || lowerValue.startsWith(`${root}/`)
      );
      if (!isAllowed) {
        const savedNote = isSnapshotPath ? ', /Saved/' : '';
        return `Security violation: '${key}' uses unauthorized absolute path. Only /Game/, /Engine/, /Script/, /Temp/${savedNote}, /Niagara/ paths are allowed by default. Set MCP_ADDITIONAL_PATH_PREFIXES to whitelist custom plugin content mount points.`;
      }
    }
  }

  return undefined;
}

export function validateArgsSecurity(args: HandlerArgs): void {
  ensureArgsPresent(args);
  const securityError = validateSecurityPatterns(args);
  if (securityError) {
    throw new Error(securityError);
  }
}

export function requireAction(args: HandlerArgs): string {
  ensureArgsPresent(args);
  const action = args.action;
  if (typeof action !== 'string' || action.trim() === '') {
    throw new Error('Missing required parameter: action');
  }
  return action;
}

export function requireNonEmptyString(value: unknown, field: string, message?: string): string {
  if (typeof value !== 'string' || value.trim() === '') {
    throw new Error(message ?? `Invalid ${field}: must be a non-empty string`);
  }
  return value;
}

export function requireAssetName(value: unknown, field: string, message?: string): string {
  const strValue = requireNonEmptyString(value, field, message);

  if (strValue.includes('/') || strValue.includes('\\')) {
    throw new Error(message ?? `Invalid ${field}: '${strValue}' appears to be a path, not an asset name. Asset names should not contain '/' or '\\' characters. If you meant to specify a path, use the appropriate path parameter instead.`);
  }

  return strValue;
}

export function validateExpectedParams(
  args: Record<string, unknown>,
  allowedParams: string[],
  context: string = 'handler'
): void {
  const alwaysAllowed = ['action', 'subAction', 'timeoutMs'];
  const allAllowed = new Set([...alwaysAllowed, ...allowedParams]);
  const unknownParams = Object.keys(args).filter(key => !allAllowed.has(key));

  if (unknownParams.length > 0) {
    throw new Error(
      `Invalid parameters for ${context}: unknown parameters [${unknownParams.join(', ')}]. ` +
      `Allowed: [${allowedParams.join(', ')}]`
    );
  }
}

export function validateRequiredParams(
  args: Record<string, unknown>,
  requiredParams: string[],
  context: string = 'handler'
): void {
  const missingParams = requiredParams.filter(param => {
    const value = args[param];
    return value === undefined || value === null ||
           (typeof value === 'string' && value.trim() === '');
  });

  if (missingParams.length > 0) {
    throw new Error(
      `Missing required parameters for ${context}: [${missingParams.join(', ')}]`
    );
  }
}
