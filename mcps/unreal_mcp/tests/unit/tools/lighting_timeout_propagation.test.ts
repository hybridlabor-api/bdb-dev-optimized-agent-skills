import { describe, expect, it, vi } from 'vitest';
import { LONG_RUNNING_OP_TIMEOUT_MS } from '../../../src/constants.js';
import type { ITools } from '../../../src/types/tools/tool-interfaces.js';
import { handleEnvironmentTools } from '../../../src/tools/handlers/environment/environment-handlers.js';
import { handleLevelTools } from '../../../src/tools/handlers/level/runtime/level-handlers.js';
import { handleLightingTools } from '../../../src/tools/handlers/lighting/lighting-handlers.js';

function createTools() {
  const sendAutomationRequest = vi.fn(async () => ({ success: true }));
  const tools: ITools = {
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

  return { tools, sendAutomationRequest };
}

describe('lighting build timeout propagation', () => {
  it('uses the caller timeout for the lighting tool without sending it in the payload', async () => {
    const { tools, sendAutomationRequest } = createTools();

    await handleLightingTools('build_lighting', {
      action: 'build_lighting',
      quality: 'High',
      timeoutMs: 240000
    }, tools);

    expect(sendAutomationRequest).toHaveBeenCalledWith('bake_lightmap', {
      quality: 'High',
      buildOnlySelected: false,
      buildReflectionCaptures: true,
      levelPath: undefined
    }, {
      timeoutMs: 240000
    });
  });

  it('uses the caller timeout for the level tool without sending it in the payload', async () => {
    const { tools, sendAutomationRequest } = createTools();

    await handleLevelTools('build_lighting', {
      action: 'build_lighting',
      quality: 'Production',
      timeoutMs: 300000
    }, tools);

    expect(sendAutomationRequest).toHaveBeenCalledWith('manage_lighting', {
      action: 'build_lighting',
      quality: 'Production',
      buildOnlySelected: false,
      buildReflectionCaptures: false
    }, {
      timeoutMs: 300000
    });
  });

  it('uses the caller timeout for the environment tool without sending it in the payload', async () => {
    const { tools, sendAutomationRequest } = createTools();

    await handleEnvironmentTools('bake_lightmap', {
      action: 'bake_lightmap',
      quality: 'Preview',
      timeoutMs: 270000
    }, tools);

    expect(sendAutomationRequest).toHaveBeenCalledWith('bake_lightmap', {
      quality: 'Preview',
      buildOnlySelected: false,
      buildReflectionCaptures: false
    }, {
      timeoutMs: 270000
    });
  });

  it.each([
    {
      name: 'lighting',
      run: async (tools: ITools) =>
        handleLightingTools('build_lighting', {
          action: 'build_lighting',
          quality: 'High',
        }, tools),
      request: 'bake_lightmap',
    },
    {
      name: 'level',
      run: async (tools: ITools) =>
        handleLevelTools('build_lighting', {
          action: 'build_lighting',
          quality: 'Production',
        }, tools),
      request: 'manage_lighting',
    },
    {
      name: 'environment',
      run: async (tools: ITools) =>
        handleEnvironmentTools('bake_lightmap', {
          action: 'bake_lightmap',
          quality: 'Preview',
        }, tools),
      request: 'bake_lightmap',
    },
  ])('uses the long-running default timeout for the $name tool', async ({ run, request }) => {
    const { tools, sendAutomationRequest } = createTools();

    await run(tools);

    expect(sendAutomationRequest).toHaveBeenCalledWith(
      request,
      expect.any(Object),
      { timeoutMs: LONG_RUNNING_OP_TIMEOUT_MS },
    );
  });
});
