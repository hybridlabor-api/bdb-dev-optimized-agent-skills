import { isRecord } from '../validation/type-guards.js';

export const ErrorType = {
  VALIDATION: 'VALIDATION',
  CONNECTION: 'CONNECTION',
  UNREAL_ENGINE: 'UNREAL_ENGINE',
  PARAMETER: 'PARAMETER',
  EXECUTION: 'EXECUTION',
  TIMEOUT: 'TIMEOUT',
  UNKNOWN: 'UNKNOWN'
} as const;

export type ErrorType = typeof ErrorType[keyof typeof ErrorType];

export interface ErrorLike {
  message?: string;
  code?: string;
  type?: string;
  errorType?: string;
  stack?: string;
  response?: { status?: number };
}

function stringFromUnknown(value: unknown): string | undefined {
  if (typeof value === 'string') return value;
  if (typeof value === 'number') return String(value);
  return undefined;
}

function numberFromUnknown(value: unknown): number | undefined {
  if (typeof value === 'number' && Number.isFinite(value)) return value;
  if (typeof value === 'string' && value.trim()) {
    const parsed = Number(value.trim());
    if (Number.isFinite(parsed)) return parsed;
  }
  return undefined;
}

export function normalizeErrorToLike(error: unknown): ErrorLike {
  if (error instanceof Error) {
    const code = isRecord(error) ? stringFromUnknown(error.code) : undefined;
    return {
      message: error.message,
      stack: error.stack,
      code
    };
  }
  if (isRecord(error)) {
    const response = isRecord(error.response) ? error.response : null;
    return {
      message: stringFromUnknown(error.message),
      code: stringFromUnknown(error.code),
      type: stringFromUnknown(error.type),
      errorType: stringFromUnknown(error.errorType),
      stack: typeof error.stack === 'string' ? error.stack : undefined,
      response: response
        ? {
          status: numberFromUnknown(response.status)
        }
        : undefined
    };
  }
  return { message: String(error) };
}

export function categorizeError(error: unknown): ErrorType {
  const errorObj = normalizeErrorToLike(error);
  const explicitType = (errorObj.type || errorObj.errorType || '').toString().toUpperCase();
  switch (explicitType) {
    case ErrorType.VALIDATION:
      return ErrorType.VALIDATION;
    case ErrorType.CONNECTION:
      return ErrorType.CONNECTION;
    case ErrorType.UNREAL_ENGINE:
      return ErrorType.UNREAL_ENGINE;
    case ErrorType.PARAMETER:
      return ErrorType.PARAMETER;
    case ErrorType.EXECUTION:
      return ErrorType.EXECUTION;
    case ErrorType.TIMEOUT:
      return ErrorType.TIMEOUT;
    case ErrorType.UNKNOWN:
      return ErrorType.UNKNOWN;
  }

  const errorMessage = (errorObj.message || String(error)).toLowerCase();
  if (errorMessage.includes('timeout') || errorMessage.includes('timed out')) {
    return ErrorType.TIMEOUT;
  }

  if (
    errorMessage.includes('econnrefused') ||
    errorMessage.includes('connection') ||
    errorMessage.includes('network')
  ) {
    return ErrorType.CONNECTION;
  }

  if (
    errorMessage.includes('invalid') ||
    errorMessage.includes('required') ||
    errorMessage.includes('must be') ||
    errorMessage.includes('validation')
  ) {
    return ErrorType.VALIDATION;
  }

  if (
    errorMessage.includes('unreal') ||
    errorMessage.includes('connection failed') ||
    errorMessage.includes('blueprint') ||
    errorMessage.includes('actor') ||
    errorMessage.includes('asset')
  ) {
    return ErrorType.UNREAL_ENGINE;
  }

  if (
    errorMessage.includes('parameter') ||
    errorMessage.includes('argument') ||
    errorMessage.includes('missing')
  ) {
    return ErrorType.PARAMETER;
  }

  return ErrorType.UNKNOWN;
}

export function getUserFriendlyMessage(type: ErrorType, error: unknown): string {
  const errorObj = normalizeErrorToLike(error);
  const originalMessage = errorObj.message || String(error);

  switch (type) {
    case ErrorType.CONNECTION:
      return 'Failed to connect to Unreal Engine. Please ensure the Automation Bridge plugin is active and the editor is running.';

    case ErrorType.VALIDATION:
      return `Invalid input: ${originalMessage}`;

    case ErrorType.UNREAL_ENGINE:
      return `Unreal Engine error: ${originalMessage}`;

    case ErrorType.PARAMETER:
      return `Invalid parameters: ${originalMessage}`;

    case ErrorType.TIMEOUT:
      return 'Operation timed out. Unreal Engine may be busy or unresponsive.';

    case ErrorType.EXECUTION:
      return `Execution failed: ${originalMessage}`;

    default:
      return originalMessage;
  }
}

export function isRetriableError(error: unknown): boolean {
  const errorObj = normalizeErrorToLike(error);
  const code = (errorObj.code || '').toString().toUpperCase();
  const msg = (errorObj.message || String(error) || '').toLowerCase();
  const status = numberFromUnknown(errorObj.response?.status);
  if (['ECONNRESET', 'ECONNREFUSED', 'ETIMEDOUT', 'EPIPE'].includes(code)) return true;
  if (/timeout|timed out|network|connection|closed|unavailable|busy|temporar/.test(msg)) return true;
  return status !== undefined && (status === 408 || status === 429 || (status >= 500 && status < 600));
}
