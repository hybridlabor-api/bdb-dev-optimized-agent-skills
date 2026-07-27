import type { BaseToolResponse, ScreenshotMode } from './tool-base-types.js';

export interface AssetInfo {
  Name: string;
  Path: string;
  Class?: string;
  PackagePath?: string;
}

export interface ManageAssetResponse extends BaseToolResponse {
  assets?: AssetInfo[];
  paths?: string[];
  materialPath?: string;
  materialInstancePath?: string;
}

export interface ControlActorResponse extends BaseToolResponse {
  actor?: string;
  actorName?: string;
  actorPath?: string;
  componentName?: string;
  componentPath?: string;
  componentClass?: string;
  componentPaths?: Array<{ name: string; path: string; class?: string }>;
  components?: Array<Record<string, unknown>>;
  actors?: Array<Record<string, unknown>>;
  deleted?: string | string[];
  deletedCount?: number;
  missing?: string[];
  physicsEnabled?: boolean;
  visible?: boolean;
  tag?: string;
  snapshotName?: string;
}

export interface ControlEditorResponse extends BaseToolResponse {
  playing?: boolean;
  location?: [number, number, number];
  rotation?: [number, number, number];
  viewMode?: string;
  filename?: string;
  path?: string;
  screenshotPath?: string;
  mode?: ScreenshotMode;
  async?: boolean;
  saved?: boolean;
  imageBase64?: string;
  mimeType?: string;
  width?: number;
  height?: number;
  sizeBytes?: number;
}

export interface ManageLevelResponse extends BaseToolResponse {
  levelName?: string;
  loaded?: boolean;
  visible?: boolean;
  lightName?: string;
  buildQuality?: string;
}

export interface AnimationPhysicsResponse extends BaseToolResponse {
  blueprintPath?: string;
  playing?: boolean;
  playRate?: number;
  ragdollActive?: boolean;
  path?: string;
  blendSpacePath?: string;
  skeletonPath?: string;
  controlRigPath?: string;
  twoDimensional?: boolean;
  warnings?: string[];
  details?: unknown;
}

export interface CreateEffectResponse extends BaseToolResponse {
  effectName?: string;
  effectPath?: string;
  spawned?: boolean;
  location?: [number, number, number];
}

export interface ManageBlueprintResponse extends BaseToolResponse {
  blueprintPath?: string;
  componentAdded?: string;
}

export interface BuildEnvironmentResponse extends BaseToolResponse {
  landscapeName?: string;
  foliageTypeName?: string;
  instancesPlaced?: number;
}

export interface SystemControlResponse extends BaseToolResponse {
  profiling?: boolean;
  fpsVisible?: boolean;
  qualityLevel?: number;
  soundPlaying?: boolean;
  widgetPath?: string;
  widgetVisible?: boolean;
  imagePath?: string;
  filename?: string;
  path?: string;
  screenshotPath?: string;
  mode?: ScreenshotMode;
  async?: boolean;
  saved?: boolean;
  imageBase64?: string;
  mimeType?: string;
  width?: number;
  height?: number;
  sizeBytes?: number;
  pid?: number;
  logPath?: string;
  entries?: Array<{ timestamp?: string; category?: string; level?: string; message: string }>;
  filteredCount?: number;
}

export interface ConsoleCommandResponse extends BaseToolResponse {
  command?: string;
  result?: unknown;
  info?: string;
}

export interface VerifyEnvironmentResponse extends BaseToolResponse {
  exists?: boolean;
  count?: number;
  actual?: number;
  method?: string;
}
