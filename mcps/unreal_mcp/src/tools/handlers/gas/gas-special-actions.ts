import { cleanObject } from '../../../utils/serialization/safe-json.js';
import { normalizeAndSanitizeAssetPath, sanitizeAssetName } from '../../../utils/validation/validation.js';
import type { GASActionContext } from './gas-action-context.js';

export async function handleCreateGameplayEffect(context: GASActionContext): Promise<Record<string, unknown>> {
  const requestedName = stringValue(context.argsRecord.name);
  const requestedPath = stringValue(context.argsRecord.path)?.trim() || '/Game';

  return await context.sendSubAction('create_gameplay_effect', {
    name: sanitizeAssetName(requestedName),
    path: normalizeAndSanitizeAssetPath(requestedPath)
  });
}

export async function handleAddTagToAsset(context: GASActionContext): Promise<Record<string, unknown>> {
  const tagValue = stringValue(context.argsRecord.tagName) || stringValue(context.argsRecord.tag);
  if (!tagValue) {
    return cleanObject({
      success: false,
      error: 'INVALID_ARGUMENT',
      message: 'Missing required parameter: tagName or tag'
    });
  }

  return await context.sendSubAction('add_tag_to_asset', { tag: tagValue });
}

function stringValue(value: unknown): string {
  return typeof value === 'string' ? value : '';
}
