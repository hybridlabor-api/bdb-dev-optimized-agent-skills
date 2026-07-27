import { spawn } from 'node:child_process';
import fs from 'node:fs';
import path from 'node:path';
import { cleanObject } from '../../../utils/serialization/safe-json.js';
import type { ITools } from '../../../types/tools/tool-interfaces.js';
import type { PipelineArgs } from '../../../types/handlers/handler-types.js';
import { executeAutomationRequest } from '../foundation/dispatch/common-handlers.js';
import { findBundledDotNetRoot, findUbtExecutable } from './pipeline-ubt-discovery.js';
import {
  tokenizeArgs,
  validateUbtArgumentsString,
  validateUbtConfiguration,
  validateUbtPlatform,
  validateUbtTarget
} from './pipeline-ubt-validation.js';

async function resolveProjectFile(projectPath: string): Promise<string> {
  if (projectPath.endsWith('.uproject')) {
    return projectPath;
  }

  try {
    const files = await fs.promises.readdir(projectPath);
    const found = files.find(file => file.endsWith('.uproject'));
    if (found) {
      return path.join(projectPath, found);
    }
  } catch (error) {
    if (!(error instanceof Error)) {
      throw error;
    }
    throw new Error(`Could not read project directory: ${projectPath}`);
  }

  return projectPath;
}

function quoteCommandArgs(args: string[]): string[] {
  return args.map(arg => arg.includes(' ') ? `"${arg}"` : arg);
}

function buildChildEnv(bundledDotNetRoot: string | undefined): NodeJS.ProcessEnv {
  return bundledDotNetRoot
    ? {
      ...process.env,
      DOTNET_ROOT: bundledDotNetRoot,
      DOTNET_MULTILEVEL_LOOKUP: '0',
      PATH: `${bundledDotNetRoot}${path.delimiter}${process.env.PATH ?? ''}`,
    }
    : process.env;
}

function spawnUbt(executable: string, actualArgs: string[], cmdArgs: string[], childEnv: NodeJS.ProcessEnv) {
  return new Promise((resolve) => {
    const child = spawn(executable, actualArgs, { shell: false, env: childEnv });
    const maxOutputSize = 20 * 1024;
    let stdout = '';
    let stderr = '';

    child.stdout.on('data', (data) => {
      const str = data.toString();
      process.stderr.write(str);
      stdout += str;
      if (stdout.length > maxOutputSize) {
        stdout = stdout.substring(stdout.length - maxOutputSize);
      }
    });

    child.stderr.on('data', (data) => {
      const str = data.toString();
      process.stderr.write(str);
      stderr += str;
      if (stderr.length > maxOutputSize) {
        stderr = stderr.substring(stderr.length - maxOutputSize);
      }
    });

    child.on('close', (code) => {
      const truncatedNote = (stdout.length >= maxOutputSize || stderr.length >= maxOutputSize)
        ? '\n[Output truncated for response payload]'
        : '';
      const quotedArgs = quoteCommandArgs(cmdArgs);
      const command = `${executable} ${quotedArgs.join(' ')}`;

      if (code === 0) {
        resolve({
          success: true,
          message: 'UnrealBuildTool finished successfully',
          output: stdout + truncatedNote,
          command
        });
      } else {
        resolve({
          success: false,
          error: 'UBT_FAILED',
          message: `UnrealBuildTool failed with code ${code}`,
          output: stdout + truncatedNote,
          errorOutput: stderr + truncatedNote,
          command
        });
      }
    });

    child.on('error', (err) => {
      const quotedArgs = quoteCommandArgs(cmdArgs);
      resolve({
        success: false,
        error: 'SPAWN_FAILED',
        message: `Failed to spawn UnrealBuildTool: ${err.message}`,
        command: `${executable} ${quotedArgs.join(' ')}`
      });
    });
  });
}

export async function handleRunUbt(args: PipelineArgs, tools: ITools) {
  const target = args.target;
  const platform = args.platform || 'Win64';
  const configuration = args.configuration || 'Development';
  const extraArgs = args.arguments || '';

  if (!target) {
    throw new Error('Target is required for run_ubt');
  }

  validateUbtTarget(target);
  validateUbtPlatform(platform);
  validateUbtConfiguration(configuration);
  validateUbtArgumentsString(extraArgs);

  const discoveredUbtPath = await findUbtExecutable();
  if (!discoveredUbtPath) {
    const res = await executeAutomationRequest(
      tools,
      'manage_pipeline',
      { ...args, subAction: 'run_ubt' },
      'Automation bridge not available for run_ubt'
    );
    return cleanObject(res);
  }

  const projectPath = process.env.UE_PROJECT_PATH ?? args.projectPath;
  if (!projectPath) {
    throw new Error('UE_PROJECT_PATH environment variable is not set and no projectPath argument was provided.');
  }

  const uprojectFile = await resolveProjectFile(projectPath);
  const projectArg = `-Project=${uprojectFile}`;
  const cmdArgs = [
    target,
    platform,
    configuration,
    projectArg,
    ...tokenizeArgs(extraArgs)
  ];

  const isDll = discoveredUbtPath.endsWith('.dll');
  const executable = isDll ? 'dotnet' : discoveredUbtPath;
  const actualArgs = isDll ? [discoveredUbtPath, ...cmdArgs] : cmdArgs;
  const bundledDotNetRoot = await findBundledDotNetRoot(discoveredUbtPath);
  const childEnv = buildChildEnv(bundledDotNetRoot);

  return spawnUbt(executable, actualArgs, cmdArgs, childEnv);
}
