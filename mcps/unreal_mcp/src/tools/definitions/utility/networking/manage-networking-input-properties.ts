import { commonSchemas } from '../../../catalog/tool-definition-utils.js';

export const manageNetworkingInputProperties = {
contextPath: commonSchemas.assetPath,
actionPath: commonSchemas.assetPath,
actionName: { type: 'string', description: 'Legacy input action mapping name.' },
axisName: { type: 'string', description: 'Legacy input axis mapping name.' },
key: commonSchemas.stringProp,
scale: { type: 'number', description: 'Legacy input axis scale.' },
shift: { type: 'boolean', description: 'Require Shift for a legacy action mapping.' },
ctrl: { type: 'boolean', description: 'Require Ctrl for a legacy action mapping.' },
alt: { type: 'boolean', description: 'Require Alt for a legacy action mapping.' },
cmd: { type: 'boolean', description: 'Require Cmd for a legacy action mapping.' },
triggerType: commonSchemas.stringProp,
modifierType: commonSchemas.stringProp,
assetPath: commonSchemas.assetPath,
priority: { type: 'number', description: 'Priority for input mapping context (default: 0).' },
timeoutMs: commonSchemas.numberProp,
canRespawn: commonSchemas.booleanProp,
executeTravel: commonSchemas.booleanProp,
forceRespawn: commonSchemas.booleanProp,
localPlayerNum: commonSchemas.numberProp,
maxRespawns: commonSchemas.numberProp,
respawnLives: commonSchemas.numberProp,
scorePerDeath: commonSchemas.numberProp,
systemWide: commonSchemas.booleanProp,
variableName: commonSchemas.variableName,
winScore: commonSchemas.numberProp
};
