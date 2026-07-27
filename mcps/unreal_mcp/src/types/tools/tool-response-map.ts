import type { ConsolidatedToolParams } from './tool-consolidated-params.js';
import type {
  AnimationPhysicsResponse,
  BuildEnvironmentResponse,
  ConsoleCommandResponse,
  ControlActorResponse,
  ControlEditorResponse,
  CreateEffectResponse,
  ManageAssetResponse,
  ManageBlueprintResponse,
  ManageLevelResponse,
  SystemControlResponse,
  VerifyEnvironmentResponse,
} from './tool-response-types.js';

export interface ToolResponseMap {
  manage_asset: ManageAssetResponse;
  control_actor: ControlActorResponse;
  control_editor: ControlEditorResponse;
  manage_level: ManageLevelResponse;
  animation_physics: AnimationPhysicsResponse;
  create_effect: CreateEffectResponse;
  manage_blueprint: ManageBlueprintResponse;
  build_environment: BuildEnvironmentResponse;
  system_control: SystemControlResponse;
  console_command: ConsoleCommandResponse;
  verify_environment: VerifyEnvironmentResponse;
  list_assets: ManageAssetResponse;
  import_asset: ManageAssetResponse;
  spawn_actor: ControlActorResponse;
  delete_actor: ControlActorResponse;
  create_material: ManageAssetResponse;
  play_in_editor: ControlEditorResponse;
  stop_play_in_editor: ControlEditorResponse;
  set_camera: ControlEditorResponse;
}

export type ToolName = keyof ToolResponseMap;

export type GetToolResponse<T extends ToolName> = ToolResponseMap[T];

export type GetToolParams<T extends keyof ConsolidatedToolParams> = ConsolidatedToolParams[T];
