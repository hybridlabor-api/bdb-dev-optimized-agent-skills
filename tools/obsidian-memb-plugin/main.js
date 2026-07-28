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
    const rootFolder = "memB_Knowledge_Graph";
    await this.ensureFolder(rootFolder);
    await this.ensureFolder(`${rootFolder}/Projects`);
    await this.ensureFolder(`${rootFolder}/Categories`);
    await this.ensureFolder(`${rootFolder}/Memories`);
    const projectsSet = /* @__PURE__ */ new Set();
    const categoriesSet = /* @__PURE__ */ new Set();
    for (const entry of entries) {
      if (entry.project && entry.project !== "Global")
        projectsSet.add(entry.project);
      if (entry.category && entry.category !== "godmode")
        categoriesSet.add(entry.category);
    }
    let godModeContent = `# \u{1F451} GOD MODE: General Knowledge

`;
    godModeContent += `> **Total Memories:** ${entries.length}

`;
    godModeContent += `This is the absolute center of the BDB memB Architecture.

`;
    await this.writeOrUpdateFile(`${rootFolder}/God_Mode.md`, godModeContent);
    for (const proj of projectsSet) {
      let pContent = `---
project: "${proj}"
tags:
  - memB/project
---

`;
      pContent += `# \u{1F680} Project Hub: ${proj}

`;
      pContent += `**Parent:** [[${rootFolder}/God_Mode|God Mode]]

`;
      pContent += `*This is a structural hub. All memories related to ${proj} gravitate here.*
`;
      await this.writeOrUpdateFile(`${rootFolder}/Projects/${proj}.md`, pContent);
    }
    for (const cat of categoriesSet) {
      let cContent = `---
category: "${cat}"
tags:
  - memB/category
---

`;
      cContent += `# \u{1F3F7}\uFE0F Category Hub: ${cat}

`;
      cContent += `**Parent:** [[${rootFolder}/God_Mode|God Mode]]

`;
      cContent += `*This is a structural hub. All memories categorized as ${cat} gravitate here.*
`;
      await this.writeOrUpdateFile(`${rootFolder}/Categories/${cat}.md`, cContent);
    }
    for (const item of entries) {
      const shortId = item.id.substring(0, 8);
      let mContent = `---
id: "${item.id}"
date: "${item.created_at}"
tags:
  - memB/memory
---

`;
      mContent += `# \u{1F9E0} Memory: ${shortId}

`;
      if (item.project === "Global" && item.category === "godmode") {
        mContent += `**Linked to:** [[${rootFolder}/God_Mode|God Mode]]

`;
      } else {
        if (item.project && item.project !== "Global") {
          mContent += `**Project:** [[${rootFolder}/Projects/${item.project}|${item.project}]]
`;
        } else {
          mContent += `**Project:** [[${rootFolder}/God_Mode|God Mode]]
`;
        }
        if (item.category && item.category !== "godmode") {
          mContent += `**Category:** [[${rootFolder}/Categories/${item.category}|${item.category}]]
`;
        } else {
          mContent += `**Category:** [[${rootFolder}/God_Mode|God Mode]]
`;
        }
        mContent += `
`;
      }
      mContent += `## \u{1F4DC} Payload

`;
      mContent += `${item.data}
`;
      await this.writeOrUpdateFile(`${rootFolder}/Memories/${shortId}.md`, mContent);
    }
    await this.injectSexyGraphSettings();
  }
  async injectSexyGraphSettings() {
    const configDir = this.app.vault.configDir || ".obsidian";
    const graphPath = `${configDir}/graph.json`;
    const sexyConfig = {
      "collapse-filter": true,
      "search": "",
      "showSearch": false,
      "searchItemExclude": "",
      "searchItemTags": false,
      "searchItemAttachment": false,
      "hideUnresolved": true,
      "showTags": false,
      "showAttachments": false,
      "hideOrphans": true,
      "collapse-color-groups": false,
      "colorGroups": [
        {
          "query": "path:memB_Knowledge_Graph/God_Mode.md",
          "color": { "a": 1, "rgb": 16766720 }
        },
        {
          "query": "tag:#memB/project",
          "color": { "a": 1, "rgb": 5291775 }
        },
        {
          "query": "tag:#memB/category",
          "color": { "a": 1, "rgb": 16733610 }
        },
        {
          "query": "tag:#memB/memory",
          "color": { "a": 1, "rgb": 8947967 }
        }
      ],
      "collapse-display": false,
      "showArrow": false,
      "textFadeMultiplier": -1,
      "nodeSizeMultiplier": 1.1,
      "lineSizeMultiplier": 0.5,
      "collapse-forces": false,
      "centerStrength": 0.2,
      "repelStrength": 16.5,
      "linkStrength": 0.8,
      "linkDistance": 150,
      "scale": 0.7,
      "close": false
    };
    try {
      await this.app.vault.adapter.write(graphPath, JSON.stringify(sexyConfig, null, 2));
    } catch (e) {
      console.error("Failed to inject graph settings:", e);
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
