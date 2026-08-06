const os = require('os');
const path = require('path');
const fs = require('fs');

const sandboxDir = path.join(os.tmpdir(), 'bdb-sandbox');
if (!fs.existsSync(sandboxDir)) {
    fs.mkdirSync(sandboxDir, { recursive: true });
}

console.log("\n\x1b[36m=======================================================");
console.log(" 🏖️  SANDBOX MODE ACTIVATED");
console.log(" Alle Installationspfade werden umgeleitet nach:");
console.log(" -> " + sandboxDir);
console.log(" Deine echten Systemdateien bleiben zu 100% unberührt!");
console.log("=======================================================\x1b[0m\n");

// Überschreibe os.homedir()
const originalHomedir = os.homedir;
os.homedir = () => sandboxDir;

// Erstelle Dummy-Ordner, damit der Installer die Plattformen erkennt
const fakePaths = [
    '.codex/config.toml',
    '.gemini',
    '.claude.json',
    'Library/Application Support/Cursor',
    'Library/Application Support/Windsurf',
    'Library/Application Support/Claude',
    'Library/Application Support/Code',
    '.roo',
    '.aider'
];

fakePaths.forEach(p => {
    const fullPath = path.join(sandboxDir, p);
    fs.mkdirSync(path.dirname(fullPath), { recursive: true });
    if (p.endsWith('.json') || p.endsWith('.toml')) {
        fs.writeFileSync(fullPath, '');
    } else {
        if (!fs.existsSync(fullPath)) fs.mkdirSync(fullPath, { recursive: true });
    }
});

// Führe den originalen Installer aus
require('./installer.js');
