#!/usr/bin/env bash
# GitHub repository metadata and release setup for GOLEM-3DMCP
# Run this script after authenticating with: gh auth login
#
# Usage: bash scripts/github-setup.sh

set -euo pipefail

REPO="TheKingHippopotamus/GOLEM-3DMCP-Rhino-"

echo "=== 1. Setting repository description ==="
gh repo edit "$REPO" \
  --description "MCP server giving AI agents (Claude, Cursor, Windsurf) full control over Rhinoceros 3D v8 — 105 tools for geometry, surfaces, booleans, Grasshopper, viewport capture, and script execution"

echo "=== 2. Setting repository topics ==="
gh repo edit "$REPO" \
  --add-topic mcp \
  --add-topic mcp-server \
  --add-topic rhino3d \
  --add-topic rhinoceros \
  --add-topic 3d-modeling \
  --add-topic cad \
  --add-topic claude \
  --add-topic cursor \
  --add-topic windsurf \
  --add-topic grasshopper \
  --add-topic ai-agents \
  --add-topic model-context-protocol \
  --add-topic python \
  --add-topic rhinocommon

echo "=== 3. Creating GitHub Release v0.1.0 ==="
gh release create v0.1.0 \
  --repo "$REPO" \
  --title "v0.1.0 — Initial Release" \
  --notes "$(cat <<'EOF'
## GOLEM-3DMCP v0.1.0

The first public release of GOLEM-3DMCP — an MCP server that gives AI agents full control over Rhinoceros 3D v8.

### Highlights

- **105 tools** across 9 categories: geometry creation, scene management, file I/O, boolean operations, surface tools, object manipulation, viewport control, scripting, and Grasshopper integration
- **Full read/write access** to Rhino 8 documents via RhinoCommon and rhinoscriptsyntax
- **Real-time viewport capture** as base64 PNG for visual feedback
- **Grasshopper parametric design** control — create/connect components, set sliders, run definitions
- **Arbitrary Python/RhinoScript execution** for operations beyond the built-in tool set
- Works with **Claude Code**, **Cursor**, **Windsurf**, and any MCP-compatible host

### Install

```bash
pip install golem-3dmcp
```

Or from source:

```bash
git clone https://github.com/TheKingHippopotamus/GOLEM-3DMCP-Rhino-.git
cd GOLEM-3DMCP-Rhino-
pip install -e .
```

### Requirements

- Python 3.10+
- Rhinoceros 3D v8 (macOS 12+)
- An MCP-compatible AI host (Claude Code, Cursor, or Windsurf)

See the [README](https://github.com/TheKingHippopotamus/GOLEM-3DMCP-Rhino-#readme) for full setup instructions.
EOF
)"

echo ""
echo "Done! Repository metadata and release v0.1.0 have been created."
