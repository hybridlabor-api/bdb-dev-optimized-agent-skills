import { commonSchemas } from '../../../catalog/tool-definition-utils.js';

export const manageAiNavigationProperties = {
agentRadius: { type: 'number', description: 'Navigation agent radius (default: 35).' },
agentHeight: { type: 'number', description: 'Navigation agent height (default: 144).' },
agentStepHeight: { type: 'number', description: 'Maximum step height agent can climb (default: 35).' },
agentMaxSlope: { type: 'number', description: 'Maximum slope angle in degrees (default: 44).' },
cellSize: { type: 'number', description: 'NavMesh cell size (default: 19).' },
cellHeight: { type: 'number', description: 'NavMesh cell height (default: 10).' },
tileSizeUU: { type: 'number', description: 'NavMesh tile size in UU (default: 1000).' },
minRegionArea: { type: 'number', description: 'Minimum region area to keep.' },
mergeRegionSize: { type: 'number', description: 'Region merge threshold.' },
maxSimplificationError: { type: 'number', description: 'Edge simplification error.' },
areaClass: commonSchemas.areaClass,
failsafeExtent: {
          type: 'object',
          properties: commonSchemas.vector3.properties,
          description: 'Failsafe extent for nav modifier when actor has no collision.'
        },
areaCost: { type: 'number', description: 'Pathfinding cost multiplier for area (1.0 = normal).' },
startPoint: {
          type: 'object',
          properties: commonSchemas.vector3.properties,
          description: 'Start point of navigation link (relative to actor).'
        },
endPoint: {
          type: 'object',
          properties: commonSchemas.vector3.properties,
          description: 'End point of navigation link (relative to actor).'
        },
direction: {
          type: 'string',
          enum: ['BothWays', 'LeftToRight', 'RightToLeft'],
          description: 'Link traversal direction.'
        },
snapRadius: { type: 'number', description: 'Snap radius for link endpoints (default: 30).' },
linkEnabled: { type: 'boolean', description: 'Whether the link is enabled.' },
linkType: {
          type: 'string',
          enum: ['simple', 'smart'],
          description: 'Type of navigation link.'
        },
enabledAreaClass: { type: 'string', description: 'Area class when smart link is enabled.' },
disabledAreaClass: { type: 'string', description: 'Area class when smart link is disabled.' },
broadcastRadius: { type: 'number', description: 'Radius for state change broadcast.' },
broadcastInterval: { type: 'number', description: 'Interval for state change broadcast (0 = single).' },
bCreateBoxObstacle: { type: 'boolean', description: 'Add box obstacle during nav generation.' },
obstacleOffset: {
          type: 'object',
          properties: commonSchemas.vector3.properties,
          description: 'Offset of simple box obstacle.'
        },
obstacleExtent: {
          type: 'object',
          properties: commonSchemas.vector3.properties,
          description: 'Extent of simple box obstacle.'
        },
obstacleAreaClass: { type: 'string', description: 'Area class for box obstacle.' },
save: commonSchemas.save
};
