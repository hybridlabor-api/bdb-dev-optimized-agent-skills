const fs = require('fs');
let code = fs.readFileSync('installer.js', 'utf8');

const oldPromptMenu = `    console.log("\\nTarget AI Platform:");
    console.log(" (1) Google Antigravity (Default)");
    console.log(" (2) Claude Desktop / Claude Code");
    console.log(" (3) Cursor / Generic IDE (Project-local)");
    console.log(" (4) Custom Installation (Specify custom paths manually)");
    
    rl.question("\\nSelect platform [1/2/3/4]: ", (platformAns) => {
        const platform = platformAns.trim() || '1';`;

const newPromptMenu = `    console.log("\\nTarget AI Platform:");
    console.log(" (1) Google Antigravity (Default)");
    console.log(" (2) Claude Desktop / Claude Code");
    console.log(" (3) Cursor / Generic IDE (Project-local)");
    console.log(" (4) Custom Installation (Specify custom paths manually)");
    console.log(" (5) ChatGPT Codex CLI");
    console.log(" (6) Windsurf IDE");
    console.log(" (7) Roo Code / Cline / VS Code");
    console.log(" (8) Aider CLI");
    
    rl.question("\\nSelect platform [1-8]: ", (platformAns) => {
        const platform = platformAns.trim() || '1';`;

code = code.replace(oldPromptMenu, newPromptMenu);

const oldPathLogic = `    if (platform === '2') {
        // Claude Desktop
        console.log("\\n[Platform: Claude Desktop] Adapting installation paths...");
        targetSkillDir = path.join(homeDir, '.bdb-skills');
        targetLegacyDir = path.join(homeDir, '.bdb-skills', 'legacy');
        
        let claudeAppSupport = process.platform === 'win32' 
            ? path.join(process.env.APPDATA || homeDir, 'Claude')
            : path.join(homeDir, 'Library', 'Application Support', 'Claude');
            
        targetMcpDir = claudeAppSupport;
        mcpConfigPath = path.join(claudeAppSupport, 'claude_desktop_config.json');
    } else if (platform === '3') {
        // Cursor / Generic
        console.log("\\n[Platform: Cursor / Generic IDE] Adapting installation paths...");
        targetSkillDir = path.join(currentDir, '.cursor', 'bdb-skills');
        targetLegacyDir = path.join(currentDir, '.cursor', 'bdb-skills', 'legacy');
        targetWorkspaceDir = path.join(currentDir, '.cursor', 'workspace_skills');
        targetMcpDir = path.join(currentDir, '.cursor');
        mcpConfigPath = path.join(targetMcpDir, 'mcp.json');
    } else if (platform === '4' && customPaths) {
        // Custom paths
        console.log("\\n[Platform: Custom Path] Applying custom paths...");
        targetSkillDir = customPaths.skillDir;
        targetLegacyDir = customPaths.legacyDir;
        targetWorkspaceDir = customPaths.workspaceDir;
        targetMcpDir = customPaths.mcpDir;
        mcpConfigPath = customPaths.mcpConfigPath;
    }`;

const newPathLogic = `    if (platform === '2') {
        // Claude Desktop
        console.log("\\n[Platform: Claude Desktop] Adapting installation paths...");
        targetSkillDir = path.join(homeDir, '.bdb-skills');
        targetLegacyDir = path.join(homeDir, '.bdb-skills', 'legacy');
        
        let claudeAppSupport = process.platform === 'win32' 
            ? path.join(process.env.APPDATA || homeDir, 'Claude')
            : path.join(homeDir, 'Library', 'Application Support', 'Claude');
            
        targetMcpDir = claudeAppSupport;
        mcpConfigPath = path.join(claudeAppSupport, 'claude_desktop_config.json');
    } else if (platform === '3') {
        // Cursor / Generic
        console.log("\\n[Platform: Cursor / Generic IDE] Adapting installation paths...");
        targetSkillDir = path.join(currentDir, '.cursor', 'bdb-skills');
        targetLegacyDir = path.join(currentDir, '.cursor', 'bdb-skills', 'legacy');
        targetWorkspaceDir = path.join(currentDir, '.cursor', 'workspace_skills');
        targetMcpDir = path.join(currentDir, '.cursor');
        mcpConfigPath = path.join(targetMcpDir, 'mcp.json');
    } else if (platform === '5') {
        // Codex
        console.log("\\n[Platform: ChatGPT Codex CLI] Adapting installation paths...");
        targetSkillDir = path.join(homeDir, '.codex', 'skills');
        targetLegacyDir = path.join(homeDir, '.codex', 'skills', 'legacy');
        targetMcpDir = path.join(homeDir, '.codex');
        mcpConfigPath = path.join(targetMcpDir, 'config.toml');
    } else if (platform === '6') {
        // Windsurf
        console.log("\\n[Platform: Windsurf IDE] Adapting installation paths...");
        targetSkillDir = path.join(homeDir, '.windsurf', 'bdb-skills');
        targetLegacyDir = path.join(homeDir, '.windsurf', 'bdb-skills', 'legacy');
        targetMcpDir = path.join(homeDir, '.windsurf');
        mcpConfigPath = path.join(targetMcpDir, 'mcp.json');
    } else if (platform === '7') {
        // Roo / Cline / VS Code
        console.log("\\n[Platform: Roo Code / Cline] Adapting installation paths...");
        targetSkillDir = path.join(homeDir, '.roo', 'bdb-skills');
        targetLegacyDir = path.join(homeDir, '.roo', 'bdb-skills', 'legacy');
        targetMcpDir = path.join(homeDir, '.roo');
        mcpConfigPath = path.join(targetMcpDir, 'mcp.json');
    } else if (platform === '8') {
        // Aider
        console.log("\\n[Platform: Aider CLI] Adapting installation paths...");
        targetSkillDir = path.join(homeDir, '.aider', 'bdb-skills');
        targetLegacyDir = path.join(homeDir, '.aider', 'bdb-skills', 'legacy');
        targetMcpDir = path.join(homeDir, '.aider');
        mcpConfigPath = path.join(targetMcpDir, 'mcp.json');
    } else if (platform === '4' && customPaths) {
        // Custom paths
        console.log("\\n[Platform: Custom Path] Applying custom paths...");
        targetSkillDir = customPaths.skillDir;
        targetLegacyDir = customPaths.legacyDir;
        targetWorkspaceDir = customPaths.workspaceDir;
        targetMcpDir = customPaths.mcpDir;
        mcpConfigPath = customPaths.mcpConfigPath;
    }`;

code = code.replace(oldPathLogic, newPathLogic);

fs.writeFileSync('installer.js', code);
console.log("installer.js patched.");
