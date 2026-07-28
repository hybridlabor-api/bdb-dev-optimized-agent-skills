#!/usr/bin/env python3
"""
memB Obsidian Vault Exporter & Graph Visualizer
Exports stored local vector memories (~/.MemBDB/memb.db) into an Obsidian-Flavored Markdown Vault with Wikilinks, Tags, and Mermaid Graphs.
"""

import os
import sys
import sqlite3
import json
import re
from typing import List, Dict, Any, Optional

def get_memb_db_path():
    db_dir = os.environ.get("MEMB_DATA_DIR") or os.path.expanduser("~/.MemBDB")
    return os.path.join(db_dir, "memb.db")

def export_to_obsidian_vault(vault_dir: Optional[str] = None) -> str:
    """Read all entries from memb_vectors SQLite table and export as Obsidian Vault notes."""
    db_path = get_memb_db_path()
    if not os.path.exists(db_path):
        return f"Error: memB database at {db_path} does not exist."

    if not vault_dir:
        vault_dir = os.path.expanduser("~/.MemBDB/obsidian_vault")

    os.makedirs(vault_dir, exist_ok=True)
    os.makedirs(os.path.join(vault_dir, "Projects"), exist_ok=True)
    os.makedirs(os.path.join(vault_dir, "Categories"), exist_ok=True)

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        cursor.execute("SELECT id, collection, payload, created_at FROM memb_vectors;")
        rows = cursor.fetchall()
    except Exception as e:
        conn.close()
        return f"Error reading memb_vectors: {e}"

    conn.close()

    if not rows:
        return "No memory records found in memB database."

    print(f"📊 Processing {len(rows)} memory items for Obsidian Vault export...")

    projects_map: Dict[str, List[Dict[str, Any]]] = {}
    categories_map: Dict[str, List[Dict[str, Any]]] = {}

    for row in rows:
        m_id, collection, payload_str, created_at = row
        try:
            payload = json.loads(payload_str)
        except Exception:
            payload = {"data": payload_str}

        data_text = payload.get("data", "")
        project = payload.get("project") or payload.get("project_id") or "Global"
        category = payload.get("category") or "General"
        user_id = payload.get("user_id") or "bdb_developer"

        record = {
            "id": m_id,
            "data": data_text,
            "project": project,
            "category": category,
            "created_at": created_at,
            "user_id": user_id
        }

        projects_map.setdefault(project, []).append(record)
        categories_map.setdefault(category, []).append(record)

    # 1. Generate Index / Dashboard Note
    index_path = os.path.join(vault_dir, "memB_Knowledge_Graph.md")
    with open(index_path, "w", encoding="utf-8") as f:
        f.write("# 🧠 memB Knowledge Graph & Vault Index\n\n")
        f.write(f"> **Total Memories Indexed:** `{len(rows)}` | **Projects:** `{len(projects_map)}` | **Categories:** `{len(categories_map)}`\n\n")
        
        f.write("## 🌐 Visual Knowledge Graph\n\n```mermaid\nmindmap\n")
        f.write("  root((🧠 memB Vector Memory))\n")
        f.write("    Projects\n")
        for proj in projects_map.keys():
            safe_p = re.sub(r'[^a-zA-Z0-9_\- ]', '', proj)
            f.write(f"      [{safe_p}]\n")
        f.write("    Categories\n")
        for cat in categories_map.keys():
            safe_c = re.sub(r'[^a-zA-Z0-9_\- ]', '', cat)
            f.write(f"      ({safe_c})\n")
        f.write("```\n\n")

        f.write("## 📂 Projects Overview\n")
        for proj, items in projects_map.items():
            f.write(f"- [[Projects/{proj}|{proj}]] (`{len(items)} notes`)\n")

        f.write("\n## 🏷️ Categories\n")
        for cat, items in categories_map.items():
            f.write(f"- [[Categories/{cat}|{cat}]] (`{len(items)} notes`)\n")

    # 2. Generate Project Notes
    for proj, items in projects_map.items():
        p_path = os.path.join(vault_dir, "Projects", f"{proj}.md")
        with open(p_path, "w", encoding="utf-8") as f:
            f.write(f"---\ntags:\n  - memB/project\n  - project/{proj}\nproject: \"{proj}\"\ntotal_memories: {len(items)}\n---\n\n")
            f.write(f"# 🚀 Project: {proj}\n\n")
            f.write(f"Back to [[memB_Knowledge_Graph|Main Index]]\n\n")
            f.write("## 📜 Documented Memories & Decisions\n\n")
            for item in items:
                f.write(f"> [!NOTE] Memory Record (`{item['id'][:8]}`)\n")
                f.write(f"> **Category:** [[Categories/{item['category']}|#{item['category']}]]  \n")
                f.write(f"> **Date:** `{item['created_at']}`  \n")
                f.write(">\n")
                lines = item['data'].split("\n")
                for l in lines:
                    f.write(f"> {l}\n")
                f.write("\n---\n\n")

    # 3. Generate Category Notes
    for cat, items in categories_map.items():
        c_path = os.path.join(vault_dir, "Categories", f"{cat}.md")
        with open(c_path, "w", encoding="utf-8") as f:
            f.write(f"---\ntags:\n  - memB/category\n  - category/{cat}\ncategory: \"{cat}\"\ntotal_memories: {len(items)}\n---\n\n")
            f.write(f"# 🏷️ Category: {cat}\n\n")
            f.write(f"Back to [[memB_Knowledge_Graph|Main Index]]\n\n")
            f.write("## 📜 Category Entries\n\n")
            for item in items:
                f.write(f"- **Project:** [[Projects/{item['project']}|{item['project']}]]  \n")
                f.write(f"  ```text\n  {item['data'][:300]}...\n  ```\n\n")

    return f"Successfully exported {len(rows)} memory items to Obsidian Vault at:\n{vault_dir}"

if __name__ == "__main__":
    out_dir = sys.argv[1] if len(sys.argv) > 1 else None
    res = export_to_obsidian_vault(out_dir)
    print(res)
