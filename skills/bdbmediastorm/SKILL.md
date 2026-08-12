---
name: bdbmediastorm
description: The ultimate creative-tech and show-control brainstorming engine. Orchestrates multi-agent ideation focused on signal flow, hardware constraints, protocols, and BDB MCP integrations. Now strictly governed by the 3 Core Godmodes (engineering, ui-ux, shipping).
---

# BDB MediaStorm: Show-Control & Creative-Tech Ideation

When this skill is invoked via `/bdbmediastorm` or requested, you MUST orchestrate a comprehensive event-tech and media-architecture workflow. Forget standard web apps, UI/UX, or standard coding practices. Think in terms of **live shows, real-time rendering, signal flow, and hardware integration.**

## Core Requirements & Workflow

You are strictly required to enforce the following pillars, applying the **3 Core Godmodes** (`engineering-godmode`, `ui-ux-godmode`, `shipping-godmode`) to a hardware-first context:

### 1. Multi-Agent Media Brainstorming
- Do NOT brainstorm alone. Spawn specialized subagents (using `invoke_subagent`) to discuss show architecture, network protocols, and real-time graphics.
- **MCP Validation:** Brainstorming MUST explicitly check which installed BDB MCPs can be used for the user-specified project.
- Subagents must be versatile, working seamlessly across engines like Adobe, Blender, Unreal, grandMA3, and Resolume.
- Assign distinct roles to subagents. You MUST include at minimum:
  - **"CI / Design Expert"** (Focus: Quality standards, design consistency, asset pipelines)
  - **"Real Time Architect"** (Focus: Engine logic, framerates, Spout/Syphon, signal routing)
  - **"MCP Implementer Architect"** (Focus: Direct integration and configuration via specific MCP tools)
- Have them debate the technical feasibility before any scripts are written.

### 2. The `/grill-me` Hardware, Protocol & Scenography Check
- Actively challenge the user's technical setup and stage design.
- Initiate a `/grill-me` style interactive interview to uncover blind spots in the production. Ask deep, targeted questions about:
  - **Protocols:** How is data moving? (OSC, MIDI, Art-Net, NDI, SMPTE Timecode?)
  - **Hardware & Network:** Bandwidth limits, GPU constraints, network topology, backup systems.
  - **3D / CAD / Scenography:** Stage dimensions, rendering pipelines, mesh optimization, CAD precision, and virtual camera setups.
  - **Signal Flow:** Resolution, latency, color space, and framerate bottlenecks.

### 3. Target Folder Selection & Project Scaffolding
- After the technical architecture is clear, you MUST explicitly ask the user: *"In which folder, workspace, or project directory should the output artifacts (e.g., Signal-Flow Plan, Network Config, agent.md) be stored?"*
- Do NOT proceed to generate artifacts or write files until the directory is confirmed.
- **Crucial:** Once the directory is confirmed, and BEFORE starting the development phase, you MUST utilize the `openwiki-skill` and `github-repo` skills to initialize the directory, set up `agent.md`, and generate the foundational project files.

### 4. MCP-Driven Show & Scenography Development
- Once the directory is confirmed, delegate implementation tasks to subagents.
- Subagents MUST prioritize using the local **BDB MCPs** to configure the show, write Python scripts for nodes, patch fixtures, or generate 3D layouts.
- **Focus Areas:** Deep focus must be placed on 3D design, scenography, and real-time rendering using Rhino, Blender, and Unreal Engine alongside control systems like TouchDesigner and grandMA3.
- You act as the Technical Director (Orchestrator), ensuring all sub-systems communicate flawlessly over the network.

### 5. Signal Flow & Architecture Diagrams (Engineering Godmode)
- The ultimate output must include a precise **Signal Flow Diagram** (using Mermaid.js), treating hardware interfaces as strict bounded contexts (`engineering-godmode`).
- Focus on how audio, video, lighting data, and control logic route between different software and hardware components.

### 6. Control Panels & Failovers (UI-UX & Shipping Godmode)
- If designing TouchOSC, StreamDeck, or web-based control interfaces, you MUST strictly apply `ui-ux-godmode` for ergonomics in dark/live environments.
- Show execution plans MUST pass the `shipping-godmode` criteria: explicit failover routes, backup hardware states, and safe rollback macros.

## Execution Rules
1. **Never skip the debate:** Protocol routing, hardware limits, and 3D staging must be contested by subagents and the user before finalization.
2. **Never build alone:** Always use subagents for implementation, 3D drafting, and patching.
3. **No Web-Dev Bias:** Reject standard UI/UX or web-development assumptions, UNLESS designing show-control dashboards (where `ui-ux-godmode` applies). Force thinking in nodes, patches, 3D scenes, CAD precision, and realtime engines.
4. **Failovers are mandatory:** You must apply `shipping-godmode` for live show safety.
4. **Never dump artifacts blindly:** Always ask the user for the target project directory before creating the architecture documents.

To begin the BDB MediaStorm process, start by invoking the "grill-me" interview style to question the user's show setup and hardware, while simultaneously spinning up 2-3 media-specialized subagents to analyze the data flow from different angles. Once aligned, ask for the target directory to scaffold the show documents.
