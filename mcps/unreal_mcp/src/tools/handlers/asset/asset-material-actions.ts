import { cleanObject } from '../../../utils/serialization/safe-json.js';
import { ResponseFactory } from '../../../utils/responses/response-factory.js';
import { executeAutomationRequest, promoteScalarResultFields } from '../foundation/dispatch/common-handlers.js';
import { extractOptionalBoolean, extractOptionalNumber, extractOptionalString, extractString, normalizeArgs } from '../foundation/arguments/argument-helper.js';
import type { AssetHandlerContext, AssetOperationResponse } from './asset-handler-types.js';
import { automationFailureResponse, failedOperationResponse, findAutomationFailure, isRecord } from './asset-responses.js';

const MATERIAL_NODE_ALIASES: Record<string, string> = {
  Multiply: 'MaterialExpressionMultiply',
  Add: 'MaterialExpressionAdd',
  Subtract: 'MaterialExpressionSubtract',
  Divide: 'MaterialExpressionDivide',
  Power: 'MaterialExpressionPower',
  Clamp: 'MaterialExpressionClamp',
  Constant: 'MaterialExpressionConstant',
  Constant2Vector: 'MaterialExpressionConstant2Vector',
  Constant3Vector: 'MaterialExpressionConstant3Vector',
  Constant4Vector: 'MaterialExpressionConstant4Vector',
  TextureSample: 'MaterialExpressionTextureSample',
  TextureCoordinate: 'MaterialExpressionTextureCoordinate',
  Panner: 'MaterialExpressionPanner',
  Rotator: 'MaterialExpressionRotator',
  Lerp: 'MaterialExpressionLinearInterpolate',
  LinearInterpolate: 'MaterialExpressionLinearInterpolate',
  Sine: 'MaterialExpressionSine',
  Cosine: 'MaterialExpressionCosine',
  Append: 'MaterialExpressionAppendVector',
  AppendVector: 'MaterialExpressionAppendVector',
  ComponentMask: 'MaterialExpressionComponentMask',
  Fresnel: 'MaterialExpressionFresnel',
  Time: 'MaterialExpressionTime',
  ScalarParameter: 'MaterialExpressionScalarParameter',
  VectorParameter: 'MaterialExpressionVectorParameter',
  StaticSwitchParameter: 'MaterialExpressionStaticSwitchParameter'
};

export async function handleMaterialAssetAction(action: string, context: AssetHandlerContext): Promise<Record<string, unknown> | undefined> {
  switch (action) {
    case 'create_material_instance':
      return handleCreateMaterialInstance(context);
    case 'create_render_target':
      return handleCreateRenderTarget(context);
    case 'nanite_rebuild_mesh':
    case 'add_material_parameter':
    case 'list_instances':
    case 'reset_instance_parameters':
    case 'get_material_stats':
      return handleSimpleMaterialAction(action, context);
    case 'add_material_node':
    case 'connect_material_pins':
    case 'remove_material_node':
    case 'break_material_connections':
    case 'get_material_node_details':
    case 'rebuild_material':
      return handleMaterialGraphAction(action, context);
    default:
      return undefined;
  }
}

async function handleCreateMaterialInstance(context: AssetHandlerContext): Promise<Record<string, unknown>> {
  const params = normalizeArgs(context.args, [
    { key: 'name', required: true },
    { key: 'parentMaterial', required: true },
    { key: 'savePath', aliases: ['path'] }
  ]);
  const name = extractString(params, 'name');
  const parentMaterial = extractString(params, 'parentMaterial');
  const savePath = extractOptionalString(params, 'savePath');
  const res = await executeAutomationRequest(
    context.tools,
    'create_material_instance',
    { ...context.args, name, parentMaterial, savePath },
    'Automation bridge not available for create_material_instance'
  ) as AssetOperationResponse;
  const errorCode = typeof res.error === 'string' ? res.error.toUpperCase() : '';
  const message = typeof res.message === 'string' ? res.message : '';
  if (errorCode === 'PARENT_NOT_FOUND' || message.toLowerCase().includes('parent material not found')) {
    return cleanObject({
      success: false,
      error: 'PARENT_NOT_FOUND',
      message: message || 'Parent material not found',
      path: (res as Record<string, unknown>).path,
      parentMaterial: context.assetArgs.parentMaterial
    });
  }
  return ResponseFactory.success(res, 'Material instance created successfully');
}

async function handleCreateRenderTarget(context: AssetHandlerContext): Promise<Record<string, unknown>> {
  const params = normalizeArgs(context.args, [
    { key: 'name', required: true },
    { key: 'packagePath', aliases: ['path'], default: '/Game' },
    { key: 'width' }, { key: 'height' }, { key: 'format' }, { key: 'save', default: true }
  ]);
  const name = extractString(params, 'name');
  const packagePath = extractOptionalString(params, 'packagePath') ?? '/Game';
  const rawResponse = await executeAutomationRequest(context.tools, 'manage_texture', {
    subAction: 'create_render_target',
    name,
    path: packagePath,
    width: extractOptionalNumber(params, 'width'),
    height: extractOptionalNumber(params, 'height'),
    format: extractOptionalString(params, 'format'),
    save: extractOptionalBoolean(params, 'save') ?? true
  });
  const res = rawResponse && typeof rawResponse === 'object' && !Array.isArray(rawResponse)
    ? promoteScalarResultFields(rawResponse as Record<string, unknown>)
    : rawResponse;
  const failure = findAutomationFailure(res);
  if (failure && isRecord(res)) {
    return automationFailureResponse(res, failure, 'Failed to create render target', { name, packagePath });
  }
  return ResponseFactory.success(res, 'Render target created successfully');
}

async function handleSimpleMaterialAction(action: string, context: AssetHandlerContext): Promise<Record<string, unknown>> {
  const params = normalizeArgs(context.args, [
    { key: 'assetPath', aliases: ['meshPath'], required: true },
    { key: 'parameterName', aliases: ['name'] },
    { key: 'parameterType', aliases: ['type'] },
    { key: 'value', aliases: ['defaultValue'] }
  ]);
  const assetPath = extractString(params, 'assetPath');
  const requestMap: Record<string, string> = {
    nanite_rebuild_mesh: 'manage_render',
    add_material_parameter: 'add_material_parameter',
    list_instances: 'list_instances',
    reset_instance_parameters: 'reset_instance_parameters',
    get_material_stats: 'get_material_stats'
  };
  const payload: Record<string, unknown> = action === 'nanite_rebuild_mesh'
    ? { subAction: 'nanite_rebuild_mesh', assetPath }
    : { assetPath };
  if (action === 'add_material_parameter') {
    payload.name = extractString(params, 'parameterName');
    payload.type = extractOptionalString(params, 'parameterType');
    payload.value = params.value;
  }
  const messages: Record<string, string> = {
    nanite_rebuild_mesh: 'Nanite mesh rebuilt successfully',
    add_material_parameter: 'Material parameter added successfully',
    list_instances: 'Instances listed successfully',
    reset_instance_parameters: 'Instance parameters reset successfully',
    get_material_stats: 'Material stats retrieved'
  };
  return ResponseFactory.success(await executeAutomationRequest(context.tools, requestMap[action], payload), messages[action]);
}

async function handleMaterialGraphAction(action: string, context: AssetHandlerContext): Promise<Record<string, unknown>> {
  if (action === 'rebuild_material') {
    const assetPath = extractString(normalizeArgs(context.args, [{ key: 'assetPath', aliases: ['materialPath'], required: true }]), 'assetPath');
    const res = await executeAutomationRequest(context.tools, 'rebuild_material', { assetPath }) as AssetOperationResponse;
    return res.success === false
      ? failedOperationResponse(res, 'REBUILD_FAILED', 'Material rebuild failed', { assetPath })
      : ResponseFactory.success(res, 'Material rebuilt successfully');
  }

  const params = normalizeArgs(context.args, [
    { key: 'assetPath', aliases: ['materialPath'], required: true },
    { key: 'nodeType', aliases: ['type'], map: MATERIAL_NODE_ALIASES },
    { key: 'nodeId' }, { key: 'expressionIndex' }, { key: 'posX' }, { key: 'posY' },
    { key: 'sourceNodeId', aliases: ['sourceNode'] }, { key: 'sourcePin', aliases: ['fromPin', 'outputPin'] },
    { key: 'targetNodeId', aliases: ['targetNode'] }, { key: 'targetPin', aliases: ['toPin', 'inputPin'] },
    { key: 'pinName' }
  ]);
  const assetPath = extractString(params, 'assetPath');
  const payload: Record<string, unknown> = { assetPath };
  const requestAction = action;
  if (action === 'add_material_node') Object.assign(payload, { nodeType: extractString(params, 'nodeType'), posX: extractOptionalNumber(params, 'posX'), posY: extractOptionalNumber(params, 'posY') });
  if (action === 'connect_material_pins') Object.assign(payload, { sourceNodeId: extractString(params, 'sourceNodeId'), sourcePin: extractString(params, 'sourcePin'), targetNodeId: extractString(params, 'targetNodeId'), targetPin: extractString(params, 'targetPin') });
  if (action === 'remove_material_node') payload.nodeId = extractString(params, 'nodeId');
  if (action === 'break_material_connections') Object.assign(payload, { nodeId: extractOptionalString(params, 'nodeId'), pinName: extractOptionalString(params, 'pinName') });
  if (action === 'get_material_node_details') Object.assign(payload, { nodeId: extractOptionalString(params, 'nodeId'), expressionIndex: extractOptionalNumber(params, 'expressionIndex') });

  const messages: Record<string, string> = {
    add_material_node: 'Material node added successfully',
    connect_material_pins: 'Material pins connected successfully',
    remove_material_node: 'Material node removed successfully',
    break_material_connections: 'Material connections broken successfully',
    get_material_node_details: 'Material node details retrieved'
  };
  return ResponseFactory.success(await executeAutomationRequest(context.tools, requestAction, payload), messages[action]);
}
