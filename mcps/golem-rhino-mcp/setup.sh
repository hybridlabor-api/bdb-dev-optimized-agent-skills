#!/usr/bin/env bash
# =============================================================================
# GOLEM-3DMCP — Setup Script
# Sets up the Python virtual environment, installs all dependencies,
# installs the Rhino plugin startup shim, and configures Claude Code.
#
# Flags
# -----
#   --skip-rhino      Skip the Rhino plugin installation step.
#   --skip-claude     Skip the Claude Code configuration step.
#   --non-interactive Run without prompting (uses defaults for configure_claude).
#   --help            Show this message and exit.
# =============================================================================

set -euo pipefail

# ---------------------------------------------------------------------------
# Colour helpers (gracefully degrade if the terminal doesn't support them)
# ---------------------------------------------------------------------------
if tput colors &>/dev/null 2>&1 && [ "$(tput colors)" -ge 8 ]; then
    RED='\033[0;31m'
    GREEN='\033[0;32m'
    YELLOW='\033[1;33m'
    CYAN='\033[0;36m'
    BOLD='\033[1m'
    RESET='\033[0m'
else
    RED='' GREEN='' YELLOW='' CYAN='' BOLD='' RESET=''
fi

info()    { echo -e "${CYAN}[INFO]${RESET}  $*"; }
success() { echo -e "${GREEN}[OK]${RESET}    $*"; }
warn()    { echo -e "${YELLOW}[WARN]${RESET}  $*"; }
error()   { echo -e "${RED}[ERROR]${RESET} $*" >&2; }
header()  { echo -e "\n${BOLD}$*${RESET}"; }

# ---------------------------------------------------------------------------
# Parse flags
# ---------------------------------------------------------------------------
SKIP_RHINO=0
SKIP_CLAUDE=0
NON_INTERACTIVE=0

for arg in "$@"; do
    case "$arg" in
        --skip-rhino)       SKIP_RHINO=1 ;;
        --skip-claude)      SKIP_CLAUDE=1 ;;
        --non-interactive)  NON_INTERACTIVE=1 ;;
        --help|-h)
            echo "Usage: $0 [--skip-rhino] [--skip-claude] [--non-interactive]"
            echo ""
            echo "  --skip-rhino      Skip Rhino plugin installation (step 5)"
            echo "  --skip-claude     Skip Claude Code configuration (step 6)"
            echo "  --non-interactive Do not prompt; use defaults (implies --mode local"
            echo "                   for configure_claude)"
            echo ""
            exit 0
            ;;
        *)
            error "Unknown option: $arg  (use --help for usage)"
            exit 1
            ;;
    esac
done

# ---------------------------------------------------------------------------
# Resolve the project root (the directory this script lives in)
# ---------------------------------------------------------------------------
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$SCRIPT_DIR"
VENV_DIR="$PROJECT_ROOT/.venv"

header "============================================================"
header " GOLEM-3DMCP Setup"
header "============================================================"
echo ""

# ---------------------------------------------------------------------------
# Step 1: Find a suitable Python 3.10+ interpreter
# ---------------------------------------------------------------------------
header "Step 1 — Locating Python 3.10+"

PYTHON_BIN=""

# Helper: check if a given binary is Python >= 3.10
check_python() {
    local bin="$1"
    if command -v "$bin" &>/dev/null; then
        local ver
        ver="$("$bin" -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")' 2>/dev/null || true)"
        local major minor
        major="${ver%%.*}"
        minor="${ver##*.}"
        if [ -n "$ver" ] && [ "$major" -ge 3 ] && [ "$minor" -ge 10 ]; then
            echo "$bin"
            return 0
        fi
    fi
    return 1
}

# Priority order: pyenv shim → explicit version bins → brew → system python3
CANDIDATES=(
    "python3.13"
    "python3.12"
    "python3.11"
    "python3.10"
    "python3"
)

# If pyenv is present, prepend the pyenv-managed python
if command -v pyenv &>/dev/null; then
    PYENV_PYTHON="$(pyenv which python3 2>/dev/null || true)"
    if [ -n "$PYENV_PYTHON" ]; then
        CANDIDATES=("$PYENV_PYTHON" "${CANDIDATES[@]}")
    fi
fi

# Homebrew python path (Apple Silicon and Intel)
BREW_PATHS=(
    "/opt/homebrew/bin/python3"
    "/usr/local/bin/python3"
)
for bp in "${BREW_PATHS[@]}"; do
    CANDIDATES=("${CANDIDATES[@]}" "$bp")
done

for candidate in "${CANDIDATES[@]}"; do
    result="$(check_python "$candidate" 2>/dev/null || true)"
    if [ -n "$result" ]; then
        PYTHON_BIN="$result"
        break
    fi
done

if [ -z "$PYTHON_BIN" ]; then
    error "Could not find Python 3.10 or newer."
    echo ""
    echo "  Install options:"
    echo "    brew install python@3.12   # Homebrew"
    echo "    pyenv install 3.12.4       # pyenv"
    echo "    https://www.python.org/downloads/"
    echo ""
    exit 1
fi

PYTHON_VERSION="$("$PYTHON_BIN" --version 2>&1)"
success "Found: $PYTHON_BIN  ($PYTHON_VERSION)"

# ---------------------------------------------------------------------------
# Step 2: Create virtual environment
# ---------------------------------------------------------------------------
header "Step 2 — Virtual Environment"

if [ -d "$VENV_DIR" ]; then
    info "Existing .venv found at $VENV_DIR"
    # Verify it is functional
    if "$VENV_DIR/bin/python" -c "import sys" &>/dev/null; then
        success "Existing .venv is healthy — skipping creation"
    else
        warn ".venv appears broken — recreating"
        rm -rf "$VENV_DIR"
        "$PYTHON_BIN" -m venv "$VENV_DIR"
        success "Virtual environment recreated"
    fi
else
    info "Creating .venv with $PYTHON_BIN ..."
    "$PYTHON_BIN" -m venv "$VENV_DIR"
    success "Virtual environment created at $VENV_DIR"
fi

VENV_PYTHON="$VENV_DIR/bin/python"
VENV_PIP="$VENV_DIR/bin/pip"

# ---------------------------------------------------------------------------
# Step 3: Upgrade pip + install project dependencies
# ---------------------------------------------------------------------------
header "Step 3 — Installing Dependencies"

info "Upgrading pip ..."
"$VENV_PYTHON" -m pip install --upgrade pip --quiet

info "Installing golem-3dmcp (with dev extras) from pyproject.toml ..."
"$VENV_PYTHON" -m pip install -e ".[dev]" --quiet

success "All dependencies installed"

# Quick sanity check
"$VENV_PYTHON" -c "import mcp; import pydantic; import httpx" 2>/dev/null && \
    success "Core imports verified (mcp, pydantic, httpx)" || \
    warn "Could not verify core imports — check pip output above"

# ---------------------------------------------------------------------------
# Step 4: rhinocode CLI check
# ---------------------------------------------------------------------------
header "Step 4 — rhinocode CLI"

RHINOCODE_PATHS=(
    # Rhino 8 default install locations on macOS
    "/Applications/Rhino 8.app/Contents/Resources/bin/rhinocode"
    "/Applications/RhinoWIP.app/Contents/Resources/bin/rhinocode"
    # User may have added it to PATH manually
    "rhinocode"
)

RHINOCODE_BIN=""
for rp in "${RHINOCODE_PATHS[@]}"; do
    if command -v "$rp" &>/dev/null 2>&1 || [ -x "$rp" ]; then
        RHINOCODE_BIN="$rp"
        break
    fi
done

if [ -n "$RHINOCODE_BIN" ]; then
    success "rhinocode found: $RHINOCODE_BIN"
else
    warn "rhinocode CLI not found on PATH or in default locations."
    echo ""
    echo "  To add rhinocode to your shell PATH, run ONE of:"
    echo ""
    echo "    # zsh (default on macOS 10.15+):"
    echo "    echo 'export PATH=\"/Applications/Rhino 8.app/Contents/Resources/bin:\$PATH\"' >> ~/.zshrc"
    echo "    source ~/.zshrc"
    echo ""
    echo "    # bash:"
    echo "    echo 'export PATH=\"/Applications/Rhino 8.app/Contents/Resources/bin:\$PATH\"' >> ~/.bash_profile"
    echo "    source ~/.bash_profile"
    echo ""
    echo "  rhinocode is required for the Rhino plugin installation step."
    echo "  The MCP server itself will still work once the plugin is running."
fi

# ---------------------------------------------------------------------------
# Step 5: Rhino plugin installation
# ---------------------------------------------------------------------------
header "Step 5 — Rhino Plugin Installation"

if [ "$SKIP_RHINO" -eq 1 ]; then
    warn "Skipping Rhino plugin installation (--skip-rhino passed)."
else
    info "Running scripts/install_plugin.py ..."
    # Pass --dry-run so it only fails hard on a missing project structure,
    # not on a missing Rhino scripts directory (gracefully prints instructions).
    if "$VENV_PYTHON" "$PROJECT_ROOT/scripts/install_plugin.py"; then
        success "Rhino plugin installer completed."
    else
        warn "Rhino plugin installer exited with a non-zero status."
        warn "Review the output above for manual installation instructions."
        warn "(Setup will continue — this step is not fatal.)"
    fi
fi

# ---------------------------------------------------------------------------
# Step 6: Claude Code configuration
# ---------------------------------------------------------------------------
header "Step 6 — Claude Code Configuration"

if [ "$SKIP_CLAUDE" -eq 1 ]; then
    warn "Skipping Claude Code configuration (--skip-claude passed)."
else
    CONFIGURE_ARGS=()
    if [ "$NON_INTERACTIVE" -eq 1 ]; then
        # Default to project-local .mcp.json without prompting
        CONFIGURE_ARGS=("--mode" "local")
    fi

    info "Running scripts/configure_claude.py ..."
    if "$VENV_PYTHON" "$PROJECT_ROOT/scripts/configure_claude.py" "${CONFIGURE_ARGS[@]}"; then
        success "Claude Code configuration completed."
    else
        warn "configure_claude.py exited with a non-zero status."
        warn "You can re-run it manually:"
        warn "  $VENV_PYTHON $PROJECT_ROOT/scripts/configure_claude.py"
        warn "(Setup will continue — this step is not fatal.)"
    fi
fi

# ---------------------------------------------------------------------------
# Step 7: Summary
# ---------------------------------------------------------------------------
header "============================================================"
success "Setup complete."
header "============================================================"
echo ""
echo "  Python interpreter : $VENV_PYTHON"
echo "  Project root       : $PROJECT_ROOT"
echo ""
echo "  Flags used:"
echo "    --skip-rhino       : $SKIP_RHINO"
echo "    --skip-claude      : $SKIP_CLAUDE"
echo "    --non-interactive  : $NON_INTERACTIVE"
echo ""
echo "  Next steps:"
echo ""
echo "  1. Ensure Rhinoceros 8 is installed and open."
echo ""
echo "  2. Start the GOLEM server in Rhino:"
echo "       $VENV_PYTHON $PROJECT_ROOT/scripts/start_rhino_server.py"
echo ""
echo "  3. Test the full connection:"
echo "       $VENV_PYTHON $PROJECT_ROOT/scripts/test_connection.py"
echo ""
echo "  4. Start a Claude Code session from the project directory:"
echo "       cd $PROJECT_ROOT && claude"
echo "       # GOLEM-3DMCP tools will be available automatically."
echo ""
echo "  Re-run this script any time — it is safe to run multiple times."
echo ""
