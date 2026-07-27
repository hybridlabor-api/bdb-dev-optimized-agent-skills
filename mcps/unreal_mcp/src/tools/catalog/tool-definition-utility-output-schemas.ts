export const outputAndGeometryCommonSchemas = {
  outputBase: {
    success: { type: 'boolean' },
    message: { type: 'string' },
    error: { type: ['string', 'null'] }
  },
  outputWithPath: {
    success: { type: 'boolean' },
    message: { type: 'string' },
    error: { type: ['string', 'null'] },
    path: { type: 'string' },
    assetPath: { type: 'string' }
  },
  outputWithActor: {
    success: { type: 'boolean' },
    message: { type: 'string' },
    error: { type: ['string', 'null'] },
    actor: {
      type: 'object',
      properties: {
        id: { type: 'string' },
        name: { type: 'string' },
        path: { type: 'string' }
      }
    },
    actorPath: { type: 'string' }
  },
  outputWithNodeId: {
    success: { type: 'boolean' },
    message: { type: 'string' },
    error: { type: ['string', 'null'] },
    nodeId: { type: 'string' }
  },

  dimensions: {
    type: 'object',
    properties: {
      width: { type: 'number' },
      height: { type: 'number' },
      depth: { type: 'number' }
    },
    description: '3D dimensions (width, height, depth).'
  },
  size2D: {
    type: 'object',
    properties: {
      width: { type: 'number' },
      height: { type: 'number' }
    },
    description: '2D dimensions (width, height).'
  },
  extent: {
    type: 'object',
    properties: {
      x: { type: 'number' },
      y: { type: 'number' },
      z: { type: 'number' }
    },
    description: '3D extent (half-size).'
  },

  width: { type: 'number', description: 'Width value.' },
  height: { type: 'number', description: 'Height value.' },
  depth: { type: 'number', description: 'Depth value.' },
  radius: { type: 'number', description: 'Radius value.' },
  intensity: { type: 'number', description: 'Intensity value.' },
  angle: { type: 'number', description: 'Angle in degrees.' },
  strength: { type: 'number', description: 'Strength or weight.' },
  speed: { type: 'number', description: 'Speed value.' },
  duration: { type: 'number', description: 'Duration in seconds.' },
  distance: { type: 'number', description: 'Distance value.' },

  floatRange: {
    type: 'object',
    properties: {
      min: { type: 'number' },
      max: { type: 'number' }
    },
    description: 'Range of float values.'
  },
  intRange: {
    type: 'object',
    properties: {
      min: { type: 'integer' },
      max: { type: 'integer' }
    },
    description: 'Range of integer values.'
  },
  bounds: {
    type: 'object',
    properties: {
      min: {
        type: 'object',
        properties: {
          x: { type: 'number' },
          y: { type: 'number' },
          z: { type: 'number' }
        }
      },
      max: {
        type: 'object',
        properties: {
          x: { type: 'number' },
          y: { type: 'number' },
          z: { type: 'number' }
        }
      }
    },
    description: 'Bounding box (min, max vectors).'
  }
};
