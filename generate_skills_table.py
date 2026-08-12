import os
import yaml
import glob
import re

directories = {
    "👑 Core Godmodes": "skills/basic/*",
    "⚙️ System & Config": "skills/global_config/*",
    "🛠️ Development & Languages": "skills/global_legacy/*"
}

subgenres = {
    "🤖 Agents & Automation": ["agent", "crewai", "n8n", "automation", "workflow", "apify"],
    "🎨 Frontend & UI/UX": ["frontend", "ui-", "ux-", "react", "tailwind", "shadcn", "nextjs", "css", "wcag", "zustand", "design"],
    "🗄️ Backend & Databases": ["database", "postgres", "prisma", "neon", "drizzle", "microservice", "api", "go-", "golang", "python", "backend"],
    "🚀 DevOps & Infrastructure": ["docker", "github", "git-", "vercel", "cloudflare", "os-", "bash", "linux", "tmux", "turborepo", "deploy", "infrastructure"],
    "🧠 AI & LLM": ["llm", "prompt", "gemini", "rag", "vector", "ai-", "model"],
    "📝 Documentation & Planning": ["doc", "readme", "openwiki", "plan", "writ", "architect", "product-manager", "linear", "notion"],
    "🧊 3D & Motion": ["threejs", "spline", "remotion", "video", "3d", "motion"],
    "📈 SEO & Marketing": ["seo", "copywriting", "schema", "marketing", "geo"],
    "🔧 Core Programming & Debugging": ["clean-code", "debug", "test", "tdd", "typescript", "javascript", "simplify", "playwright"]
}

output = []

for main_category, path_pattern in directories.items():
    output.append(f"<details>")
    output.append(f"<summary><h3>{main_category}</h3></summary>\n")
    
    skill_dirs = glob.glob(path_pattern)
    skills = []
    
    for sdir in skill_dirs:
        skill_md = os.path.join(sdir, "SKILL.md")
        if os.path.isdir(sdir) and os.path.exists(skill_md):
            with open(skill_md, 'r', encoding='utf-8') as f:
                content = f.read()
                match = re.match(r'^---\n(.*?)\n---', content, re.DOTALL)
                if match:
                    try:
                        frontmatter = yaml.safe_load(match.group(1))
                        name = frontmatter.get('name', os.path.basename(sdir))
                        desc = frontmatter.get('description', '')
                        desc = desc.replace('\n', ' ').strip()
                        skills.append((name, desc))
                    except:
                        pass
    
    # If it's a small category like Godmodes, don't use subgenres, just list them.
    if len(skills) < 10:
        skills.sort(key=lambda x: x[0])
        output.append("| Skill Name | Description |")
        output.append("|------------|-------------|")
        for name, desc in skills:
            output.append(f"| `{name}` | {desc} |")
        output.append("\n</details>\n")
        continue

    # Categorize into subgenres
    categorized = {k: [] for k in subgenres.keys()}
    categorized["📦 Other Utilities"] = []

    for name, desc in skills:
        placed = False
        search_str = (name + " " + desc).lower()
        for genre, keywords in subgenres.items():
            if any(kw in search_str for kw in keywords):
                categorized[genre].append((name, desc))
                placed = True
                break
        if not placed:
            categorized["📦 Other Utilities"].append((name, desc))

    for genre, items in categorized.items():
        if items:
            items.sort(key=lambda x: x[0])
            output.append(f"#### {genre}")
            output.append("| Skill Name | Description |")
            output.append("|------------|-------------|")
            for name, desc in items:
                output.append(f"| `{name}` | {desc} |")
            output.append("")
            
    output.append("</details>\n")

with open("skills_table.md", "w", encoding="utf-8") as f:
    f.write("\n".join(output))

print("Created skills_table.md with Dropdowns and Subgenres")
