import { config } from '../config.js';
import type { Logger } from '../utils/logging/logger.js';
import type { RequestTracker } from './request-tracker.js';
import type {
    AutomationBridgeEvents,
    AutomationBridgeMessage,
    AutomationBridgeResponseMessage,
    QueuedRequestItem
} from './types.js';

type AutomationRequestOptions = { timeoutMs?: number };

interface AutomationRequestDispatcherDependencies {
    readonly enabled: boolean;
    readonly maxQueuedRequests: number;
    readonly connectionTimeoutMs: number;
    readonly requestTracker: RequestTracker;
    readonly log: Logger;
    readonly isConnected: () => boolean;
    readonly send: (payload: AutomationBridgeMessage) => boolean;
    readonly startClient: () => void;
    readonly abortPendingConnection: (reason: Error) => void;
    readonly once: <K extends keyof AutomationBridgeEvents>(
        event: K,
        listener: AutomationBridgeEvents[K]
    ) => void;
    readonly off: <K extends keyof AutomationBridgeEvents>(
        event: K,
        listener: AutomationBridgeEvents[K]
    ) => void;
}

export class AutomationRequestDispatcher {
    private readonly queuedRequestItems: QueuedRequestItem[] = [];
    private connectionPromise?: Promise<void>;
    private connectionLock = false;
    private connectionAttemptCleanup?: () => void;
    private connectionAttemptReject?: (reason: Error) => void;

    constructor(private readonly deps: AutomationRequestDispatcherDependencies) { }

    public async sendAutomationRequest<T = AutomationBridgeResponseMessage>(
        action: string,
        payload: Record<string, unknown> = {},
        options: AutomationRequestOptions = {}
    ): Promise<T> {
        if (!this.deps.isConnected()) {
            await this.ensureConnected();
        }

        if (!this.deps.isConnected()) {
            throw new Error('Automation bridge not connected');
        }

        if (this.deps.requestTracker.getPendingCount() >= this.deps.requestTracker.getMaxPendingRequests()) {
            if (this.queuedRequestItems.length >= this.deps.maxQueuedRequests) {
                throw new Error(`Automation bridge request queue is full (max: ${this.deps.maxQueuedRequests}). Please retry later.`);
            }

            return new Promise<T>((resolve, reject) => {
                this.queuedRequestItems.push({
                    resolve: resolve as (value: unknown) => void,
                    reject: reject as (reason: unknown) => void,
                    action,
                    payload,
                    options
                });
            });
        }

        return this.sendRequestInternal<T>(action, payload, options);
    }

    public stop(reason: Error): void {
        this.abortConnectionAttempt(reason);
        this.rejectQueuedRequests(reason);
        this.deps.requestTracker.rejectAll(reason);
    }

    public rejectQueuedRequests(error: Error): void {
        for (const item of this.queuedRequestItems.splice(0)) {
            item.reject(error);
        }
    }

    public rejectPendingRequests(error: Error): void {
        this.deps.requestTracker.rejectAll(error);
    }

    private async ensureConnected(): Promise<void> {
        if (!this.deps.enabled) {
            throw new Error('Automation bridge disabled');
        }

        this.deps.log.info('Automation bridge not connected, attempting lazy connection...');
        if (!this.connectionPromise && !this.connectionLock) {
            this.connectionLock = true;
            this.connectionPromise = this.createConnectionPromise();
        }

        try {
            await this.waitForConnection();
        } catch (error) {
            const message = getErrorMessage(error);
            if (message === 'Lazy connection timeout') {
                this.abortConnectionAttempt(new Error('Lazy connection timeout'));
            }
            this.deps.log.error('Lazy connection failed', error);
            throw new Error(`Failed to establish connection to Unreal Engine: ${message}`);
        }
    }

    private createConnectionPromise(): Promise<void> {
        return new Promise<void>((resolve, reject) => {
            const onConnect = () => {
                cleanup();
                resolve();
            };
            const onError = (error: Error) => {
                cleanup();
                reject(error);
            };
            const onHandshakeFail = (info: { reason: string }) => {
                cleanup();
                reject(new Error(`Handshake failed: ${String(info.reason)}`));
            };
            const cleanup = () => {
                this.deps.off('connected', onConnect);
                this.deps.off('error', onError);
                this.deps.off('handshakeFailed', onHandshakeFail);
                this.connectionLock = false;
                this.connectionPromise = undefined;
                if (this.connectionAttemptCleanup === cleanup) {
                    this.connectionAttemptCleanup = undefined;
                    this.connectionAttemptReject = undefined;
                }
            };

            this.connectionAttemptCleanup = cleanup;
            this.connectionAttemptReject = reject;
            this.deps.once('connected', onConnect);
            this.deps.once('error', onError);
            this.deps.once('handshakeFailed', onHandshakeFail);

            try {
                this.deps.startClient();
            } catch (error) {
                onError(error instanceof Error ? error : new Error(String(error)));
            }
        });
    }

    private async waitForConnection(): Promise<void> {
        let timeoutId: ReturnType<typeof setTimeout> | undefined;
        const timeoutPromise = new Promise<never>((_, reject) => {
            timeoutId = setTimeout(() => reject(new Error('Lazy connection timeout')), this.deps.connectionTimeoutMs);
        });

        try {
            await Promise.race([this.connectionPromise, timeoutPromise]);
        } finally {
            if (timeoutId) clearTimeout(timeoutId);
        }
    }

    private abortConnectionAttempt(reason: Error): void {
        const rejectConnectionAttempt = this.connectionAttemptReject;
        const cleanup = this.connectionAttemptCleanup;
        if (cleanup) {
            cleanup();
        } else {
            this.connectionLock = false;
            this.connectionPromise = undefined;
            this.connectionAttemptReject = undefined;
        }

        if (rejectConnectionAttempt) {
            rejectConnectionAttempt(reason);
        }
        this.deps.abortPendingConnection(reason);
    }

    private async sendRequestInternal<T>(
        action: string,
        payload: Record<string, unknown>,
        options: AutomationRequestOptions
    ): Promise<T> {
        const timeoutMs = options.timeoutMs ?? config.MCP_REQUEST_TIMEOUT_MS;
        const coalesceKey = this.deps.requestTracker.createCoalesceKey(action, payload);
        if (coalesceKey) {
            const existing = this.deps.requestTracker.getCoalescedRequest(coalesceKey);
            if (existing) {
                return existing.then(castAutomationResponse<T>);
            }
        }

        const { requestId, promise } = this.deps.requestTracker.createRequest(action, payload, timeoutMs);
        if (coalesceKey) {
            this.deps.requestTracker.setCoalescedRequest(coalesceKey, promise);
        }

        const resultPromise = promise.then(castAutomationResponse<T>);
        void resultPromise.then(
            () => this.processRequestQueue(),
            () => this.processRequestQueue()
        );

        if (this.deps.send({ type: 'automation_request', requestId, action, payload })) {
            this.deps.requestTracker.updateLastRequestSentAt();
            return resultPromise;
        }

        this.deps.requestTracker.rejectRequest(requestId, new Error('Failed to send request'));
        throw new Error('Failed to send request');
    }

    private processRequestQueue(): void {
        if (this.queuedRequestItems.length === 0) return;
        if (!this.deps.isConnected()) {
            this.rejectQueuedRequests(new Error('Connection lost'));
            return;
        }

        while (
            this.queuedRequestItems.length > 0 &&
            this.deps.requestTracker.getPendingCount() < this.deps.requestTracker.getMaxPendingRequests()
        ) {
            const item = this.queuedRequestItems.shift();
            if (!item) continue;

            this.sendRequestInternal(item.action, item.payload, getQueuedOptions(item.options))
                .then(item.resolve)
                .catch(item.reject);
        }
    }
}

function castAutomationResponse<T>(response: AutomationBridgeResponseMessage): T {
    return response as T;
}

function getQueuedOptions(options: Record<string, unknown>): AutomationRequestOptions {
    return typeof options.timeoutMs === 'number' ? { timeoutMs: options.timeoutMs } : {};
}

function getErrorMessage(error: unknown): string {
    return error instanceof Error ? error.message : String(error);
}
