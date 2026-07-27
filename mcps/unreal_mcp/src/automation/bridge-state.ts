import type { AutomationBridgeMessage } from './types.js';

export interface AutomationBridgeRuntimeState {
    lastHandshakeAt?: Date;
    lastHandshakeMetadata?: Record<string, unknown>;
    lastHandshakeAck?: AutomationBridgeMessage;
    lastHandshakeFailure?: { reason: string; at: Date };
    lastDisconnect?: { code: number; reason: string; at: Date };
    lastError?: { message: string; at: Date };
}
