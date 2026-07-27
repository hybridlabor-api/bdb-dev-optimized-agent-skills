import { ResponseFactory } from '../../../utils/responses/response-factory.js';
import {
  extractOptionalNumber,
  extractOptionalString,
  extractString,
  normalizeArgs,
} from '../foundation/arguments/argument-helper.js';
import {
  completeMaterialAutomation,
  executeMaterialAutomation,
  promoteNodeId,
  type MaterialActionContext,
  validateCustomExpressionEntries,
} from './material-authoring-types.js';

export async function handleAddUtilityNode({ action, args, tools }: MaterialActionContext): Promise<Record<string, unknown>> {
  const params = normalizeArgs(args, [
    { key: 'assetPath', aliases: ['materialPath'], required: true },
    { key: 'x', default: 0 },
    { key: 'y', default: 0 },
  ]);

  const assetPath = extractString(params, 'assetPath');
  const x = extractOptionalNumber(params, 'x') ?? 0;
  const y = extractOptionalNumber(params, 'y') ?? 0;

  return completeMaterialAutomation(
    tools,
    { subAction: action, assetPath, x, y, ...args },
    `Failed to add ${action}`,
    `${action} node added`
  );
}

export async function handleAddConditionalNode({ action, args, tools }: MaterialActionContext): Promise<Record<string, unknown>> {
  const params = normalizeArgs(args, [
    { key: 'assetPath', aliases: ['materialPath'], required: true },
    { key: 'x', default: 0 },
    { key: 'y', default: 0 },
  ]);

  const assetPath = extractString(params, 'assetPath');
  const x = extractOptionalNumber(params, 'x') ?? 0;
  const y = extractOptionalNumber(params, 'y') ?? 0;

  return completeMaterialAutomation(
    tools,
    { subAction: action, assetPath, x, y },
    `Failed to add ${action}`,
    `${action} node added`
  );
}

export async function handleAddCustomExpression({ args, tools }: MaterialActionContext): Promise<Record<string, unknown>> {
  const params = normalizeArgs(args, [
    { key: 'assetPath', aliases: ['materialPath'], required: true },
    { key: 'code', aliases: ['hlsl'], required: true },
    { key: 'outputType', default: 'Float1' },
    { key: 'description' },
    { key: 'inputs' },
    { key: 'additionalOutputs' },
    { key: 'x', default: 0 },
    { key: 'y', default: 0 },
  ]);

  const assetPath = extractString(params, 'assetPath');
  const code = extractString(params, 'code');
  const outputType = extractOptionalString(params, 'outputType') ?? 'Float1';
  const description = extractOptionalString(params, 'description');
  const inputs = params.inputs;
  const additionalOutputs = params.additionalOutputs;
  const inputError = validateCustomExpressionEntries(inputs, 'inputs', 'add_custom_expression');
  if (inputError) return inputError;
  const outputError = validateCustomExpressionEntries(additionalOutputs, 'additionalOutputs', 'add_custom_expression');
  if (outputError) return outputError;

  const x = extractOptionalNumber(params, 'x') ?? 0;
  const y = extractOptionalNumber(params, 'y') ?? 0;
  const payload: Record<string, unknown> = {
    subAction: 'add_custom_expression',
    assetPath,
    code,
    outputType,
    description,
    x,
    y,
  };
  if (inputs != null) payload.inputs = inputs;
  if (additionalOutputs != null) payload.additionalOutputs = additionalOutputs;

  const res = await executeMaterialAutomation(tools, payload);
  if (res.success === false) {
    return ResponseFactory.error(res.error ?? 'Failed to add custom expression', res.errorCode);
  }
  const response = ResponseFactory.success(res, res.message ?? 'Custom HLSL expression added');
  promoteNodeId(response, res.result);
  return response;
}
