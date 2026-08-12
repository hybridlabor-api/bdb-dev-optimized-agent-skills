---
name: godmode-eventtech
description: BDB EventTech Godmode. The supreme rulebook for the BDB Creator Engine, governing Godmode-3D, Godmode-Media, and the 22 creative-tech MCPs (TouchDesigner, Unreal, Resolve, Adobe, etc.).
---

# 🎬 BDB EventTech Godmode

This skill is the overarching architectural authority for the **BDB Creator Engine** (and its dedicated agents, like Godmode-3D and Godmode-Media). It dictates how AI agents must interact with the 22 creative-tech MCPs (TouchDesigner, Unreal Engine, DaVinci Resolve, Adobe, Rhino, GrandMA3, Resolume, etc.).

When working on creative, generative, or show-control environments, you must strictly follow these rules instead of standard web-development patterns.

## 1. The 11-Skill Mapping & Routing
This Godmode delegates specialized tasks to the 11 dedicated Creator Engine skills. Before attempting to execute node-based logic or 3D rendering, you MUST load the respective dedicated skill (if available in the agent's harness) to understand the tool's specifics:
*   **TouchDesigner / Nodes**: Route to the dedicated TouchDesigner skill for CHOP/TOP/DAT logic.
*   **Unreal Engine / 3D**: Route to the dedicated Unreal Blueprint & Geometry skills.
*   **GrandMA3 / DMX**: Route to the dedicated lighting logic skill.
*   **Adobe Suite / Resolve**: Route to the dedicated post-production scripting skills.
*(Note: These 11 dedicated skills are injected when the user installs the BDB Creator Extension).*

## 2. Real-Time Performance & Signal Flow
Generative and show-control systems cannot afford latency spikes.
*   **Frame Drops are Fatal**: Never write an external Python script that polls a 3D engine or TouchDesigner at 60fps via heavy REST requests. Always use optimized protocols (OSC, Shared Memory, or native C++ integrations).
*   **Deterministic Signal Flow**: Avoid circular dependencies in node graphs (e.g., feedback loops in TouchDesigner must have explicit 1-frame delays/feedback TOPs).

## 3. Generative Constraints (Anti-Slop 3D)
Do not build "AI-slop" in 3D or video.
*   **Intentionality over Noise**: Do not rely on generic Perlin noise or default particle systems. Every parameter must have a distinct artistic or physical intent.
*   **Physical Lighting**: In Unreal or Blender, enforce physically based rendering (PBR) rules. Lights must have inverse-square falloff; materials must have realistic roughness/metallic values.

## 4. Hardware & MCP Validation
Before executing complex generation or compiling a massive Blueprint:
*   Always validate that the corresponding MCP server (e.g., `touchdesigner-mcp`, `unreal_mcp`, `grandma3_mcp.py`) is actually connected and responsive via `ping` or `status` tools.
*   Validate GPU VRAM constraints before suggesting massive texture generation or heavy ComfyUI workflows.

## Universal Agent Harness Integration
This Godmode is universally compatible with the BDB Creator Extension.
*   **Cursor:** Auto-injected via `.cursor/rules/godmode-eventtech.mdc`.
*   **Claude Code:** Reads principles via `CLAUDE.md`.
*   **Agy / CLI Agents:** Automatically loaded during `/bdbmediastorm` sessions.
