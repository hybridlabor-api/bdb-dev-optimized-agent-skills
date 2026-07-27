import { commonSchemas } from '../../catalog/tool-definition-utils.js';
import type { ToolDefinition } from '../shared/tool-definition.js';

export const manageGasToolDefinition: ToolDefinition = {
    name: 'manage_gas',
    category: 'gameplay',
    description: 'Create Gameplay Abilities, Effects, Attribute Sets, and Gameplay Cues for ability systems.',
    inputSchema: {
      type: 'object',
      properties: {
        action: {
          type: 'string',
          enum: [
            'add_ability_system_component',
            'configure_asc',
            'create_attribute_set',
            'add_attribute',
            'set_attribute_base_value',
            'set_attribute_clamping',
            'create_gameplay_ability',
            'set_ability_tags',
            'set_ability_costs',
            'set_ability_cooldown',
            'set_ability_targeting',
            'add_ability_task',
            'set_activation_policy',
            'set_instancing_policy',
            'create_gameplay_effect',
            'set_effect_duration',
            'add_effect_modifier',
            'set_modifier_magnitude',
            'add_effect_execution_calculation',
            'add_effect_cue',
            'set_effect_stacking',
            'set_effect_tags',
            'create_gameplay_cue_notify',
            'configure_cue_trigger',
            'set_cue_effects',
            'add_tag_to_asset',
            'get_gas_info'
          ],
          description: 'GAS action to perform.'
        },
        name: commonSchemas.assetNameForCreation,
        path: commonSchemas.directoryPathForCreation,
        assetPath: commonSchemas.assetPath,
        blueprintPath: commonSchemas.blueprintPath,
        replicationMode: {
          type: 'string',
          enum: ['Full', 'Minimal', 'Mixed'],
          description: 'ASC replication mode.'
        },
        attributeSetPath: { type: 'string', description: 'Path to Attribute Set asset.' },
        attributeName: commonSchemas.attributeName,
        attributeType: {
          type: 'string',
          enum: ['Health', 'MaxHealth', 'Mana', 'MaxMana', 'Stamina', 'MaxStamina', 'Damage', 'Armor', 'AttackPower', 'MoveSpeed', 'Custom'],
          description: 'Predefined attribute type or Custom.'
        },
        baseValue: { type: 'number', description: 'Base value for attribute.' },
        minValue: { type: 'number', description: 'Minimum value for clamping.' },
        maxValue: { type: 'number', description: 'Maximum value for clamping.' },
        clampMode: {
          type: 'string',
          enum: ['None', 'Min', 'Max', 'MinMax'],
          description: 'Attribute clamping mode.'
        },
        abilityPath: commonSchemas.abilityPath,
        abilityTags: {
          type: 'array',
          items: commonSchemas.stringProp,
          description: 'Gameplay tags for this ability.'
        },
        cancelAbilitiesWithTag: {
          type: 'array',
          items: commonSchemas.stringProp,
          description: 'Tags of abilities to cancel when this activates.'
        },
        blockAbilitiesWithTag: {
          type: 'array',
          items: commonSchemas.stringProp,
          description: 'Tags of abilities blocked while this is active.'
        },
        activationRequiredTags: {
          type: 'array',
          items: commonSchemas.stringProp,
          description: 'Tags required to activate this ability.'
        },
        activationBlockedTags: {
          type: 'array',
          items: commonSchemas.stringProp,
          description: 'Tags that block activation of this ability.'
        },
        costEffectPath: { type: 'string', description: 'Path to cost Gameplay Effect.' },
        cooldownEffectPath: { type: 'string', description: 'Path to cooldown Gameplay Effect.' },
        targetingMode: {
          type: 'string',
          enum: ['None', 'SingleTarget', 'AOE', 'Directional', 'Ground', 'ActorPlacement'],
          description: 'Targeting mode for ability.'
        },
        targetRange: { type: 'number', description: 'Maximum targeting range.' },
        aoeRadius: { type: 'number', description: 'Area of effect radius.' },
        taskType: {
          type: 'string',
          enum: ['WaitDelay', 'WaitInputPress', 'WaitInputRelease', 'WaitGameplayEvent', 'WaitTargetData', 'WaitConfirmCancel', 'PlayMontageAndWait', 'ApplyRootMotionConstantForce', 'WaitMovementModeChange'],
          description: 'Type of ability task to add.'
        },
        activationPolicy: {
          type: 'string',
          enum: ['OnInputPressed', 'WhileInputActive', 'OnSpawn', 'OnGiven'],
          description: 'When the ability activates.'
        },
        instancingPolicy: {
          type: 'string',
          enum: ['NonInstanced', 'InstancedPerActor', 'InstancedPerExecution'],
          description: 'How the ability is instanced.'
        },
        effectPath: commonSchemas.effectPath,
        durationType: {
          type: 'string',
          enum: ['Instant', 'Infinite', 'HasDuration'],
          description: 'Effect duration type.'
        },
        duration: commonSchemas.duration,
        period: { type: 'number', description: 'Period for periodic effects.' },
        modifierOperation: {
          type: 'string',
          enum: ['Add', 'Multiply', 'Divide', 'Override'],
          description: 'Modifier operation on attribute.'
        },
        modifierMagnitude: { type: 'number', description: 'Magnitude of the modifier.' },
        magnitudeCalculationType: {
          type: 'string',
          enum: ['ScalableFloat', 'AttributeBased', 'SetByCaller', 'CustomCalculationClass'],
          description: 'How magnitude is calculated.'
        },
        setByCallerTag: { type: 'string', description: 'Tag for SetByCaller magnitude.' },
        targetAttribute: { type: 'string', description: 'Target attribute for modifier.' },
        calculationClass: { type: 'string', description: 'UGameplayEffectExecutionCalculation class path.' },
        cueTag: { type: 'string', description: 'Gameplay Cue tag (e.g., GameplayCue.Damage.Fire).' },
        cuePath: { type: 'string', description: 'Path to Gameplay Cue asset.' },
        stackingType: {
          type: 'string',
          enum: ['None', 'AggregateBySource', 'AggregateByTarget'],
          description: 'Stacking type for effect.'
        },
        stackLimitCount: { type: 'number', description: 'Maximum stack count.' },
        stackDurationRefreshPolicy: {
          type: 'string',
          enum: ['RefreshOnSuccessfulApplication', 'NeverRefresh'],
          description: 'When to refresh stack duration.'
        },
        stackPeriodResetPolicy: {
          type: 'string',
          enum: ['ResetOnSuccessfulApplication', 'NeverReset'],
          description: 'When to reset stack period.'
        },
        stackExpirationPolicy: {
          type: 'string',
          enum: ['ClearEntireStack', 'RemoveSingleStackAndRefreshDuration', 'RefreshDuration'],
          description: 'What happens when stack expires.'
        },
        grantedTags: {
          type: 'array',
          items: commonSchemas.stringProp,
          description: 'Tags granted while effect is active.'
        },
        applicationRequiredTags: {
          type: 'array',
          items: commonSchemas.stringProp,
          description: 'Tags required to apply this effect.'
        },
        removalTags: {
          type: 'array',
          items: commonSchemas.stringProp,
          description: 'Tags that cause effect removal.'
        },
        immunityTags: {
          type: 'array',
          items: commonSchemas.stringProp,
          description: 'Tags that block this effect.'
        },
        cueType: {
          type: 'string',
          enum: ['Static', 'Actor'],
          description: 'Type of gameplay cue notify.'
        },
        triggerType: {
          type: 'string',
          enum: ['OnActive', 'WhileActive', 'Executed', 'OnRemove'],
          description: 'When the cue triggers.'
        },
        particleSystemPath: commonSchemas.particleSystemPath,
        soundPath: commonSchemas.soundPath,
        cameraShakePath: commonSchemas.cameraShakePath,
        decalPath: commonSchemas.decalPath,
        tagName: commonSchemas.tagName,
        componentName: commonSchemas.componentName,
        defaultValue: commonSchemas.value,
        modifierIndex: commonSchemas.numberProp
      },
      required: ['action']
    },
    outputSchema: {
      type: 'object',
      properties: {
        ...commonSchemas.outputBase,
        assetPath: commonSchemas.assetPath,
        componentName: commonSchemas.componentName,
        attributeName: commonSchemas.stringProp,
        modifierIndex: commonSchemas.numberProp,
        gasInfo: {
          type: 'object',
          properties: {
            assetType: { type: 'string', enum: ['AttributeSet', 'GameplayAbility', 'GameplayEffect', 'GameplayCue'] },
            attributes: commonSchemas.arrayOfObjects,
            abilityTags: commonSchemas.arrayOfStrings,
            effectDuration: commonSchemas.stringProp,
            modifierCount: commonSchemas.numberProp,
            cueType: commonSchemas.stringProp
          }
        },
        error: commonSchemas.stringProp
      }
    }
  };
