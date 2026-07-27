import { manageAiBehaviorProperties } from './manage-ai-behavior-properties.js';
import { manageAiNavigationProperties } from './manage-ai-navigation-properties.js';
import { manageAiRuntimeProperties } from './manage-ai-runtime-properties.js';

export const manageAiInputSchema = {
      type: 'object',
      properties: {
        ...manageAiBehaviorProperties,
        ...manageAiNavigationProperties,
        ...manageAiRuntimeProperties
      },
      required: ['action']
    };
