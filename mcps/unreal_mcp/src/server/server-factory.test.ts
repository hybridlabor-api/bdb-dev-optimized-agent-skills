import { describe, expect, it, vi } from 'vitest';
import { createServer } from './server-factory.js';

describe('createServer automation event notifications', () => {
    it('forwards automation bridge events through the MCP notification API', async () => {
        const { server, bridge, automationBridge, metricsServer } = createServer();
        const notificationSpy = vi
            .spyOn(server, 'notification')
            .mockImplementation(async () => undefined);

        try {
            automationBridge.emit('automationEvent', {
                type: 'automation_event',
                event: 'asset_saved',
                requestId: 'orphan-request',
                message: 'Saved /Game/Maps/Arena',
                payload: { assetPath: '/Game/Maps/Arena' }
            });

            expect(notificationSpy).toHaveBeenCalledWith({
                method: 'notifications/unreal/automation_event',
                params: {
                    type: 'automation_event',
                    event: 'asset_saved',
                    requestId: 'orphan-request',
                    message: 'Saved /Game/Maps/Arena',
                    payload: { assetPath: '/Game/Maps/Arena' }
                }
            });
        } finally {
            notificationSpy.mockRestore();
            automationBridge.stop();
            bridge.dispose();
            metricsServer?.close();
        }
    });
});
