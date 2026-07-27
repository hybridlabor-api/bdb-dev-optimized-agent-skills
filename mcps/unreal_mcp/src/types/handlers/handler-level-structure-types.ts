/**
 * Level structure handler argument types.
 */
import type { HandlerArgs, Rotator, Vector3 } from './handler-common-types.js';

// ============================================================================
// Level Structure Types
// ============================================================================

/**
 * Arguments for manage_level_structure tool
 *
 * Covers:
 * - Levels: create levels, sublevels, streaming, bounds
 * - World Partition: grid configuration, data layers, HLOD
 * - Level Blueprint: open, add nodes, connect nodes
 * - Level Instances: packed level actors, level instances
 */
export interface LevelStructureArgs extends HandlerArgs {
    // Level identification
    levelName?: string;
    levelPath?: string;
    parentLevel?: string;

    // Level creation
    templateLevel?: string;
    bCreateWorldPartition?: boolean;

    // Sublevel configuration
    sublevelName?: string;
    sublevelPath?: string;

    // Level streaming
    streamingMethod?: 'Blueprint' | 'AlwaysLoaded' | 'Disabled';
    bShouldBeVisible?: boolean;
    bShouldBlockOnLoad?: boolean;
    bDisableDistanceStreaming?: boolean;

    // Streaming distance
    streamingDistance?: number;
    minStreamingDistance?: number;

    // Level bounds
    boundsOrigin?: Vector3;
    boundsExtent?: Vector3;
    bAutoCalculateBounds?: boolean;

    // World Partition
    bEnableWorldPartition?: boolean;
    gridCellSize?: number;
    loadingRange?: number;

    // Data layers
    dataLayerName?: string;
    dataLayerLabel?: string;
    bIsInitiallyVisible?: boolean;
    bIsInitiallyLoaded?: boolean;
    dataLayerType?: 'Runtime' | 'Editor';

    // Actor assignment to data layer
    actorName?: string;
    actorPath?: string;

    // HLOD configuration
    hlodLayerName?: string;
    hlodLayerPath?: string;
    bIsSpatiallyLoaded?: boolean;
    cellSize?: number;
    loadingDistance?: number;

    // Minimap volume
    volumeName?: string;
    volumeLocation?: Vector3;
    volumeExtent?: Vector3;

    // Level Blueprint
    nodeClass?: string;
    nodePosition?: { x: number; y: number };
    nodeName?: string;

    // Node connections
    sourceNodeName?: string;
    sourcePinName?: string;
    targetNodeName?: string;
    targetPinName?: string;

    // Level instances
    levelInstanceName?: string;
    levelAssetPath?: string;
    instanceLocation?: Vector3;
    instanceRotation?: Rotator;
    instanceScale?: Vector3;

    // Packed level actor
    packedLevelName?: string;
    bPackBlueprints?: boolean;
    bPackStaticMeshes?: boolean;

    // Save option
    save?: boolean;
}
