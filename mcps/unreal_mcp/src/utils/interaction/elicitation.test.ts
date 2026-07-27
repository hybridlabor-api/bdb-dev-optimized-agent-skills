import { afterEach, describe, expect, it, vi } from 'vitest';
import { Logger } from '../logging/logger.js';
import { createElicitationHelper, type ElicitSchema } from './elicitation.js';

function createTestLogger(): Logger {
  return new Logger('ElicitationTest', 'error');
}

describe('createElicitationHelper timeout env parsing', () => {
  afterEach(() => {
    vi.unstubAllEnvs();
  });

  it('rejects partial numeric timeout strings', () => {
    vi.stubEnv('MCP_ELICITATION_TIMEOUT_MS', '120000ms');
    vi.stubEnv('ELICITATION_TIMEOUT_MS', '');
    const helper = createElicitationHelper({}, createTestLogger());

    expect(helper.getDefaultTimeoutMs()).toBe(180000);
  });

  it('accepts positive decimal integer timeout strings', () => {
    vi.stubEnv('MCP_ELICITATION_TIMEOUT_MS', '120000');
    vi.stubEnv('ELICITATION_TIMEOUT_MS', '');
    const helper = createElicitationHelper({}, createTestLogger());

    expect(helper.getDefaultTimeoutMs()).toBe(120000);
  });

  it('caps per-request timeout overrides at the supported maximum', async () => {
    vi.stubEnv('MCP_ELICITATION_TIMEOUT_MS', '');
    vi.stubEnv('ELICITATION_TIMEOUT_MS', '');
    const elicitInput = vi.fn(async () => ({ action: 'accept', content: { ok: true } }));
    const helper = createElicitationHelper({ elicitInput }, createTestLogger());
    const schema: ElicitSchema = { type: 'object', properties: { name: { type: 'string' } } };

    await helper.elicit('Provide a name', schema, { timeoutMs: 999_999_999 });

    expect(elicitInput).toHaveBeenCalledWith(expect.any(Object), { timeout: 600000 });
  });

  it('routes malformed schema objects to the alternate handler without RPC', async () => {
    const elicitInput = vi.fn(async () => ({ action: 'accept', content: { ok: true } }));
    const alternate = vi.fn(async () => ({ ok: true, value: 'fallback' }));
    const helper = createElicitationHelper({ elicitInput }, createTestLogger());
    const malformedSchema = { type: 'object', properties: null };

    const result = await helper.elicit('Provide a name', malformedSchema, { alternate });

    expect(result).toEqual({ ok: true, value: 'fallback' });
    expect(alternate).toHaveBeenCalledOnce();
    expect(elicitInput).not.toHaveBeenCalled();
  });
});
