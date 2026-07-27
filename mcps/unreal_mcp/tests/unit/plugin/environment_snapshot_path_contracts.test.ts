/// <reference types="node" />

import { readFileSync } from 'node:fs';
import { resolve } from 'node:path';

import { describe, expect, it } from 'vitest';

const environmentSource = (filename: string): string =>
  readFileSync(
    resolve(
      process.cwd(),
      'plugins/McpAutomationBridge/Source/McpAutomationBridge/Private/Domains/Environment',
      filename,
    ),
    'utf8',
  );

const snapshotSource = (): string =>
  [
    environmentSource('McpAutomationBridge_EnvironmentSnapshotPaths.cpp'),
    environmentSource('McpAutomationBridge_EnvironmentHandlersBuildSnapshots.cpp'),
  ].join('\n');

describe('environment snapshot path contracts', () => {
  it('rejects embedded nulls without treating the FString terminator as input', () => {
    // Given
    const source = snapshotSource();
    const nullCheck = source.slice(
      source.indexOf('bool ContainsNullCharacter'),
      source.indexOf('bool NormalizeSnapshotRelativePath'),
    );

    // When
    const explicitLengthCheck = nullCheck.indexOf(
      'Value.Len() != FCString::Strlen(*Value)',
    );

    // Then
    expect(explicitLengthCheck).toBeGreaterThan(-1);
    expect(nullCheck).not.toContain("FindChar(TEXT('\\0')");
  });

  it('rewrites accepted prefix casing before exact allowlist enforcement', () => {
    // Given
    const source = snapshotSource();
    const canonicalizer = source.slice(
      source.indexOf('bool CanonicalizeAllowedSnapshotRelativePath'),
      source.indexOf('bool ResolveSnapshotPath'),
    );

    // When
    const caseInsensitiveMatch = canonicalizer.indexOf(
      'ESearchCase::IgnoreCase',
    );
    const canonicalRewrite = canonicalizer.indexOf(
      'Path = FString(CanonicalPrefix) + Path.RightChop',
    );
    const exactPrefixCheck = canonicalizer.indexOf(
      'Path.StartsWith(CanonicalPrefix, ESearchCase::CaseSensitive)',
    );
    const projectResolution = source.indexOf('McpResolveProjectFilePath(');

    // Then
    expect(caseInsensitiveMatch).toBeGreaterThan(-1);
    expect(canonicalRewrite).toBeGreaterThan(caseInsensitiveMatch);
    expect(exactPrefixCheck).toBeGreaterThan(canonicalRewrite);
    expect(source).toContain(
      'if (!CanonicalizeAllowedSnapshotRelativePath(RelativePath))',
    );
    expect(projectResolution).toBeGreaterThan(exactPrefixCheck);
  });

  it('rejects Windows device basenames before resolving or accessing the file', () => {
    // Given
    const source = snapshotSource();
    const reservedValidation = source.slice(
      source.indexOf('bool IsWindowsReservedFilename'),
      source.indexOf('bool IsSafeSnapshotFilename'),
    );
    const filenameCheck = source.slice(
      source.indexOf('bool IsSafeSnapshotFilename'),
      source.indexOf('bool CanonicalizeAllowedSnapshotRelativePath'),
    );

    // When
    const reservedCheck = filenameCheck.indexOf('IsWindowsReservedFilename');
    const finalLeafCheck = source.indexOf(
      'IsSafeSnapshotFilename(FPaths::GetCleanFilename(RelativePath))',
    );
    const projectResolution = source.indexOf('McpResolveProjectFilePath(');

    // Then
    expect(reservedCheck).toBeGreaterThan(-1);
    expect(reservedValidation).toContain('TEXT("CON")');
    expect(reservedValidation).toContain('TEXT("PRN")');
    expect(reservedValidation).toContain('TEXT("AUX")');
    expect(reservedValidation).toContain('TEXT("NUL")');
    expect(reservedValidation).toContain('TEXT("COM")');
    expect(reservedValidation).toContain('TEXT("LPT")');
    expect(finalLeafCheck).toBeGreaterThan(-1);
    expect(projectResolution).toBeGreaterThan(finalLeafCheck);
  });

  it('writes snapshot JSON with the UTF-8 encoding used for byte accounting', () => {
    // Given
    const source = snapshotSource();

    // When
    const utf8Conversion = source.indexOf('const FTCHARToUTF8 JsonUtf8');
    const encodedWrite = source.indexOf(
      'FFileHelper::EEncodingOptions::ForceUTF8WithoutBOM',
    );
    const byteAccounting = source.indexOf(
      'TEXT("bytesWritten"), JsonUtf8.Length()',
    );

    // Then
    expect(utf8Conversion).toBeGreaterThan(-1);
    expect(encodedWrite).toBeGreaterThan(utf8Conversion);
    expect(byteAccounting).toBeGreaterThan(encodedWrite);
  });
});
