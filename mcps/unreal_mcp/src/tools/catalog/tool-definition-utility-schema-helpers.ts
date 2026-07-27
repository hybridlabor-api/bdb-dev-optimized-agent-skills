import { commonSchemas } from './tool-definition-utility-common-schemas.js';

type ToolInputSchemaDefinition = {
  readonly inputSchema: Record<string, unknown>;
};

function isSchemaObject(value: unknown): value is Record<string, unknown> {
  return typeof value === 'object' && value !== null && !Array.isArray(value);
}

export function createOutputSchema(additionalProperties: Record<string, unknown> = {}): Record<string, unknown> {
  return {
    type: 'object',
    properties: {
      success: { type: 'boolean' },
      message: { type: 'string' },
      error: { type: 'string' },
      ...additionalProperties
    }
  };
}

export function addActionParamsSchema(definitions: ToolInputSchemaDefinition[]): void {
  for (const definition of definitions) {
    const schema = definition.inputSchema;
    const rawProperties = schema.properties;
    if (!isSchemaObject(rawProperties)) continue;

    if (rawProperties.action === undefined || rawProperties.params !== undefined) continue;

    rawProperties.params = commonSchemas.actionParams;
    if (schema.additionalProperties === undefined) {
      schema.additionalProperties = true;
    }
  }
}

export function actionDescription(description: string, actions: string[]): string {
  if (!actions || actions.length === 0) return description;
  return `${description}\n\nSupported actions: ${actions.join(', ')}.`;
}
