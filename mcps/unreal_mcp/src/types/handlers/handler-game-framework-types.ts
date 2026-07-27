/**
 * Game framework handler argument types.
 */
import type { HandlerArgs } from './handler-common-types.js';

// ============================================================================
// Game Framework Types
// ============================================================================

/**
 * Match state definition for game mode configuration
 */
export interface MatchStateDefinition {
    name: 'waiting' | 'warmup' | 'in_progress' | 'post_match' | 'custom';
    duration?: number;
    customName?: string;
}

/**
 * Arguments for manage_game_framework tool
 *
 * Covers:
 * - Core Classes: GameMode, GameState, PlayerController, PlayerState, GameInstance, HUD
 * - Game Mode Configuration: class assignments, game rules
 * - Match Flow: match states, rounds, teams, scoring, spawning
 * - Player Management: spawn points, respawning, spectating
 */
export interface GameFrameworkArgs extends HandlerArgs {
    // Asset identification
    name?: string;
    path?: string;
    gameModeBlueprint?: string;
    blueprintPath?: string;

    // Class assignments
    parentClass?: string;
    pawnClass?: string;
    defaultPawnClass?: string;
    playerControllerClass?: string;
    gameStateClass?: string;
    playerStateClass?: string;
    spectatorClass?: string;
    hudClass?: string;

    // Game rules
    bDelayedStart?: boolean;

    // Match states
    states?: MatchStateDefinition[];

    // Round system
    numRounds?: number;
    roundTime?: number;
    intermissionTime?: number;

    // Team system
    numTeams?: number;
    teamSize?: number;
    autoBalance?: boolean;
    friendlyFire?: boolean;
    teamIndex?: number;

    // Scoring
    scorePerKill?: number;
    scorePerObjective?: number;
    scorePerAssist?: number;

    // Spawn system
    spawnSelectionMethod?: 'Random' | 'RoundRobin' | 'FarthestFromEnemies';
    respawnDelay?: number;
    respawnLocation?: 'PlayerStart' | 'LastDeath' | 'TeamBase';
    usePlayerStarts?: boolean;

    // Spectating
    allowSpectating?: boolean;
    spectatorViewMode?: 'FreeCam' | 'ThirdPerson' | 'FirstPerson' | 'DeathCam';

    // Save option
    save?: boolean;
}
