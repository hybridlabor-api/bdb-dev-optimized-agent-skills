export const screenshotModeSchema = {
  type: 'string',
  enum: ['editor_viewport', 'game_viewport', 'full_editor_window'],
  description: 'Screenshot source. editor_viewport captures the active editor viewport; game_viewport captures the PIE/game viewport; full_editor_window captures the full Slate editor window and returns imageBase64 by default.'
};
