import { commonSchemas } from '../../../catalog/tool-definition-utils.js';

export const manageAiRuntimeProperties = {
componentName: commonSchemas.componentName,
location: {
                  type: 'object',
                  properties: {
                    x: commonSchemas.numberProp, y: commonSchemas.numberProp, z: commonSchemas.numberProp
                  },
                  description: 'World location for nav link proxy.'
                },
rotation: {
                  type: 'object',
                  properties: {
                    pitch: commonSchemas.numberProp, yaw: commonSchemas.numberProp, roll: commonSchemas.numberProp
                  },
                  description: 'Rotation for nav link proxy.'
                },
assetPath: commonSchemas.assetPath,
childNodeId: commonSchemas.nodeId,
comment: commonSchemas.stringProp,
enableDamage: commonSchemas.booleanProp,
enableHearing: commonSchemas.booleanProp,
enableSight: commonSchemas.booleanProp,
enabled: commonSchemas.booleanProp,
focusActorName: commonSchemas.actorName,
hearingRange: commonSchemas.numberProp,
loseSightRadius: commonSchemas.numberProp,
nodeType: commonSchemas.stringProp,
offset: commonSchemas.vector3,
parentStateName: commonSchemas.stringProp,
peripheralVisionAngle: commonSchemas.numberProp,
properties: commonSchemas.objectProp,
savePath: commonSchemas.savePath,
sightRadius: commonSchemas.numberProp,
spawnCount: commonSchemas.numberProp,
stateType: commonSchemas.stringProp,
triggerType: commonSchemas.stringProp,
value: commonSchemas.value,
x: commonSchemas.numberProp,
y: commonSchemas.numberProp
};
