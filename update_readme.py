import re

with open("README.md", "r") as f:
    readme = f.read()

# Define the new content to insert
new_content = """
---

## 💻 BDB OS Agent Workspace (AI Orchestrator)

Running multiple coding agents simultaneously often results in chaotic workspaces, overlapping branches, and lost terminal sessions. **BDB OS Agent Workspace** is a Meta-Harness and desktop orchestrator that acts as an Agentic IDE.

- **Parallel Workspaces:** Launch Claude Code, Cursor, Aider, and Codex simultaneously on the same project. AO isolates them into separate git worktrees automatically.
- **Unified Feedback Loops:** CI failures, PR review comments, and merge conflicts are captured by the daemon and routed back to the exact agent session responsible for the code.
- **Live Supervision:** Monitor all active agent terminals, browser previews, and task progress from a single centralized desktop dashboard.

---

## 🎬 BDB Creator Extension (3D, Video & Node Engines)

To keep the core BDB DEV skills lightweight (<25MB), all heavy generative and media pipelines have been decoupled into the **BDB Creator Extension**. 

- **Generative 3D & Animation:** Integrates native MCP servers for Unreal Engine, Rhino 7/8, and Spline.
- **Node-Based Media:** Full API and MCP integration for TouchDesigner (MindDesigner), DaVinci Resolve, and ComfyUI.
- **Event Technology:** Deep integrations for grandMA3 and Resolume, tailored specifically for show control and live event programming.

---
"""

# Insert it right before the "## 🗃️ memB: BDB's Native Long-Term Memory" section
if "## 🗃️ memB" in readme:
    readme = readme.replace("## 🗃️ memB", new_content + "\n## 🗃️ memB")
else:
    print("Could not find memB section.")

with open("README.md", "w") as f:
    f.write(readme)

print("Updated README.md")
