import { normalizePathFields } from '../foundation/dispatch/common-handlers.js';
import { sanitizePath } from '../../../utils/paths/path-security.js';

export function parseMaterialPath(fullPath: string | undefined): { name: string; path: string } | null {
  if (fullPath === undefined) return null;
  const lastSlash = fullPath.lastIndexOf('/');
  if (lastSlash < 0) return { name: fullPath, path: '/Game' };
  const name = fullPath.substring(lastSlash + 1);
  const path = fullPath.substring(0, lastSlash);
  return { name, path };
}

export function normalizeAssetPath(path: string): string {
  const normalized = normalizePathFields({ path }, ['path']).path as string;
  return sanitizePath(normalized);
}
