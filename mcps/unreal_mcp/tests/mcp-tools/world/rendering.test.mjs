#!/usr/bin/env node
/**
 * build_environment Tool Integration Tests
 * Covers Advanced lighting, rendering, post-process, and scene-capture actions.
 */

import { runToolTests } from '../../test-runner.mjs';

const { createRequire } = await import('node:module');
const localRequire = createRequire(`${process.cwd()}/tests/mcp-tools/world/rendering.test.mjs`);
const { createRenderingCaseSet } = localRequire('./rendering-cases.cjs');

const { suiteCases } = createRenderingCaseSet();

runToolTests('rendering', suiteCases);
