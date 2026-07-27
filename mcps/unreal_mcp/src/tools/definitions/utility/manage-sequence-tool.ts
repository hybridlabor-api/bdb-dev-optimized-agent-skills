import { commonSchemas } from '../../catalog/tool-definition-utils.js';
import type { ToolDefinition } from '../shared/tool-definition.js';

export const manageSequenceToolDefinition: ToolDefinition = {
    name: 'manage_sequence',
    category: 'utility',
    description: 'Edit Level Sequences: add tracks, bind actors, set keyframes, control playback, and record camera.',
    inputSchema: {
      type: 'object',
      properties: {
        action: {
          type: 'string',
          enum: [
            'create', 'open', 'add_camera', 'add_actor', 'add_actors', 'remove_actors',
            'get_bindings', 'play', 'pause', 'stop', 'set_playback_speed', 'add_keyframe',
            'get_properties', 'set_properties', 'duplicate', 'rename', 'delete', 'list', 'get_metadata', 'set_metadata',
            'add_spawnable_from_class', 'add_track', 'add_section', 'set_display_rate', 'set_tick_resolution',
            'set_work_range', 'set_view_range', 'set_track_muted', 'set_track_solo', 'set_track_locked',
            'list_tracks', 'remove_track', 'list_track_types'
          ],
          description: 'Action'
        },
        name: commonSchemas.name,
        path: commonSchemas.assetPath,
        actorName: commonSchemas.actorName,
        actorNames: commonSchemas.arrayOfStrings,
        frame: commonSchemas.numberProp,
        value: commonSchemas.objectProp,
        property: commonSchemas.propertyName,
        destinationPath: commonSchemas.destinationPath,
        newName: commonSchemas.newName,
        speed: commonSchemas.numberProp,
        startTime: commonSchemas.numberProp,
        loopMode: commonSchemas.stringProp,
        className: commonSchemas.stringProp,
        spawnable: commonSchemas.booleanProp,
        trackType: commonSchemas.stringProp,
        trackName: commonSchemas.stringProp,
        muted: commonSchemas.booleanProp,
        solo: commonSchemas.booleanProp,
        locked: commonSchemas.booleanProp,
        startFrame: commonSchemas.numberProp,
        endFrame: commonSchemas.numberProp,
        frameRate: commonSchemas.stringProp,
        resolution: commonSchemas.stringProp,
        start: commonSchemas.numberProp,
        end: commonSchemas.numberProp,
        lengthInFrames: commonSchemas.numberProp,
        playbackStart: commonSchemas.numberProp,
        playbackEnd: commonSchemas.numberProp,
        metadata: commonSchemas.objectProp
      },
      required: ['action']
    },
    outputSchema: {
      type: 'object',
      properties: {
        ...commonSchemas.outputBase
      }
    }
  };
