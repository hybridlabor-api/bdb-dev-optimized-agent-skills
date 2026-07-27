import type { ToolDefinition } from '../../shared/tool-definition.js';
import { manageNetworkingInputSchema } from './manage-networking-input-schema.js';
import { manageNetworkingOutputSchema } from './manage-networking-output-schema.js';

export const manageNetworkingToolDefinition: ToolDefinition = {
  name: 'manage_networking',
  category: 'utility',
  description: 'Configure multiplayer and player flow: replication, RPCs, authority/relevancy, network prediction, sessions, split-screen, LAN/voice chat, game framework classes, match rules, and input mappings.',
  inputSchema: manageNetworkingInputSchema,
  outputSchema: manageNetworkingOutputSchema
};
