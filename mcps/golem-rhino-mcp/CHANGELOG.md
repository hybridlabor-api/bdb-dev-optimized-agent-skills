# Changelog

All notable changes to GOLEM-3DMCP will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.2.0] - 2026-03-22

### Added
- `glama.json` metadata file for Glama.ai MCP directory integration
- Dockerfile for container-based server inspection and tool detection
- `.dockerignore` for optimized Docker builds
- Docker build & push workflow (GitHub Container Registry)
- GitHub Release creation in release workflow (alongside PyPI publish)
- Glama.ai score and card badges in README
- Related MCP servers metadata (blender-mcp, filesystem, github)
- Full tool inventory (87 tools) in glama.json for automated detection
- PyPI package distribution (`pip install golem-3dmcp`)
- CLI tool with commands: `golem start`, `golem install-rhino`, `golem uninstall-rhino`, `golem doctor`, `golem config`, `golem version`
- Cross-platform Rhino plugin deployment (macOS, Windows, Linux)
- `uvx` support for zero-config MCP server startup
- GitHub Actions CI/CD (test matrix + PyPI publishing)
- `src/` layout for proper Python packaging
- `hatch-vcs` for git tag-based versioning

### Changed
- Restructured from `mcp_server/` to `src/golem_3dmcp/` (src layout)
- Bundled `rhino_plugin/` as `_rhino_plugin` package data
- Updated all internal imports from `mcp_server` to `golem_3dmcp`
- Release workflow now creates GitHub Releases with auto-generated notes

## [0.1.0] - 2026-03-20

### Added
- Initial release with 105 MCP tools across 9 categories
- Scene intelligence (document info, layers, objects, groups, blocks)
- Geometry creation (points, curves, NURBS, solids, mesh, SubD, text)
- Geometry operations (booleans, trim, split, offset, fillet, chamfer)
- Surface operations (loft, sweep, revolve, extrude, network surface, patch)
- Object manipulation (transform, copy, array, group, properties)
- Grasshopper integration (definitions, parameters, recompute, bake)
- Viewport control (capture, camera, named views, display modes)
- File I/O (save, open, import, export in multiple formats)
- Script execution (Python, RhinoScript, Rhino commands)
- TCP bridge with length-prefixed JSON protocol
- Auto-reconnect with retry logic
- Rhino plugin with dispatcher and handler architecture
