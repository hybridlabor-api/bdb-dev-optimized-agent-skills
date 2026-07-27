import { beforeEach, describe, expect, it, vi } from 'vitest';
import type { AutomationRequestBridge, ITools } from '../../../types/tools/tool-interfaces.js';

const { executeAutomationRequestMock } = vi.hoisted(() => ({
  executeAutomationRequestMock: vi.fn(async () => ({ success: true, result: {} }))
}));

vi.mock('../foundation/dispatch/common-handlers.js', async () => {
  const actual = await vi.importActual<typeof import('../foundation/dispatch/common-handlers.js')>('../foundation/dispatch/common-handlers.js');
  return {
    ...actual,
    executeAutomationRequest: executeAutomationRequestMock
  };
});

import { handleEffectTools } from './effect-handlers.js';

function createTools(): ITools {
  const sendAutomationRequest = vi.fn<AutomationRequestBridge['sendAutomationRequest']>(async () => ({ success: true }));

  return {
    systemTools: {
      executeConsoleCommand: vi.fn(async () => ({ success: true })),
      getProjectSettings: vi.fn(async () => ({}))
    },
    assetResources: {
      list: vi.fn(async () => ({}))
    },
    automationBridge: {
      isConnected: () => true,
      sendAutomationRequest
    }
  };
}

describe('handleEffectTools payload mapping', () => {
  beforeEach(() => {
    executeAutomationRequestMock.mockClear();
    executeAutomationRequestMock.mockResolvedValue({ success: true, result: {} });
  });

  it('preserves systemName and path aliases for Niagara system creation', async () => {
    const tools = createTools();

    await handleEffectTools('create_niagara_system', {
      action: 'create_niagara_system',
      systemName: 'NS_Test',
      path: '/Game/FX/Test'
    }, tools);

    expect(executeAutomationRequestMock).toHaveBeenCalledWith(tools, 'create_niagara_system', {
      name: 'NS_Test',
      path: '/Game/FX/Test',
      savePath: '/Game/FX/Test'
    });
  });

  it('maps spawn_niagara system aliases before routing through create_effect', async () => {
    const tools = createTools();

    await handleEffectTools('spawn_niagara', {
      action: 'spawn_niagara',
      system: '/Game/FX/NS_Test.NS_Test'
    }, tools);

    expect(executeAutomationRequestMock).toHaveBeenCalledWith(
      tools,
      'create_effect',
      expect.objectContaining({
        action: 'niagara',
        subAction: 'niagara',
        system: '/Game/FX/NS_Test.NS_Test',
        systemPath: '/Game/FX/NS_Test.NS_Test',
        actorName: expect.stringMatching(/^MCP_ManageEffectDefaultActor_/)
      })
    );
  });

  it('maps debug shape aliases and default location before dispatch', async () => {
    const tools = createTools();

    await handleEffectTools('debug_shape', {
      action: 'debug_shape',
      shape: 'box'
    }, tools);

    expect(executeAutomationRequestMock).toHaveBeenCalledWith(
      tools,
      'create_effect',
      expect.objectContaining({
        action: 'debug_shape',
        subAction: 'debug_shape',
        shape: 'box',
        shapeType: 'box',
        location: { x: 0, y: 0, z: 100 }
      })
    );
  });

  it('uses an explicit graph asset path as the matching system path', async () => {
    const tools = createTools();
    const systemPath = '/Game/FX/NS_Graph.NS_Graph';

    await handleEffectTools('connect_niagara_pins', {
      action: 'connect_niagara_pins',
      assetPath: systemPath,
      autoConnect: true
    }, tools);

    expect(executeAutomationRequestMock).toHaveBeenLastCalledWith(
      tools,
      'manage_niagara_graph',
      expect.objectContaining({
        assetPath: systemPath,
        systemPath
      })
    );
  });
});
