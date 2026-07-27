import type { Rotation3D, Vector3D } from './tool-base-types.js';

export interface ToolParameters {
  ListAssetsParams: {
    directory: string;
    recursive?: boolean;
  };

  ImportAssetParams: {
    sourcePath: string;
    destinationPath: string;
  };

  CreateMaterialParams: {
    name: string;
    path: string;
  };

  SpawnActorParams: {
    classPath: string;
    location?: Vector3D;
    rotation?: Rotation3D;
  };

  DeleteActorParams: {
    actorName: string;
  };

  ApplyForceParams: {
    actorName: string;
    force: Vector3D;
  };

  SpawnBlueprintParams: {
    blueprintPath: string;
    actorName?: string;
    location?: Vector3D;
    rotation?: Rotation3D;
  };

  SetTransformParams: {
    actorName: string;
    location?: Vector3D;
    rotation?: Rotation3D;
    scale?: Vector3D;
  };

  SetVisibilityParams: {
    actorName: string;
    visible: boolean;
  };

  ComponentParams: {
    actorName: string;
    componentType?: string;
    componentName?: string;
    properties?: Record<string, unknown>;
  };

  DuplicateActorParams: {
    actorName: string;
    newName?: string;
    offset?: Vector3D;
  };

  AttachActorParams: {
    childActor: string;
    parentActor: string;
  };

  DetachActorParams: {
    actorName: string;
  };

  TagActorParams: {
    actorName: string;
    tag: string;
  };

  FindByTagParams: {
    tag: string;
    matchType?: string;
  };

  FindByNameParams: {
    name: string;
  };

  BlueprintVariablesParams: {
    actorName: string;
    variables: Record<string, unknown>;
  };

  SnapshotActorParams: {
    actorName: string;
    snapshotName: string;
  };

  SetCameraParams: {
    location?: Vector3D;
    rotation?: Rotation3D;
  };

  SetViewModeParams: {
    mode: string;
  };

  ConsoleCommandParams: {
    command: string;
  };
}
