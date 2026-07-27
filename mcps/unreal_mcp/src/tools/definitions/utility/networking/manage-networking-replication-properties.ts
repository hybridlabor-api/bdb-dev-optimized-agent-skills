import { commonSchemas } from '../../../catalog/tool-definition-utils.js';
import { SESSION_ACTIONS, GAME_FRAMEWORK_ACTIONS, INPUT_ACTIONS } from '../../shared/action-sets.js';

export const manageNetworkingReplicationProperties = {
action: {
          type: 'string',
          enum: [
            'set_property_replicated',
            'set_replication_condition',
            'configure_net_update_frequency',
            'configure_net_priority',
            'set_net_dormancy',
            'configure_replication_graph',
            'create_rpc_function',
            'configure_rpc_validation',
            'set_rpc_reliability',
            'set_owner',
            'set_autonomous_proxy',
            'check_has_authority',
            'check_is_locally_controlled',
            'configure_net_cull_distance',
            'set_always_relevant',
            'set_only_relevant_to_owner',
            'configure_net_serialization',
            'set_replicated_using',
            'configure_push_model',
            'configure_client_prediction',
            'configure_server_correction',
            'add_network_prediction_data',
            'configure_movement_prediction',
            'configure_net_driver',
            'set_net_role',
            'configure_replicated_movement',
            'get_networking_info'
          ,
            ...SESSION_ACTIONS, ...GAME_FRAMEWORK_ACTIONS, ...INPUT_ACTIONS],
          description: 'Networking action to perform'
        },
blueprintPath: commonSchemas.blueprintPath,
actorName: commonSchemas.actorName,
propertyName: commonSchemas.propertyName,
replicated: { type: 'boolean', description: 'Whether property should be replicated.' },
condition: {
          type: 'string',
          enum: [
            'COND_None',
            'COND_InitialOnly',
            'COND_OwnerOnly',
            'COND_SkipOwner',
            'COND_SimulatedOnly',
            'COND_AutonomousOnly',
            'COND_SimulatedOrPhysics',
            'COND_InitialOrOwner',
            'COND_Custom',
            'COND_ReplayOrOwner',
            'COND_ReplayOnly',
            'COND_SimulatedOnlyNoReplay',
            'COND_SimulatedOrPhysicsNoReplay',
            'COND_SkipReplay',
            'COND_Never'
          ],
          description: 'Replication condition.'
        },
repNotifyFunc: commonSchemas.repNotifyFunc,
netUpdateFrequency: { type: 'number', description: 'How often actor replicates (Hz, default 100).' },
minNetUpdateFrequency: { type: 'number', description: 'Minimum update frequency when idle (Hz, default 2).' },
netPriority: { type: 'number', description: 'Network priority for bandwidth (default 1.0).' },
dormancy: {
          type: 'string',
          enum: [
            'DORM_Never',
            'DORM_Awake',
            'DORM_DormantAll',
            'DORM_DormantPartial',
            'DORM_Initial'
          ],
          description: 'Net dormancy mode.'
        },
functionName: commonSchemas.functionName,
rpcType: {
          type: 'string',
          enum: ['Server', 'Client', 'NetMulticast'],
          description: 'Type of RPC.'
        },
reliable: commonSchemas.reliable,
withValidation: { type: 'boolean', description: 'Enable RPC validation.' },
ownerActorName: { type: 'string', description: 'Name of owner actor (null to clear).' },
isAutonomousProxy: { type: 'boolean', description: 'Configure as autonomous proxy.' },
netCullDistanceSquared: { type: 'number', description: 'Network cull distance squared.' },
useOwnerNetRelevancy: { type: 'boolean', description: 'Use owner relevancy.' },
alwaysRelevant: { type: 'boolean', description: 'Always relevant to all clients.' },
onlyRelevantToOwner: { type: 'boolean', description: 'Only relevant to owner.' },
structName: { type: 'string', description: 'Name of struct for custom serialization.' },
usePushModel: { type: 'boolean', description: 'Use push-model replication.' },
enablePrediction: { type: 'boolean', description: 'Enable client-side prediction.' },
correctionThreshold: { type: 'number', description: 'Server correction threshold.' },
smoothingRate: { type: 'number', description: 'Smoothing rate for corrections.' },
dataType: {
          type: 'string',
          enum: ['Transform', 'Vector', 'Rotator', 'Float'],
          description: 'Network prediction data type.'
        },
networkSmoothingMode: {
          type: 'string',
          enum: ['Disabled', 'Linear', 'Exponential'],
          description: 'Movement smoothing mode.'
        },
networkMaxSmoothUpdateDistance: { type: 'number', description: 'Max smooth update distance.' },
networkNoSmoothUpdateDistance: { type: 'number', description: 'No smooth update distance.' },
maxClientRate: { type: 'number', description: 'Max client rate.' },
maxInternetClientRate: { type: 'number', description: 'Max internet client rate.' },
netServerMaxTickRate: { type: 'number', description: 'Server max tick rate.' },
role: {
          type: 'string',
          enum: ['ROLE_None', 'ROLE_SimulatedProxy', 'ROLE_AutonomousProxy', 'ROLE_Authority'],
          description: 'Net role.'
        },
replicateMovement: { type: 'boolean', description: 'Replicate movement.' },
// Additional params for C++ handler alignment (NetworkingHandlers.cpp)
        spatiallyLoaded: { type: 'boolean', description: 'Spatially loaded for replication graph.' },
netLoadOnClient: { type: 'boolean', description: 'Net load on client for replication graph.' },
replicationPolicy: { type: 'string', description: 'Replication policy for replication graph.' },
customSerialization: { type: 'boolean', description: 'Use custom serialization.' },
predictionThreshold: { type: 'number', description: 'Prediction threshold for client prediction.' }
};
