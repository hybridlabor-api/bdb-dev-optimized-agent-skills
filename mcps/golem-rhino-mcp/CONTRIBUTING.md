# Contributing to GOLEM-3DMCP

Thank you for your interest in contributing to GOLEM-3DMCP!

## Development Setup

```bash
# Clone the repository
git clone https://github.com/TheKingHippopotamus/GOLEM-3DMCP-Rhino-.git
cd GOLEM-3DMCP-Rhino-

# Create virtual environment and install dev dependencies
python -m venv .venv
source .venv/bin/activate  # or .venv\Scripts\activate on Windows
pip install -e ".[dev]"

# Install pre-commit hooks
pre-commit install
```

## Running Tests

```bash
# Unit tests (no Rhino required)
pytest tests/ -v --ignore=tests/test_integration.py

# Integration tests (requires Rhino 8 with plugin running)
pytest tests/test_integration.py -v -m integration
```

## Code Quality

```bash
# Lint
ruff check src/ tests/

# Format
ruff format src/ tests/

# Type check
mypy src/golem_3dmcp/
```

## Project Structure

- `src/golem_3dmcp/` — MCP server package (Python 3.10+)
- `src/golem_3dmcp/_rhino_plugin/` — Bundled Rhino plugin (Python 3.9, runs inside Rhino)
- `tests/` — Test suite
- `docs/` — Documentation
- `scripts/` — Development utility scripts

## Pull Request Process

1. Create a feature branch from `main`
2. Make your changes
3. Ensure tests pass and linting is clean
4. Submit a pull request with a clear description

## Architecture

See [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) for the full system design.

## License

By contributing, you agree that your contributions will be licensed under the MIT License.
