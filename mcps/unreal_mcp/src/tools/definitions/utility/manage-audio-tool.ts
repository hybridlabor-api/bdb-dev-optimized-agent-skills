import { commonSchemas } from '../../catalog/tool-definition-utils.js';
import type { ToolDefinition } from '../shared/tool-definition.js';

export const manageAudioToolDefinition: ToolDefinition = {
    name: 'manage_audio',
    category: 'utility',
    description: 'Play/stop sounds, add audio components, configure mixes, attenuation, spatial audio, and author Sound Cues/MetaSounds.',
    inputSchema: {
      type: 'object',
      properties: {
        action: {
          type: 'string',
          enum: [
            // Runtime audio control
            'create_sound_cue', 'play_sound_at_location', 'play_sound_2d', 'create_audio_component',
            'create_sound_mix', 'push_sound_mix', 'pop_sound_mix',
            'set_sound_mix_class_override', 'clear_sound_mix_class_override', 'set_base_sound_mix',
            'prime_sound', 'play_sound_attached', 'spawn_sound_at_location',
            'fade_sound_in', 'fade_sound_out', 'create_ambient_sound',
            'create_sound_class', 'set_sound_attenuation', 'create_reverb_zone',
            'enable_audio_analysis', 'fade_sound', 'set_doppler_effect', 'set_audio_occlusion',
        // Sound Cue authoring
            'add_cue_node', 'connect_cue_nodes', 'set_cue_attenuation', 'set_cue_concurrency',
            // MetaSound authoring
            'create_metasound', 'add_metasound_node', 'connect_metasound_nodes',
            'add_metasound_input', 'add_metasound_output', 'set_metasound_default',
            // Sound class/mix authoring
            'set_class_properties', 'set_class_parent', 'add_mix_modifier', 'configure_mix_eq',
            // Attenuation authoring
            'create_attenuation_settings', 'configure_distance_attenuation',
            'configure_spatialization', 'configure_occlusion', 'configure_reverb_send',
            // Dialogue system
            'create_dialogue_voice', 'create_dialogue_wave', 'set_dialogue_context',
            // Effects
            'create_reverb_effect', 'create_source_effect_chain', 'add_source_effect', 'create_submix_effect',
            // Utility
            'get_audio_info'
          ],
          description: 'Action'
        },
        name: commonSchemas.name,
        soundPath: commonSchemas.soundPath,
        location: commonSchemas.location,
        rotation: commonSchemas.rotation,
        volume: commonSchemas.numberProp,
        pitch: commonSchemas.numberProp,
        startTime: commonSchemas.numberProp,
        attenuationPath: commonSchemas.assetPath,
        concurrencyPath: commonSchemas.assetPath,
        mixName: commonSchemas.stringProp,
        soundClassName: commonSchemas.stringProp,
        fadeInTime: commonSchemas.numberProp,
        fadeOutTime: commonSchemas.numberProp,
        fadeTime: commonSchemas.numberProp,
        targetVolume: commonSchemas.numberProp,
        attachPointName: commonSchemas.socketName,
        actorName: commonSchemas.actorName,
        componentName: commonSchemas.componentName,
        parentClass: commonSchemas.stringProp,
        properties: commonSchemas.objectProp,
        innerRadius: commonSchemas.numberProp,
        falloffDistance: commonSchemas.numberProp,
        attenuationShape: commonSchemas.stringProp,
        falloffMode: commonSchemas.stringProp,
        reverbEffect: commonSchemas.stringProp,
        size: commonSchemas.scale,
        analysisType: commonSchemas.stringProp,
        windowSize: commonSchemas.numberProp,
        outputType: commonSchemas.stringProp,
        soundName: commonSchemas.stringProp,
        fadeType: commonSchemas.stringProp,
        lowPassFilterFrequency: commonSchemas.numberProp,
        enabled: commonSchemas.enabled,
        // Authoring properties
        path: commonSchemas.directoryPathForCreation,
        assetPath: commonSchemas.assetPath,
        save: commonSchemas.save,
        wavePath: commonSchemas.wavePath,
        nodeType: commonSchemas.stringProp,
        sourceNodeId: commonSchemas.sourceNodeId,
        targetNodeId: commonSchemas.targetNodeId,
        looping: commonSchemas.looping,
        inputName: commonSchemas.inputName,
        inputType: commonSchemas.stringProp,
        outputName: commonSchemas.outputName,
        sourceNode: commonSchemas.sourceNode,
        sourcePin: commonSchemas.sourcePin,
        targetNode: commonSchemas.targetNode,
        targetPin: commonSchemas.targetPin,
        defaultValue: commonSchemas.value,
        soundClassPath: commonSchemas.soundClassPath,
        dopplerIntensity: commonSchemas.numberProp,
        effectType: commonSchemas.stringProp,
        enable: commonSchemas.booleanProp,
        enableReverbSend: commonSchemas.booleanProp,
        occlusionFilterScale: commonSchemas.numberProp,
        occlusionInterpolationTime: commonSchemas.numberProp,
        occlusionVolumeScale: commonSchemas.numberProp,
        reverbDistanceMax: commonSchemas.numberProp,
        reverbDistanceMin: commonSchemas.numberProp,
        reverbWetLevelMax: commonSchemas.numberProp,
        reverbWetLevelMin: commonSchemas.numberProp,
        sourceOutputName: commonSchemas.stringProp,
        spatialization: commonSchemas.stringProp,
        speakerPath: commonSchemas.assetPath,
        targetInputName: commonSchemas.stringProp,
        velocityScale: commonSchemas.numberProp,
        volumeAdjuster: commonSchemas.numberProp
      },
      required: ['action']
    },
    outputSchema: {
      type: 'object',
      properties: {
        ...commonSchemas.outputBase,
        assetPath: commonSchemas.assetPath,
        nodeId: commonSchemas.nodeId
      }
    }
  };
