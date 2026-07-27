import { describe, expect, it } from 'vitest';
import { RequestTracker } from './request-tracker.js';
import { MessageHandler } from './message-handler.js';

type AutomationEventFixture = {
    readonly type: 'automation_event';
    readonly event: string;
    readonly requestId?: string;
    readonly payload?: unknown;
    readonly result?: unknown;
    readonly message?: string;
};

describe('MessageHandler automation events', () => {
    it('emits normalized automation events when no pending request exists', () => {
        // Given
        const events: AutomationEventFixture[] = [];
        const handler = new MessageHandler(
            new RequestTracker(10),
            (event: AutomationEventFixture) => {
                events.push(event);
            }
        );

        // When
        handler.handleMessage({
            type: 'automation_event',
            event: 'asset_saved',
            requestId: 'orphan-request',
            message: 'Saved /Game/Maps/Arena',
            payload: { assetPath: '/Game/Maps/Arena' },
            unexpected: 'not forwarded'
        });

        // Then
        expect(events).toEqual([
            {
                type: 'automation_event',
                event: 'asset_saved',
                requestId: 'orphan-request',
                message: 'Saved /Game/Maps/Arena',
                payload: { assetPath: '/Game/Maps/Arena' }
            }
        ]);
    });

    it('drops malformed automation events without an event name', () => {
        // Given
        const events: AutomationEventFixture[] = [];
        const handler = new MessageHandler(
            new RequestTracker(10),
            (event: AutomationEventFixture) => {
                events.push(event);
            }
        );

        // When
        handler.handleMessage({
            type: 'automation_event',
            message: 'Missing event name',
            payload: { assetPath: '/Game/Maps/Arena' }
        });

        // Then
        expect(events).toEqual([]);
    });
});
