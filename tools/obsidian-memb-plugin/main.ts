import { Plugin, Notice, TFile, TFolder } from 'obsidian';
import * as child_process from 'child_process';
import * as path from 'path';
import * as os from 'os';

export default class MembSyncPlugin extends Plugin {
    async onload() {
        console.log('Loading memB AI Memory Sync Plugin');

        // Add ribbon icon
        const ribbonIconEl = this.addRibbonIcon('brain-circuit', 'Sync memB Knowledge Graph', (evt: MouseEvent) => {
            this.syncMemBData();
        });

        // Add command to command palette
        this.addCommand({
            id: 'sync-memb-data',
            name: 'Sync memB Knowledge Graph',
            callback: () => {
                this.syncMemBData();
            }
        });
    }

    onunload() {
        console.log('Unloading memB AI Memory Sync Plugin');
    }

    async syncMemBData() {
        new Notice('🧠 Syncing memB local vector memories...');
        
        try {
            // Get Python path and DB path
            const dbDir = process.env.MEMB_DATA_DIR || path.join(os.homedir(), '.MemBDB');
            const dbPath = path.join(dbDir, 'memb.db');
            
            // Inline python script to dump sqlite table safely to JSON
            const pythonScript = `
import sqlite3, json, sys
try:
    conn = sqlite3.connect('${dbPath.replace(/\\/g, '\\\\')}')
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
                    new Notice('❌ Failed to run Python SQLite dump: ' + error.message);
                    return;
                }
                
                try {
                    const data = JSON.parse(stdout);
                    if (data.error) {
                        new Notice('❌ memB DB Error: ' + data.error);
                        return;
                    }
                    
                    await this.generateVaultFiles(data);
                    new Notice(`✅ Successfully synced ${data.length} memB entries into Obsidian!`);
                    
                } catch (e) {
                    new Notice('❌ Failed to parse memB data: ' + e);
                }
            });
            
        } catch (error) {
            new Notice('❌ Plugin Error: ' + error);
        }
    }
    
    async generateVaultFiles(entries: any[]) {
        const rootFolder = "memB_Knowledge_Graph";
        
        // Ensure folders exist
        await this.ensureFolder(rootFolder);
        await this.ensureFolder(`${rootFolder}/Projects`);
        await this.ensureFolder(`${rootFolder}/Categories`);
        await this.ensureFolder(`${rootFolder}/Memories`);
        
        const projectsSet = new Set<string>();
        const categoriesSet = new Set<string>();
        
        // 1. Gather all unique Projects and Categories
        for (const entry of entries) {
            if (entry.project && entry.project !== "Global") projectsSet.add(entry.project);
            if (entry.category && entry.category !== "godmode") categoriesSet.add(entry.category);
        }
        
        // 2. Generate God Mode (Central Hub)
        let godModeContent = `# 👑 GOD MODE: General Knowledge\n\n`;
        godModeContent += `> **Total Memories:** ${entries.length}\n\n`;
        godModeContent += `This is the absolute center of the BDB memB Architecture.\n\n`;
        await this.writeOrUpdateFile(`${rootFolder}/God_Mode.md`, godModeContent);
        
        // 3. Generate Project Hubs
        for (const proj of projectsSet) {
            let pContent = `---\nproject: "${proj}"\ntags:\n  - memB/project\n---\n\n`;
            pContent += `# 🚀 Project Hub: ${proj}\n\n`;
            pContent += `**Parent:** [[${rootFolder}/God_Mode|God Mode]]\n\n`;
            pContent += `*This is a structural hub. All memories related to ${proj} gravitate here.*\n`;
            await this.writeOrUpdateFile(`${rootFolder}/Projects/${proj}.md`, pContent);
        }
        
        // 4. Generate Category Hubs
        for (const cat of categoriesSet) {
            let cContent = `---\ncategory: "${cat}"\ntags:\n  - memB/category\n---\n\n`;
            cContent += `# 🏷️ Category Hub: ${cat}\n\n`;
            cContent += `**Parent:** [[${rootFolder}/God_Mode|God Mode]]\n\n`;
            cContent += `*This is a structural hub. All memories categorized as ${cat} gravitate here.*\n`;
            await this.writeOrUpdateFile(`${rootFolder}/Categories/${cat}.md`, cContent);
        }
        
        // 5. Generate Individual Memories (The Neurons)
        for (const item of entries) {
            const shortId = item.id.substring(0, 8);
            let mContent = `---\nid: "${item.id}"\ndate: "${item.created_at}"\ntags:\n  - memB/memory\n---\n\n`;
            mContent += `# 🧠 Memory: ${shortId}\n\n`;
            
            // Connect to Parent Hubs to create gravitational pull
            if (item.project === "Global" && item.category === "godmode") {
                mContent += `**Linked to:** [[${rootFolder}/God_Mode|God Mode]]\n\n`;
            } else {
                if (item.project && item.project !== "Global") {
                    mContent += `**Project:** [[${rootFolder}/Projects/${item.project}|${item.project}]]\n`;
                } else {
                    mContent += `**Project:** [[${rootFolder}/God_Mode|God Mode]]\n`;
                }
                
                if (item.category && item.category !== "godmode") {
                    mContent += `**Category:** [[${rootFolder}/Categories/${item.category}|${item.category}]]\n`;
                } else {
                    mContent += `**Category:** [[${rootFolder}/God_Mode|God Mode]]\n`;
                }
                mContent += `\n`;
            }
            
            mContent += `## 📜 Payload\n\n`;
            mContent += `${item.data}\n`;
            
            await this.writeOrUpdateFile(`${rootFolder}/Memories/${shortId}.md`, mContent);
        }
        
        // 6. Inject Sexy Graph Settings
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
    
    async ensureFolder(folderPath: string) {
        const folder = this.app.vault.getAbstractFileByPath(folderPath);
        if (!folder) {
            await this.app.vault.createFolder(folderPath);
        }
    }
    
    async writeOrUpdateFile(filePath: string, content: string) {
        const file = this.app.vault.getAbstractFileByPath(filePath);
        if (file instanceof TFile) {
            await this.app.vault.modify(file, content);
        } else {
            await this.app.vault.create(filePath, content);
        }
    }
}
