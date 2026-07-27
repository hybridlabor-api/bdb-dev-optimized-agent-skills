import type { HandlerArgs } from '../../../../types/handlers/handler-types.js';
import type { ITools } from '../../../../types/tools/tool-interfaces.js';
import type { AutomationResponse } from '../../../../types/automation/automation-responses.js';
import { ResponseFactory } from '../../../../utils/responses/response-factory.js';
import { executeAutomationRequest } from '../../foundation/dispatch/common-handlers.js';
import { normalizeArgs, extractString, extractOptionalString, extractOptionalBoolean, extractOptionalObject } from '../../foundation/arguments/argument-helper.js';
import { validateAnimationPath as validatePath } from './animation-authoring-utils.js';

export async function handleControlRigAction(
  action: string,
  args: HandlerArgs,
  tools: ITools
): Promise<Record<string, unknown> | undefined> {
  switch (action) {
	case 'create_control_rig': {
			const params = normalizeArgs(args, [
				{ key: 'name', required: true },
				{ key: 'path', aliases: ['directory'], default: '/Game/ControlRigs' },
				{ key: 'skeletalMeshPath', required: false },
				{ key: 'skeletonPath', required: false },
				{ key: 'save', default: true },
			]);

			const name = extractString(params, 'name');
			const path = extractOptionalString(params, 'path') ?? '/Game/ControlRigs';
			const skeletalMeshPath = extractOptionalString(params, 'skeletalMeshPath');
			const skeletonPath = extractOptionalString(params, 'skeletonPath');
			const save = extractOptionalBoolean(params, 'save') ?? true;

			const res = (await executeAutomationRequest(tools, 'manage_animation_authoring', {
				subAction: 'create_control_rig',
				name,
				path,
				skeletalMeshPath,
				skeletonPath,
				save,
			})) as AutomationResponse;

        if (res.success === false) {
          return ResponseFactory.error(res.error ?? 'Failed to create control rig', res.errorCode);
        }
        return ResponseFactory.success(res, res.message ?? `Control Rig '${name}' created`);
      }

      case 'add_control': {
        const params = normalizeArgs(args, [
          { key: 'assetPath', required: false },
          { key: 'controlName', required: true },
          { key: 'controlType', default: 'Transform' }, // Transform, Bool, Float, Integer, Vector2D
          { key: 'parentBone' },
          { key: 'parentControl' },
          { key: 'save', default: true },
        ]);

  const rawAssetPath = extractOptionalString(params, 'assetPath');
  const assetPath = rawAssetPath ? validatePath(rawAssetPath, 'assetPath') : undefined;
  if (assetPath && !assetPath.valid) {
    return assetPath.error;
  }
  const controlName = extractString(params, 'controlName');
  const controlType = extractOptionalString(params, 'controlType') ?? 'Transform';
  const parentBone = extractOptionalString(params, 'parentBone');
  const parentControl = extractOptionalString(params, 'parentControl');
  const save = extractOptionalBoolean(params, 'save') ?? true;

  const res = (await executeAutomationRequest(tools, 'manage_animation_authoring', {
    subAction: 'add_control',
    assetPath: assetPath?.sanitized,
          controlName,
          controlType,
          parentBone,
          parentControl,
          save,
        })) as AutomationResponse;

        if (res.success === false) {
          return ResponseFactory.error(res.error ?? 'Failed to add control', res.errorCode);
        }
        return ResponseFactory.success(res, res.message ?? `Control '${controlName}' added`);
      }

      case 'add_rig_unit': {
        const params = normalizeArgs(args, [
          { key: 'assetPath', required: false },
          { key: 'unitType', required: true }, // FKIK, Aim, BasicIK, TwoBoneIK, FABRIK, etc.
          { key: 'unitName' },
          { key: 'settings' }, // Unit-specific settings
          { key: 'save', default: true },
        ]);

  const rawAssetPath = extractOptionalString(params, 'assetPath');
  const assetPath = rawAssetPath ? validatePath(rawAssetPath, 'assetPath') : undefined;
  if (assetPath && !assetPath.valid) {
    return assetPath.error;
  }
  const unitType = extractString(params, 'unitType');
  const unitName = extractOptionalString(params, 'unitName');
  const settings = extractOptionalObject(params, 'settings');
  const save = extractOptionalBoolean(params, 'save') ?? true;

  const res = (await executeAutomationRequest(tools, 'manage_animation_authoring', {
    subAction: 'add_rig_unit',
    assetPath: assetPath?.sanitized,
          unitType,
          unitName,
          settings,
          save,
        })) as AutomationResponse;

        if (res.success === false) {
          return ResponseFactory.error(res.error ?? 'Failed to add rig unit', res.errorCode);
        }
        return ResponseFactory.success(res, res.message ?? `Rig unit '${unitType}' added`);
      }

      case 'connect_rig_elements': {
        const params = normalizeArgs(args, [
          { key: 'assetPath', required: false },
          { key: 'sourceElement', required: true },
          { key: 'sourcePin', required: true },
          { key: 'targetElement', required: true },
          { key: 'targetPin', required: true },
          { key: 'save', default: true },
        ]);

  const rawAssetPath = extractOptionalString(params, 'assetPath');
  const assetPath = rawAssetPath ? validatePath(rawAssetPath, 'assetPath') : undefined;
  if (assetPath && !assetPath.valid) {
    return assetPath.error;
  }
  const sourceElement = extractString(params, 'sourceElement');
  const sourcePin = extractString(params, 'sourcePin');
  const targetElement = extractString(params, 'targetElement');
  const targetPin = extractString(params, 'targetPin');
  const save = extractOptionalBoolean(params, 'save') ?? true;

  const res = (await executeAutomationRequest(tools, 'manage_animation_authoring', {
    subAction: 'connect_rig_elements',
    assetPath: assetPath?.sanitized,
          sourceElement,
          sourcePin,
          targetElement,
          targetPin,
          save,
        })) as AutomationResponse;

        if (res.success === false) {
          return ResponseFactory.error(res.error ?? 'Failed to connect rig elements', res.errorCode);
        }
        return ResponseFactory.success(res, res.message ?? 'Rig elements connected');
      }

    default:
      return undefined;
  }
}
