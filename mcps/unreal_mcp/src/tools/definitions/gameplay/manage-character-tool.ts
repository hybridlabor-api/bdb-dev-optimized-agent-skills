import { commonSchemas } from '../../catalog/tool-definition-utils.js';
import type { ToolDefinition } from '../shared/tool-definition.js';

export const manageCharacterToolDefinition: ToolDefinition = {
    name: 'manage_character',
    category: 'gameplay',
    description: 'Create Character Blueprints with movement, locomotion, and animation state machines.',
    inputSchema: {
      type: 'object',
      properties: {
        action: {
          type: 'string',
          enum: [
            'create_character_blueprint',
            'configure_capsule_component',
            'configure_mesh_component',
            'configure_camera_component',
            'configure_movement_speeds',
            'configure_jump',
            'configure_rotation',
            'add_custom_movement_mode',
            'configure_nav_movement',
            'setup_mantling',
            'setup_vaulting',
            'setup_climbing',
            'setup_sliding',
            'setup_wall_running',
            'setup_grappling',
            'setup_footstep_system',
            'map_surface_to_sound',
            'configure_footstep_fx',
            'get_character_info',
            'setup_movement', 'set_walk_speed', 'set_jump_height', 'set_gravity_scale',
            'set_ground_friction', 'set_braking_deceleration', 'configure_crouch', 'configure_sprint'
          ],
          description: 'Character action to perform.'
        },
        name: commonSchemas.assetNameForCreation,
        path: commonSchemas.directoryPathForCreation,
        blueprintPath: commonSchemas.blueprintPath,
        parentClass: {
          type: 'string',
          enum: ['Character', 'ACharacter', 'PlayerCharacter', 'AICharacter'],
          description: 'Parent class for character blueprint.'
        },
        skeletalMeshPath: commonSchemas.skeletalMeshPath,
        animBlueprintPath: commonSchemas.animBlueprintPath,
        capsuleRadius: commonSchemas.numberProp,
        capsuleHalfHeight: commonSchemas.numberProp,
        meshOffset: {
          type: 'object',
          properties: {
            x: commonSchemas.numberProp,
            y: commonSchemas.numberProp,
            z: commonSchemas.numberProp
          },
          description: 'Mesh location offset.'
        },
        meshRotation: {
          type: 'object',
          properties: {
            pitch: commonSchemas.numberProp,
            yaw: commonSchemas.numberProp,
            roll: commonSchemas.numberProp
          },
          description: 'Mesh rotation offset.'
        },
        cameraUsePawnControlRotation: { type: 'boolean', description: 'Camera follows controller rotation.' },
        springArmLength: commonSchemas.numberProp,
        springArmLagEnabled: { type: 'boolean', description: 'Enable camera lag.' },
        springArmLagSpeed: { type: 'number', description: 'Camera lag speed.' },
        walkSpeed: commonSchemas.numberProp,
        runSpeed: commonSchemas.numberProp,
        sprintSpeed: commonSchemas.numberProp,
        crouchSpeed: commonSchemas.numberProp,
        swimSpeed: commonSchemas.numberProp,
        flySpeed: commonSchemas.numberProp,
        acceleration: commonSchemas.numberProp,
        deceleration: commonSchemas.numberProp,
        groundFriction: commonSchemas.numberProp,
        jumpHeight: commonSchemas.numberProp,
        airControl: commonSchemas.numberProp,
        maxJumpCount: commonSchemas.numberProp,
        jumpHoldTime: { type: 'number', description: 'Max hold time for variable jump.' },
        gravityScale: commonSchemas.numberProp,
        fallingLateralFriction: { type: 'number', description: 'Air friction.' },
        orientToMovement: { type: 'boolean', description: 'Orient rotation to movement direction.' },
        useControllerRotationYaw: { type: 'boolean', description: 'Use controller yaw rotation.' },
        useControllerRotationPitch: { type: 'boolean', description: 'Use controller pitch rotation.' },
        useControllerRotationRoll: { type: 'boolean', description: 'Use controller roll rotation.' },
        rotationRate: commonSchemas.numberProp,
        modeName: { type: 'string', description: 'Name for custom movement mode.' },
        modeId: { type: 'number', description: 'Custom movement mode ID.' },
        navAgentRadius: commonSchemas.numberProp,
        navAgentHeight: commonSchemas.numberProp,
        avoidanceEnabled: { type: 'boolean', description: 'Enable AI avoidance.' },
        mantleHeight: { type: 'number', description: 'Maximum mantle height.' },
        mantleReachDistance: { type: 'number', description: 'Forward reach for mantle check.' },
        vaultHeight: { type: 'number', description: 'Maximum vault obstacle height.' },
        vaultDepth: { type: 'number', description: 'Obstacle depth to check.' },
        climbSpeed: commonSchemas.numberProp,
        climbableTag: { type: 'string', description: 'Tag for climbable surfaces.' },
        slideSpeed: commonSchemas.numberProp,
        slideDuration: commonSchemas.numberProp,
        slideCooldown: commonSchemas.numberProp,
        wallRunSpeed: { type: 'number', description: 'Wall running speed.' },
        wallRunDuration: { type: 'number', description: 'Maximum wall run duration.' },
        wallRunGravityScale: { type: 'number', description: 'Gravity during wall run.' },
        grappleRange: { type: 'number', description: 'Maximum grapple distance.' },
        grappleSpeed: { type: 'number', description: 'Grapple pull speed.' },
        grappleTargetTag: { type: 'string', description: 'Tag for grapple targets.' },
        footstepEnabled: { type: 'boolean', description: 'Enable footstep system.' },
        footstepSocketLeft: { type: 'string', description: 'Left foot socket name.' },
        footstepSocketRight: { type: 'string', description: 'Right foot socket name.' },
        footstepTraceDistance: { type: 'number', description: 'Ground trace distance.' },
        surfaceType: {
          type: 'string',
          enum: ['Default', 'Concrete', 'Grass', 'Dirt', 'Metal', 'Wood', 'Water', 'Snow', 'Sand', 'Gravel', 'Custom'],
          description: 'Physical surface type.'
        },
        brakingDeceleration: commonSchemas.numberProp,
        canCrouch: commonSchemas.booleanProp,
        crouchedHalfHeight: commonSchemas.numberProp,
        customSpeed: commonSchemas.numberProp,
        particleScale: commonSchemas.numberProp,
        volumeMultiplier: commonSchemas.numberProp
      },
      required: ['action']
    },
    outputSchema: {
      type: 'object',
      properties: {
        ...commonSchemas.outputBase,
        blueprintPath: commonSchemas.blueprintPath,
        componentName: commonSchemas.componentName,
        modeName: commonSchemas.stringProp,
        characterInfo: {
          type: 'object',
          properties: {
            capsuleRadius: commonSchemas.numberProp,
            capsuleHalfHeight: commonSchemas.numberProp,
            walkSpeed: commonSchemas.numberProp,
            jumpZVelocity: commonSchemas.numberProp,
            airControl: commonSchemas.numberProp,
            orientToMovement: commonSchemas.booleanProp,
            hasSpringArm: commonSchemas.booleanProp,
            hasCamera: commonSchemas.booleanProp,
            springArmTemplates: { ...commonSchemas.arrayOfObjects, description: 'Spring arm component templates on the Character Blueprint.' },
            cameraTemplates: { ...commonSchemas.arrayOfObjects, description: 'Camera component templates on the Character Blueprint.' },
            bFindCameraComponentWhenViewTarget: commonSchemas.booleanProp,
            playerViewState: { ...commonSchemas.objectProp, description: 'Active PIE player controller, pawn, view target, and PlayerCameraManager state.' },
            movementVariables: commonSchemas.arrayOfStrings,
            customMovementModes: commonSchemas.arrayOfStrings
          }
        },
        error: commonSchemas.stringProp
      }
    }
  };
