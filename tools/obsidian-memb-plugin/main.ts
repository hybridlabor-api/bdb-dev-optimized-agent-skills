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
        
        const projectsMap = new Map<string, any[]>();
        const categoriesMap = new Map<string, any[]>();
        
        for (const entry of entries) {
            const p = entry.project;
            const c = entry.category;
            
            if (!projectsMap.has(p)) projectsMap.set(p, []);
            projectsMap.get(p)?.push(entry);
            
            if (!categoriesMap.has(c)) categoriesMap.set(c, []);
            categoriesMap.get(c)?.push(entry);
        }
        
        // 1. Generate Index
        let indexContent = `# 🧠 memB Knowledge Graph Dashboard\n\n`;
        indexContent += `> **Total Memories Indexed:** ${entries.length} | **Projects:** ${projectsMap.size} | **Categories:** ${categoriesMap.size}\n\n`;
        indexContent += `## 📂 Projects Overview\n`;
        projectsMap.forEach((v, k) => {
            indexContent += `- [[Projects/${k}|${k}]] (${v.length} notes)\n`;
        });
        indexContent += `\n## 🏷️ Categories\n`;
        categoriesMap.forEach((v, k) => {
            indexContent += `- [[Categories/${k}|${k}]] (${v.length} notes)\n`;
        });
        
        await this.writeOrUpdateFile(`${rootFolder}/Dashboard.md`, indexContent);
        
        // 2. Generate Project Files
        for (const [proj, items] of projectsMap.entries()) {
            let pContent = `---\nproject: "${proj}"\ntotal_memories: ${items.length}\ntags:\n  - memB/project\n---\n\n`;
            pContent += `# 🚀 Project: ${proj}\n\nBack to [[Dashboard|Main Index]]\n\n## 📜 Documented Memories & Decisions\n\n`;
            
            for (const item of items) {
                pContent += `> [!NOTE] Memory Record (${item.id.substring(0,8)})\n`;
                pContent += `> **Category:** [[Categories/${item.category}|#${item.category}]]\n`;
                pContent += `> **Date:** ${item.created_at}\n>\n`;
                
                const lines = item.data.split('\n');
                for (const l of lines) {
                    pContent += `> ${l}\n`;
                }
                pContent += `\n---\n\n`;
            }
            
            await this.writeOrUpdateFile(`${rootFolder}/Projects/${proj}.md`, pContent);
        }
        
        // 3. Generate Category Files
        for (const [cat, items] of categoriesMap.entries()) {
            let cContent = `---\ncategory: "${cat}"\ntotal_memories: ${items.length}\ntags:\n  - memB/category\n---\n\n`;
            cContent += `# 🏷️ Category: ${cat}\n\nBack to [[Dashboard|Main Index]]\n\n## 📜 Category Entries\n\n`;
            
            for (const item of items) {
                cContent += `- **Project:** [[Projects/${item.project}|${item.project}]]\n`;
                cContent += `  \`\`\`text\n  ${item.data.substring(0, 300)}...\n  \`\`\`\n\n`;
            }
            
            await this.writeOrUpdateFile(`${rootFolder}/Categories/${cat}.md`, cContent);
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
