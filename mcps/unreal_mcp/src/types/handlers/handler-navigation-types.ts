/**
 * Navigation handler argument types.
 */
import type { HandlerArgs, Rotator, Vector3 } from './handler-common-types.js';

// ============================================================================
// Navigation System Types
// ============================================================================

/**
 * Arguments for manage_navigation tool
 *
 * Covers:
 * - NavMesh: settings configuration, agent properties, rebuild
 * - Nav Modifiers: component creation, area class, cost configuration
 * - Nav Links: proxy creation, link configuration, smart links
 */
export interface NavigationArgs extends HandlerArgs {
    // NavMesh identification
    navMeshPath?: string;
    actorName?: string;
    actorPath?: string;
    blueprintPath?: string;

    // Nav agent properties (ARecastNavMesh)
    agentRadius?: number;
    agentHeight?: number;
    agentStepHeight?: number;
    agentMaxSlope?: number;

    // NavMesh generation settings (FNavMeshResolutionParam)
    cellSize?: number;
    cellHeight?: number;
    tileSizeUU?: number;
    minRegionArea?: number;
    mergeRegionSize?: number;
    maxSimplificationError?: number;

    // Nav modifier component (UNavModifierComponent)
    componentName?: string;
    areaClass?: string;
    areaClassToReplace?: string;
    failsafeExtent?: Vector3;
    bIncludeAgentHeight?: boolean;

    // Nav area cost configuration
    areaCost?: number;
    fixedAreaEnteringCost?: number;

    // Nav link configuration (ANavLinkProxy, FNavigationLink)
    linkName?: string;
    startPoint?: Vector3;
    endPoint?: Vector3;
    direction?: 'BothWays' | 'LeftToRight' | 'RightToLeft';
    snapRadius?: number;
    linkEnabled?: boolean;

    // Smart link configuration (UNavLinkCustomComponent)
    linkType?: 'simple' | 'smart';
    bSmartLinkIsRelevant?: boolean;
    enabledAreaClass?: string;
    disabledAreaClass?: string;
    broadcastRadius?: number;
    broadcastInterval?: number;

    // Obstacle configuration
    bCreateBoxObstacle?: boolean;
    obstacleOffset?: Vector3;
    obstacleExtent?: Vector3;
    obstacleAreaClass?: string;

    // Location and transform
    location?: Vector3;
    rotation?: Rotator;

    // Query parameters
    filter?: string;

    // Save option
    save?: boolean;
}
