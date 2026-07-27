import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { AutomationBridge } from './bridge.js';
import { DEFAULT_AUTOMATION_PORT } from '../constants.js';

describe('AutomationBridge Host Validation', () => {
    const originalEnv = process.env;

    beforeEach(() => {
        vi.resetModules();
        process.env = { ...originalEnv };
        delete process.env.MCP_AUTOMATION_ALLOW_NON_LOOPBACK;
        delete process.env.MCP_AUTOMATION_HOST;
        delete process.env.MCP_AUTOMATION_WS_HOST;
        delete process.env.MCP_AUTOMATION_WS_PORT;
        delete process.env.MCP_AUTOMATION_CLIENT_PORT;
        delete process.env.MCP_AUTOMATION_PORT;
    });

    afterEach(() => {
        process.env = originalEnv;
    });

    describe('Loopback addresses (always allowed)', () => {
        it('should accept 127.0.0.1 by default', () => {
            const bridge = new AutomationBridge({ host: '127.0.0.1', port: 8091 });
            expect(bridge.getStatus().host).toBe('127.0.0.1');
        });

        it('should normalize localhost to 127.0.0.1', () => {
            const bridge = new AutomationBridge({ host: 'localhost', port: 8091 });
            expect(bridge.getStatus().host).toBe('127.0.0.1');
        });

        it('should normalize LOCALHOST to 127.0.0.1 (case insensitive)', () => {
            const bridge = new AutomationBridge({ host: 'LOCALHOST', port: 8091 });
            expect(bridge.getStatus().host).toBe('127.0.0.1');
        });

        it('should accept IPv6 loopback ::1', () => {
            const bridge = new AutomationBridge({ host: '::1', port: 8091 });
            expect(bridge.getStatus().host).toBe('::1');
        });

        it('should accept bracketed IPv6 loopback [::1]', () => {
            const bridge = new AutomationBridge({ host: '[::1]', port: 8091 });
            expect(bridge.getStatus().host).toBe('::1');
        });
    });

    describe('Non-loopback addresses (default: rejected)', () => {
        it('should reject 0.0.0.0 by default and fallback to 127.0.0.1', () => {
            const bridge = new AutomationBridge({ host: '0.0.0.0', port: 8091 });
            expect(bridge.getStatus().host).toBe('127.0.0.1');
        });

        it('should reject LAN IP by default and fallback to 127.0.0.1', () => {
            const bridge = new AutomationBridge({ host: '192.168.1.100', port: 8091 });
            expect(bridge.getStatus().host).toBe('127.0.0.1');
        });

        it('should reject public IP by default and fallback to 127.0.0.1', () => {
            const bridge = new AutomationBridge({ host: '8.8.8.8', port: 8091 });
            expect(bridge.getStatus().host).toBe('127.0.0.1');
        });

        it('should reject IPv6 all-interfaces :: by default and fallback to 127.0.0.1', () => {
            const bridge = new AutomationBridge({ host: '::', port: 8091 });
            expect(bridge.getStatus().host).toBe('127.0.0.1');
        });

        it('should reject IPv6 LAN address by default and fallback to 127.0.0.1', () => {
            const bridge = new AutomationBridge({ host: 'fe80::1', port: 8091 });
            expect(bridge.getStatus().host).toBe('127.0.0.1');
        });
    });

    describe('MCP_AUTOMATION_ALLOW_NON_LOOPBACK env var', () => {
        it('should accept 0.0.0.0 when env var is "true"', () => {
            process.env.MCP_AUTOMATION_ALLOW_NON_LOOPBACK = 'true';
            const bridge = new AutomationBridge({ host: '0.0.0.0', port: 8091 });
            expect(bridge.getStatus().host).toBe('0.0.0.0');
        });

        it('should accept LAN IP when env var is "TRUE" (case insensitive)', () => {
            process.env.MCP_AUTOMATION_ALLOW_NON_LOOPBACK = 'TRUE';
            const bridge = new AutomationBridge({ host: '192.168.1.50', port: 8091 });
            expect(bridge.getStatus().host).toBe('192.168.1.50');
        });

        it('should accept IPv6 :: when env var is "true"', () => {
            process.env.MCP_AUTOMATION_ALLOW_NON_LOOPBACK = 'true';
            const bridge = new AutomationBridge({ host: '::', port: 8091 });
            expect(bridge.getStatus().host).toBe('::');
        });

        it('should reject non-loopback when env var is "false"', () => {
            process.env.MCP_AUTOMATION_ALLOW_NON_LOOPBACK = 'false';
            const bridge = new AutomationBridge({ host: '0.0.0.0', port: 8091 });
            expect(bridge.getStatus().host).toBe('127.0.0.1');
        });

        it('should reject non-loopback when env var is empty', () => {
            process.env.MCP_AUTOMATION_ALLOW_NON_LOOPBACK = '';
            const bridge = new AutomationBridge({ host: '0.0.0.0', port: 8091 });
            expect(bridge.getStatus().host).toBe('127.0.0.1');
        });
    });

    describe('Edge cases', () => {
        it('should handle empty host string', () => {
            const bridge = new AutomationBridge({ host: '', port: 8091 });
            expect(bridge.getStatus().host).toBe('127.0.0.1');
        });

        it('should handle whitespace-only host', () => {
            const bridge = new AutomationBridge({ host: '   ', port: 8091 });
            expect(bridge.getStatus().host).toBe('127.0.0.1');
        });

        it('should trim whitespace from valid host', () => {
            const bridge = new AutomationBridge({ host: '  127.0.0.1  ', port: 8091 });
            expect(bridge.getStatus().host).toBe('127.0.0.1');
        });

        it('should use default when no host provided', () => {
            const bridge = new AutomationBridge({ port: 8091 });
            expect(bridge.getStatus().host).toBe('127.0.0.1');
        });

        it('should reject partially numeric port strings from environment', () => {
            process.env.MCP_AUTOMATION_WS_PORT = '8092abc';
            const bridge = new AutomationBridge({});
            expect(bridge.getStatus().configuredPorts[0]).toBe(DEFAULT_AUTOMATION_PORT);
        });

        it('should reject non-decimal port strings from environment', () => {
            process.env.MCP_AUTOMATION_WS_PORT = '0x1f9b';
            const bridge = new AutomationBridge({});
            expect(bridge.getStatus().configuredPorts[0]).toBe(DEFAULT_AUTOMATION_PORT);
        });

        it('should accept the documented MCP_AUTOMATION_PORT alias', () => {
            process.env.MCP_AUTOMATION_PORT = '8097';
            const bridge = new AutomationBridge({});
            const status = bridge.getStatus();

            expect(status.configuredPorts[0]).toBe(8097);
            expect(status.port).toBe(8097);
        });

        it('should prefer the websocket-specific port over MCP_AUTOMATION_PORT', () => {
            process.env.MCP_AUTOMATION_PORT = '8097';
            process.env.MCP_AUTOMATION_WS_PORT = '8098';
            const bridge = new AutomationBridge({});
            const status = bridge.getStatus();

            expect(status.configuredPorts[0]).toBe(8098);
            expect(status.port).toBe(8098);
        });

        it('should use options.host for the actual client URL when clientHost is absent', () => {
            const bridge = new AutomationBridge({ host: '::1', port: 8098, enabled: false });

            expect(bridge.getStatus().host).toBe('::1');
            expect(bridge.getClientUrl()).toBe('ws://[::1]:8098');
        });

        it('should use MCP_AUTOMATION_WS_HOST for the actual client URL when clientHost is absent', () => {
            process.env.MCP_AUTOMATION_WS_HOST = '::1';
            const bridge = new AutomationBridge({ port: 8098, enabled: false });

            expect(bridge.getStatus().host).toBe('::1');
            expect(bridge.getClientUrl()).toBe('ws://[::1]:8098');
        });

        it('should handle null host', () => {
            const bridge = new AutomationBridge({ host: null, port: 8091 });
            expect(bridge.getStatus().host).toBe('127.0.0.1');
        });

        it('should handle undefined host', () => {
            const bridge = new AutomationBridge({ host: undefined, port: 8091 });
            expect(bridge.getStatus().host).toBe('127.0.0.1');
        });

        it('option allowNonLoopback should override env var false', () => {
            process.env.MCP_AUTOMATION_ALLOW_NON_LOOPBACK = 'false';
            const bridge = new AutomationBridge({
                host: '0.0.0.0',
                port: 8091,
                allowNonLoopback: true
            });
            expect(bridge.getStatus().host).toBe('0.0.0.0');
        });
    });

    describe('IPv6 zone IDs', () => {
        it('should accept link-local with zone ID when allowNonLoopback is true', () => {
            const bridge = new AutomationBridge({
                host: 'fe80::1%eth0',
                port: 8091,
                allowNonLoopback: true
            });
            // Zone ID is preserved in the returned value
            expect(bridge.getStatus().host).toBe('fe80::1%eth0');
        });
    });
});
