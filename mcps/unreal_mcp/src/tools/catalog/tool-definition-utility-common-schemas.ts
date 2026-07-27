import { coreCommonSchemas } from './tool-definition-utility-core-schemas.js';
import { domainCommonSchemas } from './tool-definition-utility-domain-schemas.js';
import { outputAndGeometryCommonSchemas } from './tool-definition-utility-output-schemas.js';

export const commonSchemas = {
  ...coreCommonSchemas,
  ...outputAndGeometryCommonSchemas,
  ...domainCommonSchemas
};
