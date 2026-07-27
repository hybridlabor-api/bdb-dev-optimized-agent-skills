import { describe, expect, it } from 'vitest';

import {
  evaluateAssertions,
  selectCaptureValue,
} from '../test-runner-response-utils.mjs';

describe('test runner response helpers', () => {
  it('accepts numeric assertions within an explicit tolerance', () => {
    const result = evaluateAssertions(
      {
        assertions: [
          {
            path: 'structuredContent.result.rotation.pitch',
            approximately: 35,
            tolerance: 0.001,
            label: 'restored pitch',
          },
        ],
      },
      {
        structuredContent: {
          result: {
            rotation: {
              pitch: 35.000000000000014,
            },
          },
        },
      },
    );

    expect(result).toEqual({ passed: true });
  });

  it('rejects numeric assertions outside their explicit tolerance', () => {
    const result = evaluateAssertions(
      {
        assertions: [
          {
            path: 'structuredContent.result.rotation.pitch',
            approximately: 35,
            tolerance: 0.001,
            label: 'restored pitch',
          },
        ],
      },
      {
        structuredContent: {
          result: {
            rotation: {
              pitch: 35.01,
            },
          },
        },
      },
    );

    expect(result.passed).toBe(false);
    expect(result.reason).toContain('within 0.001');
  });

  it('captures a selected field from the matching array item', () => {
    const value = selectCaptureValue(
      {
        result: {
          components: [
            { name: 'Sprite', class: 'BillboardComponent' },
            { name: 'SkyLightComponent0', class: 'SkyLightComponent' },
          ],
        },
      },
      {
        fromField: 'result.components',
        where: { path: 'class', includes: 'SkyLightComponent' },
        selectField: 'name',
      },
    );

    expect(value).toBe('SkyLightComponent0');
  });

  it('checks string fragments before dependent test actions run', () => {
    const result = evaluateAssertions(
      {
        assertions: [
          {
            path: 'structuredContent.result.directionalLightActorPath',
            includes: 'SnapshotSun_123',
            label: 'snapshot directional light selection',
          },
        ],
      },
      {
        structuredContent: {
          result: {
            directionalLightActorPath:
              '/Game/Test.Test:PersistentLevel.SnapshotSun_123',
          },
        },
      },
    );

    expect(result).toEqual({ passed: true });
  });
});
