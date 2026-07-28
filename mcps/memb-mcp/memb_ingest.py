#!/usr/bin/env python3
"""
memB Deep Ingestion Tool
Scans any directory path (e.g. /Users/timrennings/bdb-dev or custom project folders),
extracts project architectures, tech specs, READMEs, agent.md, openwiki notes, and past transcripts,
and ingests them into memB local vector memory (~/.MemBDB/memb.db).
"""

import os
import sys
import json
import glob
import argparse
from typing import List, Dict, Any, Optional

# Ensure local memb module is importable
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

try:
    from memb import Memory
except ImportError:
    print("Error: Could not import memB module.", file=sys.stderr)
    sys.exit(1)


def init_memory():
    """Initialize the local memB Memory instance with ONNX embedder."""
    if "OPENAI_API_KEY" not in os.environ and "GEMINI_API_KEY" not in os.environ:
        os.environ["OPENAI_API_KEY"] = "sk-dummy-key-for-local-onnx-ingestion"

    db_dir = os.environ.get("MEMB_DATA_DIR") or os.path.expanduser("~/.MemBDB")
    os.makedirs(db_dir, exist_ok=True)
    db_path = os.path.join(db_dir, "memb.db")
    history_db_path = os.path.join(db_dir, "history.db")
    
    memory_config = {
        "embedder": {
            "provider": "local_onnx",
            "config": {}
        },
        "vector_store": {
            "provider": "numpy_flat",
            "config": {
                "collection_name": "bdb_agent_memory",
                "path": db_path
            }
        },
        "history_db_path": history_db_path
    }
    return Memory.from_config(memory_config)


IGNORE_DIRS = {
    "node_modules", "vendor", ".git", ".venv", "venv", "__pycache__",
    ".pytest_cache", "dist", "build", ".next", ".cache", "backups"
}

TARGET_FILES = [
    "agent.md", "README.md", "README.de.md", "package.json",
    "pyproject.toml", "mcp_config.json", "registry.json", "CLAUDE.md"
]


def scan_directory(root_dir: str) -> List[Dict[str, Any]]:
    """Scan root_dir recursively for key project architecture files."""
    documents = []
    print(f"🔍 Scanning directory: {root_dir}...")

    for dirpath, dirnames, filenames in os.walk(root_dir):
        # Skip ignored directories
        dirnames[:] = [d for d in dirnames if d not in IGNORE_DIRS and not d.startswith(".")]

        rel_path = os.path.relpath(dirpath, root_dir)
        project_name = os.path.basename(dirpath) if rel_path != "." else os.path.basename(root_dir)

        # Check for openwiki docs
        openwiki_dir = os.path.join(dirpath, ".openwiki")
        if os.path.isdir(openwiki_dir):
            for wiki_file in os.listdir(openwiki_dir):
                if wiki_file.endswith(".md"):
                    w_path = os.path.join(openwiki_dir, wiki_file)
                    try:
                        with open(w_path, "r", encoding="utf-8") as f:
                            content = f.read().strip()
                        if content:
                            documents.append({
                                "source": f"{project_name}/.openwiki/{wiki_file}",
                                "project": project_name,
                                "type": "openwiki_doc",
                                "content": content[:3000]
                            })
                    except Exception:
                        pass

        # Check for target project files
        for fname in filenames:
            if fname in TARGET_FILES:
                f_path = os.path.join(dirpath, fname)
                try:
                    with open(f_path, "r", encoding="utf-8") as f:
                        content = f.read().strip()
                    if content:
                        documents.append({
                            "source": os.path.relpath(f_path, root_dir),
                            "project": project_name,
                            "type": fname,
                            "content": content[:4000]
                        })
                except Exception:
                    pass

    return documents


def scan_antigravity_transcripts(max_sessions: int = 20) -> List[Dict[str, Any]]:
    """Scan Antigravity past conversation logs for key user instructions & decisions."""
    logs_base = os.path.expanduser("~/.gemini/antigravity-cli/brain")
    documents = []

    if not os.path.isdir(logs_base):
        return documents

    print(f"🧠 Scanning Antigravity conversation brain logs...")
    session_dirs = sorted(
        [os.path.join(logs_base, d) for d in os.listdir(logs_base) if os.path.isdir(os.path.join(logs_base, d))],
        key=os.path.getmtime,
        reverse=True
    )[:max_sessions]

    for sdir in session_dirs:
        transcript_path = os.path.join(sdir, ".system_generated", "logs", "transcript.jsonl")
        if not os.path.isfile(transcript_path):
            continue

        try:
            with open(transcript_path, "r", encoding="utf-8") as f:
                user_prompts = []
                for line in f:
                    try:
                        step = json.loads(line)
                        if step.get("type") == "USER_INPUT" and step.get("content"):
                            txt = step["content"].strip()
                            if len(txt) > 20 and not txt.startswith("/"):
                                user_prompts.append(txt)
                    except Exception:
                        pass

                if user_prompts:
                    session_id = os.path.basename(sdir)
                    summary = "\n- ".join(user_prompts[:5])
                    documents.append({
                        "source": f"chat_session_{session_id[:8]}",
                        "project": "chat_history",
                        "type": "conversation_transcript",
                        "content": f"User Decisions & Requirements in Session {session_id[:8]}:\n- {summary}"
                    })
        except Exception:
            pass

    return documents


def ingest_to_memb(memory: Any, documents: List[Dict[str, Any]], category: str = "project_architecture"):
    """Ingest extracted documents into memB vector memory."""
    print(f"💾 Ingesting {len(documents)} document snippets into memB (~/.MemBDB/memb.db)...")
    success_count = 0

    for doc in documents:
        text_entry = f"[{doc['project']} | {doc['type']} | {doc['source']}]\n{doc['content']}"
        try:
            memory.add(
                text_entry,
                user_id="bdb_developer",
                metadata={"project": doc["project"], "type": doc["type"], "source": doc["source"], "category": category},
                infer=False
            )
            success_count += 1
            print(f"  ✓ Ingested: {doc['source']}")
        except Exception as e:
            print(f"  ✕ Failed ({doc['source']}): {e}")

    print(f"\n🎉 Finished memB ingestion: {success_count}/{len(documents)} entries successfully indexed!")


def main():
    parser = argparse.ArgumentParser(description="memB Deep Ingestion Tool")
    parser.add_argument("path", nargs="?", default="/Users/timrennings/bdb-dev", help="Directory path to scan (default: /Users/timrennings/bdb-dev)")
    parser.add_argument("--transcripts", action="store_true", help="Also mine past Antigravity conversation logs")
    parser.add_argument("--category", default="project_architecture", help="Memory category (default: project_architecture)")
    args = parser.parse_args()

    target_path = os.path.abspath(args.path)
    if not os.path.exists(target_path):
        print(f"Error: Path '{target_path}' does not exist.", file=sys.stderr)
        sys.exit(1)

    memory = init_memory()
    docs = scan_directory(target_path)

    if args.transcripts:
        chat_docs = scan_antigravity_transcripts(max_sessions=30)
        docs.extend(chat_docs)

    if not docs:
        print("No eligible documentation or project files found.")
        return

    ingest_to_memb(memory, docs, category=args.category)


if __name__ == "__main__":
    main()
