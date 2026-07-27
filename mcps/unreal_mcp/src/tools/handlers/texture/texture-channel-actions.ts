import {
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

export async function handleTextureChannelAction(
  action: string,
  context: TextureHandlerContext
): Promise<Record<string, unknown> | undefined> {
  switch (action) {
    case 'channel_pack':
      return await runTextureAction(context, channelPackConfig);
    case 'channel_extract':
      return await runTextureAction(context, channelExtractConfig);
    case 'combine_textures':
      return await runTextureAction(context, combineTexturesConfig);
    default:
      return undefined;
  }
}

const channelPackConfig: TextureActionConfig = {
  subAction: 'channel_pack',
  params: [
    { key: 'name', required: true },
    { key: 'path', aliases: ['directory'], default: '/Game/Textures' },
    { key: 'redTexture', aliases: ['redChannel'] },
    { key: 'greenTexture', aliases: ['greenChannel'] },
    { key: 'blueTexture', aliases: ['blueChannel'] },
    { key: 'alphaTexture', aliases: ['alphaChannel'] },
    { key: 'redSourceChannel', default: 'Red' },
    { key: 'greenSourceChannel', default: 'Green' },
    { key: 'blueSourceChannel', default: 'Blue' },
    { key: 'alphaSourceChannel', default: 'Alpha' },
    { key: 'width' },
    { key: 'height' },
    { key: 'save', default: true }
  ],
  failureMessage: 'Failed to pack channels',
  build: params => {
    const name = extractString(params, 'name');
    return {
      payload: {
        name,
        path: extractOptionalString(params, 'path') ?? '/Game/Textures',
        redTexture: extractOptionalString(params, 'redTexture'),
        greenTexture: extractOptionalString(params, 'greenTexture'),
        blueTexture: extractOptionalString(params, 'blueTexture'),
        alphaTexture: extractOptionalString(params, 'alphaTexture'),
        redSourceChannel: extractOptionalString(params, 'redSourceChannel') ?? 'Red',
        greenSourceChannel: extractOptionalString(params, 'greenSourceChannel') ?? 'Green',
        blueSourceChannel: extractOptionalString(params, 'blueSourceChannel') ?? 'Blue',
        alphaSourceChannel: extractOptionalString(params, 'alphaSourceChannel') ?? 'Alpha',
        width: extractOptionalNumber(params, 'width'),
        height: extractOptionalNumber(params, 'height'),
        save: extractOptionalBoolean(params, 'save') ?? true
      },
      successMessage: `Packed texture '${name}' created`
    };
  }
};

const channelExtractConfig: TextureActionConfig = {
  subAction: 'channel_extract',
  params: [
    { key: 'texturePath', aliases: ['assetPath'], required: true },
    { key: 'channel', required: true },
    { key: 'outputPath' },
    { key: 'name' },
    { key: 'save', default: true }
  ],
  failureMessage: 'Failed to extract channel',
  build: params => {
    const channel = extractString(params, 'channel');
    return {
      payload: {
        texturePath: extractString(params, 'texturePath'),
        channel,
        outputPath: extractOptionalString(params, 'outputPath'),
        name: extractOptionalString(params, 'name'),
        save: extractOptionalBoolean(params, 'save') ?? true
      },
      successMessage: `Channel ${channel} extracted`
    };
  }
};

const combineTexturesConfig: TextureActionConfig = {
  subAction: 'combine_textures',
  params: [
    { key: 'name', required: true },
    { key: 'path', aliases: ['directory'], default: '/Game/Textures' },
    { key: 'baseTexture', required: true },
    { key: 'blendTexture', aliases: ['overlayTexture'], required: true },
    { key: 'blendMode', default: 'Multiply' },
    { key: 'opacity', default: 1.0 },
    { key: 'maskTexture' },
    { key: 'save', default: true }
  ],
  failureMessage: 'Failed to combine textures',
  build: params => {
    const name = extractString(params, 'name');
    return {
      payload: {
        name,
        path: extractOptionalString(params, 'path') ?? '/Game/Textures',
        baseTexture: extractString(params, 'baseTexture'),
        blendTexture: extractString(params, 'blendTexture'),
        blendMode: extractOptionalString(params, 'blendMode') ?? 'Multiply',
        opacity: extractOptionalNumber(params, 'opacity') ?? 1.0,
        maskTexture: extractOptionalString(params, 'maskTexture'),
        save: extractOptionalBoolean(params, 'save') ?? true
      },
      successMessage: `Combined texture '${name}' created`
    };
  }
};
