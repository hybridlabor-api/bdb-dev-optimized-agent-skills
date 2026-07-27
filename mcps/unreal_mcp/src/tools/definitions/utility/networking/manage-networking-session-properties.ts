import { commonSchemas } from '../../../catalog/tool-definition-utils.js';

export const manageNetworkingSessionProperties = {
sessionName: commonSchemas.sessionName,
maxPlayers: commonSchemas.numberProp,
bIsLANMatch: { type: 'boolean', description: 'Whether this is a LAN match.' },
bAllowJoinInProgress: { type: 'boolean', description: 'Allow joining games in progress.' },
bAllowInvites: { type: 'boolean', description: 'Allow player invites.' },
bUsesPresence: { type: 'boolean', description: 'Use presence for session discovery.' },
bUseLobbiesIfAvailable: { type: 'boolean', description: 'Use lobby system if available.' },
bShouldAdvertise: { type: 'boolean', description: 'Advertise session publicly.' },
interfaceType: {
                  type: 'string',
                  enum: ['Default', 'LAN', 'Null'],
                  description: 'Type of session interface to use. REQUIRED for configure_session_interface.'
                },
enabled: commonSchemas.enabled,
splitScreenType: {
                  type: 'string',
                  enum: ['None', 'TwoPlayer_Horizontal', 'TwoPlayer_Vertical', 'ThreePlayer_FavorTop', 'ThreePlayer_FavorBottom', 'FourPlayer_Grid'],
                  description: 'Split-screen layout type. REQUIRED for set_split_screen_type.'
                },
playerIndex: { ...commonSchemas.numberProp, description: 'Local player index. REQUIRED for remove_local_player.' },
controllerId: { ...commonSchemas.numberProp, description: 'Controller ID for player input. REQUIRED for add_local_player.' },
serverAddress: { ...commonSchemas.serverAddress, description: 'Server IP address. REQUIRED for join_lan_server.' },
serverPort: commonSchemas.numberProp,
serverPassword: { type: 'string', description: 'Server password for protected games.' },
serverName: { type: 'string', description: 'Display name for the server.' },
mapName: { type: 'string', description: 'Map to load for hosting. REQUIRED for host_lan_server.' },
travelOptions: { type: 'string', description: 'Travel URL options string.' },
voiceEnabled: { type: 'boolean', description: 'Enable/disable voice chat. REQUIRED for enable_voice_chat.' },
voiceSettings: {
                  type: 'object',
                  properties: {
                    volume: { type: 'number', description: 'Voice volume (0.0 - 1.0).' },
                    noiseGateThreshold: { type: 'number', description: 'Noise gate threshold.' },
                    noiseSuppression: { type: 'boolean', description: 'Enable noise suppression.' },
                    echoCancellation: { type: 'boolean', description: 'Enable echo cancellation.' },
                    sampleRate: { type: 'number', description: 'Audio sample rate in Hz.' }
                  },
                  description: 'Voice processing settings. REQUIRED for configure_voice_settings.'
                },
channelName: { ...commonSchemas.channelName, description: 'Voice channel name. REQUIRED for set_voice_channel.' },
channelType: {
                  type: 'string',
                  enum: ['Team', 'Global', 'Proximity', 'Party'],
                  description: 'Voice channel type.'
                },
playerName: { type: 'string', description: 'Player name for voice operations. REQUIRED for mute_player (or targetPlayerId).' },
targetPlayerId: { type: 'string', description: 'Target player ID. REQUIRED for mute_player (or playerName).' },
muted: commonSchemas.muted,
attenuationRadius: { type: 'number', description: 'Radius for voice attenuation (Proximity chat). REQUIRED for set_voice_attenuation.' },
attenuationFalloff: { type: 'number', description: 'Falloff rate for voice attenuation.' },
pushToTalkEnabled: { type: 'boolean', description: 'Enable push-to-talk mode. REQUIRED for configure_push_to_talk.' },
pushToTalkKey: { type: 'string', description: 'Key binding for push-to-talk.' }
};
