#!/usr/bin/env bash
# publish.sh — Build and publish golem-3dmcp to PyPI
# Usage:
#   ./scripts/publish.sh              # publish to PyPI
#   ./scripts/publish.sh --test       # publish to TestPyPI first
#   PYPI_TOKEN=pypi-... ./scripts/publish.sh   # pass token via env var

set -euo pipefail

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

info()  { echo -e "${GREEN}[INFO]${NC}  $*"; }
warn()  { echo -e "${YELLOW}[WARN]${NC}  $*"; }
error() { echo -e "${RED}[ERROR]${NC} $*"; exit 1; }

# ── Move to repo root ──────────────────────────────────────────────
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR/.."
info "Working directory: $(pwd)"

# ── Check prerequisites ────────────────────────────────────────────
command -v python3 >/dev/null 2>&1 || error "python3 is not installed"

info "Installing / upgrading build tools..."
python3 -m pip install build "twine>=5.0,<6.0" --quiet

# ── Clean previous builds ──────────────────────────────────────────
if [ -d dist ]; then
    warn "Removing old dist/ directory"
    rm -rf dist
fi

# ── Build ──────────────────────────────────────────────────────────
info "Building sdist and wheel..."
python3 -m build

info "Built artifacts:"
ls -lh dist/

# ── Validate ───────────────────────────────────────────────────────
info "Checking packages with twine..."
python3 -m twine check dist/*

# ── Publish ────────────────────────────────────────────────────────
USE_TEST_PYPI=false
if [[ "${1:-}" == "--test" ]]; then
    USE_TEST_PYPI=true
fi

if [ "$USE_TEST_PYPI" = true ]; then
    info "Uploading to TestPyPI..."
    REPO_URL="https://test.pypi.org/legacy/"
    if [ -n "${TEST_PYPI_TOKEN:-}" ]; then
        python3 -m twine upload dist/* \
            --repository-url "$REPO_URL" \
            --username __token__ \
            --password "$TEST_PYPI_TOKEN"
    else
        python3 -m twine upload dist/* --repository-url "$REPO_URL"
    fi
    echo ""
    info "Done! View at: https://test.pypi.org/project/golem-3dmcp/"
    echo ""
    warn "To test install: pip install -i https://test.pypi.org/simple/ golem-3dmcp"
else
    info "Uploading to PyPI..."
    if [ -n "${PYPI_TOKEN:-}" ]; then
        python3 -m twine upload dist/* \
            --username __token__ \
            --password "$PYPI_TOKEN"
    else
        python3 -m twine upload dist/*
    fi
    echo ""
    info "Done! View at: https://pypi.org/project/golem-3dmcp/"
    echo ""
    info "Install with: pip install golem-3dmcp"
fi
