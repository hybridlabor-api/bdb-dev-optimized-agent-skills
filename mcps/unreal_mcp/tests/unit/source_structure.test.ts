import {
  readdirSync,
} from 'node:fs';
import {
  resolve,
} from 'node:path';

import {
  describe,
  expect,
  it,
} from 'vitest';

const sourceRoots = [
  {
    directory: resolve(process.cwd(), 'src/tools'),
    allowedTypeScriptFiles: [],
  },
  {
    directory: resolve(process.cwd(), 'src/tools/definitions'),
    allowedTypeScriptFiles: [],
  },
  {
    directory: resolve(process.cwd(), 'src/utils'),
    allowedTypeScriptFiles: ['index.ts'],
  },
  {
    directory: resolve(process.cwd(), 'src/types'),
    allowedTypeScriptFiles: ['index.ts'],
  },
] as const;

const listDirectories = (directory: string): readonly string[] =>
  readdirSync(directory, { withFileTypes: true }).flatMap((entry) => {
    if (!entry.isDirectory()) {
      return [];
    }

    const entryPath = resolve(directory, entry.name);
    return [entryPath, ...listDirectories(entryPath)];
  });

describe('TypeScript source structure', () => {
  it('keeps implementation files out of organized source roots', () => {
    const unexpectedRootFiles = sourceRoots.flatMap(
      ({ directory, allowedTypeScriptFiles }) => {
        const allowedFiles = new Set<string>(allowedTypeScriptFiles);
        return readdirSync(directory, { withFileTypes: true })
          .filter(
            (entry) =>
              entry.isFile() &&
              entry.name.endsWith('.ts') &&
              !allowedFiles.has(entry.name),
          )
          .map((entry) => resolve(directory, entry.name));
      },
    );

    expect(unexpectedRootFiles).toEqual([]);
  });

  it('keeps responsibility folders within a reviewable file count', () => {
    const overloadedDirectories = sourceRoots.flatMap(({ directory }) =>
      listDirectories(directory).flatMap((nestedDirectory) => {
        const typeScriptFileCount = readdirSync(nestedDirectory, {
          withFileTypes: true,
        }).filter(
          (entry) => entry.isFile() && entry.name.endsWith('.ts'),
        ).length;

        return typeScriptFileCount > 25
          ? [`${nestedDirectory}: ${typeScriptFileCount}`]
          : [];
      }),
    );

    expect(overloadedDirectories).toEqual([]);
  });
});
