import { describe, it, expect, vi, beforeEach } from 'vitest';
import { LevelTools } from '../../../src/tools/level/level.js';
import { UnrealBridge } from '../../../src/unreal-bridge.js';

describe('LevelTools Security', () => {
    let bridge: UnrealBridge;
    let levelTools: LevelTools;

    beforeEach(() => {
        bridge = new UnrealBridge();
        vi.spyOn(bridge, 'executeConsoleCommand').mockImplementation((cmd: string) => {
            if (cmd.startsWith('GetLevelPath')) {
                return Promise.resolve({ success: true, message: '/Game/Maps/MyMap' });
            }
            return Promise.resolve({ success: true, message: 'OK' });
        });
        levelTools = new LevelTools(bridge);
    });

    it('should use sanitized path in console fallback for loadLevel', async () => {
        const rawPath = '\\Game\\Maps\\MyMap';
        const expectedPath = '/Game/Maps/MyMap';

        await levelTools.loadLevel({ levelPath: rawPath });

        const executeCommandMock = vi.mocked(bridge.executeConsoleCommand);
        expect(executeCommandMock).toHaveBeenCalled();

        const calls = executeCommandMock.mock.calls;
        const openCall = calls.find((call) => call[0].startsWith('Open'));
        expect(openCall).toBeDefined();
        expect(openCall?.[0]).toBe(`Open ${expectedPath}`);
    });

    it('should validate level path before falling back to console', async () => {
        const maliciousPath = '../../Secret/Map';

        await expect(levelTools.loadLevel({ levelPath: maliciousPath }))
            .rejects.toThrow(/Security validation failed/);

        const executeCommandMock = vi.mocked(bridge.executeConsoleCommand);
        expect(executeCommandMock).not.toHaveBeenCalled();
    });

    it('should return error when level not found via GetLevelPath', async () => {
        vi.mocked(bridge.executeConsoleCommand).mockResolvedValueOnce({
            success: false,
            message: 'Level not found: /Game/Maps/NonExistent'
        });

        const result = await levelTools.loadLevel({ levelPath: '/Game/Maps/NonExistent' });

        expect(result.success).toBe(false);
        expect(result.error).toBe('LEVEL_NOT_FOUND');
    });
});
