import { commonSchemas } from '../catalog/tool-definition-utils.js';
import type { ToolDefinition } from './core-tool-definition.js';

const screenshotModeSchema = {
  type: 'string',
  enum: ['editor_viewport', 'game_viewport', 'full_editor_window'],
  description: 'Screenshot source. editor_viewport captures the active editor viewport; game_viewport captures the PIE/game viewport; full_editor_window captures the full Slate editor window and returns imageBase64 by default.'
};

export const systemControlToolDefinition: ToolDefinition = {
  name: 'system_control',
  category: 'core',
  description: 'Control the project runtime: profiling, benchmarks, scalability/LOD/Nanite settings, CVars, console commands, Python scripts, UBT, tests, logs, and widgets.',
  inputSchema: {
    type: 'object',
    properties: {
      action: {
        type: 'string',
        enum: [
          'profile', 'show_fps', 'set_quality', 'screenshot', 'set_resolution', 'set_fullscreen', 'execute_command', 'console_command',
          'run_ubt', 'run_tests', 'subscribe', 'unsubscribe', 'spawn_category',
          'start_session', 'start_unreal_insights', 'capture_insights_trace',
          'get_trace_status', 'pause_session', 'resume_session', 'stop_session',
          'write_snapshot', 'send_snapshot', 'analyze_trace', 'lumen_update_scene',
          'play_sound', 'create_widget', 'show_widget', 'add_widget_child',
          'set_cvar', 'get_project_settings', 'validate_assets',
          'set_project_setting'
        ],
        description: 'Action'
      },
      profileType: commonSchemas.stringProp,
      category: commonSchemas.stringProp,
      level: commonSchemas.numberProp,
      enabled: commonSchemas.enabled,
      resolution: commonSchemas.resolution,
      command: commonSchemas.stringProp,
      target: commonSchemas.stringProp,
      platform: commonSchemas.stringProp,
      configuration: commonSchemas.stringProp,
      arguments: commonSchemas.stringProp,
      filter: commonSchemas.stringProp,
      channels: commonSchemas.stringProp,
      connectionType: { type: 'string', enum: ['file', 'network'], description: 'Trace connection type. Network traces are restricted to loopback hosts by the bridge.' },
      host: commonSchemas.stringProp,
      port: commonSchemas.numberProp,
      traceFile: commonSchemas.outputPath,
      tracePath: commonSchemas.outputPath,
      snapshotPath: commonSchemas.outputPath,
      overwrite: commonSchemas.overwrite,
      widgetPath: commonSchemas.widgetPath,
      childClass: commonSchemas.stringProp,
      parentName: commonSchemas.stringProp,
      section: commonSchemas.stringProp,
      key: commonSchemas.stringProp,
      value: commonSchemas.stringProp,
      configName: commonSchemas.stringProp,
      mode: screenshotModeSchema,
      returnBase64: { type: 'boolean', description: 'Return PNG image data as base64 when supported. Defaults to true for full_editor_window and game_viewport screenshot modes.' },
      includeMetadata: commonSchemas.booleanProp,
      metadata: commonSchemas.objectProp
    },
    required: ['action']
  },
  outputSchema: {
    type: 'object',
    properties: {
      ...commonSchemas.outputBase,
      output: commonSchemas.stringProp,
      imageBase64: commonSchemas.stringProp,
      mimeType: commonSchemas.stringProp,
      width: commonSchemas.numberProp,
      height: commonSchemas.numberProp,
      sizeBytes: commonSchemas.numberProp,
      path: commonSchemas.stringProp,
      screenshotPath: commonSchemas.stringProp,
      mode: commonSchemas.stringProp
    }
  }
};
