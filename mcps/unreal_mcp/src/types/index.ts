/**
 * Central exports for type definitions.
 *
 * @example
 * import { StandardActionResponse, HandlerArgs } from '../types/index.js';
 */

// Core response types
export type {
  AutomationErrorDetail,
  Vector3Response,
  RotatorResponse,
  ResolutionResponse,
  AutomationResponse,
  LevelResponse,
  ActorResponse,
  AssetResponse,
  EditorResponse,
  SequenceResponse,
  ConsoleResponse,
} from './automation/automation-responses.js';

// Environment configuration
export type { Env } from './config/env.js';
export { loadEnv } from './config/env.js';

// Handler argument types
export type {
  Vector3,
  Rotator,
  Transform,
  HandlerArgs,
  ComponentInfo,
  ActorArgs,
  AssetArgs,
  BlueprintArgs,
  EditorArgs,
  LevelArgs,
  SequenceArgs,
  EffectArgs,
  EnvironmentArgs,
  LightingArgs,
  PerformanceArgs,
  InspectArgs,
  GraphArgs,
  SystemArgs,
  InputArgs,
  PipelineArgs,
  BlendSpaceAxis,
  AnimationArgs,
  AudioArgs,
  MatchStateDefinition,
  GameFrameworkArgs,
  NavigationArgs,
  VoiceSettings,
  SessionsArgs,
  LevelStructureArgs,
  SplinePointType,
  SplineMeshAxis,
  SplineCoordinateSpace,
  SplinesArgs,
  VolumeProperties,
  VolumesArgs,
} from './handlers/handler-types.js';

// Tool interfaces
export type {
  IBaseTool,
  StandardActionResponse,
  IAssetResources,
  ITools,
} from './tools/tool-interfaces.js';

// Tool-specific types
export * from './tools/tool-types.js';
