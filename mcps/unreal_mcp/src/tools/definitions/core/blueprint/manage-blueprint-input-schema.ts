import { manageBlueprintCoreProperties } from './manage-blueprint-core-properties.js';
import { manageBlueprintWidgetProperties } from './manage-blueprint-widget-properties.js';

export const manageBlueprintInputSchema = {
      type: 'object',
      properties: {
        ...manageBlueprintCoreProperties,
        ...manageBlueprintWidgetProperties
      },
      required: ['action']
    };
