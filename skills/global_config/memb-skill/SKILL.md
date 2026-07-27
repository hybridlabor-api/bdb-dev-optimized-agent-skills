---
name: memb-skill
description: "BDB local-first long-term memory engine (memB). Query, remember, and adapt preferences, code architectures, and developer patterns across tasks."
risk: low
source: bdb
date_added: "2026-07-11"
---

# memB: Local Long-Term Memory Skill

This skill allows agents to access and maintain a persistent, offline-first long-term memory bank using the **`memb-mcp`** server. It manages user preferences, project structures, and complex developer workarounds.

---

## 🔒 Memory Safety & Secret Filtration

> [!IMPORTANT]
> **Secret Ingestion Rule:** Under no circumstances should raw credentials, passwords, API keys (e.g. `GEMINI_API_KEY`, `POSTGRES_PRISMA_URL`), or raw environment configurations be written to memory. 
> Ensure all inputs are scrubbed of high-entropy strings before calling memory tools.

---

## 🛠️ Memory Categorization (Dynamic Flower-Like Graph Layout)

`memB` implements a dynamic, project-agnostic hierarchical layout that structures memories into clusters automatically without hardcoded categories:

1.  **"God Mode" / General Knowledge Hub (Center):**
    *   Mapped using **`category="godmode"`** (with `project_id=None`).
    *   Holds universal developer preferences, coding philosophies, global style sheets, and general core commands.
2.  **Dynamic Project Leaves (Petals):**
    *   Mapped using a specific **`project_id`** (e.g. `project_id="VisualSelect_By_BDB"` or `project_id="litha-gathering"`).
    *   Isolates facts, custom configurations, and files routing patterns to the specific workspace project, preventing context pollution.
    *   *System Integration:* The agent dynamically resolves the basename of the active workspace directory to scan and bind project memories automatically.

---

## 🔌 Using Memory Tools

When working on tasks, query memory at the start of your turn to retrieve relevant developer context, and add critical decisions at the end.

### 1. Ingestion (`add_memory`)
Use `add_memory` to commit a new fact, style preference, or design decision.
*   **Args:** `text` (string), `user_id` (string, default: "bdb_developer"), `category` (string, default: "godmode"), `project_id` (string, optional)
*   **Usage Guidelines:**
    *   *General Preferences:* "Alice prefers to use absolute import paths globally." -> `add_memory({ text: "Prefers absolute import paths globally", category: "godmode" })`
    *   *Project Learned Facts:* "In project VisualSelect, we must bypass the Firebase Auth login on localhost." -> `add_memory({ text: "Bypass Firebase Auth login on localhost", category: "project_node", project_id: "VisualSelect_By_BDB" })`

### 2. Retrieval (`search_memory`)
Use `search_memory` at the beginning of a task to load context.
*   **Args:** `query` (string), `user_id` (string), `limit` (integer), `project_id` (string, optional)
*   **Behavior:** The search queries both global `godmode` memory and the active `project_id` memory in parallel, merging and ranking results by similarity.

### 3. Cleanup & Auditing (`list_memories` / `delete_memory`)
*   Use `list_memories` to audit active records.
*   Use `delete_memory` with a UUID to remove outdated or erroneous facts.

---

## 🚀 Workflow Pattern

1.  **Task Start (Context Loading):** Query `search_memory` using keywords from the user prompt and passing the active `project_id` if working in a specific project.
2.  **Execution:** Proceed with coding, applying the retrieved styles and preferences.
3.  **Task End (Knowledge Capture):** If you resolved a complex setup bug or the user specified a new preference, run `add_memory` to persist it.
