import { normalizeName } from '../../../utils/validation/type-coercion.js';

export const normalizeLightName = (value: unknown, defaultName?: string): string =>
  normalizeName(value, defaultName, 'Light');
