#!/usr/bin/env python3
import os
import sys
import json
import time
import glob
import argparse
import subprocess
from datetime import datetime

try:
    from google import genai
except ImportError:
    genai = None

LOG_DIR = os.path.join(os.path.expanduser("~"), ".openwiki")
LOG_FILE = os.path.join(LOG_DIR, "daemon.log")
MODEL_ID = "gemma-4-12b-it"

SYSTEM_PROMPT = """You are a technical documentation generator for software projects.
You receive git evidence (recent commits, diffs, status) and existing wiki pages.
Your job is to produce updated wiki documentation.

Respond with a JSON object where keys are file paths relative to .openwiki/ and values are the full markdown content for each page.
Only include pages that need updates. Use these page names:
- quickstart.md: Developer onboarding, CLI commands, workspace orientation
- architecture.md: Tech stack, module boundaries, data flows, directory structure
- release_notes.md: Version history, changelogs, features shipped
- decisions.md: Key design decisions, trade-offs, constraints

Rules:
- Document ONLY what is evidenced in the git data. Never invent features.
- Use professional technical writing: clear headings, markdown tables, code blocks.
- Never include absolute paths with usernames. Use relative paths or ~ notation.
- Never include API keys, secrets, or credentials.
- Keep content concise and scannable.

Respond with ONLY valid JSON. No markdown fencing, no explanation."""


def log(msg):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    formatted = f"[{timestamp}] {msg}"
    print(formatted)
    os.makedirs(LOG_DIR, exist_ok=True)
    try:
        with open(LOG_FILE, "a") as f:
            f.write(formatted + "\n")
    except Exception:
        pass


def get_projects():
    config_file = os.path.join(LOG_DIR, "projects.json")
    os.makedirs(LOG_DIR, exist_ok=True)

    if not os.path.exists(config_file):
        repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../.."))
        default_data = {"projects": [repo_root], "interval_seconds": 7200}
        try:
            with open(config_file, "w") as f:
                json.dump(default_data, f, indent=2)
        except Exception as e:
            log(f"Error writing default config: {e}")
            return [], 7200

    try:
        with open(config_file, "r") as f:
            data = json.load(f)
            return data.get("projects", []), data.get("interval_seconds", 7200)
    except Exception as e:
        log(f"Error reading config: {e}")
        return [], 7200


def find_helper():
    candidates = [
        os.path.expanduser("~/.gemini/config/skills/openwiki-skill/scripts/openwiki_helper.py"),
        os.path.join(os.path.dirname(__file__), "openwiki_helper.py"),
    ]
    for c in candidates:
        if os.path.exists(c):
            return c
    return None


def run_helper(helper_path, command, cwd, extra_args=None):
    cmd = [sys.executable, helper_path, "--command", command, "--cwd", cwd]
    if extra_args:
        cmd.extend(extra_args)
    try:
        res = subprocess.run(cmd, capture_output=True, text=True, check=True)
        return res.stdout.strip()
    except Exception as e:
        log(f"Helper error ({command}): {e}")
        return None


def read_existing_wiki(project_dir):
    wiki_dir = os.path.join(project_dir, ".openwiki")
    pages = {}
    if not os.path.isdir(wiki_dir):
        return pages
    for md_file in glob.glob(os.path.join(wiki_dir, "*.md")):
        name = os.path.basename(md_file)
        try:
            with open(md_file, "r") as f:
                pages[name] = f.read()
        except Exception:
            pass
    return pages


def has_meaningful_changes(evidence):
    if not evidence:
        return False

    if "### Git Changes since last Wiki Update" in evidence:
        section = evidence.split("### Git Changes since last Wiki Update")[1].split("###")[0].strip()
        if section and section not in ("(no output)", "(no changes in commits)"):
            return True

    if "### Unstaged File Diffs" in evidence:
        section = evidence.split("### Unstaged File Diffs")[1].strip()
        if section and section not in ("(no unstaged changes)", "(clean working directory)"):
            return True

    return False


def call_gemma(api_key, evidence, existing_pages):
    client = genai.Client(api_key=api_key)

    existing_context = ""
    if existing_pages:
        existing_context = "\n\n---\n\n".join(
            f"## Existing: {name}\n{content}" for name, content in existing_pages.items()
        )

    user_msg = f"## Git Evidence\n\n{evidence}"
    if existing_context:
        user_msg += f"\n\n## Existing Wiki Pages\n\n{existing_context}"

    response = client.models.generate_content(
        model=MODEL_ID,
        contents=user_msg,
        config=genai.types.GenerateContentConfig(
            system_instruction=SYSTEM_PROMPT,
            temperature=0.3,
            max_output_tokens=8192,
        ),
    )

    raw = response.text.strip()
    if raw.startswith("```"):
        raw = raw.split("\n", 1)[1] if "\n" in raw else raw[3:]
        if raw.endswith("```"):
            raw = raw[:-3]
        raw = raw.strip()

    return json.loads(raw)


def write_wiki_pages(project_dir, pages):
    wiki_dir = os.path.join(project_dir, ".openwiki")
    os.makedirs(wiki_dir, exist_ok=True)
    written = []
    for name, content in pages.items():
        safe_name = os.path.basename(name)
        if not safe_name.endswith(".md"):
            safe_name += ".md"
        path = os.path.join(wiki_dir, safe_name)
        try:
            with open(path, "w") as f:
                f.write(content)
            written.append(safe_name)
        except Exception as e:
            log(f"Error writing {safe_name}: {e}")
    return written


def check_and_update_project(project_dir, api_key):
    if not os.path.isdir(os.path.join(project_dir, ".git")):
        log(f"Not a git repo: {project_dir}")
        return False

    log(f"Checking: {project_dir}")

    helper = find_helper()
    if not helper:
        log("Cannot find openwiki_helper.py")
        return False

    evidence = run_helper(helper, "collect", project_dir)
    if not evidence or "Not a git repository" in evidence:
        log(f"Collect failed for {project_dir}")
        return False

    wiki_exists = os.path.isdir(os.path.join(project_dir, ".openwiki"))
    if wiki_exists and not has_meaningful_changes(evidence):
        log(f"No changes detected for {project_dir}, skipping.")
        return False

    if not api_key:
        log("No GEMINI_API_KEY set. Skipping API call (collect-only mode).")
        return False

    existing_pages = read_existing_wiki(project_dir)

    pre_hash = run_helper(helper, "pre-snapshot", project_dir)

    log(f"Calling {MODEL_ID} for documentation update...")
    try:
        pages = call_gemma(api_key, evidence, existing_pages)
    except Exception as e:
        log(f"Gemma API error: {e}")
        return False

    if not pages or not isinstance(pages, dict):
        log("Empty or invalid response from model.")
        return False

    written = write_wiki_pages(project_dir, pages)
    log(f"Updated {len(written)} pages: {', '.join(written)}")

    if pre_hash:
        run_helper(helper, "post-snapshot", project_dir, ["--pre-hash", pre_hash])

    commit_result = run_helper(helper, "commit", project_dir)
    if commit_result:
        log(f"Commit: {commit_result}")

    return True


def run_daemon_loop(api_key):
    log("OpenWiki daemon started (Gemma 4 direct API mode)")
    while True:
        try:
            projects, interval = get_projects()
            log(f"Scanning {len(projects)} projects...")
            for project in projects:
                try:
                    check_and_update_project(project, api_key)
                except Exception as e:
                    log(f"Error processing {project}: {e}")
            log(f"Scan complete. Sleeping {interval}s...")
            time.sleep(interval)
        except KeyboardInterrupt:
            log("Daemon stopped by user.")
            break
        except Exception as e:
            log(f"Loop error: {e}")
            time.sleep(60)


def main():
    if genai is None:
        print("ERROR: google-genai package not installed.")
        print("Install it with: pip3 install google-genai")
        sys.exit(1)

    parser = argparse.ArgumentParser(description="OpenWiki Daemon - Gemma 4 Direct API")
    parser.add_argument("--one-shot", action="store_true", help="Run once and exit")
    args = parser.parse_args()

    api_key = os.environ.get("GEMINI_API_KEY", "").strip()
    if not api_key:
        log("WARNING: GEMINI_API_KEY not set. Will collect evidence but skip documentation generation.")
        log("Set it with: export GEMINI_API_KEY=your-key")

    if args.one_shot:
        log("One-shot mode")
        projects, _ = get_projects()
        for project in projects:
            try:
                check_and_update_project(project, api_key or None)
            except Exception as e:
                log(f"Error: {e}")
    else:
        run_daemon_loop(api_key or None)


if __name__ == "__main__":
    main()
