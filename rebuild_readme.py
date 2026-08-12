import re

with open("README.md", "r") as f:
    old_readme = f.read()

# Extract the bottom half of the README starting from the Pipeline section
bottom_half = re.search(r'(## 🔄 BDB Software Engineering Pipeline.*)', old_readme, re.DOTALL).group(1)

with open("skills_table.md", "r") as f:
    skills_table = f.read()

new_readme = f"""# BDB DEV Optimized Agent Skills (v3.0.0)

[![GitHub License](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![NPM Version](https://img.shields.io/npm/v/@hybridlabor-api/bdb-dev-optimized-agent-skills)](https://www.npmjs.com/package/@hybridlabor-api/bdb-dev-optimized-agent-skills)

Welcome to the **BDB DEV Optimized Agent Skills** repository. This is a hyper-curated, enterprise-grade toolkit of ~250 optimized AI Agent skills, strict system configurations, and advanced local MCP servers designed for autonomous software engineering.

---

## 🏗️ Architecture Overview

The BDB OS ecosystem bridges the gap between raw LLMs and production-grade engineering environments. It consists of four core pillars:

1. **The 144+ Optimized Skills:** A massive library of meticulously crafted Markdown skills covering everything from AWS Terraform to UI/UX design.
2. **The 3 Godmodes:** The absolute apex of the skill hierarchy. These three skills dictate strict Domain-Driven Design, UI/UX "Anti-Slop", and safe shipping practices across the entire ecosystem.
3. **Universal Agent Harness:** The core setup injects rules directly into Agy, Claude Code, Cursor, Windsurf, GitHub Copilot, and Codex.
4. **Active Daemons (memB & OpenWiki):** Background Python/Node daemons that manage persistent long-term memory (memB) and auto-document codebases (OpenWiki).

---

## 🛡️ The 3 Godmodes (Apex Layer)

Instead of letting agents wander through generic instructions, the top-tier of this repository enforces three **Hyper-Curated Godmodes**. These act as the ultimate gatekeepers for your codebase and are automatically injected into all agent harnesses:

*   **`engineering-godmode`:** Forces Domain-Driven Design, strict TypeScript checks, Clean Architecture, and systematic 5-step debugging. 
*   **`ui-ux-godmode`:** The frontend Gold-Standard. Enforces BDB "Anti-Slop" principles, enterprise accessibility, fluid motion dynamics, and precise data-driven design.
*   **`shipping-godmode`:** The final gatekeeper. Enforces Spec-Driven Development, rigorous pre-launch environment checks, feature flags, and safe rollback strategies before any deployment.

---

## 🗂️ The Comprehensive Skill Library

Below is the complete overview of all curated agent skills included in this package. These are automatically deployed to your agent's workspace by the interactive installer.

{skills_table}

---

{bottom_half}
"""

with open("README.md", "w") as f:
    f.write(new_readme)

print("Successfully rebuilt README.md")
