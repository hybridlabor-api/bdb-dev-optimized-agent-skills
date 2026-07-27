import { manageNetworkingReplicationProperties } from './manage-networking-replication-properties.js';
import { manageNetworkingSessionProperties } from './manage-networking-session-properties.js';
import { manageNetworkingFrameworkProperties } from './manage-networking-framework-properties.js';
import { manageNetworkingInputProperties } from './manage-networking-input-properties.js';

export const manageNetworkingInputSchema = {
      type: 'object',
      properties: {
        ...manageNetworkingReplicationProperties,
        ...manageNetworkingSessionProperties,
        ...manageNetworkingFrameworkProperties,
        ...manageNetworkingInputProperties
      },
      required: ['action']
    };
