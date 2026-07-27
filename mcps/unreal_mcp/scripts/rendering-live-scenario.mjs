#!/usr/bin/env node

import fs from 'node:fs/promises';
import { createRequire } from 'node:module';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { runToolTests } from '../tests/test-runner.mjs';

const __filename = fileURLToPath(import.meta.url);
const repoRoot = path.resolve(path.dirname(__filename), '..');
const require = createRequire(__filename);
const { createRenderingCaseSet } = require('../tests/mcp-tools/world/rendering-cases.cjs');

function parseArgs(argv) {
  const args = { mode: 'happy', evidence: '' };
  for (let i = 0; i < argv.length; i += 1) {
    const arg = argv[i];
    if (arg === '--mode') {
      args.mode = argv[++i] ?? args.mode;
    } else if (arg === '--evidence') {
      args.evidence = argv[++i] ?? '';
    }
  }
  if (!['happy', 'adversarial', 'all'].includes(args.mode)) {
    throw new Error('--mode must be happy, adversarial, or all');
  }
  if (!args.evidence) {
    throw new Error('--evidence is required');
  }
  return args;
}

async function latestReportPath(suiteName) {
  const reportsDir = path.join(repoRoot, 'tests', 'reports');
  const files = await fs.readdir(reportsDir);
  const prefix = `${suiteName}-test-results-`;
  const matches = [];
  for (const file of files) {
    if (!file.startsWith(prefix) || !file.endsWith('.json')) {
      continue;
    }
    const fullPath = path.join(reportsDir, file);
    const stat = await fs.stat(fullPath);
    matches.push({ fullPath, mtimeMs: stat.mtimeMs });
  }
  matches.sort((a, b) => b.mtimeMs - a.mtimeMs);
  if (matches.length === 0) {
    throw new Error(`No report found for ${suiteName}`);
  }
  return matches[0].fullPath;
}

function adversarialCases(caseSet) {
  const createCapture = caseSet.happyCases.find((testCase) =>
    testCase.arguments?.action === 'create_scene_capture_2d');
  const createPlanar = caseSet.happyCases.find((testCase) =>
    testCase.arguments?.action === 'create_planar_reflection');
  const createSphereCapture = caseSet.happyCases.find((testCase) =>
    testCase.arguments?.action === 'create_sphere_reflection_capture');
  const screenPercentage = caseSet.happyCases.find((testCase) =>
    testCase.arguments?.action === 'configure_screen_percentage');
  return [
    ...caseSet.setupCases,
    ...(createCapture ? [createCapture] : []),
    ...(createPlanar ? [createPlanar] : []),
    ...(createSphereCapture ? [createSphereCapture] : []),
    ...caseSet.adversarialCases,
    ...(screenPercentage ? [{
      ...screenPercentage,
      scenario: 'Adversarial: valid follow-up after structured errors'
    }] : []),
    ...caseSet.cleanupCases
  ];
}

function casesForMode(mode, caseSet) {
  if (mode === 'happy') {
    return [...caseSet.setupCases, ...caseSet.happyCases, ...caseSet.cleanupCases];
  }
  if (mode === 'adversarial') {
    return adversarialCases(caseSet);
  }
  return caseSet.suiteCases;
}

async function writeEvidence(evidencePath, mode, suiteName, cases, reportPath) {
  const report = JSON.parse(await fs.readFile(reportPath, 'utf8'));
  const results = Array.isArray(report.results) ? report.results : [];
  const totals = results.reduce((acc, result) => {
    acc.total += 1;
    acc[result.status] = (acc[result.status] ?? 0) + 1;
    return acc;
  }, { total: 0, passed: 0, failed: 0, skipped: 0 });
  const cleanupResults = results.filter((result) => result.scenario.startsWith('Cleanup:'));
  const evidence = {
    generatedAt: new Date().toISOString(),
    mode,
    suiteName,
    reportPath,
    totals,
    allPassed: (totals.failed ?? 0) === 0 && totals.total === cases.length,
    actions: results.map((result) => ({
      scenario: result.scenario,
      action: result.arguments?.action,
      status: result.status,
      detail: result.detail
    })),
    cleanup: {
      attempted: cleanupResults.length,
      passed: cleanupResults.filter((result) => result.status === 'passed').length
    }
  };
  await fs.mkdir(path.dirname(evidencePath), { recursive: true });
  await fs.writeFile(evidencePath, JSON.stringify(evidence, null, 2));
  return evidence;
}

const args = parseArgs(process.argv.slice(2));
const caseSet = createRenderingCaseSet();
const suiteName = `rendering-${args.mode}`;
const cases = casesForMode(args.mode, caseSet);

await runToolTests(suiteName, cases);
const reportPath = await latestReportPath(suiteName);
const evidence = await writeEvidence(args.evidence, args.mode, suiteName, cases, reportPath);
if (!evidence.allPassed) {
  process.exitCode = 1;
}
