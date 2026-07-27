import { z } from 'zod';

import {
  createServer,
  log,
  routeStdoutLogsToStderr,
} from './server/server-factory.js';
import { startStdioServer } from './server/stdio-lifecycle.js';

routeStdoutLogsToStderr();

export {
  createServer,
  startStdioServer,
};

export const configSchema = z.object({
  logLevel: z.enum(['debug', 'info', 'warn', 'error']).optional().default('info').describe('Runtime log level'),
  projectPath: z.string().optional().default('C:/Users/YourName/Documents/Unreal Projects/YourProject').describe('Absolute path to your Unreal .uproject file'),
});

export default function createServerDefault({ config }: { config?: Record<string, unknown> } = {}) {
  try {
    if (config) {
      if (typeof config.logLevel === 'string') {
        process.env.LOG_LEVEL = config.logLevel;
      }
      if (typeof config.projectPath === 'string' && config.projectPath.trim()) {
        process.env.UE_PROJECT_PATH = config.projectPath;
      }
    }
  } catch (error) {
    const message = error instanceof Error ? error.message : String(error);
    log.debug('[createServerDefault] Failed to apply config to environment:', message);
  }

  return createServer().server;
}

// Direct execution is handled via src/cli.ts to keep this module side-effect free.
