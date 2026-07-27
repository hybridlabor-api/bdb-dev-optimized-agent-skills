#!/usr/bin/env node

import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import {
  enclosingClassSource,
  maskCppLiteralsAndComments
} from './native-mcp-source-parser.mjs';
import { extractTypeScriptTools } from './native-mcp-typescript-parity-parser.mjs';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const repoRoot = path.resolve(__dirname, '..');

function auditPaths(config = {}) {
  const configuredRepoRoot = config.repoRoot ?? repoRoot;
  const nativeMcpRoot = config.nativeMcpRoot ?? path.join(
    configuredRepoRoot,
    'plugins/McpAutomationBridge/Source/McpAutomationBridge/Private/MCP'
  );
  return {
    repoRoot: configuredRepoRoot,
    tsDefinitionsRoot: config.tsDefinitionsRoot ?? path.join(configuredRepoRoot, 'src/tools/definitions'),
    nativeMcpRoot,
    nativeToolRegistryPath: config.nativeToolRegistryPath
      ?? path.join(nativeMcpRoot, 'Registry', 'McpToolRegistry.cpp'),
    nativeRoutingRoot: config.nativeRoutingRoot ?? path.join(nativeMcpRoot, 'Routing'),
    nativeToolsRoot: config.nativeToolsRoot ?? path.join(nativeMcpRoot, 'Tools')
  };
}

function recursiveFiles(root, predicate) {
  return fs.readdirSync(root, { withFileTypes: true })
    .flatMap((entry) => {
      const entryPath = path.join(root, entry.name);
      return entry.isDirectory() ? recursiveFiles(entryPath, predicate) : [entryPath];
    })
    .filter(predicate)
    .sort();
}

function sourceInsideMatch(source, match, openCharacter, closeCharacter) {
  if (match.index === undefined) return '';
  const openIndex = match.index + match[0].indexOf(openCharacter) + 1;
  const closeIndex = match.index + match[0].lastIndexOf(closeCharacter);
  return source.slice(openIndex, closeIndex);
}

function extractTextValues(text) {
  const maskedText = maskCppLiteralsAndComments(text);
  return [...text.matchAll(/TEXT\(\s*"([^"]+)"\s*\)/g)]
    .filter((match) => match.index !== undefined && maskedText.slice(match.index, match.index + 4) === 'TEXT')
    .map((match) => match[1]);
}

function extractNativeCanonicalRegistry(paths) {
  const source = fs.readFileSync(paths.nativeToolRegistryPath, 'utf8');
  const maskedSource = maskCppLiteralsAndComments(source);
  const registryMatch = maskedSource.match(/CanonicalToolNames\s*=\s*\{[\s\S]*?\};/);
  const registryBody = registryMatch
    ? sourceInsideMatch(source, registryMatch, '{', '}')
    : '';
  return extractTextValues(registryBody);
}

function nativeToolFiles(paths) {
  return recursiveFiles(paths.nativeToolsRoot, (filePath) => filePath.endsWith('.cpp'));
}

function buildNativeActionEvaluator(paths) {
  const source = recursiveFiles(
    paths.nativeRoutingRoot,
    (filePath) => /^McpConsolidatedActionRouting.*\.h$/.test(path.basename(filePath))
  )
    .map((filePath) => fs.readFileSync(filePath, 'utf8'))
    .join('\n');
  const maskedSource = maskCppLiteralsAndComments(source);
  const functionBodies = new Map(
    [...maskedSource.matchAll(
      /inline\s+(?:const\s+)?TArray<FString>&?\s+(\w+)\s*\(\)\s*\{[\s\S]*?\n\}/g
    )].map((match) => [match[1], sourceInsideMatch(source, match, '{', '}')])
  );
  const memo = new Map();

  function evaluate(functionName) {
    if (memo.has(functionName)) return memo.get(functionName);
    const body = functionBodies.get(functionName);
    if (!body) return [];

    const maskedBody = maskCppLiteralsAndComments(body);
    const staticList = maskedBody.match(
      /static const TArray<FString> Actions = \{[\s\S]*?\};/
    );
    if (staticList) {
      const listBody = sourceInsideMatch(body, staticList, '{', '}');
      const values = [...new Set(extractTextValues(listBody))].sort();
      memo.set(functionName, values);
      return values;
    }

    const firstSource = maskedBody.match(/TArray<FString> Actions = (\w+)\(\);/);
    let values = firstSource ? evaluate(firstSource[1]) : [];
    for (const append of maskedBody.matchAll(
      /AppendUniqueActions\(Actions, (\w+)\(\)\);/g
    )) {
      values = [...new Set([...values, ...evaluate(append[1])])].sort();
    }
    memo.set(functionName, values);
    return values;
  }

  return evaluate;
}

function extractActionEnumFromNativeTool(source, evaluateActions) {
  const maskedSource = maskCppLiteralsAndComments(source);
  const routedActionEnum = [...source.matchAll(
    /\.StringEnum\(\s*TEXT\(\s*"action"\s*\)\s*,\s*McpConsolidatedActions::(\w+)\(\)\s*,/g
  )].find((match) => match.index !== undefined
    && maskedSource.slice(match.index, match.index + '.StringEnum'.length) === '.StringEnum');
  if (routedActionEnum) {
    return evaluateActions(routedActionEnum[1]);
  }

  const inlineActionEnum = [...source.matchAll(
    /\.StringEnum\(\s*TEXT\(\s*"action"\s*\)\s*,\s*\{([\s\S]*?)\}\s*,/g
  )].find((match) => match.index !== undefined
    && maskedSource.slice(match.index, match.index + '.StringEnum'.length) === '.StringEnum');
  return [...new Set(extractTextValues(inlineActionEnum?.[1] ?? ''))].sort();
}

function extractNativeToolDefinitions(paths) {
  const evaluateActions = buildNativeActionEvaluator(paths);
  const tools = [];

  for (const filePath of nativeToolFiles(paths)) {
    const source = fs.readFileSync(filePath, 'utf8');
    const maskedSource = maskCppLiteralsAndComments(source);
    for (const match of source.matchAll(
      /GetName\(\)\s+const\s+override\s*\{\s*return\s+TEXT\(\s*"([^"]+)"\s*\)\s*;/g
    )) {
      if (match.index === undefined || maskedSource.slice(match.index, match.index + 'GetName'.length) !== 'GetName') {
        continue;
      }
      const toolSource = enclosingClassSource(source, match.index ?? 0);
      tools.push({
        name: match[1],
        actions: extractActionEnumFromNativeTool(toolSource, evaluateActions)
      });
    }
  }

  return tools.sort((left, right) => left.name.localeCompare(right.name));
}

function difference(left, right) {
  const rightSet = new Set(right);
  return left.filter((value) => !rightSet.has(value)).sort();
}

function uniqueSorted(values) {
  return [...new Set(values)].sort();
}

function duplicateValues(values) {
  const counts = new Map();
  for (const value of values) {
    counts.set(value, (counts.get(value) ?? 0) + 1);
  }
  return [...counts.entries()]
    .filter(([, count]) => count > 1)
    .map(([value]) => value)
    .sort();
}

export function auditNativeMcpParity(config = {}) {
  const paths = auditPaths(config);
  const typeScriptTools = extractTypeScriptTools(paths);
  const nativeRegistry = extractNativeCanonicalRegistry(paths);
  const nativeTools = extractNativeToolDefinitions(paths);
  const typeScriptNames = typeScriptTools.map((tool) => tool.name);
  const nativeDefinitionNames = nativeTools.map((tool) => tool.name);
  const duplicateNames = {
    typeScriptTools: duplicateValues(typeScriptNames),
    nativeCanonicalRegistry: duplicateValues(nativeRegistry),
    nativeToolDefinitions: duplicateValues(nativeDefinitionNames)
  };
  const uniqueTypeScriptNames = uniqueSorted(typeScriptNames);
  const uniqueNativeRegistryNames = uniqueSorted(nativeRegistry);
  const nativeRegistrySet = new Set(uniqueNativeRegistryNames);
  const nativeCanonicalTools = nativeTools.filter((tool) => nativeRegistrySet.has(tool.name));
  const nativeCanonicalDefinitionNames = nativeCanonicalTools.map((tool) => tool.name);
  const uniqueNativeCanonicalDefinitionNames = uniqueSorted(nativeCanonicalDefinitionNames);
  const nativeToolsByName = new Map(nativeCanonicalTools.map((tool) => [tool.name, tool]));
  const toolNameGaps = {
    missingFromNativeRegistry: difference(uniqueTypeScriptNames, uniqueNativeRegistryNames),
    extraInNativeRegistry: difference(uniqueNativeRegistryNames, uniqueTypeScriptNames),
    missingNativeDefinitions: difference(
      uniqueNativeRegistryNames,
      uniqueNativeCanonicalDefinitionNames
    )
  };
  const actionGaps = [];

  for (const tool of typeScriptTools) {
    const nativeActions = nativeToolsByName.get(tool.name)?.actions ?? [];
    const missingNativeActions = difference(tool.actions, nativeActions);
    const extraNativeActions = difference(nativeActions, tool.actions);
    if (missingNativeActions.length > 0 || extraNativeActions.length > 0) {
      actionGaps.push({ tool: tool.name, missingNativeActions, extraNativeActions });
    }
  }

  const counts = {
    typeScriptDefinitions: typeScriptTools.length,
    uniqueTypeScriptNames: uniqueTypeScriptNames.length,
    nativeRegistryEntries: nativeRegistry.length,
    uniqueNativeRegistryNames: uniqueNativeRegistryNames.length,
    nativeDefinitions: nativeCanonicalTools.length,
    uniqueNativeDefinitionNames: uniqueNativeCanonicalDefinitionNames.length
  };
  const hasMismatches = Object.values(duplicateNames).some((values) => values.length > 0)
    || Object.values(toolNameGaps).some((values) => values.length > 0)
    || actionGaps.length > 0;

  return {
    paths,
    counts,
    duplicateNames,
    toolNameGaps,
    actionGaps,
    hasMismatches
  };
}

export function runNativeMcpParityCli(config = {}) {
  const result = auditNativeMcpParity(config);
  console.log('Native MCP Action Parity Audit');
  console.log(`TypeScript tools: ${result.counts.typeScriptDefinitions}`);
  console.log(`Native canonical tools: ${result.counts.nativeRegistryEntries}`);
  console.log(`Native canonical definitions: ${result.counts.nativeDefinitions}`);
  console.log(`Tools with action mismatches: ${result.actionGaps.length}`);

  if (result.hasMismatches) {
    console.error(JSON.stringify({
      counts: result.counts,
      duplicateNames: result.duplicateNames,
      toolNameGaps: result.toolNameGaps,
      actionGaps: result.actionGaps
    }, null, 2));
    process.exitCode = 1;
  }

  return result;
}

if (process.argv[1] && path.resolve(process.argv[1]) === __filename) {
  runNativeMcpParityCli();
}
