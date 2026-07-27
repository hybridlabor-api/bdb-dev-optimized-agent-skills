export const coreCommonSchemas = {
  actionParams: {
    type: 'object',
    description: 'Optional action-specific parameters. These are merged with top-level arguments before routing for clients that cannot send arbitrary top-level fields.',
    additionalProperties: true
  },

  location: {
    type: 'object',
    properties: {
      x: { type: 'number' },
      y: { type: 'number' },
      z: { type: 'number' }
    },
    description: '3D location (x, y, z).'
  },
  rotation: {
    type: 'object',
    properties: {
      pitch: { type: 'number' },
      yaw: { type: 'number' },
      roll: { type: 'number' }
    },
    description: '3D rotation (pitch, yaw, roll).'
  },
  scale: {
    type: 'object',
    properties: {
      x: { type: 'number' },
      y: { type: 'number' },
      z: { type: 'number' }
    },
    description: '3D scale (x, y, z).'
  },
  vector3: {
    type: 'object',
    properties: {
      x: { type: 'number' },
      y: { type: 'number' },
      z: { type: 'number' }
    },
    description: '3D vector.'
  },
  vector2: {
    type: 'object',
    properties: {
      x: { type: 'number' },
      y: { type: 'number' }
    },
    description: '2D vector.'
  },

  color: {
    type: 'array',
    items: { type: 'number' },
    description: 'RGBA color as an array [r, g, b, a].'
  },
  colorObject: {
    type: 'object',
    properties: {
      r: { type: 'number' },
      g: { type: 'number' },
      b: { type: 'number' },
      a: { type: 'number' }
    },
    description: 'RGBA color as an object.'
  },

  assetPath: { type: 'string', description: 'Asset path (e.g., /Game/Path/Asset).' },
  blueprintPath: { type: 'string', description: 'Blueprint asset path.' },
  meshPath: { type: 'string', description: 'Mesh asset path.' },
  texturePath: { type: 'string', description: 'Texture asset path.' },
  materialPath: { type: 'string', description: 'Material asset path.' },
  soundPath: { type: 'string', description: 'Sound asset path.' },
  animationPath: { type: 'string', description: 'Animation asset path.' },
  levelPath: { type: 'string', description: 'Level asset path.' },
  skeletonPath: { type: 'string', description: 'Skeleton asset path.' },
  skeletalMeshPath: { type: 'string', description: 'Skeletal mesh path.' },
  niagaraPath: { type: 'string', description: 'Niagara system path.' },
  widgetPath: { type: 'string', description: 'Widget blueprint path.' },

  physicsAssetPath: { type: 'string', description: 'Path to physics asset.' },
  morphTargetPath: { type: 'string', description: 'Path to morph target.' },
  clothAssetPath: { type: 'string', description: 'Path to cloth asset.' },
  iconPath: { type: 'string', description: 'Path to icon texture.' },
  itemDataPath: { type: 'string', description: 'Path to item data asset.' },
  gameplayAbilityPath: { type: 'string', description: 'Path to gameplay ability.' },
  gameplayEffectPath: { type: 'string', description: 'Path to gameplay effect.' },
  gameplayCuePath: { type: 'string', description: 'Path to gameplay cue.' },
  meshAssetPath: { type: 'string', description: 'Path to mesh asset.' },
  textureAssetPath: { type: 'string', description: 'Path to texture asset.' },
  materialAssetPath: { type: 'string', description: 'Path to material asset.' },
  soundAssetPath: { type: 'string', description: 'Path to sound asset.' },
  animationAssetPath: { type: 'string', description: 'Path to animation asset.' },
  blueprintAssetPath: { type: 'string', description: 'Path to blueprint asset.' },

  directoryPath: { type: 'string', description: 'Path to a directory.' },
  outputPath: { type: 'string', description: 'Output file or directory path.' },
  destinationPath: { type: 'string', description: 'Destination path for move/copy.' },
  savePath: { type: 'string', description: 'Path to save the asset.' },
  sourcePath: { type: 'string', description: 'Source path for import/move/copy.' },
  targetPath: { type: 'string', description: 'Target path for operations.' },
  directoryPathForCreation: { type: 'string', description: 'Directory path for asset creation.' },

  name: { type: 'string', description: 'Name identifier.' },
  newName: { type: 'string', description: 'New name for renaming.' },
  assetNameForCreation: { type: 'string', description: 'Name of the asset to create.' },
  actorName: { type: 'string', description: 'Name of the actor.' },
  actorNameInLevel: { type: 'string', description: 'Name of the actor in the level.' },
  childActorName: { type: 'string', description: 'Name of the child actor (for attach/detach operations).' },
  parentActorName: { type: 'string', description: 'Name of the parent actor (for attach operations).' },
  componentName: { type: 'string', description: 'Name of the component.' },
  boneName: { type: 'string', description: 'Name of the bone.' },
  socketName: { type: 'string', description: 'Name of the socket.' },
  slotName: { type: 'string', description: 'Name of the slot.' },
  parameterName: { type: 'string', description: 'Name of the parameter.' },
  propertyName: { type: 'string', description: 'Name of the property.' },
  variableName: { type: 'string', description: 'Name of the variable.' },
  functionName: { type: 'string', description: 'Name of the function.' },
  eventName: { type: 'string', description: 'Name of the event.' },
  tagName: { type: 'string', description: 'Name of the tag.' },
  attributeName: { type: 'string', description: 'Name of the attribute.' },
  stateName: { type: 'string', description: 'Name of the state.' },

  nodeId: { type: 'string', description: 'ID of the node.' },
  sourceNodeId: { type: 'string', description: 'ID of the source node.' },
  targetNodeId: { type: 'string', description: 'ID of the target node.' },
  pinName: { type: 'string', description: 'Name of the pin.' },
  sourcePin: { type: 'string', description: 'Name of the source pin.' },
  targetPin: { type: 'string', description: 'Name of the target pin.' },
  graphName: { type: 'string', description: 'Name of the graph.' },
  nodeName: { type: 'string', description: 'Name of the node.' },

  booleanProp: { type: 'boolean' },
  numberProp: { type: 'number' },
  stringProp: { type: 'string' },
  integerProp: { type: 'integer' },
  objectProp: { type: 'object' },
  nullableObjectProp: { type: ['object', 'null'], description: 'Optional data object (null for error responses).' },
  arrayOfStrings: { type: 'array', items: { type: 'string' } },
  arrayOfNumbers: { type: 'array', items: { type: 'number' } },
  arrayOfObjects: { type: 'array', items: { type: 'object' } },
  value: { description: 'Generic value (any type).' },
  parentClass: { type: 'string', description: 'Path or name of the parent class.' },

  save: { type: 'boolean', description: 'Save the asset(s) after the operation.' },
  compile: { type: 'boolean', description: 'Compile the blueprint(s) after the operation.' },
  overwrite: { type: 'boolean', description: 'Overwrite if the asset/file already exists.' },
  recursive: { type: 'boolean', description: 'Perform the operation recursively.' },
  enabled: { type: 'boolean', description: 'Whether the item/feature is enabled.' },
  visible: { type: 'boolean', description: 'Whether the item/actor is visible.' },

  filter: { type: 'string', description: 'General search filter.' },
  tagFilter: { type: 'string', description: 'Filter by tags.' },
  classFilter: { type: 'string', description: 'Filter by class.' },
  resolution: { type: 'string', description: 'Resolution setting (e.g., 1024x1024).' }
};
