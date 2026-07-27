import { sanitizePath } from '../../utils/paths/path-security.js';

export type LevelExportRecord = { target: string; timestamp: number; note?: string };
export type ManagedLevelRecord = {
  path: string;
  name: string;
  partitioned: boolean;
  streaming: boolean;
  loaded: boolean;
  visible: boolean;
  createdAt: number;
  lastSavedAt?: number;
  metadata?: Record<string, unknown>;
  exports: LevelExportRecord[];
  lights: Array<{ name: string; type: string; createdAt: number; details?: Record<string, unknown> }>;
};

type LevelListResult = {
  success: true;
  message: string;
  count: number;
  levels: Array<Record<string, unknown>>;
};

export class ManagedLevelState {
  private managedLevels = new Map<string, ManagedLevelRecord>();
  private listCache?: { result: LevelListResult; timestamp: number };
  private readonly listCacheTtlMs = 750;
  private activeLevelPath?: string;

  get currentLevelPath(): string | undefined {
    return this.activeLevelPath;
  }

  normalizeLevelPath(rawPath: string | undefined): { path: string; name: string } {
    if (!rawPath) {
      return { path: '/Game/Maps/Untitled', name: 'Untitled' };
    }

    let formatted = rawPath.replace(/\\/g, '/').trim();
    if (!formatted.startsWith('/')) {
      formatted = formatted.startsWith('Game/') ? `/${formatted}` : `/Game/${formatted.replace(/^\/?Game\//i, '')}`;
    }
    if (!formatted.startsWith('/Game/')) {
      formatted = `/Game/${formatted.replace(/^\/+/, '')}`;
    }

    try {
      formatted = sanitizePath(formatted);
    } catch (error: unknown) {
      const message = error instanceof Error ? error.message : String(error);
      throw new Error(`Security validation failed for level path: ${message}`);
    }

    formatted = formatted.replace(/\.umap$/i, '');
    if (formatted.endsWith('/')) {
      formatted = formatted.slice(0, -1);
    }
    const segments = formatted.split('/').filter(Boolean);
    const lastSegment = segments[segments.length - 1] ?? 'Untitled';
    const name = lastSegment.includes('.') ? lastSegment.split('.').pop() ?? lastSegment : lastSegment;
    return { path: formatted, name: name || 'Untitled' };
  }

  ensureRecord(path: string, seed?: Partial<ManagedLevelRecord>): ManagedLevelRecord {
    const normalized = this.normalizeLevelPath(path);
    let record = this.managedLevels.get(normalized.path);
    if (!record) {
      record = {
        path: normalized.path,
        name: seed?.name ?? normalized.name,
        partitioned: seed?.partitioned ?? false,
        streaming: seed?.streaming ?? false,
        loaded: seed?.loaded ?? false,
        visible: seed?.visible ?? false,
        createdAt: seed?.createdAt ?? Date.now(),
        lastSavedAt: seed?.lastSavedAt,
        metadata: seed?.metadata ? { ...seed.metadata } : undefined,
        exports: seed?.exports ? [...seed.exports] : [],
        lights: seed?.lights ? [...seed.lights] : []
      };
      this.managedLevels.set(normalized.path, record);
      this.invalidateListCache();
    }
    return record;
  }

  mutateRecord(path: string | undefined, updates: Partial<ManagedLevelRecord>): ManagedLevelRecord | undefined {
    if (!path || !path.trim()) return undefined;
    const record = this.ensureRecord(path, updates);
    let changed = false;

    for (const key of ['name', 'partitioned', 'streaming', 'loaded', 'visible', 'createdAt', 'lastSavedAt'] as const) {
      if (updates[key] !== undefined && updates[key] !== record[key]) {
        record[key] = updates[key] as never;
        changed = true;
      }
    }
    if (updates.metadata) {
      record.metadata = { ...(record.metadata ?? {}), ...updates.metadata };
      changed = true;
    }
    if (updates.exports && updates.exports.length > 0) {
      record.exports = [...record.exports, ...updates.exports];
      changed = true;
    }
    if (updates.lights && updates.lights.length > 0) {
      record.lights = [...record.lights, ...updates.lights];
      changed = true;
    }
    if (changed) this.invalidateListCache();
    return record;
  }

  getRecord(path: string | undefined): ManagedLevelRecord | undefined {
    if (!path || !path.trim()) return undefined;
    return this.managedLevels.get(this.normalizeLevelPath(path).path);
  }

  resolveLevelPath(explicit?: string): string | undefined {
    if (explicit && explicit.trim()) {
      return this.normalizeLevelPath(explicit).path;
    }
    return this.activeLevelPath;
  }

  removeRecord(path: string): void {
    const normalized = this.normalizeLevelPath(path);
    if (this.managedLevels.delete(normalized.path)) {
      if (this.activeLevelPath === normalized.path) {
        this.activeLevelPath = undefined;
      }
      this.invalidateListCache();
    }
  }

  listManagedLevels(): LevelListResult {
    const now = Date.now();
    if (this.listCache && now - this.listCache.timestamp < this.listCacheTtlMs) {
      return this.listCache.result;
    }

    const levels = Array.from(this.managedLevels.values()).map(record => ({
      path: record.path,
      name: record.name,
      partitioned: record.partitioned,
      streaming: record.streaming,
      loaded: record.loaded,
      visible: record.visible,
      createdAt: record.createdAt,
      lastSavedAt: record.lastSavedAt,
      exports: record.exports,
      lightCount: record.lights.length
    }));
    const result = { success: true as const, message: 'Managed levels listed', count: levels.length, levels };
    this.listCache = { result, timestamp: now };
    return result;
  }

  summarizeLevel(path: string): Record<string, unknown> {
    const record = this.getRecord(path);
    if (!record) return { success: false, error: `Level not tracked: ${path}` };

    return {
      success: true,
      message: 'Level summary ready',
      path: record.path,
      name: record.name,
      partitioned: record.partitioned,
      streaming: record.streaming,
      loaded: record.loaded,
      visible: record.visible,
      createdAt: record.createdAt,
      lastSavedAt: record.lastSavedAt,
      exports: record.exports,
      lights: record.lights,
      metadata: record.metadata
    };
  }

  setCurrentLevel(path: string): void {
    const normalized = this.normalizeLevelPath(path);
    this.activeLevelPath = normalized.path;
    this.ensureRecord(normalized.path, { loaded: true, visible: true });
  }

  registerLight(levelPath: string | undefined, info: { name: string; type: string; details?: Record<string, unknown> }): void {
    const resolved = this.resolveLevelPath(levelPath);
    if (!resolved) return;
    this.mutateRecord(resolved, {
      lights: [{ name: info.name, type: info.type, createdAt: Date.now(), details: info.details }]
    });
  }

  private invalidateListCache(): void {
    this.listCache = undefined;
  }
}
