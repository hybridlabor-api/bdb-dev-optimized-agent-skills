import path from 'node:path';
import { DEFAULT_SCREENSHOT_RESOLUTION } from '../../constants.js';

type ScreenshotCommand =
  | { valid: true; filename: string; command: string }
  | { valid: false; error: string };

export function buildScreenshotCommand(filename?: string, resolution?: string): ScreenshotCommand {
  if (resolution && !/^\d+x\d+$/.test(resolution)) {
    return { valid: false, error: 'Invalid resolution format. Use WxH (e.g. 1920x1080)' };
  }

  const invalidChars = new RegExp('[<>:*?"|/\\\\]', 'g');
  const fallbackFilename = `Screenshot_${Date.now()}`;
  const requestedFilename = filename ? path.basename(filename).replace(invalidChars, '_').trim() : '';
  const sanitizedFilename = requestedFilename || fallbackFilename;
  const resString = resolution || DEFAULT_SCREENSHOT_RESOLUTION;

  return {
    valid: true,
    filename: sanitizedFilename,
    command: filename ? `highresshot ${resString} filename="${sanitizedFilename}"` : 'shot'
  };
}
