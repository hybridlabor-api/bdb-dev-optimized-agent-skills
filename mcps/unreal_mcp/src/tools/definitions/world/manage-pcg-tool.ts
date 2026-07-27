import { commonSchemas } from '../../catalog/tool-definition-utils.js';
import type { ToolDefinition } from '../shared/tool-definition.js';
import { PCG_ACTIONS } from '../shared/action-sets.js';

export const managePcgToolDefinition: ToolDefinition = {
    name: 'manage_pcg',
    category: 'world',
    description: 'Create, edit, execute, and configure PCG graphs: graph assets, input/sampler/filter/spawner nodes, pin connections, node settings, and partition grid size.',
    inputSchema: {
      type: 'object',
      properties: {
        action: {
          type: 'string',
          enum: [...PCG_ACTIONS],
          description: 'PCG graph action to perform'
        },
        graphPath: { type: 'string', description: 'PCG graph asset path (e.g., /Game/PCG/PCG_MyGraph).' },
        parentGraphPath: { type: 'string', description: 'Parent PCG graph asset path for subgraph insertion.' },
        subgraphPath: { type: 'string', description: 'PCG subgraph asset path used by subgraph nodes.' },
        assetPath: commonSchemas.assetPath,
        path: commonSchemas.directoryPath,
        name: commonSchemas.name,
        nodeType: { type: 'string', description: 'PCG node type alias or UPCGSettings class path/name.' },
        settingsClass: { type: 'string', description: 'UPCGSettings class path/name for the PCG node.' },
        nodeId: commonSchemas.nodeId,
        nodeName: commonSchemas.nodeName,
        title: commonSchemas.stringProp,
        sourceNodeId: commonSchemas.sourceNodeId,
        targetNodeId: commonSchemas.targetNodeId,
        sourcePin: commonSchemas.sourcePin,
        targetPin: commonSchemas.targetPin,
        inputName: commonSchemas.pinName,
        outputName: commonSchemas.pinName,
        actorName: commonSchemas.actorName,
        componentName: commonSchemas.componentName,
        componentPath: { type: 'string', description: 'Component path/name for PCG execution.' },
        classPath: commonSchemas.stringProp,
        actorClass: commonSchemas.stringProp,
        meshPath: commonSchemas.meshPath,
        texturePath: commonSchemas.texturePath,
        createComponent: commonSchemas.booleanProp,
        force: commonSchemas.booleanProp,
        wait: commonSchemas.booleanProp,
        gridSize: commonSchemas.numberProp,
        scope: { type: 'string', enum: ['world', 'component'], description: 'Partition grid target scope.' },
        settings: { type: 'object', description: 'Node settings keyed by reflected PCG settings property name.' },
        x: commonSchemas.numberProp,
        y: commonSchemas.numberProp,
        posX: commonSchemas.numberProp,
        posY: commonSchemas.numberProp,
        save: commonSchemas.save,
        overwrite: commonSchemas.overwrite,
        timeoutMs: commonSchemas.numberProp
      },
      required: ['action']
    },
    outputSchema: {
      type: 'object',
      properties: {
        ...commonSchemas.outputBase,
        graphPath: commonSchemas.assetPath,
        parentGraphPath: commonSchemas.assetPath,
        subgraphPath: commonSchemas.assetPath,
        assetPath: commonSchemas.assetPath,
        name: commonSchemas.stringProp,
        nodeId: commonSchemas.nodeId,
        nodeName: commonSchemas.nodeName,
        title: commonSchemas.stringProp,
        nodeType: commonSchemas.stringProp,
        sourceNodeId: commonSchemas.sourceNodeId,
        targetNodeId: commonSchemas.targetNodeId,
        sourcePin: commonSchemas.sourcePin,
        targetPin: commonSchemas.targetPin,
        settingsApplied: commonSchemas.numberProp,
        actorName: commonSchemas.actorName,
        componentName: commonSchemas.componentName,
        componentPath: commonSchemas.stringProp,
        taskId: commonSchemas.numberProp,
        gridSize: commonSchemas.numberProp,
        previousGridSize: commonSchemas.numberProp,
        saved: commonSchemas.booleanProp,
        created: commonSchemas.booleanProp
      }
    }
  };
