#!/usr/bin/env node
// Pack the Claude Desktop connector into connector.mcpb.
//
// The launcher's canonical source lives in ../shared/router-launcher.mjs. We pack
// from a staging copy and write the launcher into it straight from shared/, so the
// packed connector always carries the real shared source regardless of what (if
// anything) sits at connector/router-launcher.mjs in the working tree.

import { mkdtempSync, cpSync, readFileSync, writeFileSync, rmSync } from "node:fs";
import { join, dirname } from "node:path";
import { tmpdir } from "node:os";
import { fileURLToPath } from "node:url";
import { spawnSync } from "node:child_process";

const here = dirname(fileURLToPath(import.meta.url));
const sharedLauncher = join(here, "..", "shared", "router-launcher.mjs");
const out = join(here, "connector.mcpb");

const stage = mkdtempSync(join(tmpdir(), "rhino-connector-"));
try {
  cpSync(here, stage, {
    recursive: true,
    filter: src => src !== out && src !== join(here, "build.mjs"),
  });

  // Drop anything copied to the launcher path, then write a fresh regular file from
  // the canonical source. (rmSync clears a stale copy/link; writeFileSync would
  // otherwise follow a live symlink and clobber ../shared.)
  const staged = join(stage, "router-launcher.mjs");
  rmSync(staged, { force: true });
  writeFileSync(staged, readFileSync(sharedLauncher));

  const res = spawnSync("npx", ["--yes", "@anthropic-ai/mcpb", "pack", stage, out], {
    stdio: "inherit",
    shell: process.platform === "win32",
  });
  process.exit(res.status ?? 1);
} finally {
  rmSync(stage, { recursive: true, force: true });
}
