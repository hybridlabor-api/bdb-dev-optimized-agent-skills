import { commonSchemas } from '../../catalog/tool-definition-utils.js';
import type { ToolDefinition } from '../shared/tool-definition.js';

export const manageInventoryToolDefinition: ToolDefinition = {
    name: 'manage_inventory',
    category: 'gameplay',
    description: 'Create item data assets, inventory components, world pickups, loot tables, and crafting recipes.',
    inputSchema: {
      type: 'object',
      properties: {
        action: {
          type: 'string',
          enum: [
            'create_item_data_asset',
            'set_item_properties',
            'create_item_category',
            'assign_item_category',
            'create_inventory_component',
            'configure_inventory_slots',
            'add_inventory_functions',
            'configure_inventory_events',
            'set_inventory_replication',
            'create_pickup_actor',
            'configure_pickup_interaction',
            'configure_pickup_respawn',
            'configure_pickup_effects',
            'create_equipment_component',
            'define_equipment_slots',
            'configure_equipment_effects',
            'add_equipment_functions',
            'configure_equipment_visuals',
            'create_loot_table',
            'add_loot_entry',
            'configure_loot_drop',
            'set_loot_quality_tiers',
            'create_crafting_recipe',
            'configure_recipe_requirements',
            'create_crafting_station',
            'add_crafting_component',
            'configure_item_stacking',
            'set_item_icon',
            'add_recipe_ingredient',
            'remove_loot_entry',
            'configure_inventory_weight',
            'configure_station_recipes',
            'get_inventory_info'
          ],
          description: 'Inventory action to perform.'
        },
        name: commonSchemas.assetNameForCreation,
        path: commonSchemas.directoryPathForCreation,
        save: commonSchemas.save,
        blueprintPath: commonSchemas.blueprintPath,
        itemPath: commonSchemas.itemDataPath,
        iconPath: commonSchemas.iconPath,
        maxStackSize: commonSchemas.numberProp,
        stackable: commonSchemas.booleanProp,
        uniqueItems: commonSchemas.booleanProp,
        enableWeight: commonSchemas.booleanProp,
        encumberanceSystem: commonSchemas.booleanProp,
        encumberanceThreshold: commonSchemas.numberProp,
        categoryPath: { type: 'string', description: 'Path to item category asset.' },
        componentName: commonSchemas.componentName,
        slotCount: commonSchemas.numberProp,
        maxWeight: commonSchemas.numberProp,
        replicated: commonSchemas.replicated,
        replicationCondition: {
          type: 'string',
          enum: ['None', 'OwnerOnly', 'SkipOwner', 'SimulatedOnly', 'AutonomousOnly', 'Custom'],
          description: 'Replication condition for inventory.'
        },
        pickupPath: { type: 'string', description: 'Path to pickup actor Blueprint.' },
        interactionType: {
          type: 'string',
          enum: ['Overlap', 'Interact', 'Key', 'Hold'],
          description: 'How player picks up item.'
        },
        prompt: commonSchemas.prompt,
        respawnable: commonSchemas.booleanProp,
        respawnTime: commonSchemas.respawnTime,
        bobbing: { type: 'boolean', description: 'Enable bobbing animation.' },
        rotation: { type: 'boolean', description: 'Enable rotation animation.' },
        glowEffect: { type: 'boolean', description: 'Enable glow effect.' },
        slots: {
          type: 'array',
          items: commonSchemas.stringProp,
          description: 'Equipment slot names to configure.'
        },
        statModifiers: { type: 'boolean', description: 'Enable stat modifier support when equipped.' },
        abilityGrants: { type: 'boolean', description: 'Enable ability grant support when equipped.' },
        passiveEffects: { type: 'boolean', description: 'Enable passive effect support when equipped.' },
        attachToSocket: { type: 'boolean', description: 'Attach mesh to socket when equipped.' },
        lootTablePath: commonSchemas.lootTablePath,
        lootWeight: { type: 'number', description: 'Weight for drop chance calculation.' },
        minQuantity: { type: 'number', description: 'Minimum drop quantity.' },
        maxQuantity: { type: 'number', description: 'Maximum drop quantity.' },
        actorPath: { type: 'string', description: 'Path to actor Blueprint for loot drop.' },
        dropCount: { type: 'number', description: 'Number of drops to roll.' },
        dropRadius: { type: 'number', description: 'Radius for scattered drops.' },
        tiers: {
          type: 'array',
          items: {
            type: 'object',
            properties: {
              name: commonSchemas.stringProp,
              dropWeight: commonSchemas.numberProp
            }
          },
          description: 'Quality tier definitions.'
        },
        recipePath: commonSchemas.recipePath,
        outputItemPath: { type: 'string', description: 'Path to item produced by recipe.' },
        outputQuantity: { type: 'number', description: 'Quantity produced.' },
        craftTime: { type: 'number', description: 'Time in seconds to craft.' },
        ingredientItemPath: commonSchemas.itemDataPath,
        quantity: commonSchemas.numberProp,
        requiredLevel: { type: 'number', description: 'Required player level.' },
        requiredStation: { type: 'string', description: 'Required crafting station type.' },
        stationPath: commonSchemas.stringProp,
        recipePaths: commonSchemas.arrayOfStrings,
        craftingSpeedMultiplier: commonSchemas.numberProp,
        stationType: { type: 'string', description: 'Type of crafting station.' },
        defaultSocket: commonSchemas.socketName,
        dropOnDeath: commonSchemas.booleanProp,
        entryIndex: commonSchemas.numberProp,
        properties: commonSchemas.objectProp
      },
      required: ['action']
    },
    outputSchema: {
      type: 'object',
      properties: {
        ...commonSchemas.outputBase,
        assetPath: commonSchemas.assetPath,
        itemPath: commonSchemas.stringProp,
        categoryPath: commonSchemas.stringProp,
        pickupPath: commonSchemas.stringProp,
        lootTablePath: commonSchemas.stringProp,
        recipePath: commonSchemas.stringProp,
        stationPath: commonSchemas.stringProp,
        componentAdded: commonSchemas.booleanProp,
        slotCount: commonSchemas.integerProp,
        entryIndex: commonSchemas.integerProp,
        inventoryInfo: {
          type: 'object',
          properties: {
            assetType: { type: 'string', enum: ['Item', 'Inventory', 'Pickup', 'LootTable', 'Recipe', 'Station'] },
            itemProperties: {
              type: 'object',
              properties: {
                displayName: commonSchemas.stringProp,
                stackSize: commonSchemas.integerProp,
                weight: commonSchemas.numberProp,
                rarity: commonSchemas.stringProp,
                value: commonSchemas.numberProp
              }
            },
            inventorySlots: commonSchemas.numberProp,
            maxWeight: commonSchemas.numberProp,
            equipmentSlots: commonSchemas.arrayOfStrings,
            lootEntries: commonSchemas.numberProp,
            recipeIngredients: commonSchemas.arrayOfObjects,
            craftTime: commonSchemas.numberProp
          },
          description: 'Inventory system info (for get_inventory_info).'
        },
        error: commonSchemas.stringProp
      }
    }
  };
