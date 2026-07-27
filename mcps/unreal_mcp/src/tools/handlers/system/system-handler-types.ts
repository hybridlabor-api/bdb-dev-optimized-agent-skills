export interface OperationResponse {
  success?: boolean;
  error?: string;
  message?: string;
  settings?: unknown;
  data?: unknown;
  result?: unknown;
  [key: string]: unknown;
}

export interface AssetValidationResult {
  assetPath: string;
  success?: boolean;
  error?: string | null;
  [key: string]: unknown;
}
