export function promoteScalarResultFields(response: Record<string, unknown>): Record<string, unknown> {
  const result = response.result;
  if (!result || typeof result !== 'object' || Array.isArray(result)) {
    return response;
  }

  const promoted: Record<string, unknown> = {};
  for (const [key, value] of Object.entries(result)) {
    if (value === null || typeof value === 'string' || typeof value === 'number' || typeof value === 'boolean' || typeof value === 'bigint') {
      promoted[key] = value;
    }
  }

  return { ...response, ...promoted };
}
