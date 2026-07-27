import {
  extractOptionalBoolean,
  extractOptionalNumber,
  extractOptionalObject,
  extractOptionalString,
  extractString,
  normalizeArgs,
} from '../foundation/arguments/argument-helper.js';
import { completeMaterialAutomation, type MaterialActionContext } from './material-authoring-types.js';

export async function handleAddTextureSample({ args, tools }: MaterialActionContext): Promise<Record<string, unknown>> {
  const params = normalizeArgs(args, [
    { key: 'assetPath', aliases: ['materialPath'], required: true },
    { key: 'texturePath', required: true },
    { key: 'parameterName', aliases: ['name'] },
    { key: 'x', default: 0 },
    { key: 'y', default: 0 },
    { key: 'samplerType', default: 'Color' },
  ]);

  const assetPath = extractString(params, 'assetPath');
  const texturePath = extractString(params, 'texturePath');
  const parameterName = extractOptionalString(params, 'parameterName');
  const x = extractOptionalNumber(params, 'x') ?? 0;
  const y = extractOptionalNumber(params, 'y') ?? 0;
  const samplerType = extractOptionalString(params, 'samplerType') ?? 'Color';

  return completeMaterialAutomation(
    tools,
    { subAction: 'add_texture_sample', assetPath, texturePath, parameterName, x, y, samplerType },
    'Failed to add texture sample',
    'Texture sample added'
  );
}

export async function handleAddTextureCoordinate({ args, tools }: MaterialActionContext): Promise<Record<string, unknown>> {
  const params = normalizeArgs(args, [
    { key: 'assetPath', aliases: ['materialPath'], required: true },
    { key: 'coordinateIndex', default: 0 },
    { key: 'uTiling', default: 1.0 },
    { key: 'vTiling', default: 1.0 },
    { key: 'x', default: 0 },
    { key: 'y', default: 0 },
  ]);

  const assetPath = extractString(params, 'assetPath');
  const coordinateIndex = extractOptionalNumber(params, 'coordinateIndex') ?? 0;
  const uTiling = extractOptionalNumber(params, 'uTiling') ?? 1.0;
  const vTiling = extractOptionalNumber(params, 'vTiling') ?? 1.0;
  const x = extractOptionalNumber(params, 'x') ?? 0;
  const y = extractOptionalNumber(params, 'y') ?? 0;

  return completeMaterialAutomation(
    tools,
    { subAction: 'add_texture_coordinate', assetPath, coordinateIndex, uTiling, vTiling, x, y },
    'Failed to add texture coordinate',
    'Texture coordinate added'
  );
}

export async function handleAddScalarParameter({ args, tools }: MaterialActionContext): Promise<Record<string, unknown>> {
  const params = normalizeArgs(args, [
    { key: 'assetPath', aliases: ['materialPath'], required: true },
    { key: 'parameterName', aliases: ['name'], required: true },
    { key: 'defaultValue', default: 0.0 },
    { key: 'group', default: 'None' },
    { key: 'x', default: 0 },
    { key: 'y', default: 0 },
  ]);

  const assetPath = extractString(params, 'assetPath');
  const parameterName = extractString(params, 'parameterName');
  const defaultValue = extractOptionalNumber(params, 'defaultValue') ?? 0.0;
  const group = extractOptionalString(params, 'group') ?? 'None';
  const x = extractOptionalNumber(params, 'x') ?? 0;
  const y = extractOptionalNumber(params, 'y') ?? 0;

  return completeMaterialAutomation(
    tools,
    { subAction: 'add_scalar_parameter', assetPath, parameterName, defaultValue, group, x, y },
    'Failed to add scalar parameter',
    `Scalar parameter '${parameterName}' added`
  );
}

export async function handleAddVectorParameter({ args, tools }: MaterialActionContext): Promise<Record<string, unknown>> {
  const params = normalizeArgs(args, [
    { key: 'assetPath', aliases: ['materialPath'], required: true },
    { key: 'parameterName', aliases: ['name'], required: true },
    { key: 'defaultValue', aliases: ['color'] },
    { key: 'group', default: 'None' },
    { key: 'x', default: 0 },
    { key: 'y', default: 0 },
  ]);

  const assetPath = extractString(params, 'assetPath');
  const parameterName = extractString(params, 'parameterName');
  const defaultValue = extractOptionalObject(params, 'defaultValue') ?? { r: 1, g: 1, b: 1, a: 1 };
  const group = extractOptionalString(params, 'group') ?? 'None';
  const x = extractOptionalNumber(params, 'x') ?? 0;
  const y = extractOptionalNumber(params, 'y') ?? 0;

  return completeMaterialAutomation(
    tools,
    { subAction: 'add_vector_parameter', assetPath, parameterName, defaultValue, group, x, y },
    'Failed to add vector parameter',
    `Vector parameter '${parameterName}' added`
  );
}

export async function handleAddStaticSwitchParameter({ args, tools }: MaterialActionContext): Promise<Record<string, unknown>> {
  const params = normalizeArgs(args, [
    { key: 'assetPath', aliases: ['materialPath'], required: true },
    { key: 'parameterName', aliases: ['name'], required: true },
    { key: 'defaultValue', default: false },
    { key: 'group', default: 'None' },
    { key: 'x', default: 0 },
    { key: 'y', default: 0 },
  ]);

  const assetPath = extractString(params, 'assetPath');
  const parameterName = extractString(params, 'parameterName');
  const defaultValue = extractOptionalBoolean(params, 'defaultValue') ?? false;
  const group = extractOptionalString(params, 'group') ?? 'None';
  const x = extractOptionalNumber(params, 'x') ?? 0;
  const y = extractOptionalNumber(params, 'y') ?? 0;

  return completeMaterialAutomation(
    tools,
    { subAction: 'add_static_switch_parameter', assetPath, parameterName, defaultValue, group, x, y },
    'Failed to add static switch',
    `Static switch '${parameterName}' added`
  );
}

export async function handleAddMathNode({ args, tools }: MaterialActionContext): Promise<Record<string, unknown>> {
  const params = normalizeArgs(args, [
    { key: 'assetPath', aliases: ['materialPath'], required: true },
    { key: 'operation', required: true },
    { key: 'x', default: 0 },
    { key: 'y', default: 0 },
    { key: 'constA', aliases: ['valueA'] },
    { key: 'constB', aliases: ['valueB'] },
  ]);

  const assetPath = extractString(params, 'assetPath');
  const operation = extractString(params, 'operation');
  const x = extractOptionalNumber(params, 'x') ?? 0;
  const y = extractOptionalNumber(params, 'y') ?? 0;
  const constA = extractOptionalNumber(params, 'constA');
  const constB = extractOptionalNumber(params, 'constB');

  return completeMaterialAutomation(
    tools,
    { subAction: 'add_math_node', assetPath, operation, x, y, constA, constB },
    'Failed to add math node',
    `Math node '${operation}' added`
  );
}
