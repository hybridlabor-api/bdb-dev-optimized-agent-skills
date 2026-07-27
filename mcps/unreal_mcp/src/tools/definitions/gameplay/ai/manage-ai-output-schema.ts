import { commonSchemas } from '../../../catalog/tool-definition-utils.js';

export const manageAiOutputSchema = {
      type: 'object',
      properties: {
        ...commonSchemas.outputBase,
        assetPath: commonSchemas.assetPath,
        controllerPath: commonSchemas.stringProp,
        behaviorTreePath: commonSchemas.stringProp,
        blackboardPath: commonSchemas.stringProp,
        queryPath: commonSchemas.stringProp,
        stateTreePath: commonSchemas.stringProp,
        definitionPath: commonSchemas.stringProp,
        configPath: commonSchemas.stringProp,
        nodeId: commonSchemas.nodeId,
        keyIndex: commonSchemas.integerProp,
        testIndex: commonSchemas.integerProp,
        slotIndex: commonSchemas.integerProp,
        aiInfo: {
          type: 'object',
          properties: {
            controllerClass: commonSchemas.stringProp,
            assignedBehaviorTree: commonSchemas.stringProp,
            assignedBlackboard: commonSchemas.stringProp,
            rootGraphBlackboard: commonSchemas.stringProp,
            rootGraphBlackboardMatchesAssigned: commonSchemas.booleanProp,
            blackboardKeys: commonSchemas.arrayOfObjects,
            btNodeCount: commonSchemas.integerProp,
            rootDecoratorCount: commonSchemas.integerProp,
            rootDecoratorClasses: commonSchemas.arrayOfStrings,
            rootDecorators: commonSchemas.arrayOfObjects,
            childDecorators: commonSchemas.arrayOfObjects,
            services: commonSchemas.arrayOfObjects,
            perceptionSenses: commonSchemas.arrayOfStrings,
            teamId: commonSchemas.integerProp,
            stateTreeStates: commonSchemas.arrayOfStrings,
            smartObjectSlots: commonSchemas.numberProp,
            massTraits: commonSchemas.arrayOfStrings
          },
          description: 'AI configuration info (for get_ai_info).'
        },
        tree: {
          type: 'object',
          properties: {
            assetPath: commonSchemas.assetPath,
            // Nullable: serializer emits JSON null when the tree has no BlackboardAsset assigned.
            blackboardAsset: { type: ['string', 'null'], description: 'Blackboard asset path, or null if the tree has no blackboard assigned.' },
            hasRootNode: commonSchemas.booleanProp,
            nodeCount: commonSchemas.integerProp,
            executionNodeCount: commonSchemas.integerProp,
            rootDecorators: commonSchemas.arrayOfObjects,
            rootDecoratorOpsRaw: commonSchemas.arrayOfObjects,
            // Nullable: serializer emits JSON null for an empty tree (RootNode == nullptr), matching the success + rootNode:null contract.
            rootNode: { type: ['object', 'null'], description: 'Recursive root node hierarchy, or null for an empty tree (no RootNode).' }
          },
          description: 'Navigable Behavior Tree hierarchy (for get_tree): recursive rootNode with ordered children[], per-edge entryDecorators[]/entryDecoratorOpsRaw[], composite/task services[], top-level rootDecorators[]/rootDecoratorOpsRaw[], and per-node keyProperties{}.'
        },
        error: commonSchemas.stringProp
      }
    };
