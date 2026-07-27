/**
 * Spline handler argument types.
 */
import type { HandlerArgs, Rotator, Vector3 } from './handler-common-types.js';

// ============================================================================
// Splines Types
// ============================================================================

/**
 * Spline point type options matching ESplinePointType
 */
export type SplinePointType = 'Linear' | 'Curve' | 'Constant' | 'CurveClamped' | 'CurveCustomTangent';

/**
 * Spline mesh axis options matching ESplineMeshAxis
 */
export type SplineMeshAxis = 'X' | 'Y' | 'Z';

/**
 * Spline coordinate space
 */
export type SplineCoordinateSpace = 'Local' | 'World';

/**
 * Arguments for manage_splines tool
 *
 * Covers:
 * - Spline Creation: create_spline_actor, add_spline_point, remove_spline_point, set_spline_point_position
 * - Spline Configuration: set_spline_point_tangents, set_spline_point_rotation, set_spline_point_scale, set_spline_type
 * - Spline Mesh: create_spline_mesh_component, set_spline_mesh_asset, configure_spline_mesh_axis, set_spline_mesh_material
 * - Spline Mesh Array: scatter_meshes_along_spline, configure_mesh_spacing, configure_mesh_randomization
 * - Quick Templates: create_road_spline, create_river_spline, create_fence_spline, create_wall_spline, create_cable_spline, create_pipe_spline
 * - Utility: get_splines_info
 */
export interface SplinesArgs extends HandlerArgs {
    // Spline/Actor identification
    actorName?: string;
    actorPath?: string;
    splineName?: string;
    componentName?: string;
    blueprintPath?: string;

    // Location and transform
    location?: Vector3;
    rotation?: Rotator;
    scale?: Vector3;

    // Spline point manipulation
    pointIndex?: number;
    position?: Vector3;
    arriveTangent?: Vector3;
    leaveTangent?: Vector3;
    tangent?: Vector3;
    pointRotation?: Rotator;
    pointScale?: Vector3;
    coordinateSpace?: SplineCoordinateSpace;

    // Spline type configuration
    splineType?: SplinePointType;
    bClosedLoop?: boolean;
    bUpdateSpline?: boolean;

    // Spline mesh configuration
    meshPath?: string;
    materialPath?: string;
    forwardAxis?: SplineMeshAxis;
    startPos?: Vector3;
    startTangent?: Vector3;
    endPos?: Vector3;
    endTangent?: Vector3;
    startScale?: { x: number; y: number };
    endScale?: { x: number; y: number };
    startRoll?: number;
    endRoll?: number;
    bSmoothInterpRollScale?: boolean;

    // Mesh scattering along spline
    spacing?: number;
    startOffset?: number;
    endOffset?: number;
    bAlignToSpline?: boolean;
    bRandomizeRotation?: boolean;
    rotationRandomRange?: Rotator;
    bRandomizeScale?: boolean;
    scaleMin?: number;
    scaleMax?: number;
    randomSeed?: number;

    // Template-specific options
    templateType?: 'road' | 'river' | 'fence' | 'wall' | 'cable' | 'pipe';
    width?: number;
    segmentLength?: number;
    postSpacing?: number;
    railHeight?: number;
    pipeRadius?: number;
    cableSlack?: number;

    // Points array for batch operations
    points?: Array<{
        position: Vector3;
        arriveTangent?: Vector3;
        leaveTangent?: Vector3;
        rotation?: Rotator;
        scale?: Vector3;
        type?: SplinePointType;
    }>;

    // Query parameters
    filter?: string;

    // Save option
    save?: boolean;
}
