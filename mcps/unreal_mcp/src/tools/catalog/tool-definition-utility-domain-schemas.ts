export const domainCommonSchemas = {
  controllerPath: { type: 'string', description: 'Path to controller blueprint.' },
  behaviorTreePath: { type: 'string', description: 'Path to behavior tree asset.' },
  blackboardPath: { type: 'string', description: 'Path to blackboard asset.' },
  queryPath: { type: 'string', description: 'Path to EQS query asset.' },
  stateTreePath: { type: 'string', description: 'Path to State Tree asset.' },
  definitionPath: { type: 'string', description: 'Path to definition asset.' },
  configPath: { type: 'string', description: 'Path to config asset.' },
  lootTablePath: { type: 'string', description: 'Path to loot table asset.' },
  recipePath: { type: 'string', description: 'Path to crafting recipe asset.' },
  effectPath: { type: 'string', description: 'Path to effect asset.' },
  abilityPath: { type: 'string', description: 'Path to ability asset.' },
  animBlueprintPath: { type: 'string', description: 'Path to animation blueprint.' },

  keyName: { type: 'string', description: 'Name of the key.' },
  sessionName: { type: 'string', description: 'Name of the session.' },
  channelName: { type: 'string', description: 'Name of the channel.' },
  volumeName: { type: 'string', description: 'Name of the volume.' },
  linkName: { type: 'string', description: 'Name of the link.' },

  looping: { type: 'boolean', description: 'Whether to loop.' },
  locked: { type: 'boolean', description: 'Whether the item is locked.' },
  muted: { type: 'boolean', description: 'Whether the item is muted.' },
  replicated: { type: 'boolean', description: 'Whether to replicate.' },
  reliable: { type: 'boolean', description: 'Whether the operation is reliable.' },

  volume: { type: 'number', description: 'Volume level.' },
  pitch: { type: 'number', description: 'Pitch value.' },
  fadeTime: { type: 'number', description: 'Fade time in seconds.' },
  cooldown: { type: 'number', description: 'Cooldown time in seconds.' },
  respawnTime: { type: 'number', description: 'Respawn time in seconds.' },
  lifetime: { type: 'number', description: 'Lifetime in seconds.' },
  mass: { type: 'number', description: 'Mass value.' },
  friction: { type: 'number', description: 'Friction coefficient.' },
  restitution: { type: 'number', description: 'Restitution (bounciness).' },
  priority: { type: 'number', description: 'Priority value.' },

  inputName: { type: 'string', description: 'Name of the input.' },
  outputName: { type: 'string', description: 'Name of the output.' },

  parentBoneName: { type: 'string', description: 'Parent bone name.' },
  sourceBoneName: { type: 'string', description: 'Source bone name.' },
  targetBoneName: { type: 'string', description: 'Target bone name.' },
  attachBoneName: { type: 'string', description: 'Bone to attach to.' },
  startBone: { type: 'string', description: 'Start bone name.' },
  endBone: { type: 'string', description: 'End bone name.' },

  fromState: { type: 'string', description: 'Source state name.' },
  toState: { type: 'string', description: 'Target state name.' },

  sourceNode: { type: 'string', description: 'Source node name.' },
  targetNode: { type: 'string', description: 'Target node name.' },
  sourceElement: { type: 'string', description: 'Source element name.' },
  targetElement: { type: 'string', description: 'Target element name.' },

  chainName: { type: 'string', description: 'Name of the chain.' },
  sectionName: { type: 'string', description: 'Name of the section.' },
  cacheName: { type: 'string', description: 'Name of the cache.' },

  widgetClass: { type: 'string', description: 'Widget class path.' },
  projectileClass: { type: 'string', description: 'Projectile class path.' },
  soundClassPath: { type: 'string', description: 'Sound class path.' },
  parentClassPath: { type: 'string', description: 'Parent class path.' },
  areaClass: { type: 'string', description: 'Navigation area class path.' },

  traceChannel: { type: 'string', description: 'Collision trace channel.' },

  sourceIKRigPath: { type: 'string', description: 'Source IK rig path.' },
  targetIKRigPath: { type: 'string', description: 'Target IK rig path.' },
  sourceChain: { type: 'string', description: 'Source chain name.' },
  targetChain: { type: 'string', description: 'Target chain name.' },

  muzzleSocketName: { type: 'string', description: 'Muzzle socket name.' },
  ejectionSocketName: { type: 'string', description: 'Shell ejection socket name.' },
  cameraSocketName: { type: 'string', description: 'Camera socket name.' },

  layerName: { type: 'string', description: 'Name of the layer.' },
  dataLayerName: { type: 'string', description: 'Name of the data layer.' },

  stackSize: { type: 'number', description: 'Stack size.' },
  weight: { type: 'number', description: 'Weight value.' },
  slotCount: { type: 'number', description: 'Number of slots.' },
  maxWeight: { type: 'number', description: 'Maximum weight.' },
  maxPlayers: { type: 'number', description: 'Maximum player count.' },
  playerIndex: { type: 'number', description: 'Player index.' },
  controllerId: { type: 'number', description: 'Controller ID.' },
  serverPort: { type: 'number', description: 'Server port number.' },

  text: { type: 'string', description: 'Text content.' },
  code: { type: 'string', description: 'Code or expression.' },
  prompt: { type: 'string', description: 'Prompt text.' },

  group: { type: 'string', description: 'Group name.' },

  wavePath: { type: 'string', description: 'Path to SoundWave asset.' },
  attenuationPath: { type: 'string', description: 'Path to attenuation asset.' },
  concurrencyPath: { type: 'string', description: 'Path to concurrency asset.' },

  systemPath: { type: 'string', description: 'Path to Niagara system.' },
  emitterPath: { type: 'string', description: 'Path to Niagara emitter.' },
  emitterName: { type: 'string', description: 'Name of the emitter.' },

  sublevelName: { type: 'string', description: 'Name of the sublevel.' },
  parentLevel: { type: 'string', description: 'Parent level path.' },
  templateLevel: { type: 'string', description: 'Template level path.' },

  fromSection: { type: 'string', description: 'Source section name.' },
  toSection: { type: 'string', description: 'Target section name.' },

  axisName: { type: 'string', description: 'Axis name.' },
  horizontalAxisName: { type: 'string', description: 'Horizontal axis name.' },
  verticalAxisName: { type: 'string', description: 'Vertical axis name.' },

  controlName: { type: 'string', description: 'Control name.' },
  parentBone: { type: 'string', description: 'Parent bone name.' },
  parentControl: { type: 'string', description: 'Parent control name.' },
  unitName: { type: 'string', description: 'Rig unit name.' },
  goal: { type: 'string', description: 'IK goal name.' },

  notifyClass: { type: 'string', description: 'Animation notify class.' },
  notifyName: { type: 'string', description: 'Animation notify name.' },
  curveName: { type: 'string', description: 'Animation curve name.' },
  markerName: { type: 'string', description: 'Sync marker name.' },

  stateMachineName: { type: 'string', description: 'State machine name.' },

  exportPath: { type: 'string', description: 'Export file path.' },

  bodyName: { type: 'string', description: 'Physics body name.' },
  bodyA: { type: 'string', description: 'First physics body.' },
  bodyB: { type: 'string', description: 'Second physics body.' },
  constraintName: { type: 'string', description: 'Constraint name.' },

  morphTargetName: { type: 'string', description: 'Morph target name.' },

  brush: { type: 'string', description: 'Brush asset path.' },
  style: { type: 'string', description: 'Style preset name.' },

  bindingSource: { type: 'string', description: 'Binding source name.' },
  sourceBinding: { type: 'string', description: 'Source binding path.' },

  stageName: { type: 'string', description: 'Simulation stage name.' },

  repNotifyFunc: { type: 'string', description: 'RepNotify function name.' },

  traceDistance: { type: 'number', description: 'Trace distance.' },
  traceRadius: { type: 'number', description: 'Trace radius.' },
  traceFrequency: { type: 'number', description: 'Trace frequency.' },

  startTime: { type: 'number', description: 'Start time in seconds.' },
  endTime: { type: 'number', description: 'End time in seconds.' },
  blendTime: { type: 'number', description: 'Blend time in seconds.' },

  frameRate: { type: 'number', description: 'Frames per second.' },
  numFrames: { type: 'number', description: 'Number of frames.' },
  frame: { type: 'number', description: 'Frame number.' },

  startFrame: { type: 'number', description: 'Start frame.' },
  endFrame: { type: 'number', description: 'End frame.' },
  trackIndex: { type: 'number', description: 'Track index.' },

  nodeX: { type: 'number', description: 'Node X position.' },
  nodeY: { type: 'number', description: 'Node Y position.' },

  damageMultiplier: { type: 'number', description: 'Damage multiplier.' },
  criticalMultiplier: { type: 'number', description: 'Critical hit multiplier.' },

  minValue: { type: 'number', description: 'Minimum value.' },
  maxValue: { type: 'number', description: 'Maximum value.' },

  functionPath: { type: 'string', description: 'Path to function asset.' },
  particleSystemPath: { type: 'string', description: 'Path to particle system.' },
  cameraShakePath: { type: 'string', description: 'Path to camera shake asset.' },
  decalPath: { type: 'string', description: 'Path to decal material.' },
  actorPath: { type: 'string', description: 'Path to actor.' },
  volumePath: { type: 'string', description: 'Path to volume.' },
  sessionId: { type: 'string', description: 'Session ID.' },
  hlodLayerPath: { type: 'string', description: 'Path to HLOD layer.' },
  levelInstanceName: { type: 'string', description: 'Level instance name.' },
  serverAddress: { type: 'string', description: 'Server address.' },
  nodeClass: { type: 'string', description: 'Node class path.' },
  animationName: { type: 'string', description: 'Animation name.' }
};
