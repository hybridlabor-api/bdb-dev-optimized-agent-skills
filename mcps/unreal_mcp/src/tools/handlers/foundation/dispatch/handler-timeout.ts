import { stringToPositiveInteger } from '../../../../config.js';

export function getTimeoutMs(defaultMs: number = 120000): number {
  const raw = process.env.MCP_REQUEST_TIMEOUT_MS ?? process.env.MCP_AUTOMATION_REQUEST_TIMEOUT_MS;
  return stringToPositiveInteger(raw, defaultMs);
}
