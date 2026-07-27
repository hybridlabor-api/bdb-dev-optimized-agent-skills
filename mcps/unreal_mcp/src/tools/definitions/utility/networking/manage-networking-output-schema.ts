import { commonSchemas } from '../../../catalog/tool-definition-utils.js';

export const manageNetworkingOutputSchema = {
      type: 'object',
      properties: {
        success: commonSchemas.booleanProp,
        message: commonSchemas.stringProp,
        blueprintPath: commonSchemas.blueprintPath,
        functionName: { type: 'string', description: 'Created RPC function name.' },
        hasAuthority: { type: 'boolean', description: 'Authority check result.' },
        isLocallyControlled: { type: 'boolean', description: 'Local control check result.' },
        role: { type: 'string', description: 'Current net role.' },
        remoteRole: { type: 'string', description: 'Current remote role.' },
        networkingInfo: {
          type: 'object',
          properties: {
            bReplicates: commonSchemas.booleanProp,
            bAlwaysRelevant: commonSchemas.booleanProp,
            bOnlyRelevantToOwner: commonSchemas.booleanProp,
            netUpdateFrequency: commonSchemas.numberProp,
            minNetUpdateFrequency: commonSchemas.numberProp,
            netPriority: commonSchemas.numberProp,
            netDormancy: commonSchemas.stringProp,
            netCullDistanceSquared: commonSchemas.numberProp,
            replicatedProperties: {
              type: 'array',
              items: {
                type: 'object',
                properties: {
                  name: commonSchemas.stringProp,
                  condition: commonSchemas.stringProp,
                  repNotifyFunc: commonSchemas.stringProp
                }
              }
            },
            rpcFunctions: {
              type: 'array',
              items: {
                type: 'object',
                properties: {
                  name: commonSchemas.stringProp,
                  type: commonSchemas.stringProp,
                  reliable: commonSchemas.booleanProp
                }
              }
            }
          },
          description: 'Networking info (for get_networking_info).'
        },
        error: commonSchemas.stringProp
      }
    };
