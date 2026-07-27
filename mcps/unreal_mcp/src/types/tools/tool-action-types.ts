export type AssetAction = 'list' | 'import' | 'create_material' | 'create_material_instance';

export type ActorAction =
  | 'spawn'
  | 'spawn_blueprint'
  | 'delete'
  | 'delete_by_tag'
  | 'duplicate'
  | 'apply_force'
  | 'set_transform'
  | 'get_transform'
  | 'set_visibility'
  | 'add_component'
  | 'set_component_properties'
  | 'get_components'
  | 'add_tag'
  | 'find_by_tag'
  | 'find_by_name'
  | 'set_blueprint_variables'
  | 'create_snapshot'
  | 'attach'
  | 'detach';

export type EditorAction = 'play' | 'stop' | 'set_camera' | 'set_view_mode' | 'screenshot' | 'take_screenshot';

export type LevelAction = 'load' | 'save' | 'stream' | 'create_light' | 'build_lighting';

export type AnimationAction =
  | 'create_animation_bp'
  | 'create_anim_blueprint'
  | 'create_animation_blueprint'
  | 'play_montage'
  | 'play_anim_montage'
  | 'setup_ragdoll'
  | 'activate_ragdoll'
  | 'configure_vehicle'
  | 'create_blend_space'
  | 'create_state_machine'
  | 'setup_ik'
  | 'create_procedural_anim'
  | 'create_blend_tree'
  | 'setup_retargeting'
  | 'setup_physics_simulation'
  | 'create_animation_asset'
  | 'cleanup';

export type EffectAction =
  | 'particle'
  | 'niagara'
  | 'debug_shape'
  | 'spawn_niagara'
  | 'set_niagara_parameter'
  | 'clear_debug_shapes'
  | 'create_dynamic_light'
  | 'cleanup';

export type BlueprintAction = 'create' | 'add_component';

export type EnvironmentAction = 'create_landscape' | 'sculpt' | 'add_foliage' | 'paint_foliage';

export type SystemAction =
  | 'profile'
  | 'show_fps'
  | 'set_quality'
  | 'play_sound'
  | 'create_widget'
  | 'show_widget'
  | 'screenshot'
  | 'engine_start'
  | 'engine_quit'
  | 'read_log';

export type VerificationAction =
  | 'foliage_type_exists'
  | 'foliage_instances_near'
  | 'landscape_exists'
  | 'quality_level';
