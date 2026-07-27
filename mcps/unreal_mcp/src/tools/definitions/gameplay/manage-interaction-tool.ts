import { commonSchemas } from '../../catalog/tool-definition-utils.js';
import type { ToolDefinition } from '../shared/tool-definition.js';

export const manageInteractionToolDefinition: ToolDefinition = {
    name: 'manage_interaction',
    category: 'gameplay',
    description: 'Create interactive objects: doors, switches, chests, levers. Set up destructible meshes and trigger volumes.',
    inputSchema: {
      type: 'object',
      properties: {
        action: {
          type: 'string',
          enum: [
            'create_interaction_component',
            'configure_interaction_trace',
            'configure_interaction_widget',
            'add_interaction_events',
            'create_interactable_interface',
            'create_door_actor',
            'configure_door_properties',
            'create_switch_actor',
            'configure_switch_properties',
            'create_chest_actor',
            'configure_chest_properties',
            'create_lever_actor',
            'setup_destructible_mesh',
            'configure_destruction_levels',
            'configure_destruction_effects',
            'configure_destruction_damage',
            'add_destruction_component',
            'create_trigger_actor',
            'configure_trigger_events',
            'configure_trigger_filter',
            'configure_trigger_response',
            'get_interaction_info'
          ],
          description: 'The interaction action to perform.'
        },
        name: commonSchemas.name,
        folder: commonSchemas.directoryPath,
        blueprintPath: commonSchemas.blueprintPath,
        actorName: commonSchemas.actorName,
        componentName: commonSchemas.componentName,
        traceType: { type: 'string', enum: ['line', 'sphere', 'box'], description: 'Type of interaction trace.' },
        traceDistance: commonSchemas.traceDistance,
        traceRadius: commonSchemas.traceRadius,
        widgetClass: commonSchemas.widgetClass,
        showOnHover: { type: 'boolean', description: 'Show widget when hovering.' },
        showPromptText: { type: 'boolean', description: 'Show interaction prompt text.' },
        promptTextFormat: { type: 'string', description: 'Format string for prompt (e.g., "Press {Key} to {Action}").' },
        doorPath: { type: 'string', description: 'Path to door actor blueprint.' },
        openAngle: { type: 'number', description: 'Door open rotation angle in degrees.' },
        openTime: { type: 'number', description: 'Time to open/close door in seconds.' },
        locked: commonSchemas.locked,
        autoClose: { type: 'boolean', description: 'Automatically close after opening.' },
        autoCloseDelay: { type: 'number', description: 'Delay before auto-close in seconds.' },
        requiresKey: { type: 'boolean', description: 'Whether interaction requires a key item.' },
        switchPath: { type: 'string', description: 'Path to switch actor blueprint.' },
        switchType: { type: 'string', enum: ['button', 'lever', 'pressure_plate', 'toggle'], description: 'Type of switch.' },
        resetTime: { type: 'number', description: 'Time to reset switch in seconds.' },
        chestPath: { type: 'string', description: 'Path to chest actor blueprint.' },
        lootTablePath: commonSchemas.lootTablePath,
        triggerPath: { type: 'string', description: 'Path to trigger actor blueprint.' },
        triggerShape: { type: 'string', enum: ['box', 'sphere', 'capsule'], description: 'Shape of trigger volume.' },
        canToggle: commonSchemas.booleanProp
      },
      required: ['action']
    },
    outputSchema: {
      type: 'object',
      properties: {
        success: commonSchemas.booleanProp,
        message: commonSchemas.stringProp,
        assetPath: commonSchemas.assetPath,
        blueprintPath: commonSchemas.blueprintPath,
        interfacePath: { type: 'string', description: 'Path to created interface.' },
        componentAdded: { type: 'boolean', description: 'Whether component was added.' },
        interactionInfo: {
          type: 'object',
          properties: {
            assetType: { type: 'string', enum: ['Door', 'Switch', 'Chest', 'Lever', 'Trigger', 'Destructible', 'Component'] },
            isLocked: commonSchemas.booleanProp,
            isOpen: commonSchemas.booleanProp,
            health: commonSchemas.numberProp,
            maxHealth: commonSchemas.numberProp,
            interactionEnabled: commonSchemas.booleanProp,
            triggerShape: commonSchemas.stringProp,
            destructionLevel: commonSchemas.numberProp
          },
          description: 'Interaction system info (for get_interaction_info).'
        },
        error: commonSchemas.stringProp
      }
    }
  };
