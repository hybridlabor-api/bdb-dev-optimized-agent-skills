# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/),
and this project adheres to [Semantic Versioning](https://semver.org/).

## [Unreleased]

## [0.1.3] — 2026-06-21

### Fixed
- Packaged `models.py` in the Blender add-on zip.
- Removed the Blender add-on's runtime dependency on third-party validation packages.
- Switched the add-on model import to package-relative import for installed zip compatibility.

## [0.1.2] — 2026-06-21

### Added
- CI pipeline (`ci.yml`): ruff lint, ruff format, mypy, pytest with coverage across Python 3.10–3.13.
- Publish workflow now gates on CI passing before releasing to PyPI.
- Ruff configuration (pycodestyle, pyflakes, isort, pep8-naming, pyupgrade, bugbear, simplify, type-checking).
- Mypy configuration with `check_untyped_defs` and `ignore_missing_imports`.
- pytest-cov integration with 50 % minimum coverage threshold.
- `CONTRIBUTING.md` with development workflow, code style, and PR guidelines.
- This `CHANGELOG.md`.
- Pydantic models for runtime validation of all bridge command parameters (`addon/models.py`).
- `Dockerfile` and `.dockerignore` for containerized deployment.
- Explicit `pydantic>=2.0` dependency.

### Fixed
- Import sorting and formatting across all source files.
- Ambiguous variable names flagged by ruff (`l` → `line`, `label`).
- Replaced bare `try/except pass` with `contextlib.suppress` in headless executor.
- Kept the Blender bridge request queue timer alive across `.blend` file loads.

## [0.1.1] — 2026-03-08

### Fixed
- Blender bridge execution reliability.
- Documented Codex CLI setup in README.

## [0.1.0] — 2026-02-28

### Added
- Initial MCP server with 27 tools across 7 namespaces: scene inspection,
  object mutation, materials, rendering & export, history, and Python execution.
- Blender add-on with TCP bridge server, command handler, and job manager.
- Headless Blender execution transport (`blender -b --python`).
- Async job system (create, poll, cancel, list) for long-running scripts.
- Safety model: module blocklist, output bounding, cooperative timeouts,
  script path validation, optional tool whitelist.
- Automatic undo for mutation commands.
- Script library with 11 reusable Blender scripts.
- Demo scenes (dam-break simulation, pipe studies).
- PyPI packaging with OIDC-based GitHub Actions publishing.
- Architecture documentation and Python execution design spec.
- Unit tests for MCP server and add-on (mocked `bpy`).

[Unreleased]: https://github.com/djeada/blender-mcp-server/compare/v0.1.3...HEAD
[0.1.3]: https://github.com/djeada/blender-mcp-server/compare/v0.1.2...v0.1.3
[0.1.2]: https://github.com/djeada/blender-mcp-server/compare/v0.1.1...v0.1.2
[0.1.1]: https://github.com/djeada/blender-mcp-server/compare/v0.1.0...v0.1.1
[0.1.0]: https://github.com/djeada/blender-mcp-server/releases/tag/v0.1.0
