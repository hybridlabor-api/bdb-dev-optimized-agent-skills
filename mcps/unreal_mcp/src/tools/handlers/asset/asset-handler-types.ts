import type { ITools } from '../../../types/tools/tool-interfaces.js';
import type { AssetArgs, HandlerArgs } from '../../../types/handlers/handler-types.js';

export interface AssetHandlerContext {
  readonly args: HandlerArgs;
  readonly assetArgs: AssetArgs;
  readonly tools: ITools;
}

export interface AssetListItem {
  path?: string;
  package?: string;
  name?: string;
}

export interface AssetListResponse {
  success?: boolean;
  assets?: AssetListItem[];
  result?: { assets?: AssetListItem[]; folders?: string[] } | AssetListItem[];
  folders?: string[];
  [key: string]: unknown;
}

export interface AssetOperationResponse {
  success?: boolean;
  message?: string;
  error?: string;
  tags?: Record<string, unknown>;
  metadata?: Record<string, unknown>;
  [key: string]: unknown;
}

export function createAssetContext(args: HandlerArgs, tools: ITools): AssetHandlerContext {
  return {
    args,
    assetArgs: args as AssetArgs,
    tools
  };
}
