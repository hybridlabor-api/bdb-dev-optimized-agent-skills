export type EditorActionResult =
  | { readonly handled: true; readonly value: unknown }
  | { readonly handled: false };

export const EDITOR_ACTION_UNHANDLED: EditorActionResult = { handled: false };

export function editorActionHandled(value: unknown): EditorActionResult {
  return { handled: true, value };
}
