import type { AutomationBridgeResolvedConfig } from './bridge-config.js';
import type { AutomationBridgeRuntimeState } from './bridge-state.js';
import type { ConnectionManager } from './connection-manager.js';
import type { RequestTracker } from './request-tracker.js';
import type { AutomationBridgeStatus } from './types.js';

interface AutomationBridgeStatusDependencies {
    readonly config: AutomationBridgeResolvedConfig;
    readonly state: AutomationBridgeRuntimeState;
    readonly connectionManager: ConnectionManager;
    readonly requestTracker: RequestTracker;
    readonly connected: boolean;
}

export function buildAutomationBridgeStatus(deps: AutomationBridgeStatusDependencies): AutomationBridgeStatus {
    const connectionInfos = Array.from(deps.connectionManager.getActiveSockets().entries()).map(([socket, info]) => ({
        connectionId: info.connectionId,
        sessionId: info.sessionId ?? null,
        remoteAddress: info.remoteAddress ?? null,
        remotePort: info.remotePort ?? null,
        port: info.port,
        connectedAt: info.connectedAt.toISOString(),
        protocol: info.protocol || null,
        readyState: socket.readyState,
        isPrimary: socket === deps.connectionManager.getPrimarySocket()
    }));

    return {
        enabled: deps.config.enabled,
        host: deps.config.clientHost,
        port: deps.config.port,
        configuredPorts: [...deps.config.ports],
        listeningPorts: [],
        connected: deps.connected,
        connectedAt: connectionInfos.length > 0 ? connectionInfos[0]?.connectedAt ?? null : null,
        activePort: connectionInfos.length > 0 ? connectionInfos[0]?.port ?? null : null,
        negotiatedProtocol: connectionInfos.length > 0 ? connectionInfos[0]?.protocol ?? null : null,
        supportedProtocols: [...deps.config.negotiatedProtocols],
        supportedOpcodes: ['automation_request'],
        expectedResponseOpcodes: ['automation_response'],
        capabilityTokenRequired: Boolean(deps.config.capabilityToken),
        lastHandshakeAt: deps.state.lastHandshakeAt?.toISOString() ?? null,
        lastHandshakeMetadata: deps.state.lastHandshakeMetadata ?? null,
        lastHandshakeAck: deps.state.lastHandshakeAck ?? null,
        lastHandshakeFailure: deps.state.lastHandshakeFailure
            ? { reason: deps.state.lastHandshakeFailure.reason, at: deps.state.lastHandshakeFailure.at.toISOString() }
            : null,
        lastDisconnect: deps.state.lastDisconnect
            ? { code: deps.state.lastDisconnect.code, reason: deps.state.lastDisconnect.reason, at: deps.state.lastDisconnect.at.toISOString() }
            : null,
        lastError: deps.state.lastError
            ? { message: deps.state.lastError.message, at: deps.state.lastError.at.toISOString() }
            : null,
        lastMessageAt: deps.connectionManager.getLastMessageTime()?.toISOString() ?? null,
        lastRequestSentAt: deps.requestTracker.getLastRequestSentAt()?.toISOString() ?? null,
        pendingRequests: deps.requestTracker.getPendingCount(),
        pendingRequestDetails: deps.requestTracker.getPendingDetails(),
        connections: connectionInfos,
        webSocketListening: false,
        serverLegacyEnabled: deps.config.serverLegacyEnabled,
        serverName: deps.config.serverName,
        serverVersion: deps.config.serverVersion,
        maxConcurrentConnections: deps.config.maxConcurrentConnections,
        maxPendingRequests: deps.requestTracker.getMaxPendingRequests(),
        heartbeatIntervalMs: deps.connectionManager.getHeartbeatIntervalMs()
    };
}
