const ALLOWED_UBT_PLATFORMS = new Set(['Win64', 'Mac', 'Linux', 'LinuxArm64', 'Android', 'IOS', 'TVOS', 'HoloLens', 'VisionOS']);
const ALLOWED_UBT_CONFIGURATIONS = new Set(['Debug', 'DebugGame', 'Development', 'Shipping', 'Test']);
const BLOCKED_UBT_OVERRIDE_OPTIONS = new Set(['project', 'projectfile', 'target', 'mode']);

export function validateUbtArgumentsString(extraArgs: string): void {
  if (!extraArgs || typeof extraArgs !== 'string') {
    return;
  }

  const forbiddenChars = ['\n', '\r', ';', '|', '`', '&&', '||', '>', '<', '"', "'"];
  for (const char of forbiddenChars) {
    if (extraArgs.includes(char)) {
      throw new Error(
        `UBT arguments contain forbidden character(s) and are blocked for safety. Blocked: ${JSON.stringify(char)}.`
      );
    }
  }

  for (const token of tokenizeArgs(extraArgs)) {
    validateUbtExtraArgumentToken(token);
  }
}

function validateUbtArgumentToken(token: string, context: string): void {
  if (!token || token.trim().length === 0) {
    throw new Error(`${context} must be a non-empty UBT token.`);
  }

  const trimmed = token.trim();
  if (!/^[A-Za-z0-9_\-.=:/\\+]+$/.test(trimmed)) {
    throw new Error(`${context} contains unsafe UBT argument characters.`);
  }
}

function validateUbtPositionalToken(token: string, context: string): void {
  validateUbtArgumentToken(token, context);
  const trimmed = token.trim();
  if (/^[-/@]/.test(trimmed) || trimmed.includes('=') || trimmed.includes(':') || trimmed.includes('/') || trimmed.includes('\\')) {
    throw new Error(`${context} must be a positional UBT token and cannot be a switch or path.`);
  }
}

export function validateUbtTarget(target: string): void {
  validateUbtPositionalToken(target, 'run_ubt.target');
}

export function validateUbtPlatform(platform: string): void {
  validateUbtPositionalToken(platform, 'run_ubt.platform');
  if (!ALLOWED_UBT_PLATFORMS.has(platform)) {
    throw new Error(`run_ubt.platform is not allowed: ${platform}`);
  }
}

export function validateUbtConfiguration(configuration: string): void {
  validateUbtPositionalToken(configuration, 'run_ubt.configuration');
  if (!ALLOWED_UBT_CONFIGURATIONS.has(configuration)) {
    throw new Error(`run_ubt.configuration is not allowed: ${configuration}`);
  }
}

function getUbtOptionName(token: string): string | undefined {
  const trimmed = token.trim().toLowerCase();
  if (!trimmed.startsWith('-') && !trimmed.startsWith('/')) {
    return undefined;
  }

  const withoutPrefix = trimmed.replace(/^[-/]+/, '');
  const separatorIndex = withoutPrefix.search(/[=:]/);
  return separatorIndex >= 0 ? withoutPrefix.slice(0, separatorIndex) : withoutPrefix;
}

function validateUbtExtraArgumentToken(token: string): void {
  const trimmed = token.trim();
  if (trimmed.startsWith('@')) {
    throw new Error('UBT response-file arguments are blocked for safety.');
  }
  validateUbtArgumentToken(token, 'run_ubt.arguments');

  const optionName = getUbtOptionName(trimmed);
  if (optionName && BLOCKED_UBT_OVERRIDE_OPTIONS.has(optionName)) {
    throw new Error(`UBT argument ${optionName} cannot override the managed invocation.`);
  }
}

export function tokenizeArgs(extraArgs: string): string[] {
  if (!extraArgs) {
    return [];
  }

  const args: string[] = [];
  let current = '';
  let inQuotes = false;
  let escapeNext = false;

  for (let i = 0; i < extraArgs.length; i++) {
    const ch = extraArgs[i];

    if (escapeNext) {
      current += ch;
      escapeNext = false;
      continue;
    }

    if (ch === '\\') {
      escapeNext = true;
      continue;
    }

    if (ch === '"') {
      inQuotes = !inQuotes;
      continue;
    }

    if (!inQuotes && /\s/.test(ch)) {
      if (current.length > 0) {
        args.push(current);
        current = '';
      }
    } else {
      current += ch;
    }
  }

  if (current.length > 0) {
    args.push(current);
  }

  return args;
}
