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
        
        // Ensure root folder
        await this.ensureFolder(rootFolder);
        await this.ensureFolder(`${rootFolder}/Projects`);
        
        // 1. Build the Data Tree
        const tree: Record<string, Record<string, any[]>> = {};
        let totalMemories = 0;
        
        for (const entry of entries) {
            let p = entry.project || "Global";
            let c = entry.category || "General";
            if (c === "godmode") {
                p = "Global"; // Force godmode into Global
            }
            
            if (!tree[p]) tree[p] = {};
            if (!tree[p][c]) tree[p][c] = [];
            tree[p][c].push(entry);
            totalMemories++;
        }
        
        // 2. Generate God Mode (Central Hub & MOC)
        let godModeContent = `# 👑 GOD MODE: Core Knowledge Base\n\n`;
        godModeContent += `> **Total Ecosystem Memories:** ${totalMemories}\n\n`;
        godModeContent += `## 🌌 Ecosystem Topology (Map of Content)\n\n`;
        
        for (const [proj, categories] of Object.entries(tree)) {
            const projMemories = Object.values(categories).reduce((acc, val) => acc + val.length, 0);
            godModeContent += `### [[${rootFolder}/Projects/${proj}/_Hub|Project: ${proj}]] (${projMemories} memories)\n`;
            for (const [cat, items] of Object.entries(categories)) {
                godModeContent += `- **[[${rootFolder}/Projects/${proj}/${cat}/_Hub|${cat}]]**: ${items.length} records\n`;
            }
            godModeContent += `\n`;
        }
        await this.writeOrUpdateFile(`${rootFolder}/God_Mode.md`, godModeContent);
        
        // 3. Generate Strict Tree Hierarchy (Projects -> Categories -> Clusters -> Neurons)
        for (const [proj, categories] of Object.entries(tree)) {
            await this.ensureFolder(`${rootFolder}/Projects/${proj}`);
            
            // Project Hub
            const projMemories = Object.values(categories).reduce((acc, val) => acc + val.length, 0);
            let pContent = `---\ntags:\n  - memB/project\n---\n\n# 🚀 Project: ${proj}\n\n**Parent:** [[${rootFolder}/God_Mode|God Mode]]\n\n## Sub-Clusters\n`;
            for (const cat of Object.keys(categories)) {
                pContent += `- [[${rootFolder}/Projects/${proj}/${cat}/_Hub|Category: ${cat}]]\n`;
            }
            await this.writeOrUpdateFile(`${rootFolder}/Projects/${proj}/_Hub.md`, pContent);
            
            for (const [cat, items] of Object.entries(categories)) {
                await this.ensureFolder(`${rootFolder}/Projects/${proj}/${cat}`);
                
                // Category Hub
                let cContent = `---\ntags:\n  - memB/category\n---\n\n# 🏷️ Category: ${cat}\n\n**Parent:** [[${rootFolder}/Projects/${proj}/_Hub|Project: ${proj}]]\n\n`;
                
                // Auto-Balancing: Sub-clustering if > 25 items
                const CLUSTER_SIZE = 25;
                if (items.length > CLUSTER_SIZE) {
                    cContent += `## Memory Clusters (Auto-Balanced)\n`;
                    const numClusters = Math.ceil(items.length / CLUSTER_SIZE);
                    
                    for (let i = 0; i < numClusters; i++) {
                        const clusterName = `Cluster_${i + 1}`;
                        await this.ensureFolder(`${rootFolder}/Projects/${proj}/${cat}/${clusterName}`);
                        cContent += `- [[${rootFolder}/Projects/${proj}/${cat}/${clusterName}/_Hub|${clusterName}]]\n`;
                        
                        // Cluster Hub
                        let clContent = `---\ntags:\n  - memB/cluster\n---\n\n# 🌌 ${clusterName} (${cat})\n\n**Parent:** [[${rootFolder}/Projects/${proj}/${cat}/_Hub|Category: ${cat}]]\n\n`;
                        
                        const clusterItems = items.slice(i * CLUSTER_SIZE, (i + 1) * CLUSTER_SIZE);
                        for (const item of clusterItems) {
                            await this.generateMemoryNode(item, `${rootFolder}/Projects/${proj}/${cat}/${clusterName}`, `[[${rootFolder}/Projects/${proj}/${cat}/${clusterName}/_Hub|${clusterName}]]`);
                        }
                        await this.writeOrUpdateFile(`${rootFolder}/Projects/${proj}/${cat}/${clusterName}/_Hub.md`, clContent);
                    }
                } else {
                    cContent += `## 🧠 Memories\n`;
                    for (const item of items) {
                        await this.generateMemoryNode(item, `${rootFolder}/Projects/${proj}/${cat}`, `[[${rootFolder}/Projects/${proj}/${cat}/_Hub|Category: ${cat}]]`);
                    }
                }
                
                await this.writeOrUpdateFile(`${rootFolder}/Projects/${proj}/${cat}/_Hub.md`, cContent);
            }
        }
        
        // 4. Inject Sexy Graph Settings
        await this.injectSexyGraphSettings();
    }
    
    async generateMemoryNode(item: any, folderPath: string, parentLink: string) {
        const shortId = item.id.substring(0, 8);
        let mContent = `---\nid: "${item.id}"\ndate: "${item.created_at}"\ntags:\n  - memB/memory\n---\n\n`;
        mContent += `# 🧠 ${shortId}\n\n`;
        mContent += `**Parent:** ${parentLink}\n\n`;
        mContent += `## 📜 Payload\n\n${item.data}\n`;
        await this.writeOrUpdateFile(`${folderPath}/${shortId}.md`, mContent);
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
                    "query": "tag:#memB/cluster",
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
            "centerStrength": 0.5,
            "repelStrength": 18.5,
            "linkStrength": 1.0,
            "linkDistance": 90,
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
