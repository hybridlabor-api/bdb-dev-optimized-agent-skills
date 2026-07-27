import { commonSchemas } from '../../catalog/tool-definition-utils.js';
import type { ToolDefinition } from '../shared/tool-definition.js';

export const manageLevelToolDefinition: ToolDefinition = {
    name: 'manage_level',
    category: 'core',
    description: 'Load/save levels, configure streaming, and build lighting.',
    inputSchema: {
      type: 'object',
      properties: {
        action: {
          type: 'string',
          enum: [
            'load', 'load_level', 'save', 'save_level', 'save_as', 'save_level_as', 'stream', 'unload', 'unload_level', 'create_level', 'create_light', 'build_lighting',
            'set_metadata',
            'export_level', 'import_level', 'list_levels', 'get_summary', 'delete', 'delete_level', 'validate_level',
            'add_sublevel', 'rename_level', 'duplicate_level', 'get_current_level'
          ],
          description: 'Action'
        },
        // Level path parameters
        levelPath: commonSchemas.levelPath,
        assetPath: commonSchemas.assetPath,
        levelPaths: commonSchemas.arrayOfStrings,
        levelName: commonSchemas.stringProp,
        path: commonSchemas.directoryPathForCreation,
        // Save/export/import paths
        savePath: commonSchemas.savePath,
        destinationPath: commonSchemas.destinationPath,
        overwrite: commonSchemas.overwrite,
        targetPath: commonSchemas.directoryPath,
        exportPath: commonSchemas.exportPath,
        packagePath: commonSchemas.directoryPath,
        sourcePath: commonSchemas.sourcePath,
        // Sublevel parameters
        sublevelPath: commonSchemas.levelPath,
        parentLevel: commonSchemas.parentLevel,
        parentPath: commonSchemas.directoryPath,
        streamingMethod: commonSchemas.stringProp,
        // Streaming control
        streaming: commonSchemas.booleanProp,
        shouldBeLoaded: commonSchemas.booleanProp,
        shouldBeVisible: commonSchemas.booleanProp,
        saveDirtyPackages: commonSchemas.booleanProp,
        // Light creation
        lightType: { type: 'string', enum: ['Directional', 'Point', 'Spot', 'Rect', 'DirectionalLight', 'PointLight', 'SpotLight', 'RectLight', 'directional', 'point', 'spot', 'rect'], description: 'Light type. Accepts short names (Point), class names (PointLight), or lowercase (point).' },
        intensity: commonSchemas.numberProp,
        color: commonSchemas.color,
        location: commonSchemas.location,
        rotation: commonSchemas.rotation,
        // Level creation
        template: commonSchemas.stringProp,
        useWorldPartition: commonSchemas.booleanProp,
        // Metadata & utilities
        metadata: commonSchemas.objectProp,
        newName: commonSchemas.stringProp,
        timeoutMs: commonSchemas.numberProp,
        name: commonSchemas.name,
        quality: commonSchemas.stringProp,
        subLevelPath: commonSchemas.levelPath
      },
      required: ['action']
    },
    outputSchema: {
      type: 'object',
      properties: {
        ...commonSchemas.outputBase,
        assetPath: commonSchemas.assetPath,
        emitterName: commonSchemas.stringProp,
        moduleName: commonSchemas.stringProp,
        niagaraInfo: commonSchemas.objectProp,
        validationResult: commonSchemas.objectProp
      }
    }
  };
