import { cleanObject } from '../../../utils/serialization/safe-json.js';
import { executeAutomationRequest } from '../foundation/dispatch/common-handlers.js';
import { resolveObjectPath } from '../foundation/arguments/argument-helper.js';
import type { InspectHandlerContext, InspectResponse } from './inspect-actions.js';
import { resolveComponentObjectPathFromArgs } from './inspect-components.js';

function isNotFoundResponse(res: InspectResponse, errorNames: readonly string[], messageNeedle: string): boolean {
  const errorCode = String(res.error || '').toUpperCase();
  const message = String(res.message || '').toLowerCase();
  return errorNames.includes(errorCode) || message.includes(messageNeedle);
}

function looksLikeComponentPath(value: string | undefined): boolean {
  if (value === undefined) {
    return false;
  }
  return !value.includes('/') &&
    !value.includes('\\') &&
    value.includes('.') &&
    value.split('.').length === 2 &&
    value.split('.')[0].length > 0 &&
    value.split('.')[1].length > 0;
}

async function handleBlueprintDetails(context: InspectHandlerContext): Promise<Record<string, unknown>> {
  // Accept `blueprintPath` in addition to `objectPath`/`path`. Sibling inspect
  // actions (inspect_cdo, get_property/set_property) already take `blueprintPath`,
  // so callers reasonably pass it here too; without this it was rejected.
  const requestedPath = await resolveObjectPath(context.normalizedArgs, context.tools, {
    pathKeys: ['objectPath', 'blueprintPath', 'path']
  }) ?? '';
  if (!requestedPath) {
    throw new Error('inspect:get_blueprint_details - invalid objectPath/blueprintPath: must be a non-empty string');
  }

  const res = await executeAutomationRequest(
    context.tools,
    'blueprint_get',
    { requestedPath, blueprintCandidates: [requestedPath] },
    'inspect:get_blueprint_details -> blueprint_get: automation bridge not available'
  ) as InspectResponse;

  if (res.success === false && isNotFoundResponse(res, ['OBJECT_NOT_FOUND', 'BLUEPRINT_NOT_FOUND', 'CDO_NOT_FOUND', 'NOT_FOUND'], 'not found')) {
    return cleanObject({
      success: false,
      handled: true,
      notFound: true,
      error: res.error,
      message: res.message || 'Blueprint not found',
      requestedPath
    });
  }

  return cleanObject(res);
}

export async function handleInspectObject(context: InspectHandlerContext): Promise<Record<string, unknown>> {
  if (context.originalAction === 'get_blueprint_details') {
    return handleBlueprintDetails(context);
  }

  const rawObjectPath = typeof context.normalizedArgs.objectPath === 'string'
    ? context.normalizedArgs.objectPath
    : undefined;
  const hasComponentName = typeof context.normalizedArgs.componentName === 'string' &&
    context.normalizedArgs.componentName.trim().length > 0;
  const objectPath = hasComponentName || looksLikeComponentPath(rawObjectPath)
    ? await resolveComponentObjectPathFromArgs(context.normalizedArgs, context.tools)
    : await resolveObjectPath(context.normalizedArgs, context.tools) ?? '';

  if (!objectPath) {
    throw new Error('Invalid objectPath: must be a non-empty string');
  }

  const res = await executeAutomationRequest(
    context.tools,
    'inspect',
    {
      ...context.args,
      objectPath,
      action: 'inspect_object',
      detailed: true
    },
    'Automation bridge not available for inspect operations'
  ) as InspectResponse;

  if (res.success === false && isNotFoundResponse(res, ['OBJECT_NOT_FOUND'], 'object not found')) {
    return cleanObject({
      success: false,
      handled: true,
      notFound: true,
      error: res.error,
      message: res.message || 'Object not found'
    });
  }

  return cleanObject(res);
}
