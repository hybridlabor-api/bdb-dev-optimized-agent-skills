import { mcpClients } from 'mcp-client-capabilities';
import { config } from '../config.js';

const KNOWN_DYNAMIC_CLIENT_NAMES = ['cursor', 'cline', 'windsurf', 'kilo', 'opencode', 'vscode', 'visual studio code'];

export function parseDefaultCategories(): string[] {
    const raw = config.MCP_DEFAULT_CATEGORIES || 'all';
    const cats = raw.split(',').map(c => c.trim().toLowerCase()).filter(c => c.length > 0);
    return cats.length > 0 ? cats : ['all'];
}

export function clientSupportsListChanged(clientName: string | undefined): boolean {
    if (!clientName) return false;

    const normalizedName = clientName.toLowerCase().trim();

    for (const [key, clientInfo] of Object.entries(mcpClients)) {
        if (key.toLowerCase() === normalizedName ||
            (clientInfo.title && clientInfo.title.toLowerCase() === normalizedName)) {
            const tools = clientInfo.tools as { listChanged?: boolean } | undefined;
            return Boolean(tools?.listChanged);
        }
    }

    for (const known of KNOWN_DYNAMIC_CLIENT_NAMES) {
        if (normalizedName.includes(known)) return true;
    }

    return false;
}

export function getEffectiveCategories(supportsListChanged: boolean, currentCategories: string[]): string[] {
    return (!supportsListChanged || currentCategories.includes('all'))
        ? ['all']
        : currentCategories;
}
