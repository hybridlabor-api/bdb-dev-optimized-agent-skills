import {
  extractOptionalBoolean,
  extractOptionalArray,
  extractOptionalNumber,
  extractOptionalObject,
  extractOptionalString,
  extractString,
  normalizeArgs
} from '../foundation/arguments/argument-helper.js';
import {
  runTextureAction,
  sendTextureRequest,
  splitTextureAssetPath,
  type TextureActionConfig,
  type TextureHandlerContext
} from './texture-handler-types.js';

export async function handleTextureGenerationAction(
  action: string,
  context: TextureHandlerContext
): Promise<Record<string, unknown> | undefined> {
  switch (action) {
    case 'create_noise_texture':
    case 'create_texture':
      return await handleCreateNoiseTexture(context);
    case 'create_gradient_texture':
      return await runTextureAction(context, createGradientTextureConfig);
    case 'create_pattern_texture':
      return await runTextureAction(context, createPatternTextureConfig);
    case 'create_normal_from_height':
      return await runTextureAction(context, createNormalFromHeightConfig);
    case 'create_ao_from_mesh':
      return await runTextureAction(context, createAoFromMeshConfig);
    default:
      return undefined;
  }
}

async function handleCreateNoiseTexture(context: TextureHandlerContext): Promise<Record<string, unknown>> {
  const texturePath = extractOptionalString(context.args, 'texturePath');
  const base = texturePath
    ? splitTextureAssetPath(texturePath, '/Game/Textures')
    : extractNameAndPath(context.args);

  const payload = {
    subAction: 'create_noise_texture',
    name: base.name,
    path: base.path,
    noiseType: extractOptionalString(context.args, 'noiseType') ?? 'Perlin',
    width: extractOptionalNumber(context.args, 'width') ?? 1024,
    height: extractOptionalNumber(context.args, 'height') ?? 1024,
    scale: extractOptionalNumber(context.args, 'scale') ?? 1.0,
    octaves: extractOptionalNumber(context.args, 'octaves') ?? 4,
    persistence: extractOptionalNumber(context.args, 'persistence') ?? 0.5,
    lacunarity: extractOptionalNumber(context.args, 'lacunarity') ?? 2.0,
    seed: extractOptionalNumber(context.args, 'seed') ?? 0,
    seamless: extractOptionalBoolean(context.args, 'seamless') ?? false,
    hdr: extractOptionalBoolean(context.args, 'hdr') ?? false,
    save: extractOptionalBoolean(context.args, 'save') ?? true
  };

  return await sendTextureRequest(
    context,
    payload,
    'Failed to create noise texture',
    `Noise texture '${base.name}' created`
  );
}

function extractNameAndPath(args: TextureHandlerContext['args']) {
  const params = normalizeArgs(args, [
    { key: 'name', required: true },
    { key: 'path', aliases: ['directory'], default: '/Game/Textures' }
  ]);
  return {
    name: extractString(params, 'name'),
    path: extractOptionalString(params, 'path') ?? '/Game/Textures'
  };
}

const createGradientTextureConfig: TextureActionConfig = {
  subAction: 'create_gradient_texture',
  params: [
    { key: 'name', required: true },
    { key: 'path', aliases: ['directory'], default: '/Game/Textures' },
    { key: 'gradientType', default: 'Linear' },
    { key: 'width', default: 1024 },
    { key: 'height', default: 1024 },
    { key: 'startColor', default: { r: 0, g: 0, b: 0, a: 1 } },
    { key: 'endColor', default: { r: 1, g: 1, b: 1, a: 1 } },
    { key: 'angle', default: 0 },
    { key: 'centerX', default: 0.5 },
    { key: 'centerY', default: 0.5 },
    { key: 'radius', default: 0.5 },
    { key: 'colorStops' },
    { key: 'hdr', default: false },
    { key: 'save', default: true }
  ],
  failureMessage: 'Failed to create gradient texture',
  build: params => {
    const name = extractString(params, 'name');
    return {
      payload: {
        name,
        path: extractOptionalString(params, 'path') ?? '/Game/Textures',
        gradientType: extractOptionalString(params, 'gradientType') ?? 'Linear',
        width: extractOptionalNumber(params, 'width') ?? 1024,
        height: extractOptionalNumber(params, 'height') ?? 1024,
        startColor: extractOptionalObject(params, 'startColor') ?? { r: 0, g: 0, b: 0, a: 1 },
        endColor: extractOptionalObject(params, 'endColor') ?? { r: 1, g: 1, b: 1, a: 1 },
        angle: extractOptionalNumber(params, 'angle') ?? 0,
        centerX: extractOptionalNumber(params, 'centerX') ?? 0.5,
        centerY: extractOptionalNumber(params, 'centerY') ?? 0.5,
        radius: extractOptionalNumber(params, 'radius') ?? 0.5,
        colorStops: extractOptionalArray(params, 'colorStops'),
        hdr: extractOptionalBoolean(params, 'hdr') ?? false,
        save: extractOptionalBoolean(params, 'save') ?? true
      },
      successMessage: `Gradient texture '${name}' created`
    };
  }
};

const createPatternTextureConfig: TextureActionConfig = {
  subAction: 'create_pattern_texture',
  params: [
    { key: 'name', required: true },
    { key: 'path', aliases: ['directory'], default: '/Game/Textures' },
    { key: 'patternType', default: 'Checker' },
    { key: 'width', default: 1024 },
    { key: 'height', default: 1024 },
    { key: 'primaryColor', default: { r: 1, g: 1, b: 1, a: 1 } },
    { key: 'secondaryColor', default: { r: 0, g: 0, b: 0, a: 1 } },
    { key: 'tilesX', default: 8 },
    { key: 'tilesY', default: 8 },
    { key: 'lineWidth', default: 0.02 },
    { key: 'brickRatio', default: 2.0 },
    { key: 'offset', default: 0.5 },
    { key: 'save', default: true }
  ],
  failureMessage: 'Failed to create pattern texture',
  build: params => {
    const name = extractString(params, 'name');
    return {
      payload: {
        name,
        path: extractOptionalString(params, 'path') ?? '/Game/Textures',
        patternType: extractOptionalString(params, 'patternType') ?? 'Checker',
        width: extractOptionalNumber(params, 'width') ?? 1024,
        height: extractOptionalNumber(params, 'height') ?? 1024,
        primaryColor: extractOptionalObject(params, 'primaryColor') ?? { r: 1, g: 1, b: 1, a: 1 },
        secondaryColor: extractOptionalObject(params, 'secondaryColor') ?? { r: 0, g: 0, b: 0, a: 1 },
        tilesX: extractOptionalNumber(params, 'tilesX') ?? 8,
        tilesY: extractOptionalNumber(params, 'tilesY') ?? 8,
        lineWidth: extractOptionalNumber(params, 'lineWidth') ?? 0.02,
        brickRatio: extractOptionalNumber(params, 'brickRatio') ?? 2.0,
        offset: extractOptionalNumber(params, 'offset') ?? 0.5,
        save: extractOptionalBoolean(params, 'save') ?? true
      },
      successMessage: `Pattern texture '${name}' created`
    };
  }
};

const createNormalFromHeightConfig: TextureActionConfig = {
  subAction: 'create_normal_from_height',
  params: [
    { key: 'sourceTexture', aliases: ['heightMapPath'], required: true },
    { key: 'name' },
    { key: 'path', aliases: ['directory'] },
    { key: 'strength', default: 1.0 },
    { key: 'algorithm', default: 'Sobel' },
    { key: 'flipY', default: false },
    { key: 'save', default: true }
  ],
  failureMessage: 'Failed to create normal map from height',
  build: params => ({
    payload: {
      sourceTexture: extractString(params, 'sourceTexture'),
      name: extractOptionalString(params, 'name'),
      path: extractOptionalString(params, 'path'),
      strength: extractOptionalNumber(params, 'strength') ?? 1.0,
      algorithm: extractOptionalString(params, 'algorithm') ?? 'Sobel',
      flipY: extractOptionalBoolean(params, 'flipY') ?? false,
      save: extractOptionalBoolean(params, 'save') ?? true
    },
    successMessage: 'Normal map created from height map'
  })
};

const createAoFromMeshConfig: TextureActionConfig = {
  subAction: 'create_ao_from_mesh',
  params: [
    { key: 'meshPath', required: true },
    { key: 'name', required: true },
    { key: 'path', aliases: ['directory'], default: '/Game/Textures' },
    { key: 'width', default: 1024 },
    { key: 'height', default: 1024 },
    { key: 'samples', aliases: ['sampleCount'], default: 64 },
    { key: 'rayDistance', default: 100.0 },
    { key: 'bias', default: 0.01 },
    { key: 'uvChannel', default: 0 },
    { key: 'save', default: true }
  ],
  failureMessage: 'Failed to create AO from mesh',
  build: params => {
    const name = extractString(params, 'name');
    return {
      payload: {
        meshPath: extractString(params, 'meshPath'),
        name,
        path: extractOptionalString(params, 'path') ?? '/Game/Textures',
        width: extractOptionalNumber(params, 'width') ?? 1024,
        height: extractOptionalNumber(params, 'height') ?? 1024,
        sampleCount: extractOptionalNumber(params, 'samples') ?? 64,
        rayDistance: extractOptionalNumber(params, 'rayDistance') ?? 100.0,
        bias: extractOptionalNumber(params, 'bias') ?? 0.01,
        uvChannel: extractOptionalNumber(params, 'uvChannel') ?? 0,
        save: extractOptionalBoolean(params, 'save') ?? true
      },
      successMessage: `AO texture '${name}' created from mesh`
    };
  }
};
