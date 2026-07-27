import { readFileSync } from 'node:fs';
import { resolve } from 'node:path';

import { describe, expect, it } from 'vitest';

describe('server shutdown contracts', () => {
  it('stops health checks and the command queue before the automation bridge', () => {
    const source = readFileSync(
      resolve(process.cwd(), 'src/server/stdio-lifecycle.ts'),
      'utf8',
    );
    const shutdownStart = source.indexOf(
      'const handleShutdown = async',
    );
    const shutdownEnd = source.indexOf(
      'for (const signal of',
      shutdownStart,
    );
    const shutdownSource = source.slice(shutdownStart, shutdownEnd);

    const stopHealthChecks = shutdownSource.indexOf(
      'healthMonitor.stopHealthChecks()',
    );
    const disposeBridge = shutdownSource.indexOf('bridge.dispose()');
    const stopAutomationBridge = shutdownSource.indexOf(
      'automationBridge.stop()',
    );

    expect(stopHealthChecks).toBeGreaterThan(-1);
    expect(disposeBridge).toBeGreaterThan(stopHealthChecks);
    expect(stopAutomationBridge).toBeGreaterThan(disposeBridge);
  });
});
