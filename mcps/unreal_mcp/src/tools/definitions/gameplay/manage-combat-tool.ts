import { commonSchemas } from '../../catalog/tool-definition-utils.js';
import type { ToolDefinition } from '../shared/tool-definition.js';

export const manageCombatToolDefinition: ToolDefinition = {
    name: 'manage_combat',
    category: 'gameplay',
    description: 'Create weapons with hitscan/projectile firing, configure damage types, hitboxes, reload, and melee combat (combos, parry, block).',
    inputSchema: {
      type: 'object',
      properties: {
        action: {
          type: 'string',
          enum: [
            'create_weapon_blueprint', 'configure_weapon_mesh', 'configure_weapon_sockets', 'set_weapon_stats',
            'configure_hitscan', 'configure_projectile', 'configure_spread_pattern', 'configure_recoil_pattern', 'configure_aim_down_sights',
            'create_projectile_blueprint', 'configure_projectile_movement', 'configure_projectile_collision', 'configure_projectile_homing',
            'create_damage_type', 'configure_damage_execution', 'setup_hitbox_component',
            'setup_reload_system', 'setup_ammo_system', 'setup_attachment_system', 'setup_weapon_switching',
            'configure_muzzle_flash', 'configure_tracer', 'configure_impact_effects', 'configure_shell_ejection',
            'create_melee_trace', 'configure_combo_system', 'create_hit_pause', 'configure_hit_reaction', 'setup_parry_block_system', 'configure_weapon_trails',
            'get_combat_info',
            'setup_damage_type', 'configure_hit_detection', 'get_combat_stats',
            'create_damage_effect', 'apply_damage', 'heal', 'create_shield', 'modify_armor'
          ],
          description: 'Combat action to perform'
        },
        blueprintPath: commonSchemas.blueprintPath,
        name: commonSchemas.name,
        path: commonSchemas.directoryPathForCreation,
        weaponMeshPath: { type: 'string', description: 'Path to weapon static/skeletal mesh.' },
        muzzleSocketName: commonSchemas.muzzleSocketName,
        ejectionSocketName: commonSchemas.ejectionSocketName,
        baseDamage: commonSchemas.numberProp,
        fireRate: commonSchemas.numberProp,
        range: commonSchemas.numberProp,
        spread: commonSchemas.numberProp,
        hitscanEnabled: { type: 'boolean', description: 'Enable hitscan firing.' },
        traceChannel: {
          type: 'string',
          enum: ['Visibility', 'Camera', 'Weapon', 'Custom'],
          description: 'Trace channel for hitscan.'
        },
        projectileClass: commonSchemas.projectileClass,
        spreadPattern: {
          type: 'string',
          enum: ['Random', 'Fixed', 'FixedWithRandom', 'Shotgun'],
          description: 'Spread pattern type.'
        },
        spreadIncrease: { type: 'number', description: 'Spread increase per shot.' },
        spreadRecovery: { type: 'number', description: 'Spread recovery rate.' },
        recoilPitch: { type: 'number', description: 'Vertical recoil (degrees).' },
        recoilYaw: { type: 'number', description: 'Horizontal recoil (degrees).' },
        recoilRecovery: { type: 'number', description: 'Recoil recovery speed.' },
        adsEnabled: { type: 'boolean', description: 'Enable aim down sights.' },
        adsFov: { type: 'number', description: 'FOV when aiming.' },
        adsSpeed: { type: 'number', description: 'Time to aim down sights.' },
        adsSpreadMultiplier: { type: 'number', description: 'Spread multiplier when aiming.' },
        projectileSpeed: commonSchemas.numberProp,
        projectileGravityScale: commonSchemas.numberProp,
        projectileLifespan: commonSchemas.numberProp,
        projectileMeshPath: { type: 'string', description: 'Path to projectile mesh.' },
        collisionRadius: commonSchemas.numberProp,
        bounceEnabled: { type: 'boolean', description: 'Enable projectile bouncing.' },
        bounceVelocityRatio: { type: 'number', description: 'Velocity retained on bounce (0-1).' },
        homingEnabled: { type: 'boolean', description: 'Enable homing behavior.' },
        homingAcceleration: { type: 'number', description: 'Homing turn rate.' },
        damageImpulse: { type: 'number', description: 'Impulse applied on hit.' },
        criticalMultiplier: { type: 'number', description: 'Critical hit damage multiplier.' },
        headshotMultiplier: { type: 'number', description: 'Headshot damage multiplier.' },
        hitboxBoneName: { type: 'string', description: 'Bone name for hitbox.' },
        hitboxType: {
          type: 'string',
          enum: ['Capsule', 'Box', 'Sphere'],
          description: 'Hitbox collision shape.'
        },
        hitboxSize: {
          type: 'object',
          properties: {
            radius: commonSchemas.numberProp,
            halfHeight: commonSchemas.numberProp,
            extent: commonSchemas.extent
          },
          description: 'Hitbox dimensions.'
        },
        isDamageZoneHead: { type: 'boolean', description: 'Mark as headshot zone.' },
        damageMultiplier: { type: 'number', description: 'Damage multiplier for this hitbox.' },
        magazineSize: commonSchemas.numberProp,
        reloadTime: commonSchemas.numberProp,
        reloadAnimationPath: { type: 'string', description: 'Path to reload animation.' },
        ammoType: { type: 'string', description: 'Ammo type identifier.' },
        maxAmmo: commonSchemas.numberProp,
        startingAmmo: commonSchemas.numberProp,
        attachmentSlots: {
          type: 'array',
          items: {
            type: 'object',
            properties: {
              slotName: commonSchemas.stringProp,
              socketName: commonSchemas.stringProp,
              allowedTypes: commonSchemas.arrayOfStrings
            }
          },
          description: 'Attachment slot definitions.'
        },
        switchInTime: { type: 'number', description: 'Time to equip weapon.' },
        switchOutTime: { type: 'number', description: 'Time to unequip weapon.' },
        equipAnimationPath: { type: 'string', description: 'Path to equip animation montage.' },
        unequipAnimationPath: { type: 'string', description: 'Path to unequip animation montage.' },
        muzzleFlashParticlePath: { type: 'string', description: 'Path to muzzle flash particle.' },
        muzzleFlashScale: { type: 'number', description: 'Muzzle flash scale.' },
        muzzleSoundPath: { type: 'string', description: 'Path to firing sound.' },
        tracerParticlePath: { type: 'string', description: 'Path to tracer particle.' },
        tracerSpeed: { type: 'number', description: 'Tracer travel speed.' },
        impactParticlePath: { type: 'string', description: 'Path to impact particle.' },
        impactSoundPath: { type: 'string', description: 'Path to impact sound.' },
        impactDecalPath: { type: 'string', description: 'Path to impact decal.' },
        shellMeshPath: { type: 'string', description: 'Path to shell casing mesh.' },
        shellEjectionForce: { type: 'number', description: 'Shell ejection impulse.' },
        shellLifespan: { type: 'number', description: 'Shell casing lifetime.' },
        meleeTraceStartSocket: { type: 'string', description: 'Socket for trace start.' },
        meleeTraceEndSocket: { type: 'string', description: 'Socket for trace end.' },
        meleeTraceRadius: { type: 'number', description: 'Sphere trace radius.' },
        comboWindowTime: { type: 'number', description: 'Time window for combo input.' },
        maxComboCount: { type: 'number', description: 'Maximum combo length.' },
        hitPauseDuration: { type: 'number', description: 'Hitstop duration in seconds.' },
        hitPauseTimeDilation: { type: 'number', description: 'Time dilation during hitstop.' },
        hitReactionMontage: { type: 'string', description: 'Path to hit reaction montage.' },
        hitReactionStunTime: { type: 'number', description: 'Stun duration on hit.' },
        parryWindowStart: { type: 'number', description: 'Parry window start time (normalized).' },
        parryWindowEnd: { type: 'number', description: 'Parry window end time (normalized).' },
        parryAnimationPath: { type: 'string', description: 'Path to parry animation.' },
        blockDamageReduction: { type: 'number', description: 'Damage reduction when blocking (0-1).' },
        blockStaminaCost: { type: 'number', description: 'Stamina cost per blocked hit.' },
        weaponTrailParticlePath: { type: 'string', description: 'Path to weapon trail particle.' },
        weaponTrailStartSocket: { type: 'string', description: 'Trail start socket.' },
        weaponTrailEndSocket: { type: 'string', description: 'Trail end socket.' },
        ammoPerShot: commonSchemas.numberProp,
        armorValue: commonSchemas.numberProp,
        damageAmount: commonSchemas.numberProp,
        damagePerSecond: commonSchemas.numberProp,
        damageReduction: commonSchemas.numberProp,
        damageType: commonSchemas.stringProp,
        duration: commonSchemas.numberProp,
        effectType: commonSchemas.stringProp,
        healAmount: commonSchemas.numberProp,
        infiniteAmmo: commonSchemas.booleanProp,
        maxHealth: commonSchemas.numberProp,
        maxShield: commonSchemas.numberProp,
        shieldAmount: commonSchemas.numberProp,
        shieldRegenDelay: commonSchemas.numberProp,
        shieldRegenRate: commonSchemas.numberProp
      },
      required: ['action']
    },
    outputSchema: {
      type: 'object',
      properties: {
        ...commonSchemas.outputBase,
        blueprintPath: commonSchemas.blueprintPath,
        damageTypePath: commonSchemas.stringProp,
        combatInfo: {
          type: 'object',
          properties: {
            weaponType: commonSchemas.stringProp,
            firingMode: commonSchemas.stringProp,
            baseDamage: commonSchemas.numberProp,
            fireRate: commonSchemas.numberProp,
            magazineSize: commonSchemas.numberProp,
            hasADS: commonSchemas.booleanProp,
            hasReload: commonSchemas.booleanProp,
            isMelee: commonSchemas.booleanProp,
            comboCount: commonSchemas.numberProp,
            attachmentSlots: commonSchemas.arrayOfStrings
          },
          description: 'Combat configuration info (for get_combat_info).'
        }
      }
    }
  };
