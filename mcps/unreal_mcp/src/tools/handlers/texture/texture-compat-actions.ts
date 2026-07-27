import {
  extractOptionalBoolean,
  extractOptionalNumber,
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

export async function handleTextureCompatAction(
  action: string,
  context: TextureHandlerContext
): Promise<Record<string, unknown> | undefined> {
  switch (action) {
    case 'import_texture':
      return await runTextureAction(context, importTextureConfig);
    case 'set_filter':
    case 'set_texture_filter':
      return await runTextureAction(context, setTextureFilterConfig);
    case 'set_wrap':
    case 'set_texture_wrap':
      return await runTextureAction(context, setTextureWrapConfig);
    case 'create_render_target':
      return await handleCreateRenderTarget(context);
    case 'create_cube_texture':
      return await runTextureAction(context, createCubeTextureConfig);
    case 'create_volume_texture':
      return await runTextureAction(context, createVolumeTextureConfig);
    case 'create_texture_array':
      return await runTextureAction(context, createTextureArrayConfig);
    default:
      return undefined;
  }
}

async function handleCreateRenderTarget(context: TextureHandlerContext): Promise<Record<string, unknown>> {
  const renderTargetPath = extractOptionalString(context.args, 'renderTargetPath');
  const base = renderTargetPath
    ? splitTextureAssetPath(renderTargetPath, '/Game/Textures')
    : extractRenderTargetNameAndPath(context.args);

  return await sendTextureRequest(
    context,
    {
      subAction: 'create_render_target',
      name: base.name,
      path: base.path,
      width: extractOptionalNumber(context.args, 'width') ?? 1024,
      height: extractOptionalNumber(context.args, 'height') ?? 1024,
      format: extractOptionalString(context.args, 'format') ?? 'RGBA8',
      save: extractOptionalBoolean(context.args, 'save') ?? true
    },
    'Failed to create render target',
    `Render target '${base.name}' created`
  );
}

function extractRenderTargetNameAndPath(args: TextureHandlerContext['args']) {
  const params = normalizeArgs(args, [
    { key: 'name', required: true },
    { key: 'path', aliases: ['texturePath', 'directory'], default: '/Game/Textures' },
    { key: 'save', default: true }
  ]);
  return {
    name: extractString(params, 'name'),
    path: extractOptionalString(params, 'path') ?? '/Game/Textures'
  };
}

const importTextureConfig: TextureActionConfig = {
  subAction: 'import_texture',
  params: [
    { key: 'sourcePath', required: true },
    { key: 'destinationPath', aliases: ['texturePath', 'path'], required: true }
  ],
  failureMessage: 'Failed to import texture',
  build: params => {
    const destinationPath = extractString(params, 'destinationPath');
    return {
      payload: {
        sourcePath: extractString(params, 'sourcePath'),
        destinationPath
      },
      successMessage: `Texture imported to '${destinationPath}'`
    };
  }
};

const setTextureFilterConfig: TextureActionConfig = {
  subAction: 'set_texture_filter',
  params: [
    { key: 'assetPath', aliases: ['texturePath'], required: true },
    { key: 'filter', required: true }
  ],
  failureMessage: 'Failed to set texture filter',
  build: params => {
    const filter = extractString(params, 'filter');
    return {
      payload: {
        assetPath: extractString(params, 'assetPath'),
        filter
      },
      successMessage: `Texture filter set to '${filter}'`
    };
  }
};

const setTextureWrapConfig: TextureActionConfig = {
  subAction: 'set_texture_wrap',
  params: [
    { key: 'assetPath', aliases: ['texturePath'], required: true },
    { key: 'wrapMode', aliases: ['wrap'], required: true }
  ],
  failureMessage: 'Failed to set texture wrap mode',
  build: params => {
    const wrapMode = extractString(params, 'wrapMode');
    return {
      payload: {
        assetPath: extractString(params, 'assetPath'),
        wrapMode
      },
      successMessage: `Texture wrap mode set to '${wrapMode}'`
    };
  }
};

const createCubeTextureConfig: TextureActionConfig = {
  subAction: 'create_cube_texture',
  params: [
    { key: 'name', required: true },
    { key: 'path', aliases: ['texturePath', 'directory'], default: '/Game/Textures' },
    { key: 'size', default: 512 },
    { key: 'save', default: true }
  ],
  failureMessage: 'Failed to create cube texture',
  build: params => {
    const name = extractString(params, 'name');
    return {
      payload: {
        name,
        path: extractOptionalString(params, 'path') ?? '/Game/Textures',
        size: extractOptionalNumber(params, 'size') ?? 512,
        save: extractOptionalBoolean(params, 'save') ?? true
      },
      successMessage: `Cube texture '${name}' created`
    };
  }
};

const createVolumeTextureConfig: TextureActionConfig = {
  subAction: 'create_volume_texture',
  params: [
    { key: 'name', required: true },
    { key: 'path', aliases: ['texturePath', 'directory'], default: '/Game/Textures' },
    { key: 'width', default: 256 },
    { key: 'height', default: 256 },
    { key: 'depth', default: 256 },
    { key: 'save', default: true }
  ],
  failureMessage: 'Failed to create volume texture',
  build: params => {
    const name = extractString(params, 'name');
    return {
      payload: {
        name,
        path: extractOptionalString(params, 'path') ?? '/Game/Textures',
        width: extractOptionalNumber(params, 'width') ?? 256,
        height: extractOptionalNumber(params, 'height') ?? 256,
        depth: extractOptionalNumber(params, 'depth') ?? 256,
        save: extractOptionalBoolean(params, 'save') ?? true
      },
      successMessage: `Volume texture '${name}' created`
    };
  }
};

const createTextureArrayConfig: TextureActionConfig = {
  subAction: 'create_texture_array',
  params: [
    { key: 'name', required: true },
    { key: 'path', aliases: ['texturePath', 'directory'], default: '/Game/Textures' },
    { key: 'width', default: 512 },
    { key: 'height', default: 512 },
    { key: 'numSlices', default: 4 },
    { key: 'save', default: true }
  ],
  failureMessage: 'Failed to create texture array',
  build: params => {
    const name = extractString(params, 'name');
    return {
      payload: {
        name,
        path: extractOptionalString(params, 'path') ?? '/Game/Textures',
        width: extractOptionalNumber(params, 'width') ?? 512,
        height: extractOptionalNumber(params, 'height') ?? 512,
        numSlices: extractOptionalNumber(params, 'numSlices') ?? 4,
        save: extractOptionalBoolean(params, 'save') ?? true
      },
      successMessage: `Texture array '${name}' created`
    };
  }
};
