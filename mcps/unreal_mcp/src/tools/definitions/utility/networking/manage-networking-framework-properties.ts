import { commonSchemas } from '../../../catalog/tool-definition-utils.js';

export const manageNetworkingFrameworkProperties = {
name: commonSchemas.name,
path: commonSchemas.directoryPathForCreation,
gameModeBlueprint: { type: 'string', description: 'Path to GameMode blueprint to configure.' },
parentClass: commonSchemas.parentClass,
pawnClass: { type: 'string', description: 'Pawn class to use.' },
defaultPawnClass: { type: 'string', description: 'Default pawn class for GameMode.' },
playerControllerClass: { type: 'string', description: 'PlayerController class path.' },
gameStateClass: { type: 'string', description: 'GameState class path.' },
playerStateClass: { type: 'string', description: 'PlayerState class path.' },
spectatorClass: { type: 'string', description: 'Spectator pawn class.' },
hudClass: { type: 'string', description: 'HUD class path.' },
bDelayedStart: { type: 'boolean', description: 'Whether to delay match start.' },
states: {
                  type: 'array',
                  items: {
                    type: 'object',
                    properties: {
                      name: { type: 'string', enum: ['waiting', 'warmup', 'in_progress', 'post_match', 'custom'] },
                      duration: commonSchemas.duration,
                      customName: { type: 'string', description: 'Custom state name if name is "custom".' }
                    }
                  },
                  description: 'Match state definitions.'
                },
numRounds: commonSchemas.numberProp,
roundTime: commonSchemas.numberProp,
intermissionTime: commonSchemas.numberProp,
numTeams: commonSchemas.numberProp,
teamSize: commonSchemas.numberProp,
autoBalance: { type: 'boolean', description: 'Enable automatic team balancing.' },
friendlyFire: { type: 'boolean', description: 'Enable friendly fire damage.' },
teamIndex: { type: 'number', description: 'Team index for PlayerStart.' },
scorePerKill: { type: 'number', description: 'Points awarded per kill.' },
scorePerObjective: { type: 'number', description: 'Points awarded per objective.' },
scorePerAssist: { type: 'number', description: 'Points awarded per assist.' },
spawnSelectionMethod: {
                  type: 'string',
                  enum: ['Random', 'RoundRobin', 'FarthestFromEnemies'],
                  description: 'How to select spawn points.'
                },
respawnDelay: commonSchemas.numberProp,
respawnLocation: {
                  type: 'string',
                  enum: ['PlayerStart', 'LastDeath', 'TeamBase'],
                  description: 'Where players respawn.'
                },
usePlayerStarts: { type: 'boolean', description: 'Use PlayerStart actors.' },
allowSpectating: { type: 'boolean', description: 'Allow spectator mode.' },
spectatorViewMode: {
                  type: 'string',
                  enum: ['FreeCam', 'ThirdPerson', 'FirstPerson', 'DeathCam'],
                  description: 'Spectator view mode.'
                },
save: commonSchemas.save
};
