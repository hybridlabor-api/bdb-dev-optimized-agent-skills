import type { CategoryState, ToolCategory, ToolState } from './dynamic-tool-types.js';

export function isToolStateEnabled(
  toolStates: Map<string, ToolState>,
  categoryStates: Map<ToolCategory, CategoryState>,
  toolName: string
): boolean {
  const state = toolStates.get(toolName);
  if (state === undefined) return false;

  const catState = categoryStates.get(state.category);
  return state.enabled && (catState?.enabled ?? true);
}

export function listCategoryStates(
  toolStates: Map<string, ToolState>,
  categoryStates: Map<ToolCategory, CategoryState>
): CategoryState[] {
  const states = Array.from(toolStates.values());
  return Array.from(categoryStates.values()).map(catState => {
    const categoryTools = states.filter(tool => tool.category === catState.name);
    const enabledCount = categoryTools.filter(tool => isToolStateEnabled(toolStates, categoryStates, tool.name)).length;
    return {
      ...catState,
      toolCount: categoryTools.length,
      enabledCount
    };
  });
}

export function countEnabledTools(
  toolStates: Map<string, ToolState>,
  categoryStates: Map<ToolCategory, CategoryState>
): number {
  let enabledCount = 0;
  for (const state of toolStates.values()) {
    if (isToolStateEnabled(toolStates, categoryStates, state.name)) enabledCount++;
  }
  return enabledCount;
}
