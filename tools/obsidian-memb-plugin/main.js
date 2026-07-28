var __create = Object.create;
var __defProp = Object.defineProperty;
var __getOwnPropDesc = Object.getOwnPropertyDescriptor;
var __getOwnPropNames = Object.getOwnPropertyNames;
var __getProtoOf = Object.getPrototypeOf;
var __hasOwnProp = Object.prototype.hasOwnProperty;
var __export = (target, all) => {
  for (var name in all)
    __defProp(target, name, { get: all[name], enumerable: true });
};
var __copyProps = (to, from, except, desc) => {
  if (from && typeof from === "object" || typeof from === "function") {
    for (let key of __getOwnPropNames(from))
      if (!__hasOwnProp.call(to, key) && key !== except)
        __defProp(to, key, { get: () => from[key], enumerable: !(desc = __getOwnPropDesc(from, key)) || desc.enumerable });
  }
  return to;
};
var __toESM = (mod, isNodeMode, target) => (target = mod != null ? __create(__getProtoOf(mod)) : {}, __copyProps(
  // If the importer is in node compatibility mode or this is not an ESM
  // file that has been converted to a CommonJS file using a Babel-
  // compatible transform (i.e. "__esModule" has not been set), then set
  // "default" to the CommonJS "module.exports" for node compatibility.
  isNodeMode || !mod || !mod.__esModule ? __defProp(target, "default", { value: mod, enumerable: true }) : target,
  mod
));
var __toCommonJS = (mod) => __copyProps(__defProp({}, "__esModule", { value: true }), mod);

// main.ts
var main_exports = {};
__export(main_exports, {
  default: () => MembSyncPlugin
});
module.exports = __toCommonJS(main_exports);
var import_obsidian = require("obsidian");
var child_process = __toESM(require("child_process"));
var path = __toESM(require("path"));
var os = __toESM(require("os"));
var MembSyncPlugin = class extends import_obsidian.Plugin {
  async onload() {
    console.log("Loading memB AI Memory Sync Plugin");
    const ribbonIconEl = this.addRibbonIcon("brain-circuit", "Sync memB Knowledge Graph", (evt) => {
      this.syncMemBData();
    });
    this.addCommand({
      id: "sync-memb-data",
      name: "Sync memB Knowledge Graph",
      callback: () => {
        this.syncMemBData();
      }
    });
  }
  onunload() {
    console.log("Unloading memB AI Memory Sync Plugin");
  }
  async syncMemBData() {
    new import_obsidian.Notice("\u{1F9E0} Syncing memB local vector memories...");
    try {
      const dbDir = process.env.MEMB_DATA_DIR || path.join(os.homedir(), ".MemBDB");
      const dbPath = path.join(dbDir, "memb.db");
      const pythonScript = `
import sqlite3, json, sys
try:
    conn = sqlite3.connect('${dbPath.replace(/\\/g, "\\\\")}')
    cursor = conn.cursor()
    cursor.execute('SELECT id, collection, payload, created_at FROM memb_vectors;')
    rows = cursor.fetchall()
    conn.close()
    
    out = []
    for r in rows:
        try:
            p = json.loads(r[2])
        except:
            p = {"data": r[2]}
        out.append({
            "id": r[0],
            "project": p.get("project") or p.get("project_id") or "Global",
            "category": p.get("category") or "General",
            "data": p.get("data", ""),
            "created_at": r[3]
        })
    print(json.dumps(out))
except Exception as e:
    print(json.dumps({"error": str(e)}))
`;
      child_process.exec(`python3 -c "${pythonScript.replace(/"/g, '\\"')}"`, { maxBuffer: 1024 * 1024 * 10 }, async (error, stdout, stderr) => {
        if (error) {
          new import_obsidian.Notice("\u274C Failed to run Python SQLite dump: " + error.message);
          return;
        }
        try {
          const data = JSON.parse(stdout);
          if (data.error) {
            new import_obsidian.Notice("\u274C memB DB Error: " + data.error);
            return;
          }
          await this.generateVaultFiles(data);
          new import_obsidian.Notice(`\u2705 Successfully synced ${data.length} memB entries into Obsidian!`);
        } catch (e) {
          new import_obsidian.Notice("\u274C Failed to parse memB data: " + e);
        }
      });
    } catch (error) {
      new import_obsidian.Notice("\u274C Plugin Error: " + error);
    }
  }
  async generateVaultFiles(entries) {
    var _a, _b;
    const rootFolder = "memB_Knowledge_Graph";
    await this.ensureFolder(rootFolder);
    await this.ensureFolder(`${rootFolder}/Projects`);
    await this.ensureFolder(`${rootFolder}/Categories`);
    const projectsMap = /* @__PURE__ */ new Map();
    const categoriesMap = /* @__PURE__ */ new Map();
    for (const entry of entries) {
      const p = entry.project;
      const c = entry.category;
      if (!projectsMap.has(p))
        projectsMap.set(p, []);
      (_a = projectsMap.get(p)) == null ? void 0 : _a.push(entry);
      if (!categoriesMap.has(c))
        categoriesMap.set(c, []);
      (_b = categoriesMap.get(c)) == null ? void 0 : _b.push(entry);
    }
    let indexContent = `# \u{1F9E0} memB Knowledge Graph Dashboard

`;
    indexContent += `> **Total Memories Indexed:** ${entries.length} | **Projects:** ${projectsMap.size} | **Categories:** ${categoriesMap.size}

`;
    indexContent += `## \u{1F4C2} Projects Overview
`;
    projectsMap.forEach((v, k) => {
      indexContent += `- [[${rootFolder}/Projects/${k}|${k}]] (${v.length} notes)
`;
    });
    indexContent += `
## \u{1F3F7}\uFE0F Categories
`;
    categoriesMap.forEach((v, k) => {
      indexContent += `- [[${rootFolder}/Categories/${k}|${k}]] (${v.length} notes)
`;
    });
    await this.writeOrUpdateFile(`${rootFolder}/Dashboard.md`, indexContent);
    for (const [proj, items] of projectsMap.entries()) {
      let pContent = `---
project: "${proj}"
total_memories: ${items.length}
tags:
  - memB/project
---

`;
      pContent += `# \u{1F680} Project: ${proj}

Back to [[${rootFolder}/Dashboard|Main Index]]

## \u{1F4DC} Documented Memories & Decisions

`;
      for (const item of items) {
        pContent += `> [!NOTE] Memory Record (${item.id.substring(0, 8)})
`;
        pContent += `> **Category:** [[${rootFolder}/Categories/${item.category}|#${item.category}]]
`;
        pContent += `> **Date:** ${item.created_at}
>
`;
        const lines = item.data.split("\n");
        for (const l of lines) {
          pContent += `> ${l}
`;
        }
        pContent += `
---

`;
      }
      await this.writeOrUpdateFile(`${rootFolder}/Projects/${proj}.md`, pContent);
    }
    for (const [cat, items] of categoriesMap.entries()) {
      let cContent = `---
category: "${cat}"
total_memories: ${items.length}
tags:
  - memB/category
---

`;
      cContent += `# \u{1F3F7}\uFE0F Category: ${cat}

Back to [[${rootFolder}/Dashboard|Main Index]]

## \u{1F4DC} Category Entries

`;
      for (const item of items) {
        cContent += `- **Project:** [[${rootFolder}/Projects/${item.project}|${item.project}]]
`;
        cContent += `  \`\`\`text
  ${item.data.substring(0, 300)}...
  \`\`\`

`;
      }
      await this.writeOrUpdateFile(`${rootFolder}/Categories/${cat}.md`, cContent);
    }
  }
  async ensureFolder(folderPath) {
    const folder = this.app.vault.getAbstractFileByPath(folderPath);
    if (!folder) {
      await this.app.vault.createFolder(folderPath);
    }
  }
  async writeOrUpdateFile(filePath, content) {
    const file = this.app.vault.getAbstractFileByPath(filePath);
    if (file instanceof import_obsidian.TFile) {
      await this.app.vault.modify(file, content);
    } else {
      await this.app.vault.create(filePath, content);
    }
  }
};
// Annotate the CommonJS export names for ESM import in node:
0 && (module.exports = {});
