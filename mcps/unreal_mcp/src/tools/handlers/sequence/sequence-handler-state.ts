import type { StandardActionResponse } from '../../../types/tools/tool-interfaces.js';

export interface SequenceActionResponse extends StandardActionResponse {
  result?: {
    sequencePath?: string;
    results?: Array<{ success?: boolean; error?: string }>;
    [key: string]: unknown;
  };
  bindings?: Array<{ name?: string; [key: string]: unknown }>;
  message?: string;
}

const managedSequences = new Set<string>();
const deletedSequences = new Set<string>();

function normalizeSequencePath(path: unknown): string | undefined {
  if (typeof path !== 'string') return undefined;
  const trimmed = path.trim();
  return trimmed.length > 0 ? trimmed : undefined;
}

export function markSequenceCreated(path: unknown): void {
  const norm = normalizeSequencePath(path);
  if (!norm) return;
  deletedSequences.delete(norm);
  managedSequences.add(norm);
}

export function markSequenceDeleted(path: unknown): void {
  const norm = normalizeSequencePath(path);
  if (!norm) return;
  managedSequences.delete(norm);
  deletedSequences.delete(norm);
}

export function getErrorString(res: SequenceActionResponse | null | undefined): string {
  if (!res) return '';
  return typeof res.error === 'string' ? res.error : '';
}

export function getMessageString(res: SequenceActionResponse | null | undefined): string {
  if (!res) return '';
  return typeof res.message === 'string' ? res.message : '';
}
