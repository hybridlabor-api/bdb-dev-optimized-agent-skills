---
name: bdbrainstorm
description: Combines multi-agent brainstorming, the /grill-me slash command, subagent-driven-development, and ui-ux-pro-max to force a comprehensive, multi-agent ideation and UI/UX design workflow.
---

# BDBrainstorm: The Ultimate Multi-Agent Design & Ideation Workflow

When this skill is invoked or requested, you MUST orchestrate a comprehensive ideation and development workflow using a combination of multi-agent brainstorming, interactive user grilling, subagent-driven development, and high-end UI/UX principles. 

## Core Requirements & Workflow

You are strictly required to enforce the following 4 pillars in your process:

### 1. Multi-Agent Brainstorming
- Instead of brainstorming alone, you MUST spawn specialized subagents (using `invoke_subagent`) to discuss ideas, architecture, and features.
- Assign clear, distinct roles to subagents (e.g., "UI/UX Visionary", "Technical Architect", "Devil's Advocate") and have them debate and refine the concept before any code is written.

### 2. The `/grill-me` Approach
- Actively challenge the user's initial ideas.
- Initiate a `/grill-me` style interactive interview to uncover blind spots, resolve design decisions, and align on a robust plan. Do not accept vague requirements. Ask deep, targeted questions.

### 3. Target Folder Selection & Project Scaffolding
- After the brainstorming and grilling phase produces a solid conceptual plan, you MUST explicitly ask the user: *"In which folder, workspace, or project directory should the output artifacts (e.g., plan, README.md, agent.md) be stored?"*
- Do NOT proceed to generate artifacts or write files until the user has confirmed the specific directory.
- **Crucial:** Once the directory is confirmed, and BEFORE starting the development phase, you MUST utilize the `openwiki-skill` and `github-repo` skills to initialize the directory, set up `agent.md`, and generate the foundational project files.

### 4. Subagent-Driven Development
- Once the brainstorming and grilling phase produces a solid plan, you must strictly follow the `subagent-driven-development` skill.
- Delegate specific implementation tasks to independent subagents. 
- You act as the Orchestrator/Master Agent, reviewing the subagents' work and ensuring all components integrate perfectly.

### 5. UI/UX Pro Max Standards
- Every user interface decision, wireframe, or component generated during this process MUST adhere to the `ui-ux-pro-max` skill guidelines.
- Enforce high-agency frontend interfaces, strict design taste, calibrated color palettes, modern typography, micro-interactions, and responsive mobile-first layouts.
- Do not settle for "MVP" aesthetics. The output must look premium and state-of-the-art.

## Execution Rules
1. **Never skip the debate:** Ideas must be contested by subagents and the user before finalization.
2. **Never build alone:** Always use subagents for implementation.
3. **Never accept ugly UI:** Always apply `ui-ux-pro-max` rules.
4. **Never dump artifacts blindly:** Always ask the user for the target project directory before creating the plan, README, or agent.md files.

To begin the BDBrainstorm process, start by invoking the "grill-me" interview style to question the user's premise, while simultaneously spinning up 2-3 subagents to analyze the initial request from different angles. Once aligned, ask the user for the target directory before writing the project artifacts and spawning development subagents.
