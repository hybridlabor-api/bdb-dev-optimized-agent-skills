import {
  extractOptionalArray,
  extractOptionalBoolean,
  extractOptionalNumber,
  extractOptionalString,
  extractString
} from '../foundation/arguments/argument-helper.js';
import {
  runTextureAction,
  type TextureActionConfig,
  type TextureHandlerContext
} from './texture-handler-types.js';

export async function handleTextureProcessingAction(
  action: string,
  context: TextureHandlerContext
): Promise<Record<string, unknown> | undefined> {
  switch (action) {
    case 'resize_texture':
      return await runTextureAction(context, resizeTextureConfig);
    case 'adjust_levels':
      return await runTextureAction(context, adjustLevelsConfig);
    case 'adjust_curves':
      return await runTextureAction(context, adjustCurvesConfig);
    case 'blur':
      return await runTextureAction(context, blurTextureConfig);
    case 'sharpen':
      return await runTextureAction(context, sharpenTextureConfig);
    case 'invert':
      return await runTextureAction(context, invertTextureConfig);
    case 'desaturate':
      return await runTextureAction(context, desaturateTextureConfig);
    default:
      return undefined;
  }
}

const resizeTextureConfig: TextureActionConfig = {
  subAction: 'resize_texture',
  params: [
    { key: 'sourcePath', aliases: ['assetPath', 'texturePath'], required: true },
    { key: 'name' },
    { key: 'path' },
    { key: 'newWidth', required: true },
    { key: 'newHeight', required: true },
    { key: 'filterMethod', default: 'Bilinear' },
    { key: 'save', default: true }
  ],
  failureMessage: 'Failed to resize texture',
  build: params => {
    const newWidth = extractOptionalNumber(params, 'newWidth') ?? 512;
    const newHeight = extractOptionalNumber(params, 'newHeight') ?? 512;
    return {
      payload: {
        sourcePath: extractString(params, 'sourcePath'),
        name: extractOptionalString(params, 'name'),
        path: extractOptionalString(params, 'path'),
        newWidth,
        newHeight,
        filterMethod: extractOptionalString(params, 'filterMethod') ?? 'Bilinear',
        save: extractOptionalBoolean(params, 'save') ?? true
      },
      successMessage: `Texture resized to ${newWidth}x${newHeight}`
    };
  }
};

const adjustLevelsConfig: TextureActionConfig = {
  subAction: 'adjust_levels',
  params: [
    { key: 'assetPath', aliases: ['texturePath'], required: true },
    { key: 'inBlack', aliases: ['inputBlackPoint'], default: 0.0 },
    { key: 'inWhite', aliases: ['inputWhitePoint'], default: 1.0 },
    { key: 'gamma', default: 1.0 },
    { key: 'outBlack', aliases: ['outputBlackPoint'], default: 0.0 },
    { key: 'outWhite', aliases: ['outputWhitePoint'], default: 1.0 },
    { key: 'inPlace', default: true },
    { key: 'save', default: true }
  ],
  failureMessage: 'Failed to adjust levels',
  build: params => ({
    payload: {
      assetPath: extractString(params, 'assetPath'),
      inBlack: extractOptionalNumber(params, 'inBlack') ?? 0.0,
      inWhite: extractOptionalNumber(params, 'inWhite') ?? 1.0,
      gamma: extractOptionalNumber(params, 'gamma') ?? 1.0,
      outBlack: extractOptionalNumber(params, 'outBlack') ?? 0.0,
      outWhite: extractOptionalNumber(params, 'outWhite') ?? 1.0,
      inPlace: extractOptionalBoolean(params, 'inPlace') ?? true,
      save: extractOptionalBoolean(params, 'save') ?? true
    },
    successMessage: 'Texture levels adjusted'
  })
};

const adjustCurvesConfig: TextureActionConfig = {
  subAction: 'adjust_curves',
  params: [
    { key: 'assetPath', aliases: ['texturePath'], required: true },
    { key: 'curvePoints' },
    { key: 'channel', default: 'All' },
    { key: 'outputPath' },
    { key: 'save', default: true }
  ],
  failureMessage: 'Failed to adjust curves',
  build: params => ({
    payload: {
      assetPath: extractString(params, 'assetPath'),
      curvePoints: extractOptionalArray(params, 'curvePoints') ?? [],
      channel: extractOptionalString(params, 'channel') ?? 'All',
      outputPath: extractOptionalString(params, 'outputPath'),
      save: extractOptionalBoolean(params, 'save') ?? true
    },
    successMessage: 'Texture curves adjusted'
  })
};

const blurTextureConfig: TextureActionConfig = {
  subAction: 'blur',
  params: [
    { key: 'assetPath', aliases: ['texturePath'], required: true },
    { key: 'radius', default: 2.0 },
    { key: 'blurType', default: 'Gaussian' },
    { key: 'outputPath' },
    { key: 'save', default: true }
  ],
  failureMessage: 'Failed to blur texture',
  build: params => ({
    payload: {
      assetPath: extractString(params, 'assetPath'),
      radius: extractOptionalNumber(params, 'radius') ?? 2.0,
      blurType: extractOptionalString(params, 'blurType') ?? 'Gaussian',
      outputPath: extractOptionalString(params, 'outputPath'),
      save: extractOptionalBoolean(params, 'save') ?? true
    },
    successMessage: 'Texture blurred'
  })
};

const sharpenTextureConfig: TextureActionConfig = {
  subAction: 'sharpen',
  params: [
    { key: 'assetPath', aliases: ['texturePath'], required: true },
    { key: 'amount', aliases: ['strength'], default: 1.0 },
    { key: 'save', default: true }
  ],
  failureMessage: 'Failed to sharpen texture',
  build: params => ({
    payload: {
      assetPath: extractString(params, 'assetPath'),
      amount: extractOptionalNumber(params, 'amount') ?? 1.0,
      save: extractOptionalBoolean(params, 'save') ?? true
    },
    successMessage: 'Texture sharpened'
  })
};

const invertTextureConfig: TextureActionConfig = {
  subAction: 'invert',
  params: [
    { key: 'assetPath', aliases: ['texturePath'], required: true },
    { key: 'invertAlpha', default: false },
    { key: 'channel', default: 'All' },
    { key: 'outputPath' },
    { key: 'save', default: true }
  ],
  failureMessage: 'Failed to invert texture',
  build: params => ({
    payload: {
      assetPath: extractString(params, 'assetPath'),
      invertAlpha: extractOptionalBoolean(params, 'invertAlpha') ?? false,
      channel: extractOptionalString(params, 'channel') ?? 'All',
      outputPath: extractOptionalString(params, 'outputPath'),
      save: extractOptionalBoolean(params, 'save') ?? true
    },
    successMessage: 'Texture inverted'
  })
};

const desaturateTextureConfig: TextureActionConfig = {
  subAction: 'desaturate',
  params: [
    { key: 'assetPath', aliases: ['texturePath'], required: true },
    { key: 'amount', default: 1.0 },
    { key: 'method', default: 'Luminance' },
    { key: 'outputPath' },
    { key: 'save', default: true }
  ],
  failureMessage: 'Failed to desaturate texture',
  build: params => ({
    payload: {
      assetPath: extractString(params, 'assetPath'),
      amount: extractOptionalNumber(params, 'amount') ?? 1.0,
      method: extractOptionalString(params, 'method') ?? 'Luminance',
      outputPath: extractOptionalString(params, 'outputPath'),
      save: extractOptionalBoolean(params, 'save') ?? true
    },
    successMessage: 'Texture desaturated'
  })
};
