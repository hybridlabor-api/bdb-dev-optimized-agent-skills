<p align="center">
  <img src="https://raw.githubusercontent.com/TheKingHippopotamus/GOLEM-3DMCP-Rhino-/claude/pypi-package-setup-PMCI5/nexus-pngs/king-hippo.png" alt="GOLEM-3DMCP" width="200"/>
</p>

<h1 align="center">GOLEM-3DMCP</h1>

<p align="center"><em>"Shaped from clay, brought to life by words"</em></p>

<p align="center">
  <strong>The most powerful MCP server for Rhinoceros 3D — 105 tools giving AI full read/write access to Rhino 8.</strong>
</p>

<p align="center">
  <a href="https://pypi.org/project/golem-3dmcp/"><img src="https://img.shields.io/pypi/v/golem-3dmcp.svg" alt="PyPI"></a>
  <a href="https://pypi.org/project/golem-3dmcp/"><img src="https://img.shields.io/pypi/status/golem-3dmcp.svg" alt="Status"></a>
  <a href="LICENSE"><img src="https://img.shields.io/badge/License-MIT-yellow.svg" alt="License: MIT"></a>
  <a href="https://www.rhino3d.com/"><img src="https://img.shields.io/badge/Rhino-8.x-blue.svg" alt="Rhino 8"></a>
  <a href="https://python.org"><img src="https://img.shields.io/badge/Python-3.10+-green.svg" alt="Python 3.10+"></a>
  <a href="https://modelcontextprotocol.io/"><img src="https://img.shields.io/badge/Protocol-MCP-purple.svg" alt="MCP"></a>
  <a href="https://glama.ai/mcp/servers/TheKingHippopotamus/GOLEM-3DMCP-Rhino-"><img src="https://glama.ai/mcp/servers/TheKingHippopotamus/GOLEM-3DMCP-Rhino-/badge" alt="GOLEM-3DMCP MCP server"></a>
</p>

---

GOLEM-3DMCP implements the [Model Context Protocol](https://modelcontextprotocol.io/) to give AI agents direct, programmatic control of Rhino 8 — create geometry, run booleans, drive Grasshopper, capture viewports, and execute arbitrary Python scripts, all through natural language.

Works with **Claude Code**, **Cursor**, **Windsurf**, and any MCP-compatible host.

---

## Demo — A City Built Entirely by AI

> An entire city generated in Rhino 8 through GOLEM-3DMCP — roads, skyscrapers, houses, trees, people, vehicles, a stadium, bridge, ferris wheel, harbor, wind turbines, and a floating GOLEM hologram. All created by Claude Code using natural language commands.

<p align="center">
  <a href="https://youtu.be/GoWN9vGlWCs"><img src="https://img.youtube.com/vi/GoWN9vGlWCs/maxresdefault.jpg" alt="Watch the demo" width="700"/></a>
</p>
<p align="center"><strong><a href="https://youtu.be/GoWN9vGlWCs">Watch the full demo on YouTube</a></strong></p>

<p align="center">
  <img src="https://raw.githubusercontent.com/TheKingHippopotamus/GOLEM-3DMCP-Rhino-/claude/pypi-package-setup-PMCI5/screenshots/city_wide.png" alt="GOLEM City — Wide Overview" width="700"/>
</p>
<p align="center"><em>Full city overview — ground, roads, buildings, park, harbor, sky</em></p>

<p align="center">
  <img src="https://raw.githubusercontent.com/TheKingHippopotamus/GOLEM-3DMCP-Rhino-/claude/pypi-package-setup-PMCI5/screenshots/city_skyline.png" alt="GOLEM City — Skyline" width="700"/>
</p>
<p align="center"><em>Skyline view — skyscrapers, bridge, wind turbines, floating GOLEM hologram</em></p>

<p align="center">
  <img src="https://raw.githubusercontent.com/TheKingHippopotamus/GOLEM-3DMCP-Rhino-/claude/pypi-package-setup-PMCI5/screenshots/city_monument.png" alt="GOLEM City — Monument" width="700"/>
</p>
<p align="center"><em>Close-up — GOLEM monument plaza, residential buildings, fountain</em></p>

<p align="center">
  <img src="https://raw.githubusercontent.com/TheKingHippopotamus/GOLEM-3DMCP-Rhino-/claude/pypi-package-setup-PMCI5/screenshots/city_street.png" alt="GOLEM City — Street Level" width="700"/>
</p>
<p align="center"><em>Street level — vehicles, people, street lamps, stadium, harbor with boats</em></p>

---

## Install

```bash
pip install golem-3dmcp
```

That's it. Three commands to go from zero to AI-powered Rhino:

```bash
# 1. Install
pip install golem-3dmcp

# 2. Deploy the Rhino plugin (one-time)
golem install-rhino

# 3. Verify everything works
golem doctor
```

### Connect to Your AI Agent

Add to your MCP configuration (Claude Code, Cursor, Windsurf, etc.):

```json
{
  "mcpServers": {
    "golem-3dmcp": {
      "command": "uvx",
      "args": ["golem-3dmcp"]
    }
  }
}
```

Start talking to Rhino through AI.

---

## 105 Tools Across 9 Categories

| Category | Tools | Highlights |
|----------|:-----:|------------|
| **Scene Intelligence** | 10 | Document info, layers, objects, groups, blocks — full pagination |
| **Geometry Creation** | 38 | Points, curves, NURBS, solids, mesh, SubD, text, dimensions, hatches |
| **Geometry Operations** | 19 | Boolean union/difference/intersection, trim, split, offset, fillet, chamfer |
| **Surface Operations** | 12 | Loft, sweep1/2, revolve, extrude, network surface, patch, edge surface, unroll |
| **Object Manipulation** | 21 | Move, copy, rotate, scale, mirror, array, join, explode, group, properties |
| **Grasshopper** | 9 | Open definitions, set/get parameters, recompute, bake, inspect components |
| **Viewport & Visualization** | 13 | Capture screenshots (base64 PNG), camera control, named views, display modes |
| **File Operations** | 9 | Save, open, import, export (STL, OBJ, STEP, IGES, FBX, 3MF, DWG, PDF...) |
| **Script Execution** | 4 | Execute arbitrary Python with full RhinoCommon access, run Rhino commands |

See [Tool Reference](https://github.com/TheKingHippopotamus/GOLEM-3DMCP-Rhino-/blob/claude/pypi-package-setup-PMCI5/docs/TOOL_REFERENCE.md) for the complete API with parameters and examples.

---

## Architecture

```
 AI Agent (Claude Code / Cursor / Windsurf)
      |
      |  MCP (stdio, JSON-RPC)
      v
+---------------------------+
|     GOLEM MCP Server      |
|     Python 3.10+          |
|     FastMCP + 9 tool      |
|     modules               |
+---------------------------+
      |
      |  TCP 127.0.0.1:9876
      |  Length-prefixed JSON
      v
+---------------------------+
|     Rhino Plugin          |
|     Python 3.9 (embedded) |
|     TCP Server            |
|     9 handler modules     |
+---------------------------+
      |
      |  RhinoCommon + rhinoscriptsyntax
      v
+---------------------------+       +-------------------------+
|     Rhinoceros 3D         | <---> |   Grasshopper           |
|     Document, Geometry,   |       |   Sub-server :9877      |
|     Layers, Views         |       |   Definitions, Params   |
+---------------------------+       +-------------------------+
```

---

## Quick Start Examples

**Create and combine geometry:**
```
Create a 100 x 50 x 30 box on a layer called 'Structure',
then boolean-union it with a sphere of radius 20 centred at [50, 25, 30].
```

**Query the scene:**
```
List all objects on the 'Walls' layer and tell me their volumes.
```

**Drive Grasshopper:**
```
Open parametric_facade.gh, set the 'PanelCount' slider to 24,
recompute, and bake the result to a 'Facade' layer.
```

**Capture a viewport:**
```
Set perspective view to shaded mode, zoom to extents, and capture a screenshot.
```

**Execute arbitrary Python:**
```python
import Rhino.Geometry as rg
pts = [rg.Point3d(i*10, 0, i**2) for i in range(20)]
crv = rg.Curve.CreateInterpolatedCurve(pts, 3)
sc.doc.Objects.AddCurve(crv)
__result__ = {"point_count": len(pts), "length": crv.GetLength()}
```

---

## Loading the Rhino Plugin

1. Open Rhino 8
2. Open Script Editor: `Tools > Python Script > Edit`
3. Open `startup.py` (deployed by `golem install-rhino`) and click **Run**

```
GOLEM-3DMCP: Starting server on 127.0.0.1:9876...
GOLEM-3DMCP: Server started successfully!
GOLEM-3DMCP: 135 handler methods registered.
```

**Auto-start on every Rhino launch:** `Tools > Options > RhinoScript > Startup Scripts > Add startup.py`

---

## Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `GOLEM_RHINO_HOST` | `127.0.0.1` | Rhino plugin host |
| `GOLEM_RHINO_PORT` | `9876` | Rhino plugin TCP port |
| `GOLEM_GH_PORT` | `9877` | Grasshopper sub-server port |
| `GOLEM_TIMEOUT` | `30` | Command timeout (seconds) |
| `GOLEM_HEAVY_TIMEOUT` | `120` | Heavy operation timeout (seconds) |

---

## Requirements

| Requirement | Version |
|-------------|---------|
| Rhinoceros 3D | 8.x (macOS) |
| Python | 3.10+ |
| macOS | 12 Monterey or newer |

The Rhino plugin runs inside Rhino's embedded Python 3.9 with zero external dependencies.

---

## Troubleshooting

| Problem | Quick Fix |
|---------|-----------|
| Connection refused | Start Rhino + run `startup.py` |
| Port already in use | `lsof -i :9876` then kill the process |
| MCP server not in Claude | Check your MCP config JSON |
| Grasshopper tools fail | Open Grasshopper in Rhino first |
| Python version error | Need Python 3.10+ for MCP server |

Run `golem doctor` to diagnose issues automatically.

See [Troubleshooting Guide](https://github.com/TheKingHippopotamus/GOLEM-3DMCP-Rhino-/blob/claude/pypi-package-setup-PMCI5/docs/TROUBLESHOOTING.md) for detailed solutions.

---

## Documentation

- [Architecture](https://github.com/TheKingHippopotamus/GOLEM-3DMCP-Rhino-/blob/claude/pypi-package-setup-PMCI5/docs/ARCHITECTURE.md) — System design, threading model, data flow
- [Tool Reference](https://github.com/TheKingHippopotamus/GOLEM-3DMCP-Rhino-/blob/claude/pypi-package-setup-PMCI5/docs/TOOL_REFERENCE.md) — All 105 tools with parameters and examples
- [Protocol Specification](https://github.com/TheKingHippopotamus/GOLEM-3DMCP-Rhino-/blob/claude/pypi-package-setup-PMCI5/docs/PROTOCOL.md) — TCP wire format, message framing, error codes
- [Troubleshooting](https://github.com/TheKingHippopotamus/GOLEM-3DMCP-Rhino-/blob/claude/pypi-package-setup-PMCI5/docs/TROUBLESHOOTING.md) — Common issues and solutions

---

## Testing

```bash
# Unit tests (no Rhino needed)
pytest tests/ -v --ignore=tests/test_integration.py

# Full suite (integration tests auto-skip if Rhino not running)
pytest tests/ -v

# Integration tests only (requires Rhino + plugin running)
pytest tests/test_integration.py -v -m integration
```

---

## Branch Strategy

This repository uses two branches:

| Branch | Purpose |
|--------|---------|
| **`main`** | GOLEM-3DMCP source development — features, bug fixes, docs |
| **`claude/pypi-package-setup-PMCI5`** | PyPI packaging & releases — build config, versioning, publish scripts |

- **Develop** on `main` — all tool modules, Rhino plugin, tests, and documentation live here.
- **Release** from the PyPI branch — packaging structure (`pyproject.toml`, `src/` layout, publish scripts) is managed separately so releases don't pollute the development history.

```
main                          ← development
  └── claude/pypi-package-setup-PMCI5  ← PyPI releases (pip install golem-3dmcp)
```

---

## Project Structure

```
golem-3dmcp/
├── src/golem_3dmcp/           # MCP Server (pip install golem-3dmcp)
│   ├── cli.py                 #   CLI entry point (golem command)
│   ├── server.py              #   FastMCP server
│   ├── connection.py          #   TCP client (singleton, thread-safe)
│   ├── protocol.py            #   Wire format: 4-byte length prefix + JSON
│   ├── config.py              #   Environment variable configuration
│   ├── models/                #   Pydantic data models
│   ├── tools/                 #   9 MCP tool modules
│   └── _rhino_plugin/         #   Bundled Rhino plugin (deployed via CLI)
├── tests/                     # 226 tests (pytest)
├── docs/                      # Architecture, protocol spec, tool reference
└── pyproject.toml             # Package definition
```

---

## Contributing

We welcome contributions! Here's how to get started:

### Development Setup

```bash
# Clone the repository
git clone https://github.com/TheKingHippopotamus/GOLEM-3DMCP-Rhino-.git
cd GOLEM-3DMCP-Rhino-

# Create virtual environment (Python 3.10+ required)
python -m venv .venv
source .venv/bin/activate  # or .venv\Scripts\activate on Windows
pip install -e ".[dev]"

# Install pre-commit hooks
pre-commit install
```

### Code Quality

All CI checks must pass before merging:

```bash
# Lint
ruff check src/ tests/

# Type check (strict mode)
mypy src/golem_3dmcp/ --ignore-missing-imports

# Unit tests (no Rhino needed)
pytest tests/ -v --ignore=tests/test_integration.py

# Integration tests (requires Rhino 8 + plugin running)
pytest tests/test_integration.py -v -m integration
```

### Key Things to Know

- **Two Python runtimes** — The MCP server runs on Python 3.10+, but `_rhino_plugin/` runs inside Rhino's embedded Python 3.9. They communicate over TCP. Don't add 3.10+ syntax to the plugin.
- **`_rhino_plugin/` is excluded from mypy** — It uses Rhino-specific imports (`Rhino.*`, `Grasshopper.*`, `clr`) that don't exist in a standard environment.
- **Tool registration** — Tools use `@mcp.tool()` decorators. Each tool module imports `mcp` from `server.py`. Add new tools in `src/golem_3dmcp/tools/` and register the module in `server.py:main()`.
- **Thread safety** — `RhinoConnection` is a thread-safe singleton with a lock around socket I/O. Don't bypass `send_command()`.
- **Protocol** — TCP messages use 4-byte length-prefixed JSON. See `protocol.py` for the wire format.

### Pull Request Process

1. Create a feature branch from `main`
2. Make your changes
3. Ensure all checks pass (`ruff`, `mypy`, `pytest`)
4. Submit a PR with a clear description

See [CONTRIBUTING.md](CONTRIBUTING.md) for the full guide.

---

## License

MIT License. See [LICENSE](https://github.com/TheKingHippopotamus/GOLEM-3DMCP-Rhino-/blob/claude/pypi-package-setup-PMCI5/LICENSE) for details.

---

## MCP Server on Glama

<a href="https://glama.ai/mcp/servers/TheKingHippopotamus/GOLEM-3DMCP-Rhino-">
  <img width="380" height="200" src="https://glama.ai/mcp/servers/TheKingHippopotamus/GOLEM-3DMCP-Rhino-/badge?type=card" alt="GOLEM-3DMCP server on Glama" />
</a>

---

## Credits

<p align="center">
  <img src="https://raw.githubusercontent.com/TheKingHippopotamus/GOLEM-3DMCP-Rhino-/claude/pypi-package-setup-PMCI5/nexus-pngs/king-hippo.png" alt="King Hippopotamus" width="200"/>
</p>

<p align="center">
  Created by <strong>King Hippopotamus</strong><br/>
  Built by <strong>NEXUS AI</strong> — 195 autonomous agents | 20 departments | 11 tiers
</p>

<p align="center">
  <img src="https://raw.githubusercontent.com/TheKingHippopotamus/GOLEM-3DMCP-Rhino-/claude/pypi-package-setup-PMCI5/nexus-pngs/CEO.png" alt="CEO" width="100" title="CEO — The Lion"/>
  <img src="https://raw.githubusercontent.com/TheKingHippopotamus/GOLEM-3DMCP-Rhino-/claude/pypi-package-setup-PMCI5/nexus-pngs/CTO.png" alt="CTO" width="100" title="CTO — The Owl"/>
  <img src="https://raw.githubusercontent.com/TheKingHippopotamus/GOLEM-3DMCP-Rhino-/claude/pypi-package-setup-PMCI5/nexus-pngs/CPO.png" alt="CPO" width="100" title="CPO — The Fox"/>
  <img src="https://raw.githubusercontent.com/TheKingHippopotamus/GOLEM-3DMCP-Rhino-/claude/pypi-package-setup-PMCI5/nexus-pngs/COO.png" alt="COO" width="100" title="COO — The Bear"/>
  <img src="https://raw.githubusercontent.com/TheKingHippopotamus/GOLEM-3DMCP-Rhino-/claude/pypi-package-setup-PMCI5/nexus-pngs/CFO.png" alt="CFO" width="100" title="CFO — The Cobra"/>
  <img src="https://raw.githubusercontent.com/TheKingHippopotamus/GOLEM-3DMCP-Rhino-/claude/pypi-package-setup-PMCI5/nexus-pngs/CISO.png" alt="CISO" width="100" title="CISO — The Scorpion"/>
</p>
<p align="center">
  <img src="https://raw.githubusercontent.com/TheKingHippopotamus/GOLEM-3DMCP-Rhino-/claude/pypi-package-setup-PMCI5/nexus-pngs/CMO.png" alt="CMO" width="100" title="CMO — The Peacock"/>
  <img src="https://raw.githubusercontent.com/TheKingHippopotamus/GOLEM-3DMCP-Rhino-/claude/pypi-package-setup-PMCI5/nexus-pngs/CRO.png" alt="CRO" width="100" title="CRO — The Wolf"/>
  <img src="https://raw.githubusercontent.com/TheKingHippopotamus/GOLEM-3DMCP-Rhino-/claude/pypi-package-setup-PMCI5/nexus-pngs/CHRO.png" alt="CHRO" width="100" title="CHRO — The Elephant"/>
  <img src="https://raw.githubusercontent.com/TheKingHippopotamus/GOLEM-3DMCP-Rhino-/claude/pypi-package-setup-PMCI5/nexus-pngs/CLO.png" alt="CLO" width="100" title="CLO — The Raven"/>
  <img src="https://raw.githubusercontent.com/TheKingHippopotamus/GOLEM-3DMCP-Rhino-/claude/pypi-package-setup-PMCI5/nexus-pngs/CAIO.png" alt="CAIO" width="100" title="CAIO — The Octopus"/>
</p>

---

**Built with:**
[FastMCP](https://github.com/jlowin/fastmcp) ·
[RhinoCommon](https://developer.rhino3d.com/api/rhinocommon/) ·
[rhinoscriptsyntax](https://developer.rhino3d.com/api/RhinoScriptSyntax/) ·
[Grasshopper SDK](https://developer.rhino3d.com/api/grasshopper/)

---

<p align="center"><em>"From formless clay, through the power of words, form emerges."</em></p>
