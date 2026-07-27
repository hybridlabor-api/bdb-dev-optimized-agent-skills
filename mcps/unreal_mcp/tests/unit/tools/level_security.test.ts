import { describe, it, expect, vi, beforeEach } from 'vitest';
import { LevelTools } from '../../../src/tools/level/level.js';
import { UnrealBridge } from '../../../src/unreal-bridge.js';

describe('LevelTools Injection Security', () => {
    let bridge: UnrealBridge;
    let levelTools: LevelTools;

    beforeEach(() => {
        bridge = new UnrealBridge();
        vi.spyOn(bridge, 'executeConsoleCommand').mockResolvedValue({ success: true, message: 'OK' });
        vi.spyOn(bridge, 'executeConsoleCommands').mockResolvedValue({ success: true, message: 'OK' });
        levelTools = new LevelTools(bridge);
    });

    it('should NOT allow command injection in createSubLevel via name', async () => {
        const maliciousName = 'MyLevel;Quit';
        await levelTools.createSubLevel({ name: maliciousName, type: 'Persistent' });

        const executeCommandMock = vi.mocked(bridge.executeConsoleCommand);
        expect(executeCommandMock).toHaveBeenCalled();
        const command = executeCommandMock.mock.calls[0][0];

        expect(command).not.toContain(';Quit');
    });

    it('should NOT allow command injection in setLevelVisibility via levelName', async () => {
        const maliciousName = 'MyLevel;Quit';
        await levelTools.setLevelVisibility({ levelName: maliciousName, visible: true });

        const executeCommandMock = vi.mocked(bridge.executeConsoleCommand);
        expect(executeCommandMock).toHaveBeenCalled();
        const command = executeCommandMock.mock.calls[0][0];

        expect(command).not.toContain(';Quit');
    });

    it('should NOT allow command injection in streaming load fallback', async () => {
        await levelTools.loadLevel({ levelPath: '/Game/Maps/MyLevel;Quit', streaming: true });

        const executeCommandMock = vi.mocked(bridge.executeConsoleCommand);
        const command = executeCommandMock.mock.calls[0][0];
        expect(command).toBe('StreamLevel MyLevel_Quit Load Show');
    });
});
