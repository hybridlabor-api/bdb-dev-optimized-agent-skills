import { addActionParamsSchema } from '../catalog/tool-definition-utils.js';
import { controlActorToolDefinition } from './control-actor-tool.js';
import { controlEditorToolDefinition } from './control-editor-tool.js';
import type { ToolDefinition } from './core-tool-definition.js';
import { inspectToolDefinition } from './inspect-tool.js';
import { manageAssetToolDefinition } from './manage-asset-tool.js';
import { manageLevelToolDefinition } from './manage-level-tool.js';
import { manageToolsToolDefinition } from './manage-tools-tool.js';
import { systemControlToolDefinition } from './system-control-tool.js';

export type { ToolDefinition } from './core-tool-definition.js';

export const coreToolDefinitions: ToolDefinition[] = [
  manageToolsToolDefinition,
  manageAssetToolDefinition,
  controlActorToolDefinition,
  controlEditorToolDefinition,
  manageLevelToolDefinition,
  systemControlToolDefinition,
  inspectToolDefinition
];

addActionParamsSchema(coreToolDefinitions);
