const DEFAULT_ASSET_LIST_TTL_MS = 10000;
const DEFAULT_PAGE_SIZE = 30;
const MAX_PAGE_SIZE = 50;

export function getAssetListTtlMs(): number {
  const raw = process.env.ASSET_LIST_TTL_MS;
  if (raw === undefined || raw.trim().length === 0) return DEFAULT_ASSET_LIST_TTL_MS;
  if (!/^\d+$/.test(raw.trim())) return DEFAULT_ASSET_LIST_TTL_MS;

  const parsed = Number(raw.trim());
  return Number.isInteger(parsed) && parsed >= 0 ? parsed : DEFAULT_ASSET_LIST_TTL_MS;
}

export function normalizePage(value: number): number {
  return Number.isFinite(value) && value > 0 ? Math.floor(value) : 0;
}

export function normalizePageSize(value: number): number {
  if (!Number.isFinite(value) || value <= 0) return DEFAULT_PAGE_SIZE;
  return Math.min(Math.floor(value), MAX_PAGE_SIZE);
}
