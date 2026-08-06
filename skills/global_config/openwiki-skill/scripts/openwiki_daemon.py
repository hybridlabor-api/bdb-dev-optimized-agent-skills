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

# --- Provider config via environment variables ---
# OPENWIKI_PROVIDER: "google" | "openai" | "groq" | "grok" | "nvidia" | "openrouter" | "ollama" | "lmstudio" | "custom"
# OPENWIKI_MODEL:    model name (e.g. meta/llama-3.3-70b-instruct, grok-2-latest, llama-3.3-70b-versatile, anthropic/claude-3.5-sonnet, gpt-4o-mini)
# OPENWIKI_BASE_URL: custom base URL (e.g. https://integrate.api.nvidia.com/v1, https://api.x.ai/v1, https://api.groq.com/openai/v1)
PROVIDER = os.environ.get("OPENWIKI_PROVIDER", "google").lower()

PROVIDER_BASE_URLS = {
    "google": "",
    "openai": "https://api.openai.com/v1",
    "groq": "https://api.groq.com/openai/v1",
    "grok": "https://api.x.ai/v1",
    "xai": "https://api.x.ai/v1",
    "nvidia": "https://integrate.api.nvidia.com/v1",
    "openrouter": "https://openrouter.ai/api/v1",
    "ollama": "http://localhost:11434/v1",
    "lmstudio": "http://localhost:1234/v1",
}

PROVIDER_DEFAULT_MODELS = {
    "google": "gemma-4-12b-it",
    "openai": "gpt-4o-mini",
    "groq": "llama-3.3-70b-versatile",
    "grok": "grok-2-latest",
    "xai": "grok-2-latest",
    "nvidia": "meta/llama-3.3-70b-instruct",
    "openrouter": "anthropic/claude-3.5-sonnet",
    "ollama": "llama3",
    "lmstudio": "local-model",
}

BASE_URL = os.environ.get("OPENWIKI_BASE_URL", "").strip() or PROVIDER_BASE_URLS.get(PROVIDER, "https://api.openai.com/v1")
MODEL_ID = os.environ.get("OPENWIKI_MODEL", "").strip() or PROVIDER_DEFAULT_MODELS.get(PROVIDER, "gemma-4-12b-it")

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


def call_model(api_key, evidence, existing_pages):
    """Call configured LLM provider. Supports google, openai, ollama."""
    existing_context = ""
    if existing_pages:
        existing_context = "\n\n---\n\n".join(
            f"## Existing: {name}\n{content}" for name, content in existing_pages.items()
        )
    user_msg = f"## Git Evidence\n\n{evidence}"
    if existing_context:
        user_msg += f"\n\n## Existing Wiki Pages\n\n{existing_context}"

    if PROVIDER == "google":
        client = genai.Client(api_key=api_key)
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

    else:
        # OpenAI-compatible REST API call (covers OpenAI, Groq, Grok, Nvidia NIM, OpenRouter, Ollama, Kimi, Qwen, etc.)
        import urllib.request, json as _json
        base = BASE_URL.rstrip("/")
        payload = _json.dumps({
            "model": MODEL_ID,
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user",   "content": user_msg},
            ],
            "temperature": 0.3,
        }).encode()

        headers = {"Content-Type": "application/json"}
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"
        if PROVIDER == "openrouter":
            headers["HTTP-Referer"] = "https://github.com/bdb-dev/openwiki"
            headers["X-Title"] = "OpenWiki Daemon"

        req = urllib.request.Request(f"{base}/chat/completions", data=payload, headers=headers)
        with urllib.request.urlopen(req, timeout=120) as resp:
            data = _json.loads(resp.read())
        raw = data["choices"][0]["message"]["content"].strip()

    if raw.startswith("```"):
        raw = raw.split("\n", 1)[1] if "\n" in raw else raw[3:]
        if raw.endswith("```"):
            raw = raw[:-3]
        raw = raw.strip()
    return json.loads(raw)


def call_gemma(api_key, evidence, existing_pages):
    """Backwards-compat alias."""
    return call_model(api_key, evidence, existing_pages)


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


def compute_code_health(project_dir):
    """Compute deterministic code health metrics using git only. No LLM required."""
    health = {"hotspots": [], "bus_factor": [], "commit_freq": {}, "error": None}

    def git(args):
        try:
            r = subprocess.run(
                ["git"] + args, cwd=project_dir,
                capture_output=True, text=True, timeout=15
            )
            return r.stdout.strip()
        except Exception:
            return ""

    # --- Hotspots: files with most changes in last 90 days ---
    log_out = git(["log", "--since=90.days", "--name-only", "--pretty=format:", "--diff-filter=M"])
    file_counts = {}
    for line in log_out.splitlines():
        line = line.strip()
        if line and not line.startswith("commit"):
            file_counts[line] = file_counts.get(line, 0) + 1
    health["hotspots"] = sorted(file_counts.items(), key=lambda x: -x[1])[:10]

    # --- Bus Factor: files touched by only 1 author ---
    bus_risk = []
    top_files = [f for f, _ in health["hotspots"][:20]]
    for fpath in top_files:
        authors = git(["log", "--since=90.days", "--format=%ae", "--", fpath])
        unique = set(a for a in authors.splitlines() if a.strip())
        if len(unique) == 1:
            bus_risk.append((fpath, list(unique)[0]))
    health["bus_factor"] = bus_risk

    # --- Commit frequency: last 30 days by author ---
    shortlog = git(["shortlog", "-sne", "--since=30.days", "HEAD"])
    freq = {}
    for line in shortlog.splitlines():
        parts = line.strip().split("\t", 1)
        if len(parts) == 2:
            freq[parts[1]] = int(parts[0].strip())
    health["commit_freq"] = freq

    return health


def write_code_health_page(project_dir, health):
    """Write .openwiki/code_health.md from computed metrics."""
    wiki_dir = os.path.join(project_dir, ".openwiki")
    os.makedirs(wiki_dir, exist_ok=True)
    now = datetime.now().strftime("%Y-%m-%d %H:%M")

    lines = [
        "# 🟡 Code Health Report",
        f"> Auto-generated by OpenWiki Daemon · {now} · No LLM · Git-only\n",
    ]

    # Hotspot table
    lines.append("## 🔥 Hotspot Files (most changed, last 90 days)")
    if health["hotspots"]:
        lines.append("| File | Changes | Risk |")
        lines.append("|------|---------|------|")
        for fpath, count in health["hotspots"]:
            risk = "🔴 High" if count >= 10 else "🟡 Medium" if count >= 4 else "🟢 Low"
            lines.append(f"| `{fpath}` | {count} | {risk} |")
    else:
        lines.append("_No changes in last 90 days._")

    # Bus factor
    lines.append("\n## 👤 Bus Factor Risk (single-author files, last 90 days)")
    if health["bus_factor"]:
        lines.append("| File | Sole Author |")
        lines.append("|------|-------------|")
        for fpath, author in health["bus_factor"]:
            lines.append(f"| `{fpath}` | {author} |")
    else:
        lines.append("_No single-author hotspot files detected. ✅_")

    # Commit frequency
    lines.append("\n## 📈 Commit Activity by Author (last 30 days)")
    if health["commit_freq"]:
        lines.append("| Author | Commits |")
        lines.append("|--------|---------|")
        for author, count in sorted(health["commit_freq"].items(), key=lambda x: -x[1]):
            lines.append(f"| {author} | {count} |")
    else:
        lines.append("_No commits in last 30 days._")

    content = "\n".join(lines) + "\n"
    health_path = os.path.join(wiki_dir, "code_health.md")
    try:
        with open(health_path, "w") as f:
            f.write(content)
            
        # Also write a beautiful HTML dashboard (Repowise SVG style)
        html_path = os.path.join(wiki_dir, "code_health_dashboard.html")
        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>RepoGraph Code Health Dashboard</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Inter, Helvetica, Arial, sans-serif;
            background-color: #17131D;
            color: #EEEAF4;
            margin: 0; padding: 40px;
        }}
        .header {{ margin-bottom: 40px; }}
        h1 {{ font-size: 30px; font-weight: 700; letter-spacing: -.4px; margin: 0 0 10px 0; }}
        .sub {{ font-size: 15px; color: #A79DB3; margin: 0; }}
        .card {{
            background-color: #211B29;
            border: 1px solid rgba(213,197,232,.10);
            border-radius: 14px;
            padding: 30px;
            margin-bottom: 30px;
        }}
        .lbl {{ font-size: 11.5px; font-weight: 700; letter-spacing: 1.1px; color: #EEEAF4; margin-bottom: 20px; display: block; }}
        .grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; }}
        .metric-box {{
            background-color: #110D17;
            border: 1px solid rgba(213,197,232,.10);
            border-radius: 9px;
            padding: 20px;
        }}
        .chiplbl {{ font-size: 10.5px; color: #A79DB3; letter-spacing: .5px; text-transform: uppercase; margin-bottom: 10px; display: block; }}
        .chipval {{ font-size: 24px; font-weight: 700; }}
        .val-high {{ color: #F2A03D; }}
        .val-good {{ color: #34D399; }}
        .val-neutral {{ color: #A98FC4; }}
        table {{ width: 100%; border-collapse: collapse; margin-top: 15px; font-size: 14px; }}
        th, td {{ text-align: left; padding: 12px 10px; border-bottom: 1px solid rgba(213,197,232,.05); }}
        th {{ color: #A79DB3; font-weight: 500; font-size: 12px; text-transform: uppercase; letter-spacing: .5px; }}
        code {{ background: rgba(213,197,232,.1); padding: 3px 6px; border-radius: 4px; font-family: ui-monospace, SFMono-Regular, monospace; font-size: 12px; color: #A98FC4; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>RepoGraph Code Health</h1>
        <p class="sub">Generated {now} · Zero LLM · Git-based Analytics</p>
    </div>
    
    <div class="card">
        <span class="lbl">CODE METRICS</span>
        <div class="grid">
            <div class="metric-box">
                <span class="chiplbl">Hotspot Files</span>
                <span class="chipval val-high">{len(health["hotspots"])}</span>
            </div>
            <div class="metric-box">
                <span class="chiplbl">Bus Factor Risk</span>
                <span class="chipval val-good">{len(health["bus_factor"])}</span>
            </div>
            <div class="metric-box">
                <span class="chiplbl">Active Authors</span>
                <span class="chipval val-neutral">{len(health["commit_freq"])}</span>
            </div>
        </div>
    </div>

    <div class="grid">
        <div class="card">
            <span class="lbl">🔥 HOTSPOTS (LAST 90 DAYS)</span>
            <table>
                <tr><th>File</th><th>Changes</th></tr>
                {"".join(f"<tr><td><code>{f}</code></td><td class='{('val-high' if c >= 10 else 'val-good')}'>{c}</td></tr>" for f, c in health["hotspots"][:5])}
            </table>
        </div>
        <div class="card">
            <span class="lbl">👤 BUS FACTOR (SINGLE AUTHOR)</span>
            <table>
                <tr><th>File</th><th>Author</th></tr>
                {"".join(f"<tr><td><code>{f}</code></td><td>{a}</td></tr>" for f, a in health["bus_factor"][:5])}
            </table>
        </div>
    </div>
</body>
</html>
"""
        with open(html_path, "w") as f:
            f.write(html)
            
        return True
    except Exception as e:
        log(f"Error writing code health: {e}")
        return False


def check_and_update_project(project_dir, api_key):
    if not os.path.isdir(os.path.join(project_dir, ".git")):
        log(f"Not a git repo: {project_dir}")
        return False

    log(f"Checking: {project_dir}")

    # --- Code Health (deterministic, no LLM) ---
    health = compute_code_health(project_dir)
    if write_code_health_page(project_dir, health):
        log(f"Code health report written for {project_dir}")

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

    log(f"Calling {PROVIDER}/{MODEL_ID} for documentation update...")
    try:
        pages = call_model(api_key, evidence, existing_pages)
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

    api_key = (
        os.environ.get("OPENWIKI_API_KEY", "").strip() or
        os.environ.get("NVIDIA_API_KEY", "").strip() or
        os.environ.get("GROQ_API_KEY", "").strip() or
        os.environ.get("XAI_API_KEY", "").strip() or
        os.environ.get("OPENROUTER_API_KEY", "").strip() or
        os.environ.get("OPENAI_API_KEY", "").strip() or
        os.environ.get("GEMINI_API_KEY", "").strip()
    )
    if not api_key and PROVIDER not in ("ollama", "lmstudio"):
        log(f"WARNING: No API key set for provider '{PROVIDER}'.")
        log("Set OPENWIKI_API_KEY, NVIDIA_API_KEY, GROQ_API_KEY, XAI_API_KEY, OPENROUTER_API_KEY, OPENAI_API_KEY, or GEMINI_API_KEY.")
        log("For local providers (Ollama / LMStudio): no key needed.")

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
