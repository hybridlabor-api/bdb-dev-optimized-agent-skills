import { describe, expect, it, vi } from 'vitest';
import type { ITools } from '../../types/tools/tool-interfaces.js';
import { handleConsolidatedToolCall } from './consolidated-tool-handlers.js';
import { consolidatedToolDefinitions } from '../catalog/consolidated-tool-definitions.js';
import { toolRegistry } from './dynamic-handler-registry.js';
import { coreToolDefinitions } from '../schemas/core-tools.js';

type SendAutomationRequest = (
  action: string,
  payload: Record<string, unknown>,
  options?: { timeoutMs?: number }
) => Promise<{ success: boolean }>;

function createConnectedTools() {
  const sendAutomationRequest = vi.fn<SendAutomationRequest>(async () => ({ success: true }));
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

const isRecord = (value: unknown): value is Record<string, unknown> =>
  typeof value === 'object' && value !== null && !Array.isArray(value);

describe('consolidated action params compatibility', () => {
  it('advertises params for action tools in public schemas', () => {
    const tools = [
      consolidatedToolDefinitions.find((tool) => tool.name === 'manage_level_structure'),
      consolidatedToolDefinitions.find((tool) => tool.name === 'system_control'),
      coreToolDefinitions.find((tool) => tool.name === 'manage_level')
    ];

    for (const tool of tools) {
      const inputSchema = tool?.inputSchema as Record<string, unknown> | undefined;
      const properties = inputSchema?.properties as Record<string, unknown> | undefined;
      expect(properties).toHaveProperty('params');
      expect(inputSchema?.additionalProperties).toBe(true);
    }
  });

  it('merges params into level-structure payloads before validation and dispatch', async () => {
    const { tools, sendAutomationRequest } = createConnectedTools();

    await handleConsolidatedToolCall('manage_level_structure', {
      action: 'create_level',
      params: {
        levelName: 'MCP_Racing_Level',
        levelPath: '/Game/MCP_Racing_Level',
        save: true
      }
    }, tools);

    expect(sendAutomationRequest).toHaveBeenCalledWith('manage_level_structure', expect.objectContaining({
      action: 'create_level',
      subAction: 'create_level',
      levelName: 'MCP_Racing_Level',
      levelPath: '/Game/MCP_Racing_Level',
      save: true
    }), expect.any(Object));
    const firstCall = sendAutomationRequest.mock.calls[0];
    expect(firstCall).toBeDefined();
    const payload = firstCall?.[1] ?? {};
    expect(payload).not.toHaveProperty('params');
  });

  it('lets top-level arguments override params when both are provided', async () => {
    const { tools, sendAutomationRequest } = createConnectedTools();

    await handleConsolidatedToolCall('manage_level_structure', {
      action: 'create_level',
      levelName: 'TopLevelName',
      params: {
        action: 'create_sublevel',
        levelName: 'NestedName'
      }
    }, tools);

    expect(sendAutomationRequest).toHaveBeenCalledWith('manage_level_structure', expect.objectContaining({
      action: 'create_level',
      subAction: 'create_level',
      levelName: 'TopLevelName'
    }), expect.any(Object));
  });

  it('removes params before routing to strict input handlers', async () => {
    const { tools, sendAutomationRequest } = createConnectedTools();

    await handleConsolidatedToolCall('manage_networking', {
      action: 'create_input_action',
      params: {
        name: 'IA_Throttle',
        path: '/Game/Input'
      }
    }, tools);

    expect(sendAutomationRequest).toHaveBeenCalledWith('manage_input', expect.objectContaining({
      action: 'create_input_action',
      subAction: 'create_input_action',
      name: 'IA_Throttle',
      path: '/Game/Input'
    }), expect.any(Object));
    const firstCall = sendAutomationRequest.mock.calls[0];
    expect(firstCall).toBeDefined();
    const payload = firstCall?.[1] ?? {};
    expect(payload).not.toHaveProperty('params');
  });

  it('routes base audio asset creation through audio authoring', async () => {
    const { tools, sendAutomationRequest } = createConnectedTools();

    await handleConsolidatedToolCall('manage_audio', {
      action: 'create_sound_mix',
      name: 'SCM_Test',
      path: '/Game/Audio'
    }, tools);

    expect(sendAutomationRequest).toHaveBeenCalledWith('manage_audio_authoring', expect.objectContaining({
      subAction: 'create_sound_mix',
      name: 'SCM_Test',
      path: '/Game/Audio'
    }), expect.any(Object));
  });

  it('preserves sound cue aliases when routing through audio authoring', async () => {
    const { tools, sendAutomationRequest } = createConnectedTools();

    await handleConsolidatedToolCall('manage_audio', {
      action: 'create_sound_cue',
      name: 'SC_TestCue',
      soundPath: '/Engine/VREditor/Sounds/VR_click1',
      savePath: '/Game/Audio/Cues'
    }, tools);

    expect(sendAutomationRequest).toHaveBeenCalledWith('manage_audio_authoring', expect.objectContaining({
      subAction: 'create_sound_cue',
      name: 'SC_TestCue',
      path: '/Game/Audio/Cues',
      wavePath: '/Engine/VREditor/Sounds/VR_click1'
    }), expect.any(Object));
  });

  it('forwards overwrite for level copy-style actions', async () => {
    const { tools, sendAutomationRequest } = createConnectedTools();

    await handleConsolidatedToolCall('manage_level', {
      action: 'duplicate_level',
      sourcePath: '/Game/Maps/Source',
      destinationPath: '/Game/Maps/Destination',
      overwrite: true
    }, tools);

    expect(sendAutomationRequest).toHaveBeenCalledWith('manage_level', expect.objectContaining({
      action: 'duplicate',
      sourcePath: '/Game/Maps/Source',
      destinationPath: '/Game/Maps/Destination',
      overwrite: true
    }), expect.any(Object));
  });

  it.each([
    ['configure_ray_traced_shadows', { enabled: true }],
    ['create_sphere_reflection_capture', { actorName: 'RT_Sphere' }],
    ['configure_pp_blend', { actorName: 'PP_Global', blendWeight: 0.75 }],
    ['create_scene_capture_2d', { actorName: 'Capture2D' }]
  ])('routes rendering build_environment action %s through manage_render', async (action, extraArgs) => {
    const { tools, sendAutomationRequest } = createConnectedTools();

    await handleConsolidatedToolCall('build_environment', {
      action,
      ...extraArgs
    }, tools);

    expect(sendAutomationRequest).toHaveBeenCalledWith('manage_render', expect.objectContaining({
      action,
      subAction: action
    }), expect.any(Object));
  });

  it('returns structured error context for unknown consolidated tools', async () => {
    const { tools } = createConnectedTools();

    const result = await handleConsolidatedToolCall('missing_tool', { action: 'probe' }, tools) as Record<string, unknown>;

    expect(result).toMatchObject({
      success: false,
      isError: true,
      error: 'UNKNOWN_TOOL',
      toolName: 'missing_tool',
      action: 'probe'
    });
    expect(String(result.message)).toContain('Unknown consolidated tool: missing_tool');
  });

  it('preserves tool and action context on dispatch exceptions', async () => {
    const { tools } = createConnectedTools();

    const result = await handleConsolidatedToolCall('manage_level_structure', {
      action: 'create_level',
      levelName: 'BadLevel',
      levelPath: '/etc/passwd'
    }, tools) as Record<string, unknown>;

    expect(result).toMatchObject({
      success: false,
      isError: true,
      error: 'SECURITY_VIOLATION',
      toolName: 'manage_level_structure',
      action: 'create_level'
    });
    expect(String(result.message)).toContain('Security violation');
  });

  it('preserves string messages from non-Error dispatch exceptions', async () => {
    const { tools } = createConnectedTools();
    toolRegistry.register('throw_object_test', async () => {
      throw { message: 'Security violation: object-shaped error' };
    });

    try {
      const result = await handleConsolidatedToolCall('throw_object_test', {
        action: 'probe'
      }, tools) as Record<string, unknown>;

      expect(result).toMatchObject({
        success: false,
        isError: true,
        error: 'SECURITY_VIOLATION',
        toolName: 'throw_object_test',
        action: 'probe'
      });
      expect(String(result.message)).toContain('Security violation: object-shaped error');
    } finally {
      toolRegistry.removeHandler('throw_object_test');
    }
  });

  it('routes full editor screenshot mode with base64 image return enabled', async () => {
    const { tools, sendAutomationRequest } = createConnectedTools();

    await handleConsolidatedToolCall('system_control', {
      action: 'screenshot',
      filename: 'FullEditor',
      mode: 'full_editor_window'
    }, tools);

    expect(sendAutomationRequest).toHaveBeenCalledWith('control_editor', {
      action: 'screenshot',
      filename: 'FullEditor',
      resolution: undefined,
      mode: 'full_editor_window',
      returnBase64: true
    }, {});
  });

  it('forwards screenshot metadata opt-in for system control screenshots', async () => {
    const { tools, sendAutomationRequest } = createConnectedTools();

    await handleConsolidatedToolCall('system_control', {
      action: 'screenshot',
      filename: 'FullEditor',
      mode: 'full_editor_window',
      includeMetadata: true
    }, tools);

    expect(sendAutomationRequest).toHaveBeenCalledWith('control_editor', {
      action: 'screenshot',
      filename: 'FullEditor',
      resolution: undefined,
      mode: 'full_editor_window',
      returnBase64: true,
      includeMetadata: true
    }, {});
  });

  it('routes Unreal Insights trace actions through manage_insights', async () => {
    const { tools, sendAutomationRequest } = createConnectedTools();

    const result = await handleConsolidatedToolCall('system_control', {
      action: 'capture_insights_trace',
      channels: 'cpu,gpu',
      traceFile: 'Saved/Profiling/McpTrace.utrace',
      overwrite: true
    }, tools) as Record<string, unknown>;

    expect(sendAutomationRequest).toHaveBeenCalledWith('manage_insights', expect.objectContaining({
      action: 'capture_insights_trace',
      subAction: 'capture_insights_trace',
      channels: 'cpu,gpu',
      traceFile: 'Saved/Profiling/McpTrace.utrace',
      overwrite: true
    }), expect.any(Object));
    expect(result).toMatchObject({
      success: true,
      action: 'capture_insights_trace',
      channels: 'cpu,gpu',
      sessionType: 'trace'
    });
  });

  it('does not synthesize empty Unreal Insights channels', async () => {
    const { tools, sendAutomationRequest } = createConnectedTools();

    const result = await handleConsolidatedToolCall('system_control', {
      action: 'start_unreal_insights',
      connectionType: 'file',
      traceFile: 'McpTrace.utrace',
      overwrite: true
    }, tools);

    expect(sendAutomationRequest).toHaveBeenCalledWith('manage_insights', expect.objectContaining({
      action: 'start_unreal_insights',
      subAction: 'start_unreal_insights',
      traceFile: 'McpTrace.utrace',
      overwrite: true
    }), expect.any(Object));
    const firstCall = sendAutomationRequest.mock.calls[0];
    expect(firstCall).toBeDefined();
    expect(firstCall?.[1]).not.toHaveProperty('channels');
    expect(result).toMatchObject({
      success: true,
      action: 'start_unreal_insights',
      sessionType: 'trace'
    });
    expect(result).not.toHaveProperty('channels');
  });

  it('advertises only trace connection types backed by live bridge execution', () => {
    const tool = consolidatedToolDefinitions.find((definition) => definition.name === 'system_control');
    const coreTool = coreToolDefinitions.find((definition) => definition.name === 'system_control');
    const tools = [tool, coreTool];

    for (const definition of tools) {
      const properties = definition?.inputSchema.properties;
      expect(isRecord(properties)).toBe(true);
      if (!isRecord(properties)) {
        throw new Error('system_control properties must be a schema object');
      }

      const connectionType = properties.connectionType;
      expect(isRecord(connectionType)).toBe(true);
      if (!isRecord(connectionType)) {
        throw new Error('connectionType must be a schema object');
      }

      expect(connectionType.enum).toEqual(['file', 'network']);
    }
  });

  it('rejects unsafe Unreal Insights channels before bridge dispatch', async () => {
    const { tools, sendAutomationRequest } = createConnectedTools();

    const result = await handleConsolidatedToolCall('system_control', {
      action: 'start_unreal_insights',
      channels: 'cpu;quit'
    }, tools) as Record<string, unknown>;

    expect(sendAutomationRequest).not.toHaveBeenCalled();
    expect(result).toMatchObject({
      success: false,
      error: 'INVALID_CHANNELS'
    });
  });
});
