/**
 * Asset handler argument types.
 */
import type { HandlerArgs } from './handler-common-types.js';

// ============================================================================
// Asset Types
// ============================================================================

export interface AssetArgs extends HandlerArgs {
    assetPath?: string;
    path?: string;
    directory?: string;
    directoryPath?: string;
    sourcePath?: string;
    destinationPath?: string;
    newName?: string;
    name?: string;
    filter?: string;
    recursive?: boolean;
    overwrite?: boolean;
    classNames?: string[];
    packagePaths?: string[];
    parentMaterial?: string;
    parameters?: Record<string, unknown>;
    assetPaths?: string[];
    meshPath?: string;
    // Bulk operations (C++ TryGetStringField)
    prefix?: string;
    suffix?: string;
    searchText?: string;
    replaceText?: string;
    paths?: string[];
    // Source control (C++ TryGetStringField)
    description?: string;
    checkoutFiles?: boolean;
    // Bulk delete
    showConfirmation?: boolean;
    fixupRedirectors?: boolean;
    // Material graph operations (C++ TryGetStringField/NumberField)
    posX?: number;
    posY?: number;
    nodeType?: string;
    sourceNodeId?: string;
    targetNodeId?: string;
    inputName?: string;
    pinName?: string;
    desc?: string;
    materialPath?: string;
    texturePath?: string;
    expressionClass?: string;
    coordinateIndex?: number;
    parameterName?: string;
    parameterType?: string;
    nodes?: Array<Record<string, unknown>>;
    value?: unknown;
    // Metadata
    metadata?: Record<string, unknown>;
    tags?: string[];
}
