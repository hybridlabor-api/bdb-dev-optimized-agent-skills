#!/usr/bin/env node

const fs = require('fs');
const path = require('path');
const readline = require('readline');
const os = require('os');
const https = require('https');

const pkgPath = path.join(__dirname, 'package.json');
let pkg = { name: '@hybridlabor-api/bdb-dev-optimized-agent-skills', version: '1.1.0' };
if (fs.existsSync(pkgPath)) {
    try { pkg = JSON.parse(fs.readFileSync(pkgPath, 'utf8')); } catch (e) {}
}

const colors = {
    reset: "\x1b[0m",
    bold: "\x1b[1m",
    cyan: "\x1b[36m",
    purple: "\x1b[38;2;157;78;221m",
    purpleBold: "\x1b[1;\x1b[38;2;157;78;221m",
    green: "\x1b[32m",
    yellow: "\x1b[33m",
    magenta: "\x1b[35m",
    dim: "\x1b[2m"
};

function isNewerVersion(local, remote) {
    const lParts = local.split('.').map(Number);
    const rParts = remote.split('.').map(Number);
    for (let i = 0; i < Math.max(lParts.length, rParts.length); i++) {
        const l = lParts[i] || 0;
        const r = rParts[i] || 0;
        if (r > l) return true;
        if (l > r) return false;
    }
    return false;
}

function checkForUpdates() {
    return new Promise((resolve) => {
        const req = https.get(`https://registry.npmjs.org/${pkg.name}/latest`, { timeout: 1500 }, (res) => {
            let data = '';
            res.on('data', chunk => data += chunk);
            res.on('end', () => {
                try {
                    const latest = JSON.parse(data).version;
                    if (latest && isNewerVersion(pkg.version, latest)) {
                        console.log(`${colors.yellow}${colors.bold}╭───────────────────────────────────────────────────────────╮${colors.reset}`);
                        console.log(`${colors.yellow}${colors.bold}│  💡 Update available: ${colors.dim}${pkg.version}${colors.reset}${colors.yellow}${colors.bold} ➔ ${colors.green}${latest}${colors.reset}                   │${colors.reset}`);
                        console.log(`${colors.yellow}${colors.bold}│  Run: ${colors.cyan}npx ${pkg.name}@latest${colors.reset}                       │${colors.reset}`);
                        console.log(`${colors.yellow}${colors.bold}╰───────────────────────────────────────────────────────────╯${colors.reset}\n`);
                    }
                } catch (e) {}
                resolve();
            });
        });
        req.on('error', () => resolve());
        req.on('timeout', () => { req.destroy(); resolve(); });
    });
}

const cols = process.stdout.columns || 110;

const headerArt = `
${colors.purple}${colors.bold}                 ██████╗ ██████╗ ██████╗      █████╗  ██████╗ ███████╗███╗   ██╗████████╗     ██████╗ ███████╗
                 ██╔══██╗██╔══██╗██╔══██╗    ██╔══██╗██╔════╝ ██╔════╝████╗  ██║╚══██╔══╝    ██╔═══██╗██╔════╝
                 ██████╔╝██║  ██║██████╔╝    ███████║██║  ███╗█████╗  ██╔██╗ ██║   ██║       ██║   ██║███████╗
                 ██╔══██╗██║  ██║██╔══██╗    ██╔══██║██║   ██║██╔══╝  ██║╚██╗██║   ██║       ██║   ██║╚════██║
                 ██████╔╝██████╔╝██████╔╝    ██║  ██║╚██████╔╝███████╗██║ ╚████║   ██║       ╚██████╔╝███████║
                 ╚═════╝ ╚═════╝ ╚═════╝     ╚═╝  ╚═╝ ╚═════╝ ╚══════╝╚═╝  ╚═══╝   ╚═╝        ╚═════╝ ╚══════╝${colors.reset}

${colors.cyan}${colors.bold}                                          O P T I M I Z E D   A G E N T   S K I L L S${colors.reset}
`;

const divider = '─'.repeat(Math.max(110, cols));

console.log(headerArt);
console.log(`${colors.dim} ${divider}${colors.reset}`);
console.log(`${colors.green}${colors.bold} 🚀 Starting Installation (v${pkg.version})${colors.reset}`);
console.log(`${colors.dim} ${divider}${colors.reset}\n`);

checkForUpdates();

const rl = readline.createInterface({
  input: process.stdin,
  output: process.stdout
});

const homeDir = os.homedir();
const currentDir = process.cwd();
const scriptDir = __dirname;

let srcDir = scriptDir;
if (!fs.existsSync(path.join(srcDir, 'skills')) && fs.existsSync(path.join(srcDir, '..', 'skills'))) {
    srcDir = path.join(scriptDir, '..');
} else if (!fs.existsSync(path.join(srcDir, 'skills'))) {
    console.error("Error: Cannot find skills payload directory.");
    process.exit(1);
}

const geminiDir = path.join(homeDir, '.gemini');
const globalConfigDir = path.join(geminiDir, 'config', 'skills');
const globalLegacyDir = path.join(geminiDir, 'skills');
const workspaceDir = path.join(currentDir, '.agents', 'skills');

const now = new Date();
const timestamp = now.getFullYear().toString() + 
    (now.getMonth()+1).toString().padStart(2, '0') + 
    now.getDate().toString().padStart(2, '0') + "_" + 
    now.getHours().toString().padStart(2, '0') + 
    now.getMinutes().toString().padStart(2, '0') + 
    now.getSeconds().toString().padStart(2, '0');
    
const backupDir = path.join(geminiDir, `skills_backup_${timestamp}`);

// Auto-accept flags for CI/CD or autonomous agents
const isAutoYes = process.argv.includes('-y') || process.argv.includes('--yes');

function detectPlatforms() {
    const detections = [];
    
    // Google Antigravity
    if (fs.existsSync(geminiDir)) {
        detections.push({ name: "Google Antigravity", path: geminiDir, key: "antigravity" });
    }

    // Codex CLI / ChatGPT Codex
    const codexDir = path.join(homeDir, '.codex');
    if (fs.existsSync(codexDir) || fs.existsSync(path.join(homeDir, '.codex', 'config.toml'))) {
        detections.push({ name: "ChatGPT Codex CLI", path: codexDir, key: "codex" });
    }

    // Claude Code CLI
    const claudeCodeConfig = path.join(homeDir, '.claude.json');
    const claudeCodeDir = path.join(homeDir, '.claude');
    if (fs.existsSync(claudeCodeConfig) || fs.existsSync(claudeCodeDir)) {
        detections.push({ name: "Claude Code CLI", path: claudeCodeDir, key: "claudecode" });
    }
    
    // Claude Desktop
    const claudePath = process.platform === 'win32' 
        ? path.join(process.env.APPDATA || homeDir, 'Claude')
        : path.join(homeDir, 'Library', 'Application Support', 'Claude');
    if (fs.existsSync(claudePath)) {
        detections.push({ name: "Claude Desktop", path: claudePath, key: "claudedesktop" });
    }
    
    // Cursor IDE
    const cursorPath = process.platform === 'win32' 
        ? path.join(process.env.APPDATA || homeDir, 'Cursor')
        : path.join(homeDir, 'Library', 'Application Support', 'Cursor');
    if (fs.existsSync(cursorPath)) {
        detections.push({ name: "Cursor IDE", path: cursorPath, key: "cursor" });
    }

    // Windsurf IDE
    const windsurfPath = process.platform === 'win32' 
        ? path.join(process.env.APPDATA || homeDir, 'Windsurf')
        : path.join(homeDir, 'Library', 'Application Support', 'Windsurf');
    if (fs.existsSync(windsurfPath)) {
        detections.push({ name: "Windsurf IDE", path: windsurfPath, key: "windsurf" });
    }

    // Roo Code & Cline (VS Code Extensions)
    const vscodePath = process.platform === 'win32' 
        ? path.join(process.env.APPDATA || homeDir, 'Code')
        : path.join(homeDir, 'Library', 'Application Support', 'Code');
    const rooPath = path.join(homeDir, '.roo');
    const clinePath = path.join(homeDir, '.cline');
    if (fs.existsSync(vscodePath) || fs.existsSync(rooPath) || fs.existsSync(clinePath)) {
        detections.push({ name: "Roo Code / Cline / VS Code", path: vscodePath, key: "vscode" });
    }

    // Aider CLI
    const aiderConf = path.join(homeDir, '.aider.conf.yml');
    if (fs.existsSync(aiderConf) || fs.existsSync(path.join(homeDir, '.aider'))) {
        detections.push({ name: "Aider CLI", path: homeDir, key: "aider" });
    }

    return detections;
}

function promptMode(callback) {
    if (isAutoYes) {
        return callback({ mode: '1', platform: '1' });
    }

    const detections = detectPlatforms();
    if (detections.length > 0) {
        console.log("\nDetected Agent Environments on this system:");
        detections.forEach(d => console.log("  * " + d.name + " (detected at " + d.path + ")"));
    } else {
        console.log("\nNo active agent config directories auto-detected in standard locations.");
    }

    console.log("\nTarget AI Platform:");
    console.log(" (1) Google Antigravity (Default)");
    console.log(" (2) Claude Desktop / Claude Code");
    console.log(" (3) Cursor / Generic IDE (Project-local)");
    console.log(" (4) Custom Installation (Specify custom paths manually)");
    console.log(" (5) ChatGPT Codex CLI");
    console.log(" (6) Windsurf IDE");
    console.log(" (7) Roo Code / Cline / VS Code");
    console.log(" (8) Aider CLI");
    
    rl.question("\nSelect platform [1-8]: ", (platformAns) => {
        const platform = platformAns.trim() || '1';
        
        console.log("\nInstallation Mode:");
        console.log(" (1) Merge: Keep your existing skills/MCPs and add/update BDB tools.");
        console.log(" (2) Replace: Backup and wipe your existing skills/MCPs, installing ONLY BDB tools.");
        rl.question("\nSelect mode [1/2]: ", (modeAns) => {
            const mode = modeAns.trim() === '2' ? '2' : '1';
            
            if (platform === '4') {
                // Prompt for custom paths
                console.log("\n--- Custom Path Configuration ---");
                rl.question("Target directory for global skills [default: " + path.join(homeDir, '.bdb-skills') + "]: ", (skillDir) => {
                    const customSkillDir = skillDir.trim() || path.join(homeDir, '.bdb-skills');
                    rl.question("Target directory for legacy skills [default: " + path.join(customSkillDir, 'legacy') + "]: ", (legacyDir) => {
                        const customLegacyDir = legacyDir.trim() || path.join(customSkillDir, 'legacy');
                        rl.question("Target directory for workspace skills [default: " + workspaceDir + "]: ", (workDir) => {
                            const customWorkspaceDir = workDir.trim() || workspaceDir;
                            rl.question("Target path for MCP Config JSON file [default: " + path.join(homeDir, 'mcp_config.json') + "]: ", (mcpConf) => {
                                const customMcpConfigPath = mcpConf.trim() || path.join(homeDir, 'mcp_config.json');
                                callback({
                                    mode,
                                    platform,
                                    customPaths: {
                                        skillDir: customSkillDir,
                                        legacyDir: customLegacyDir,
                                        workspaceDir: customWorkspaceDir,
                                        mcpConfigPath: customMcpConfigPath,
                                        mcpDir: path.dirname(customMcpConfigPath)
                                    }
                                });
                            });
                        });
                    });
                });
            } else {
                callback({ mode, platform });
            }
        });
    });
}

async function promptMcpSelection(mcpsDir) {
    if (isAutoYes) {
        try { return fs.readdirSync(mcpsDir, { withFileTypes: true }).filter(d => d.isDirectory() && !d.name.startsWith('.') && d.name !== '__pycache__').map(d => d.name); } catch(e) { return []; }
    }
    let availableMcps = [];
    try { 
        availableMcps = fs.readdirSync(mcpsDir, { withFileTypes: true })
            .filter(d => d.isDirectory() && !d.name.startsWith('.') && d.name !== '__pycache__')
            .map(d => d.name); 
    } catch(e) { return []; }
    if (availableMcps.length === 0) return [];

    const selections = availableMcps.filter(m => m !== 'memb-mcp').map(mcp => ({ name: mcp, selected: false }));

    const displayMenu = () => {
        console.log(`\n${colors.magenta}${colors.bold}--- Select Optional MCPs to Install ---${colors.reset}`);
        console.log(` ${colors.green}[x] memb-mcp${colors.reset} ${colors.dim}(Core Module - Always Installed)${colors.reset}`);
        selections.forEach((mcp, index) => {
            const check = mcp.selected ? `${colors.green}x${colors.reset}` : ' ';
            console.log(` ${colors.cyan}${index + 1}.${colors.reset} [${check}] ${colors.bold}${mcp.name}${colors.reset}`);
        });
        console.log(`\n${colors.dim}Type a number to toggle, 'all' to select all, 'none' to clear, or 'done' to proceed:${colors.reset}`);
    };

    return new Promise((resolve) => {
        const ask = () => {
            displayMenu();
            rl.question('\n> ', (answer) => {
                const input = answer.trim().toLowerCase();
                if (input === 'done' || input === '') { 
                    resolve(['memb-mcp', ...selections.filter(s => s.selected).map(s => s.name)]); 
                    return; 
                }
                if (input === 'all') { selections.forEach(s => s.selected = true); }
                else if (input === 'none') { selections.forEach(s => s.selected = false); }
                else {
                    const num = parseInt(input, 10);
                    if (!isNaN(num) && num > 0 && num <= selections.length) { selections[num - 1].selected = !selections[num - 1].selected; }
                    else { console.log('Invalid input. Please try again.'); }
                }
                ask();
            });
        };
        ask();
    });
}

async function promptCredentials() {
    if (isAutoYes) return { gemini: "", github: "", openwikiProvider: "google", openwikiModel: "", openwikiBaseUrl: "" };
    return new Promise((resolve) => {
        console.log(`\n${colors.magenta}${colors.bold}--- Integrations & Credentials ---${colors.reset}`);

        // Step 1: LLM Provider for OpenWiki
        console.log(`\n${colors.cyan}${colors.bold}OpenWiki Documentation Engine - LLM Provider${colors.reset}`);
        console.log(`  ${colors.dim}[1] Gemma 4 12B / Gemini   – Google AI Studio (FREE, default)${colors.reset}`);
        console.log(`  ${colors.dim}[2] Groq                   – Ultra-Fast Llama 3.3 70B (Groq API)${colors.reset}`);
        console.log(`  ${colors.dim}[3] Grok / xAI            – Grok 2 (api.x.ai)${colors.reset}`);
        console.log(`  ${colors.dim}[4] Nvidia NIM            – Llama 3.3 70B (integrate.api.nvidia.com)${colors.reset}`);
        console.log(`  ${colors.dim}[5] OpenRouter            – Claude 3.5, Qwen, Kimi, Llama (openrouter.ai)${colors.reset}`);
        console.log(`  ${colors.dim}[6] OpenAI                – GPT-4o-mini / GPT-4o (api.openai.com)${colors.reset}`);
        console.log(`  ${colors.dim}[7] Ollama / LM Studio    – Local LLM (no API key, no cost)${colors.reset}`);
        console.log(`  ${colors.dim}[8] Custom OpenAI API     – Custom Base URL + API Key + Model${colors.reset}`);

        rl.question(`${colors.yellow}Choose provider [1-8, default: 1]: ${colors.reset}`, (choice) => {
            let provider = "google", model = "", baseUrl = "", keyEnvName = "GEMINI_API_KEY";
            const c = choice.trim();

            if (c === "2")      { provider = "groq";       model = "llama-3.3-70b-versatile"; keyEnvName = "GROQ_API_KEY"; }
            else if (c === "3") { provider = "grok";       model = "grok-2-latest";           keyEnvName = "XAI_API_KEY"; }
            else if (c === "4") { provider = "nvidia";     model = "meta/llama-3.3-70b-instruct"; keyEnvName = "NVIDIA_API_KEY"; baseUrl = "https://integrate.api.nvidia.com/v1"; }
            else if (c === "5") { provider = "openrouter"; model = "anthropic/claude-3.5-sonnet"; keyEnvName = "OPENROUTER_API_KEY"; }
            else if (c === "6") { provider = "openai";     model = "gpt-4o-mini";            keyEnvName = "OPENAI_API_KEY"; }
            else if (c === "7") { provider = "ollama";     model = "llama3";                 baseUrl = "http://localhost:11434/v1"; }
            else if (c === "8") { provider = "custom";     keyEnvName = "OPENWIKI_API_KEY"; }

            const askBaseUrl = (afterUrl) => {
                if (c === "8") {
                    rl.question(`${colors.yellow}Custom Base URL [e.g. https://integrate.api.nvidia.com/v1]: ${colors.reset}`, (u) => {
                        baseUrl = u.trim();
                        afterUrl();
                    });
                } else if (c === "7") {
                    rl.question(`${colors.yellow}Ollama Base URL [default: http://localhost:11434/v1]: ${colors.reset}`, (u) => {
                        if (u.trim()) baseUrl = u.trim();
                        afterUrl();
                    });
                } else {
                    afterUrl();
                }
            };

            const askModel = (afterModel) => {
                const defaultModel = model || (provider === "google" ? "gemma-4-12b-it" : "gpt-4o-mini");
                rl.question(`${colors.yellow}Model name [default: ${defaultModel}]: ${colors.reset}`, (m) => {
                    if (m.trim()) model = m.trim();
                    afterModel();
                });
            };

            const askApiKey = (afterKey) => {
                if (provider === "ollama") { afterKey(""); return; }
                rl.question(`${colors.yellow}Enter your ${keyEnvName} for OpenWiki${colors.reset} ${colors.dim}(leave blank to skip):${colors.reset} `, afterKey);
            };

            const askGitHub = (apiKey) => {
                rl.question(`${colors.yellow}Enter your GITHUB_PERSONAL_ACCESS_TOKEN for GitHub MCP${colors.reset} ${colors.dim}(leave blank to skip):${colors.reset} `, (github) => {
                    resolve({ gemini: apiKey.trim(), github: github.trim(), openwikiProvider: provider, openwikiModel: model, openwikiBaseUrl: baseUrl });
                });
            };

            askBaseUrl(() => askModel(() => askApiKey((apiKey) => askGitHub(apiKey))));
        });
    });
}

async function installOpenWikiDaemon(apiKey, targetSkillDir, openwikiEnv = {}) {
    const prov = openwikiEnv.provider || "google";
    if (!apiKey && !["ollama", "lmstudio"].includes(prov)) { console.log(' -> Skipping OpenWiki Daemon background installation (no API key provided).'); return; }
    console.log('\nInstalling OpenWiki Daemon...');
    const { spawn, execSync } = require('child_process');
    const scriptBase = path.join(targetSkillDir, 'openwiki-skill', 'scripts');

    const daemonEnv = Object.assign({}, process.env, {
        OPENWIKI_PROVIDER:  prov,
        OPENWIKI_MODEL:     openwikiEnv.model   || '',
        OPENWIKI_BASE_URL:  openwikiEnv.baseUrl || '',
        OPENWIKI_API_KEY:   apiKey || '',
        GEMINI_API_KEY:     prov === 'google' ? apiKey : (process.env.GEMINI_API_KEY || ''),
        OPENAI_API_KEY:     prov === 'openai' ? apiKey : (process.env.OPENAI_API_KEY || ''),
        GROQ_API_KEY:       prov === 'groq'   ? apiKey : (process.env.GROQ_API_KEY   || ''),
        XAI_API_KEY:        ['grok', 'xai'].includes(prov) ? apiKey : (process.env.XAI_API_KEY || ''),
        NVIDIA_API_KEY:     prov === 'nvidia' ? apiKey : (process.env.NVIDIA_API_KEY || ''),
        OPENROUTER_API_KEY: prov === 'openrouter' ? apiKey : (process.env.OPENROUTER_API_KEY || ''),
    });

    return new Promise((resolve) => {
        let command, args;
        if (os.platform() === 'win32') {
            command = 'powershell.exe';
            args = ['-ExecutionPolicy', 'Bypass', '-File', path.join(scriptBase, 'install_daemon.ps1')];
        } else {
            command = 'sh';
            const scriptPath = path.join(scriptBase, 'install_daemon.sh');
            args = [scriptPath];
            try { fs.chmodSync(scriptPath, '755'); } catch (e) {}
        }
        const child = spawn(command, args, { stdio: 'inherit', env: daemonEnv });
        child.on('close', (code) => {
            if (code === 0) {
                console.log(' -> OpenWiki Daemon installed successfully.');
                console.log(' -> Auto-starting OpenWiki Daemon for the first run...');
                try {
                    const pythonCmd = os.platform() === 'win32' ? 'python' : 'python3';
                    const daemonPath = path.join(scriptBase, 'openwiki_daemon.py');
                    execSync(`${pythonCmd} "${daemonPath}" --one-shot`, { stdio: 'ignore', env: daemonEnv });
                    console.log(' -> Daemon auto-started successfully.');
                } catch(e) {
                    console.warn(` -> Could not auto-start daemon: ${e.message}`);
                }
            }
            else console.error(` -> OpenWiki Daemon installation failed with code ${code}.`);
            resolve();
        });
        child.on('error', (err) => { console.error(' -> Failed to start OpenWiki Daemon script:', err); resolve(); });
    });
}

async function installTokenSaver(platformTarget) {
    const tokenSaverDir = path.join(srcDir, 'vendor', 'token-saver');
    if (!fs.existsSync(tokenSaverDir)) {
        return;
    }
    console.log(`\n${colors.magenta}${colors.bold}--- Installing Heimdall Token Saver Context Optimizer ---${colors.reset}`);
    const { execSync } = require('child_process');
    const pythonCmd = process.platform === 'win32' ? 'python' : 'python3';

    try {
        let targetFlag = '--target both';
        if (platformTarget === '1') targetFlag = '--target antigravity';
        else if (platformTarget === '2') targetFlag = '--target claude';

        console.log(` -> Running Heimdall Token Saver setup (${targetFlag})...`);
        execSync(`${pythonCmd} install.py ${targetFlag}`, {
            cwd: tokenSaverDir,
            stdio: 'inherit'
        });
        console.log(` -> Heimdall Token Saver successfully registered.`);
    } catch (err) {
        console.warn(` -> Warning: Heimdall Token Saver installation skipped or failed: ${err.message}`);
    }
}

function moveIfExists(src, dest, label) {
    if (fs.existsSync(src)) {
        fs.renameSync(src, dest);
        console.log(` -> Backed up ${label}.`);
    }
}

function copyDirRecursiveSync(source, target) {
    if (!fs.existsSync(source)) return;
    if (!fs.existsSync(target)) fs.mkdirSync(target, { recursive: true });

    const files = fs.readdirSync(source);
    files.forEach(file => {
        const curSource = path.join(source, file);
        const curTarget = path.join(target, file);
        try {
            const stat = fs.lstatSync(curSource);
            if (stat.isSymbolicLink()) {
                try {
                    const linkTarget = fs.readlinkSync(curSource);
                    if (fs.existsSync(curSource)) {
                        if (fs.existsSync(curTarget)) fs.unlinkSync(curTarget);
                        fs.symlinkSync(linkTarget, curTarget);
                    } else {
                        console.warn(`Warning: Skipping broken symlink ${curSource}`);
                    }
                } catch (e) {
                    console.warn(`Warning: Could not copy symlink ${curSource}: ${e.message}`);
                }
            } else if (stat.isDirectory()) {
                copyDirRecursiveSync(curSource, curTarget);
            } else {
                fs.copyFileSync(curSource, curTarget);
            }
        } catch (e) {
            console.warn(`Warning: Failed to copy ${curSource} -> ${curTarget}: ${e.message}`);
        }
    });
}

promptMode(({ mode, platform, customPaths }) => {
    fs.mkdirSync(backupDir, { recursive: true });
    
    let targetSkillDir = globalConfigDir;
    let targetLegacyDir = globalLegacyDir;
    let targetWorkspaceDir = workspaceDir;
    let targetMcpDir = path.join(geminiDir, 'config');
    let mcpConfigPath = path.join(targetMcpDir, 'mcp_config.json');
    
    if (platform === '2') {
        // Claude Desktop
        console.log("\n[Platform: Claude Desktop] Adapting installation paths...");
        targetSkillDir = path.join(homeDir, '.bdb-skills');
        targetLegacyDir = path.join(homeDir, '.bdb-skills', 'legacy');
        
        let claudeAppSupport = process.platform === 'win32' 
            ? path.join(process.env.APPDATA || homeDir, 'Claude')
            : path.join(homeDir, 'Library', 'Application Support', 'Claude');
            
        targetMcpDir = claudeAppSupport;
        mcpConfigPath = path.join(claudeAppSupport, 'claude_desktop_config.json');
    } else if (platform === '3') {
        // Cursor / Generic
        console.log("\n[Platform: Cursor / Generic IDE] Adapting installation paths...");
        targetSkillDir = path.join(currentDir, '.cursor', 'bdb-skills');
        targetLegacyDir = path.join(currentDir, '.cursor', 'bdb-skills', 'legacy');
        targetWorkspaceDir = path.join(currentDir, '.cursor', 'workspace_skills');
        targetMcpDir = path.join(currentDir, '.cursor');
        mcpConfigPath = path.join(targetMcpDir, 'mcp.json');
    } else if (platform === '5') {
        // Codex
        console.log("\n[Platform: ChatGPT Codex CLI] Adapting installation paths...");
        targetSkillDir = path.join(homeDir, '.codex', 'skills');
        targetLegacyDir = path.join(homeDir, '.codex', 'skills', 'legacy');
        targetMcpDir = path.join(homeDir, '.codex');
        mcpConfigPath = path.join(targetMcpDir, 'config.toml');
    } else if (platform === '6') {
        // Windsurf
        console.log("\n[Platform: Windsurf IDE] Adapting installation paths...");
        targetSkillDir = path.join(homeDir, '.windsurf', 'bdb-skills');
        targetLegacyDir = path.join(homeDir, '.windsurf', 'bdb-skills', 'legacy');
        targetMcpDir = path.join(homeDir, '.windsurf');
        mcpConfigPath = path.join(targetMcpDir, 'mcp.json');
    } else if (platform === '7') {
        // Roo / Cline / VS Code
        console.log("\n[Platform: Roo Code / Cline] Adapting installation paths...");
        targetSkillDir = path.join(homeDir, '.roo', 'bdb-skills');
        targetLegacyDir = path.join(homeDir, '.roo', 'bdb-skills', 'legacy');
        targetMcpDir = path.join(homeDir, '.roo');
        mcpConfigPath = path.join(targetMcpDir, 'mcp.json');
    } else if (platform === '8') {
        // Aider
        console.log("\n[Platform: Aider CLI] Adapting installation paths...");
        targetSkillDir = path.join(homeDir, '.aider', 'bdb-skills');
        targetLegacyDir = path.join(homeDir, '.aider', 'bdb-skills', 'legacy');
        targetMcpDir = path.join(homeDir, '.aider');
        mcpConfigPath = path.join(targetMcpDir, 'mcp.json');
    } else if (platform === '4' && customPaths) {
        // Custom paths
        console.log("\n[Platform: Custom Path] Applying custom paths...");
        targetSkillDir = customPaths.skillDir;
        targetLegacyDir = customPaths.legacyDir;
        targetWorkspaceDir = customPaths.workspaceDir;
        targetMcpDir = customPaths.mcpDir;
        mcpConfigPath = customPaths.mcpConfigPath;
    }

    if (mode === '2') {
        console.log(`\n[Replace Mode] Creating backup of current skills in ${backupDir}...`);
        moveIfExists(targetSkillDir, path.join(backupDir, 'config_skills_backup'), 'global config skills');
        moveIfExists(targetLegacyDir, path.join(backupDir, 'legacy_skills_backup'), 'global legacy skills');
        moveIfExists(targetWorkspaceDir, path.join(backupDir, 'workspace_skills_backup'), 'workspace skills');
    } else {
        console.log(`\n[Merge Mode] Installing over existing directories. Existing skills will not be deleted.`);
    }

    console.log("\nInstalling optimized skills (140 curated skills)...");
    fs.mkdirSync(targetSkillDir, { recursive: true });
    fs.mkdirSync(targetLegacyDir, { recursive: true });
    fs.mkdirSync(targetWorkspaceDir, { recursive: true });

    copyDirRecursiveSync(path.join(srcDir, 'skills', 'global_config'), targetSkillDir);
    console.log(" -> Installed global config skills.");

    copyDirRecursiveSync(path.join(srcDir, 'skills', 'global_legacy'), targetLegacyDir);
    console.log(" -> Installed global legacy skills.");

    copyDirRecursiveSync(path.join(srcDir, 'skills', 'workspace_agents'), targetWorkspaceDir);
    console.log(" -> Installed workspace skills.");

    const geminiMdSrc = path.join(srcDir, 'GEMINI.md');
    if (platform === '1' && fs.existsSync(geminiMdSrc)) {
        fs.copyFileSync(geminiMdSrc, path.join(geminiDir, 'GEMINI.md'));
        console.log(` -> Installed GEMINI.md to ${path.join(geminiDir, 'GEMINI.md')}`);
    }

    (async () => {
        const mcpSrcDir = path.join(srcDir, 'mcps');
        const mcpCodeTarget = path.join(targetMcpDir, 'mcps');
        const selectedMcps = await promptMcpSelection(mcpSrcDir);
        
        if (selectedMcps.length > 0) {
            fs.mkdirSync(targetMcpDir, { recursive: true });
            if (!fs.existsSync(mcpCodeTarget)) fs.mkdirSync(mcpCodeTarget, { recursive: true });

            console.log(`\nInstalling ${selectedMcps.length} selected MCPs...`);
            selectedMcps.forEach(mcp => {
                copyDirRecursiveSync(path.join(mcpSrcDir, mcp), path.join(mcpCodeTarget, mcp));
            });
            console.log(` -> Installed selected MCP servers to ${mcpCodeTarget}`);

            const execSync = require('child_process').execSync;
            const nodeMcps = ['adobe_uxp_mcp', 'unreal_mcp', 'tdmcp', 'touchdesigner-mcp', 'davinci-resolve-mcp', 'after-effects-mcp', 'computer-use-mcp'];
            nodeMcps.filter(m => selectedMcps.includes(m)).forEach(mcpFolder => {
                const targetFolder = path.join(mcpCodeTarget, mcpFolder);
                if (fs.existsSync(path.join(targetFolder, 'package.json'))) {
                    console.log(` -> Setting up Node dependencies for ${mcpFolder}...`);
                    try {
                        execSync('npm install --no-audit --no-fund', { cwd: targetFolder, stdio: 'ignore' });
                        if (fs.existsSync(path.join(targetFolder, 'tsconfig.json')) || fs.existsSync(path.join(targetFolder, 'tsconfig.build.json'))) {
                            console.log(` -> Compiling TypeScript for ${mcpFolder}...`);
                            execSync('npm run build', { cwd: targetFolder, stdio: 'ignore' });
                        }
                    } catch (e) { console.warn(`Warning: Failed to set up ${mcpFolder}: ${e.message}`); }
                }
            });

            if (selectedMcps.includes('memb-mcp')) {
                const membMcpFolder = path.join(mcpCodeTarget, 'memb-mcp');
                if (fs.existsSync(membMcpFolder)) {
                    console.log(` -> Bootstrapping Python virtual environment for memB MCP...`);
                    try {
                        const pythonCmd = process.platform === 'win32' ? 'python' : 'python3';
                        execSync(`${pythonCmd} -m venv .venv`, { cwd: membMcpFolder, stdio: 'ignore' });
                        const pipPath = process.platform === 'win32' ? '.venv\\Scripts\\pip.exe' : '.venv/bin/pip';
                        console.log(` -> Installing Python dependencies for memB MCP...`);
                        execSync(`"${pipPath}" install --upgrade pip`, { cwd: membMcpFolder, stdio: 'ignore' });
                        execSync(`"${pipPath}" install -r requirements.txt`, { cwd: membMcpFolder, stdio: 'ignore' });
                        console.log(` -> memB MCP setup completed successfully.`);
                    } catch (e) { console.warn(`Warning: Failed to set up Python virtual environment for memB: ${e.message}`); }
                }
            }

            const pythonMcps = [
                { folder: 'golem-rhino-mcp', cmd: 'uv run -m mcp_server --help' },
                { folder: 'davinci-mcp-professional', cmd: 'uv run main.py --help' },
                { folder: 'davinci-resolve-mcp-free', cmd: 'uv run -r requirements.txt src/resolve_mcp_bridge.py --help' },
                { folder: 'blender-mcp', cmd: 'uv run -m blender_mcp.server --help' },
                { folder: 'blender-mcp-server', cmd: 'uv run -m blender_mcp_server --help' },
                { folder: 'vectorworks-mcp', cmd: 'uv run -r requirements.txt app/mcp_server.py --help' },
                { folder: 'windows-computer-use-mcp', cmd: 'uv run run_server.py --help' }
            ];
            pythonMcps.filter(m => selectedMcps.includes(m.folder)).forEach(mcp => {
                const targetFolder = path.join(mcpCodeTarget, mcp.folder);
                if (fs.existsSync(targetFolder)) {
                    console.log(` -> Pre-warming Python dependencies for ${mcp.folder}...`);
                    try { execSync(mcp.cmd, { cwd: targetFolder, stdio: 'ignore' }); } catch (e) {}
                }
            });

            if (fs.existsSync(mcpConfigPath)) {
                fs.copyFileSync(mcpConfigPath, path.join(backupDir, 'mcp_config_backup.json'));
                console.log(` -> Backed up existing ${path.basename(mcpConfigPath)}`);
            }
            
            let mcpConfigStr = fs.readFileSync(path.join(srcDir, 'mcp_config.json'), 'utf8');
            try {
                const parsedMcpConfig = JSON.parse(mcpConfigStr);
                const finalMcpServers = {};
                const availableFolders = fs.readdirSync(mcpSrcDir);
                for (const [key, val] of Object.entries(parsedMcpConfig.mcpServers)) {
                    let keep = true;
                    for (const available of availableFolders) {
                        if (!selectedMcps.includes(available) && JSON.stringify(val).includes(available)) {
                            keep = false;
                            break;
                        }
                    }
                    if (keep) finalMcpServers[key] = val;
                }
                parsedMcpConfig.mcpServers = finalMcpServers;
                mcpConfigStr = JSON.stringify(parsedMcpConfig, null, 2);
            } catch(e) {}

            mcpConfigStr = mcpConfigStr.replace(/__MCPS_DIR__/g, mcpCodeTarget);
            mcpConfigStr = mcpConfigStr.replace(/\{\{HOME\}\}/g, homeDir);

            if (selectedMcps.includes('memb-mcp')) {
                const pythonBinPath = process.platform === 'win32'
                    ? path.join(mcpCodeTarget, 'memb-mcp', '.venv', 'Scripts', 'python.exe')
                    : path.join(mcpCodeTarget, 'memb-mcp', '.venv', 'bin', 'python');
                mcpConfigStr = mcpConfigStr.replace(/__PYTHON_BIN__/g, pythonBinPath.replace(/\\/g, '/'));
            }
            
            if (mode === '1' && fs.existsSync(mcpConfigPath)) {
                try {
                    const oldConfig = JSON.parse(fs.readFileSync(mcpConfigPath, 'utf8'));
                    const newConfig = JSON.parse(mcpConfigStr);
                    oldConfig.mcpServers = Object.assign({}, oldConfig.mcpServers || {}, newConfig.mcpServers || {});
                    fs.writeFileSync(mcpConfigPath, JSON.stringify(oldConfig, null, 2));
                    console.log(` -> Merged BDB MCPs into existing ${path.basename(mcpConfigPath)}`);
                } catch (e) {
                    console.log(` -> Failed to parse existing JSON, overwriting ${path.basename(mcpConfigPath)}`);
                    fs.writeFileSync(mcpConfigPath, mcpConfigStr);
                }
            } else {
                if ((platform === '2' || platform === '4') && !fs.existsSync(mcpConfigPath)) {
                     const wrapper = { mcpServers: JSON.parse(mcpConfigStr).mcpServers };
                     fs.writeFileSync(mcpConfigPath, JSON.stringify(wrapper, null, 2));
                } else {
                     fs.writeFileSync(mcpConfigPath, mcpConfigStr);
                }
                console.log(` -> Installed optimized MCP config to ${targetMcpDir}`);
            }
        } else {
            console.log(" -> Skipping MCP installation.");
        }

        const creds = await promptCredentials();
        
        if (creds.gemini || creds.github) {
            const envPath = path.join(targetMcpDir, '.env');
            let envContent = '';
            if (fs.existsSync(envPath)) envContent = fs.readFileSync(envPath, 'utf8') + '\n';
            if (creds.gemini && !envContent.includes('GEMINI_API_KEY=')) envContent += `GEMINI_API_KEY=${creds.gemini}\n`;
            if (creds.github && !envContent.includes('GITHUB_PERSONAL_ACCESS_TOKEN=')) envContent += `GITHUB_PERSONAL_ACCESS_TOKEN=${creds.github}\n`;
            if (envContent.trim().length > 0) fs.writeFileSync(envPath, envContent.trim() + '\n');
            console.log(` -> Saved credentials to ${envPath}`);
        }

async function promptMemBIngestion(mcpCodeTarget) {
    if (isAutoYes) return;
    
    console.log(`\n${colors.cyan}${colors.bold}🧠 memB Deep Memory Ingestion${colors.reset}`);
    const doIngest = await new Promise((resolve) => {
        rl.question(`${colors.yellow}Would you like to scan & ingest a project directory into memB memory? (y/N): ${colors.reset}`, (answer) => {
            resolve(answer.trim().toLowerCase() === 'y');
        });
    });

    if (!doIngest) return;

    const targetDir = await new Promise((resolve) => {
        rl.question(`${colors.yellow}Enter project directory path to scan [default: current workspace]: ${colors.reset}`, (answer) => {
            resolve(answer.trim() || process.cwd());
        });
    });

    const includeTranscripts = await new Promise((resolve) => {
        rl.question(`${colors.yellow}Include past conversation logs/transcripts? (y/N): ${colors.reset}`, (answer) => {
            resolve(answer.trim().toLowerCase() === 'y');
        });
    });

    const pythonBin = process.platform === 'win32'
        ? path.join(mcpCodeTarget, 'memb-mcp', '.venv', 'Scripts', 'python.exe')
        : path.join(mcpCodeTarget, 'memb-mcp', '.venv', 'bin', 'python');
        
    const ingestScript = path.join(mcpCodeTarget, 'memb-mcp', 'memb_ingest.py');

    if (fs.existsSync(ingestScript) && fs.existsSync(pythonBin)) {
        console.log(` -> Running memB deep ingestion on: ${targetDir}...`);
        try {
            const { execSync } = require('child_process');
            const cmd = `"${pythonBin}" "${ingestScript}" "${targetDir}"${includeTranscripts ? ' --transcripts' : ''}`;
            execSync(cmd, { stdio: 'inherit' });
        } catch (e) {
            console.log(` -> Failed to run ingestion script: ${e.message}`);
        }
    } else {
        console.log(` -> Ingestion script or python environment not found.`);
    }
}

async function promptCreatorExtension(mcpConfigPath) {
    if (isAutoYes) return;
    
    console.log(`\n${colors.magenta}${colors.bold}🎬 BDB Creator Extension (Generative 3D, Video & ComfyUI)${colors.reset}`);
    const doInstall = await new Promise((resolve) => {
        rl.question(`${colors.yellow}Möchtest du das Plugin 'BDB Creator Extension' (3D, Video & ComfyUI MCP Engines) einrichten? (y/N): ${colors.reset}`, (answer) => {
            resolve(answer.trim().toLowerCase() === 'y');
        });
    });

    if (!doInstall) return;

    const creatorDir = path.join(path.dirname(srcDir), 'bdb-dev-creator-extension');
    const installerScript = path.join(creatorDir, 'installer.js');

    if (fs.existsSync(installerScript)) {
        console.log(` -> Starte Setup der BDB Creator Extension...`);
        try {
            execSync(`node "${installerScript}"`, { stdio: 'inherit' });
        } catch (e) {
            console.log(` -> Hinweis beim Ausführen des Creator Extension Setups: ${e.message}`);
        }
    } else {
        console.log(` -> BDB Creator Extension Verzeichnis nicht gefunden unter ${creatorDir}.`);
    }
}

        await installOpenWikiDaemon(creds.gemini, targetSkillDir, { provider: creds.openwikiProvider, model: creds.openwikiModel, baseUrl: creds.openwikiBaseUrl });
        await installTokenSaver(platform);
        await promptCreatorExtension(mcpConfigPath);
        await promptMemBIngestion(mcpCodeTarget);
        
        console.log(`\n${colors.green}${colors.bold}=========================================================${colors.reset}`);
        console.log(`${colors.green}${colors.bold} 🎉 Installation complete! The environment now has the ${colors.reset}`);
        console.log(`${colors.green}${colors.bold}    optimized skill configuration.${colors.reset}`);
        console.log(`${colors.green}${colors.bold}=========================================================${colors.reset}`);
        rl.close();
    })();
});
