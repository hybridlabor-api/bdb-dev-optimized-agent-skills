/**
 * Animation, physics, and audio handler argument types.
 */
import type { HandlerArgs, Rotator, Vector3 } from './handler-common-types.js';

// ============================================================================
// Animation & Physics Types
// ============================================================================

/** Axis definition for blend spaces */
export interface BlendSpaceAxis {
    minValue?: number;
    maxValue?: number;
    name?: string;
}

export interface AnimationArgs extends HandlerArgs {
    name?: string;
    blueprintName?: string;
    skeletonPath?: string;
    targetSkeleton?: string;
    savePath?: string;
    path?: string;
    actorName?: string;
    meshPath?: string;
    montagePath?: string;
    playRate?: number;

    // Blend space
    horizontalAxis?: BlendSpaceAxis;
    verticalAxis?: BlendSpaceAxis;
    minX?: number;
    maxX?: number;
    minY?: number;
    maxY?: number;

    // State machine
    machineName?: string;
    states?: unknown[];
    transitions?: unknown[];
    blueprintPath?: string;

    // IK
    ikBones?: unknown[];
    enableFootPlacement?: boolean;

    // Procedural anim
    systemName?: string;
    baseAnimation?: string;
    modifiers?: unknown[];

    // Blend tree
    treeName?: string;
    blendType?: string;
    basePose?: string;
    additiveAnimations?: unknown[];

    // Animation asset
    assetType?: string;

    // Notify
    animationPath?: string;
    assetPath?: string;
    notifyName?: string;
    time?: number;
    startTime?: number;

    // Vehicle
    vehicleName?: string;
    vehicleType?: string;
    wheels?: unknown[];
    engine?: unknown;
    transmission?: unknown;
    pluginDependencies?: string[];
    plugins?: string[];

    // Physics simulation
    physicsAssetName?: string;

    // Cleanup
    artifacts?: unknown[];
}

// ============================================================================
// Audio Types
// ============================================================================

export interface AudioArgs extends HandlerArgs {
    name?: string;
    soundPath?: string;
    wavePath?: string;
    savePath?: string;
    location?: Vector3;
    rotation?: Rotator;
    volume?: number;
    pitch?: number;
    startTime?: number;
    attenuationPath?: string;
    concurrencyPath?: string;
    actorName?: string;
    componentName?: string;
    autoPlay?: boolean;
    is3D?: boolean;
    innerRadius?: number;
    falloffDistance?: number;
    attenuationShape?: string;
    falloffMode?: string;
    parentClass?: string;
    properties?: Record<string, unknown>;
    classAdjusters?: unknown[];
    mixName?: string;
    size?: Vector3;
    reverbEffect?: string;
    fadeTime?: number;
    fadeInTime?: number;
    fadeOutTime?: number;
    enabled?: boolean;
    enable?: boolean;
    analysisType?: string;
    windowSize?: number;
    outputType?: string;
    soundName?: string;
    targetVolume?: number;
    fadeType?: string;
    lowPassFilterFrequency?: number;
    looping?: boolean;
    settings?: Record<string, unknown>;
}
