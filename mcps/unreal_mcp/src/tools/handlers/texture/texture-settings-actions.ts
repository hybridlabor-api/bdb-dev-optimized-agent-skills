import {
  extractOptionalBoolean,
  extractOptionalNumber,
  extractString
} from '../foundation/arguments/argument-helper.js';
import {
  runTextureAction,
  type TextureActionConfig,
  type TextureHandlerContext
} from './texture-handler-types.js';

export async function handleTextureSettingsAction(
  action: string,
  context: TextureHandlerContext
): Promise<Record<string, unknown> | undefined> {
  switch (action) {
    case 'set_compression_settings':
      return await runTextureAction(context, setCompressionSettingsConfig);
    case 'set_texture_group':
      return await runTextureAction(context, setTextureGroupConfig);
    case 'set_lod_bias':
      return await runTextureAction(context, setLodBiasConfig);
    case 'configure_virtual_texture':
      return await runTextureAction(context, configureVirtualTextureConfig);
    case 'set_streaming_priority':
      return await runTextureAction(context, setStreamingPriorityConfig);
    case 'get_texture_info':
      return await runTextureAction(context, getTextureInfoConfig);
    default:
      return undefined;
  }
}

const setCompressionSettingsConfig: TextureActionConfig = {
  subAction: 'set_compression_settings',
  params: [
    { key: 'assetPath', aliases: ['texturePath'], required: true },
    { key: 'compressionSettings', required: true },
    { key: 'save', default: true }
  ],
  failureMessage: 'Failed to set compression settings',
  build: params => {
    const compressionSettings = extractString(params, 'compressionSettings');
    return {
      payload: {
        assetPath: extractString(params, 'assetPath'),
        compressionSettings,
        save: extractOptionalBoolean(params, 'save') ?? true
      },
      successMessage: `Compression set to ${compressionSettings}`
    };
  }
};

const setTextureGroupConfig: TextureActionConfig = {
  subAction: 'set_texture_group',
  params: [
    { key: 'assetPath', aliases: ['texturePath'], required: true },
    { key: 'textureGroup', required: true },
    { key: 'save', default: true }
  ],
  failureMessage: 'Failed to set texture group',
  build: params => {
    const textureGroup = extractString(params, 'textureGroup');
    return {
      payload: {
        assetPath: extractString(params, 'assetPath'),
        textureGroup,
        save: extractOptionalBoolean(params, 'save') ?? true
      },
      successMessage: `Texture group set to ${textureGroup}`
    };
  }
};

const setLodBiasConfig: TextureActionConfig = {
  subAction: 'set_lod_bias',
  params: [
    { key: 'assetPath', aliases: ['texturePath'], required: true },
    { key: 'lodBias', required: true },
    { key: 'save', default: true }
  ],
  failureMessage: 'Failed to set LOD bias',
  build: params => {
    const lodBias = extractOptionalNumber(params, 'lodBias') ?? 0;
    return {
      payload: {
        assetPath: extractString(params, 'assetPath'),
        lodBias,
        save: extractOptionalBoolean(params, 'save') ?? true
      },
      successMessage: `LOD bias set to ${lodBias}`
    };
  }
};

const configureVirtualTextureConfig: TextureActionConfig = {
  subAction: 'configure_virtual_texture',
  params: [
    { key: 'assetPath', aliases: ['texturePath'], required: true },
    { key: 'virtualTextureStreaming', required: true },
    { key: 'tileSize', default: 128 },
    { key: 'tileBorderSize', default: 4 },
    { key: 'save', default: true }
  ],
  failureMessage: 'Failed to configure virtual texture',
  build: params => {
    const virtualTextureStreaming = extractOptionalBoolean(params, 'virtualTextureStreaming') ?? false;
    return {
      payload: {
        assetPath: extractString(params, 'assetPath'),
        virtualTextureStreaming,
        tileSize: extractOptionalNumber(params, 'tileSize') ?? 128,
        tileBorderSize: extractOptionalNumber(params, 'tileBorderSize') ?? 4,
        save: extractOptionalBoolean(params, 'save') ?? true
      },
      successMessage: `Virtual texture streaming ${virtualTextureStreaming ? 'enabled' : 'disabled'}`
    };
  }
};

const setStreamingPriorityConfig: TextureActionConfig = {
  subAction: 'set_streaming_priority',
  params: [
    { key: 'assetPath', aliases: ['texturePath'], required: true },
    { key: 'neverStream', default: false },
    { key: 'streamingPriority', default: 0 },
    { key: 'save', default: true }
  ],
  failureMessage: 'Failed to set streaming priority',
  build: params => ({
    payload: {
      assetPath: extractString(params, 'assetPath'),
      neverStream: extractOptionalBoolean(params, 'neverStream') ?? false,
      streamingPriority: extractOptionalNumber(params, 'streamingPriority') ?? 0,
      save: extractOptionalBoolean(params, 'save') ?? true
    },
    successMessage: 'Streaming priority configured'
  })
};

const getTextureInfoConfig: TextureActionConfig = {
  subAction: 'get_texture_info',
  params: [
    { key: 'assetPath', aliases: ['texturePath'], required: true }
  ],
  failureMessage: 'Failed to get texture info',
  build: params => ({
    payload: {
      assetPath: extractString(params, 'assetPath')
    },
    successMessage: 'Texture info retrieved'
  })
};
