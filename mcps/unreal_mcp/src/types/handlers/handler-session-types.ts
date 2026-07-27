/**
 * Session and local multiplayer handler argument types.
 */
import type { HandlerArgs } from './handler-common-types.js';

// ============================================================================
// Sessions & Local Multiplayer Types
// ============================================================================

/**
 * Voice chat settings for session configuration
 */
export interface VoiceSettings {
    /** Volume level (0.0 - 1.0) */
    volume?: number;
    /** Noise gate threshold */
    noiseGateThreshold?: number;
    /** Enable noise suppression */
    noiseSuppression?: boolean;
    /** Enable echo cancellation */
    echoCancellation?: boolean;
    /** Sample rate in Hz */
    sampleRate?: number;
}

/**
 * Arguments for manage_sessions tool
 *
 * Covers:
 * - Session Management: local session settings, session interface
 * - Local Multiplayer: split-screen configuration, local players
 * - LAN: LAN play configuration, hosting/joining servers
 * - Voice Chat: voice settings, channels, muting, attenuation
 */
export interface SessionsArgs extends HandlerArgs {
    // Session identification
    sessionName?: string;

    // Local session settings
    maxPlayers?: number;
    bIsLANMatch?: boolean;
    bAllowJoinInProgress?: boolean;
    bAllowInvites?: boolean;
    bUsesPresence?: boolean;
    bUseLobbiesIfAvailable?: boolean;
    bShouldAdvertise?: boolean;

    // Session interface
    interfaceType?: 'Default' | 'LAN' | 'Null';

    // Split-screen configuration
    enabled?: boolean;
    splitScreenType?: 'None' | 'TwoPlayer_Horizontal' | 'TwoPlayer_Vertical' | 'ThreePlayer_FavorTop' | 'ThreePlayer_FavorBottom' | 'FourPlayer_Grid';

    // Local player management
    playerIndex?: number;
    controllerId?: number;

    // LAN settings
    serverAddress?: string;
    serverPort?: number;
    serverPassword?: string;
    serverName?: string;
    mapName?: string;
    travelOptions?: string;

    // Voice chat
    voiceEnabled?: boolean;
    voiceSettings?: VoiceSettings;
    channelName?: string;
    channelType?: 'Team' | 'Global' | 'Proximity' | 'Party';

    // Player targeting for voice operations
    playerName?: string;
    targetPlayerId?: string;
    muted?: boolean;

    // Voice attenuation
    attenuationRadius?: number;
    attenuationFalloff?: number;

    // Push-to-talk
    pushToTalkEnabled?: boolean;
    pushToTalkKey?: string;
}
