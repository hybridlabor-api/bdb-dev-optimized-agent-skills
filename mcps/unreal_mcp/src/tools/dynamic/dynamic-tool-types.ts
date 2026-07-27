export type ToolCategory = 'core' | 'world' | 'gameplay' | 'utility' | 'all';

export interface ToolState {
  name: string;
  category: ToolCategory;
  enabled: boolean;
  description: string;
}

export interface CategoryState {
  name: ToolCategory;
  enabled: boolean;
  toolCount: number;
  enabledCount: number;
}

export type EnableToolsResult = {
  success: boolean;
  enabled: string[];
  notFound: string[];
};

export type DisableToolsResult = {
  success: boolean;
  disabled: string[];
  notFound: string[];
  protected: string[];
};

export type CategoryEnableResult = {
  success: boolean;
  enabled: string[];
  notFound: boolean;
};

export type CategoryDisableResult = {
  success: boolean;
  disabled: string[];
  notFound: boolean;
  protected: string[];
};

export const PROTECTED_TOOL_NAMES = new Set(['manage_tools', 'inspect']);
