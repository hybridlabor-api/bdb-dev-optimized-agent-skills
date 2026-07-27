function toLowerSnakeCase(value: string): string {
  return value
    .replace(/([a-z0-9])([A-Z])/g, '$1_$2')
    .replace(/[\s-]+/g, '_')
    .toLowerCase();
}

function copyIfString(payload: Record<string, unknown>, fromKey: string, toKey: string): void {
  if (typeof payload[toKey] === 'string') {
    return;
  }

  const value = payload[fromKey];
  if (typeof value === 'string' && value.trim().length > 0) {
    payload[toKey] = value;
  }
}

function copyIfNumber(payload: Record<string, unknown>, fromKey: string, toKey: string): void {
  if (typeof payload[toKey] === 'number') {
    return;
  }

  const value = payload[fromKey];
  if (typeof value === 'number') {
    payload[toKey] = value;
  }
}

function copyIfArray(payload: Record<string, unknown>, fromKey: string, toKey: string): void {
  if (Array.isArray(payload[toKey])) {
    return;
  }

  const value = payload[fromKey];
  if (Array.isArray(value)) {
    payload[toKey] = value;
  }
}

function normalizeEnumAlias(payload: Record<string, unknown>, key: string): void {
  const value = payload[key];
  if (typeof value === 'string' && value.trim().length > 0) {
    payload[key] = toLowerSnakeCase(value);
  }
}

function normalizeCueTrigger(value: string): string {
  switch (value) {
    case 'OnActive':
      return 'on_active';
    case 'WhileActive':
      return 'while_active';
    case 'Executed':
      return 'on_execute';
    case 'OnRemove':
      return 'on_remove';
    default:
      return toLowerSnakeCase(value);
  }
}

export function normalizeGASPayloadForBridge(
  payload: Record<string, unknown>,
  subAction: string
): Record<string, unknown> {
  switch (subAction) {
    case 'configure_asc':
      normalizeEnumAlias(payload, 'replicationMode');
      break;
    case 'set_ability_tags':
      copyIfArray(payload, 'cancelAbilitiesWithTag', 'cancelAbilitiesWithTags');
      copyIfArray(payload, 'blockAbilitiesWithTag', 'blockAbilitiesWithTags');
      break;
    case 'set_ability_targeting':
      copyIfString(payload, 'targetingMode', 'targetingType');
      copyIfNumber(payload, 'targetRange', 'targetingRange');
      normalizeEnumAlias(payload, 'targetingType');
      break;
    case 'set_activation_policy':
      copyIfString(payload, 'activationPolicy', 'policy');
      normalizeEnumAlias(payload, 'policy');
      break;
    case 'set_instancing_policy':
      copyIfString(payload, 'instancingPolicy', 'policy');
      normalizeEnumAlias(payload, 'policy');
      break;
    case 'create_gameplay_effect':
    case 'set_effect_duration':
      normalizeEnumAlias(payload, 'durationType');
      break;
    case 'add_effect_modifier':
      copyIfString(payload, 'modifierOperation', 'operation');
      copyIfNumber(payload, 'modifierMagnitude', 'magnitude');
      normalizeEnumAlias(payload, 'operation');
      break;
    case 'set_modifier_magnitude':
      copyIfString(payload, 'magnitudeCalculationType', 'magnitudeType');
      copyIfNumber(payload, 'modifierMagnitude', 'value');
      normalizeEnumAlias(payload, 'magnitudeType');
      break;
    case 'set_effect_stacking':
      copyIfNumber(payload, 'stackLimitCount', 'stackLimit');
      normalizeEnumAlias(payload, 'stackingType');
      normalizeEnumAlias(payload, 'stackDurationRefreshPolicy');
      normalizeEnumAlias(payload, 'stackPeriodResetPolicy');
      normalizeEnumAlias(payload, 'stackExpirationPolicy');
      break;
    case 'configure_cue_trigger':
      normalizeCueTriggerPayload(payload);
      break;
    case 'set_cue_effects':
      copyIfString(payload, 'particleSystemPath', 'particleSystem');
      copyIfString(payload, 'soundPath', 'sound');
      copyIfString(payload, 'cameraShakePath', 'cameraShake');
      copyIfString(payload, 'decalPath', 'decal');
      break;
    default:
      break;
  }

  return payload;
}

function normalizeCueTriggerPayload(payload: Record<string, unknown>): void {
  const triggerType = payload.triggerType;
  if (typeof triggerType === 'string') {
    payload.triggerType = normalizeCueTrigger(triggerType);
  }
}
