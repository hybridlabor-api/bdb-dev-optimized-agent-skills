import { commonSchemas } from '../../catalog/tool-definition-utils.js';
import type { ToolDefinition } from '../shared/tool-definition.js';
import { VOLUME_ACTIONS } from '../shared/action-sets.js';

export const manageLevelStructureToolDefinition: ToolDefinition = {
    name: 'manage_level_structure',
    category: 'world',
    description: 'Structure worlds: levels, sublevels, World Partition, streaming, data layers, HLOD, level instances, trigger/blocking/physics/audio/post-process volumes, and nav bounds.',
    inputSchema: {
      type: 'object',
      properties: {
        action: {
          type: 'string',
          enum: [
            'create_level', 'create_sublevel', 'configure_level_streaming',
            'set_streaming_distance', 'configure_level_bounds',
            'enable_world_partition', 'configure_grid_size', 'create_data_layer',
            'assign_actor_to_data_layer', 'configure_hlod_layer', 'create_minimap_volume',
            'open_level_blueprint', 'add_level_blueprint_node', 'connect_level_blueprint_nodes',
            'create_level_instance', 'create_packed_level_actor',
            'get_level_structure_info'
          ,
            ...VOLUME_ACTIONS],
          description: 'Level structure action to perform.'
        },
        levelName: commonSchemas.stringProp,
        levelPath: commonSchemas.levelPath,
        parentLevel: commonSchemas.parentLevel,
        bCreateWorldPartition: { type: 'boolean', description: 'Create with World Partition enabled.' },
        bUseExternalActors: { type: 'boolean', description: 'Enable One File Per Actor (OFPA/External Actors) for Data Layer compatibility. Automatically enabled when bCreateWorldPartition is true.' },
        sublevelName: commonSchemas.sublevelName,
        sublevelPath: commonSchemas.levelPath,
        streamingMethod: {
          type: 'string',
          enum: ['Blueprint', 'AlwaysLoaded', 'Disabled'],
          description: 'Level streaming method.'
        },
        bShouldBeVisible: { type: 'boolean', description: 'Level should be visible when loaded.' },
        bShouldBlockOnLoad: { type: 'boolean', description: 'Block game until level is loaded.' },
        bDisableDistanceStreaming: { type: 'boolean', description: 'Disable distance-based streaming.' },
        streamingDistance: { type: 'number', description: 'Distance/radius for streaming volume (creates ALevelStreamingVolume).' },
        streamingUsage: {
          type: 'string',
          enum: ['Loading', 'LoadingAndVisibility', 'VisibilityBlockingOnLoad', 'BlockingOnLoad', 'LoadingNotVisible'],
          description: 'Streaming volume usage mode (default: LoadingAndVisibility).'
        },
        createVolume: { type: 'boolean', description: 'Create a streaming volume (true) or just report existing volumes (false). Default: true.' },
        boundsOrigin: {
          type: 'object',
          properties: {
            x: commonSchemas.numberProp, y: commonSchemas.numberProp, z: commonSchemas.numberProp
          },
          description: 'Origin of level bounds.'
        },
        boundsExtent: {
          type: 'object',
          properties: {
            x: commonSchemas.numberProp, y: commonSchemas.numberProp, z: commonSchemas.numberProp
          },
          description: 'Extent of level bounds.'
        },
        bAutoCalculateBounds: { type: 'boolean', description: 'Auto-calculate bounds from content.' },
        bEnableWorldPartition: { type: 'boolean', description: 'Enable World Partition for level.' },
        gridCellSize: { type: 'number', description: 'World Partition grid cell size.' },
        loadingRange: { type: 'number', description: 'Loading range for grid cells.' },
        dataLayerName: commonSchemas.dataLayerName,
        bIsInitiallyVisible: { type: 'boolean', description: 'Data layer initially visible.' },
        bIsInitiallyLoaded: { type: 'boolean', description: 'Data layer initially loaded.' },
        dataLayerType: {
          type: 'string',
          enum: ['Runtime', 'Editor'],
          description: 'Type of data layer.'
        },
        actorName: commonSchemas.actorName,
        actorPath: commonSchemas.actorPath,
        hlodLayerName: { type: 'string', description: 'Name of the HLOD layer.' },
        hlodLayerPath: commonSchemas.hlodLayerPath,
        bIsSpatiallyLoaded: { type: 'boolean', description: 'HLOD is spatially loaded.' },
        cellSize: { type: 'number', description: 'HLOD cell size.' },
        loadingDistance: { type: 'number', description: 'HLOD loading distance.' },
        volumeName: commonSchemas.volumeName,
        volumeLocation: {
          type: 'object',
          properties: {
            x: commonSchemas.numberProp, y: commonSchemas.numberProp, z: commonSchemas.numberProp
          },
          description: 'Location of the volume.'
        },
        volumeExtent: {
          type: 'object',
          properties: {
            x: commonSchemas.numberProp, y: commonSchemas.numberProp, z: commonSchemas.numberProp
          },
          description: 'Extent of the volume.'
        },
        nodeClass: commonSchemas.nodeClass,
        nodePosition: {
          type: 'object',
          properties: {
            x: commonSchemas.numberProp, y: commonSchemas.numberProp
          },
          description: 'Position of node in graph.'
        },
        nodeName: commonSchemas.nodeName,
        sourceNodeName: commonSchemas.sourceNode,
        sourcePinName: commonSchemas.sourcePin,
        targetNodeName: commonSchemas.targetNode,
        targetPinName: commonSchemas.targetPin,
        levelInstanceName: commonSchemas.levelInstanceName,
        levelAssetPath: { type: 'string', description: 'Path to the level asset for instancing.' },
        instanceLocation: {
          type: 'object',
          properties: {
            x: commonSchemas.numberProp, y: commonSchemas.numberProp, z: commonSchemas.numberProp
          },
          description: 'Location of the level instance.'
        },
        instanceRotation: {
          type: 'object',
          properties: {
            pitch: commonSchemas.numberProp, yaw: commonSchemas.numberProp, roll: commonSchemas.numberProp
          },
          description: 'Rotation of the level instance.'
        },
        instanceScale: {
          type: 'object',
          properties: {
            x: commonSchemas.numberProp, y: commonSchemas.numberProp, z: commonSchemas.numberProp
          },
          description: 'Scale of the level instance.'
        },
        packedLevelName: { type: 'string', description: 'Name for the packed level actor.' },
        bPackBlueprints: { type: 'boolean', description: 'Include blueprints in packed level.' },
        bPackStaticMeshes: { type: 'boolean', description: 'Include static meshes in packed level.' },
        save: commonSchemas.save
      ,
        // For add_*_volume actions that attach to existing actors
                location: {
                  type: 'object',
                  properties: {
                    x: commonSchemas.numberProp, y: commonSchemas.numberProp, z: commonSchemas.numberProp
                  },
                  description: 'World location for the volume.'
                },
        rotation: {
                  type: 'object',
                  properties: {
                    pitch: commonSchemas.numberProp, yaw: commonSchemas.numberProp, roll: commonSchemas.numberProp
                  },
                  description: 'Rotation of the volume.'
                },
        extent: {
                  type: 'object',
                  properties: {
                    x: commonSchemas.numberProp, y: commonSchemas.numberProp, z: commonSchemas.numberProp
                  },
                  description: 'Extent (half-size) of the volume in each axis.'
                },
        sphereRadius: { type: 'number', description: 'Radius for sphere trigger volumes.' },
        capsuleRadius: { type: 'number', description: 'Radius for capsule trigger volumes.' },
        capsuleHalfHeight: { type: 'number', description: 'Half-height for capsule trigger volumes.' },
        boxExtent: {
                  type: 'object',
                  properties: {
                    x: commonSchemas.numberProp, y: commonSchemas.numberProp, z: commonSchemas.numberProp
                  },
                  description: 'Extent for box trigger volumes.'
        },
        bPainCausing: { type: 'boolean', description: 'Whether the volume causes pain/damage.' },
        damagePerSec: { type: 'number', description: 'Damage per second for pain volumes.' },
        bWaterVolume: { type: 'boolean', description: 'Whether this is a water volume.' },
        fluidFriction: { type: 'number', description: 'Fluid friction for physics volumes.' },
        terminalVelocity: { type: 'number', description: 'Terminal velocity in the volume.' },
        priority: commonSchemas.priority,
        bEnabled: { type: 'boolean', description: 'Whether the audio volume is enabled.' },
        reverbVolume: { type: 'number', description: 'Volume level for reverb (0.0-1.0).' },
        fadeTime: commonSchemas.fadeTime,
        cullDistances: {
                  type: 'array',
                  items: {
                    type: 'object',
                    properties: {
                      size: { type: 'number', description: 'Object size threshold.' },
                      cullDistance: { type: 'number', description: 'Distance at which to cull.' }
                    }
                  },
                  description: 'Array of size/distance pairs for cull distance volumes.'
                },
        bUnbound: { type: 'boolean', description: 'Whether post process volume affects entire world.' },
        blendRadius: { type: 'number', description: 'Blend radius for post process volume.' },
        blendWeight: { type: 'number', description: 'Blend weight (0.0-1.0) for post process.' },
        filter: commonSchemas.filter,
        volumeType: { type: 'string', description: 'Type filter for get_volumes_info (e.g., "Trigger", "Physics").' },
        bBlockOnSlowStreaming: commonSchemas.booleanProp,
        bounds: commonSchemas.objectProp,
        createIfMissing: commonSchemas.booleanProp,
        gridName: commonSchemas.stringProp,
        layerType: commonSchemas.stringProp
      },
      required: ['action']
    },
    outputSchema: {
      type: 'object',
      properties: {
        success: commonSchemas.booleanProp,
        message: commonSchemas.stringProp,
        levelPath: commonSchemas.levelPath,
        sublevelPath: commonSchemas.levelPath,
        dataLayerName: { type: 'string', description: 'Name of created data layer.' },
        hlodLayerPath: commonSchemas.hlodLayerPath,
        nodeName: commonSchemas.nodeName,
        levelInstanceName: commonSchemas.levelInstanceName,
        levelStructureInfo: {
          type: 'object',
          properties: {
            currentLevel: commonSchemas.stringProp,
            sublevelCount: commonSchemas.numberProp,
            sublevels: {
              type: 'array',
              items: commonSchemas.stringProp
            },
            worldPartitionEnabled: commonSchemas.booleanProp,
            gridCellSize: commonSchemas.numberProp,
            dataLayers: {
              type: 'array',
              items: commonSchemas.stringProp
            },
            hlodLayers: {
              type: 'array',
              items: commonSchemas.stringProp
            },
            levelInstances: {
              type: 'array',
              items: commonSchemas.stringProp
            }
          },
          description: 'Level structure information (for get_level_structure_info).'
        },
        error: commonSchemas.stringProp
      }
    }
  };
