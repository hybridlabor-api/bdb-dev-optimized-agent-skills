import { cleanObject } from '../../../utils/serialization/safe-json.js';
import type { SubActionDispatcher } from '../foundation/dispatch/automation-request-dispatch.js';
import { requireNonEmptyString } from '../foundation/dispatch/common-handlers.js';

export async function handleAIUtilityAction(
  action: string,
  dispatcher: SubActionDispatcher
): Promise<Record<string, unknown> | null> {
  const { argsRecord, sendRequest } = dispatcher;

  switch (action) {
    case 'get_ai_info': {
      const hasPath = argsRecord.controllerPath || argsRecord.behaviorTreePath ||
                      argsRecord.blackboardPath || argsRecord.queryPath ||
                      argsRecord.stateTreePath || argsRecord.blueprintPath;
      if (!hasPath) {
        return cleanObject({
          success: false,
          error: 'MISSING_PARAMETER',
          message: 'At least one path parameter is required (controllerPath, behaviorTreePath, blackboardPath, queryPath, stateTreePath, or blueprintPath)'
        });
      }
      return sendRequest('get_ai_info');
    }

    case 'create_blackboard': {
      requireNonEmptyString(argsRecord.name, 'name', 'Missing required parameter: name');
      return sendRequest('create_blackboard');
    }

    case 'setup_perception': {
      requireNonEmptyString(argsRecord.blueprintPath, 'blueprintPath', 'Missing required parameter: blueprintPath');
      return sendRequest('setup_perception');
    }

    case 'create_nav_link_proxy': {
      requireNonEmptyString(argsRecord.blueprintPath, 'blueprintPath', 'Missing required parameter: blueprintPath');
      return sendRequest('create_nav_link_proxy');
    }

    case 'set_focus': {
      requireNonEmptyString(argsRecord.controllerPath, 'controllerPath', 'Missing required parameter: controllerPath');
      return sendRequest('set_focus');
    }

    case 'clear_focus': {
      requireNonEmptyString(argsRecord.controllerPath, 'controllerPath', 'Missing required parameter: controllerPath');
      return sendRequest('clear_focus');
    }

    case 'set_blackboard_value': {
      requireNonEmptyString(argsRecord.blackboardPath, 'blackboardPath', 'Missing required parameter: blackboardPath');
      requireNonEmptyString(argsRecord.keyName, 'keyName', 'Missing required parameter: keyName');
      return sendRequest('set_blackboard_value');
    }

    case 'get_blackboard_value': {
      requireNonEmptyString(argsRecord.blackboardPath, 'blackboardPath', 'Missing required parameter: blackboardPath');
      requireNonEmptyString(argsRecord.keyName, 'keyName', 'Missing required parameter: keyName');
      return sendRequest('get_blackboard_value');
    }

    case 'run_behavior_tree': {
      requireNonEmptyString(argsRecord.controllerPath, 'controllerPath', 'Missing required parameter: controllerPath');
      requireNonEmptyString(argsRecord.behaviorTreePath, 'behaviorTreePath', 'Missing required parameter: behaviorTreePath');
      return sendRequest('run_behavior_tree');
    }

    case 'stop_behavior_tree': {
      requireNonEmptyString(argsRecord.controllerPath, 'controllerPath', 'Missing required parameter: controllerPath');
      return sendRequest('stop_behavior_tree');
    }

    default:
      return null;
  }
}
