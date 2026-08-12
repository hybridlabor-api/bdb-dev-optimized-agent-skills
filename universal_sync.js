const fs = require('fs');
const path = require('path');
const os = require('os');
const homeDir = os.homedir();

function syncUniversal(masterMcpConfigPath, masterRulesDir, detections) {
    console.log('\n🌐 Universal Agent Harness Sync...');
    if (!fs.existsSync(masterMcpConfigPath)) {
        console.log(' -> Error: Master MCP config not found at ' + masterMcpConfigPath);
        return;
    }
    
    let masterMcpData = {};
    try {
        masterMcpData = JSON.parse(fs.readFileSync(masterMcpConfigPath, 'utf8'));
    } catch(e) {}
    
    const masterServers = masterMcpData.mcpServers || {};

    const syncMcpConfig = (targetPath) => {
        try {
            let data = { mcpServers: {} };
            if (fs.existsSync(targetPath)) {
                data = JSON.parse(fs.readFileSync(targetPath, 'utf8'));
                if (!data.mcpServers) data.mcpServers = {};
            }
            // Merge servers
            for (const [key, val] of Object.entries(masterServers)) {
                data.mcpServers[key] = val;
            }
            fs.mkdirSync(path.dirname(targetPath), { recursive: true });
            fs.writeFileSync(targetPath, JSON.stringify(data, null, 2));
        } catch(e) {
            console.log(`    Failed to sync MCP to ${targetPath}: ${e.message}`);
        }
    };
    
    const syncRules = (targetDir) => {
        if (!fs.existsSync(masterRulesDir)) return;
        try {
            fs.mkdirSync(targetDir, { recursive: true });
            const rules = fs.readdirSync(masterRulesDir);
            for (const rule of rules) {
                fs.copyFileSync(path.join(masterRulesDir, rule), path.join(targetDir, rule));
            }
        } catch(e) {
            console.log(`    Failed to sync rules to ${targetDir}: ${e.message}`);
        }
    };

    for (const d of detections) {
        console.log(` -> Injecting into ${d.name}...`);
        if (d.key === 'claude') {
            syncMcpConfig(path.join(d.path, 'claude_desktop_config.json'));
        } else if (d.key === 'cursor') {
            syncMcpConfig(path.join(d.path, 'mcp.json'));
            // Cursor global rules can be placed in user path? Cursor doesn't have a global rules dir by default, but we can put it in project if they run in a project.
            // For now just MCPs.
        } else if (d.key === 'windsurf') {
            syncMcpConfig(path.join(d.path, 'mcp.json'));
        } else if (d.key === 'vscode') {
            syncMcpConfig(path.join(d.path, 'mcp.json'));
        } else if (d.key === 'aider') {
            syncMcpConfig(path.join(d.path, 'mcp.json'));
        }
    }
    console.log(' -> Sync complete.');
}
module.exports = { syncUniversal };
