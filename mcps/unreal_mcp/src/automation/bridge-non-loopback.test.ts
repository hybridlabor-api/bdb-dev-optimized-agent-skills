import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { AutomationBridge } from './bridge.js';

describe('AutomationBridge Non-Loopback Host Validation', () => {
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

    describe('Non-loopback IPv4 addresses with allowNonLoopback=true (option)', () => {
        it('should accept 0.0.0.0 when allowNonLoopback is true', () => {
            const bridge = new AutomationBridge({
                host: '0.0.0.0',
                port: 8091,
                allowNonLoopback: true
            });
            expect(bridge.getStatus().host).toBe('0.0.0.0');
        });

        it('should accept LAN IP when allowNonLoopback is true', () => {
            const bridge = new AutomationBridge({
                host: '192.168.1.100',
                port: 8091,
                allowNonLoopback: true
            });
            expect(bridge.getStatus().host).toBe('192.168.1.100');
        });

        it('should accept any valid IPv4 when allowNonLoopback is true', () => {
            const bridge = new AutomationBridge({
                host: '10.0.0.1',
                port: 8091,
                allowNonLoopback: true
            });
            expect(bridge.getStatus().host).toBe('10.0.0.1');
        });
    });

    describe('Non-loopback IPv6 addresses with allowNonLoopback=true (option)', () => {
        it('should accept :: (all interfaces) when allowNonLoopback is true', () => {
            const bridge = new AutomationBridge({
                host: '::',
                port: 8091,
                allowNonLoopback: true
            });
            expect(bridge.getStatus().host).toBe('::');
        });

        it('should accept fe80::1 (link-local) when allowNonLoopback is true', () => {
            const bridge = new AutomationBridge({
                host: 'fe80::1',
                port: 8091,
                allowNonLoopback: true
            });
            expect(bridge.getStatus().host).toBe('fe80::1');
        });

        it('should accept 2001:db8::1 (global) when allowNonLoopback is true', () => {
            const bridge = new AutomationBridge({
                host: '2001:db8::1',
                port: 8091,
                allowNonLoopback: true
            });
            expect(bridge.getStatus().host).toBe('2001:db8::1');
        });

        it('should accept bracketed IPv6 [fe80::1] when allowNonLoopback is true', () => {
            const bridge = new AutomationBridge({
                host: '[fe80::1]',
                port: 8091,
                allowNonLoopback: true
            });
            expect(bridge.getStatus().host).toBe('fe80::1');
        });
    });

    describe('Invalid addresses with allowNonLoopback=true', () => {
        it('should reject invalid hostname format', () => {
            const bridge = new AutomationBridge({
                host: '-invalid-hostname',
                port: 8091,
                allowNonLoopback: true
            });
            expect(bridge.getStatus().host).toBe('127.0.0.1');
        });

        it('should reject out-of-range IPv4 octets', () => {
            const bridge = new AutomationBridge({
                host: '256.1.1.1',
                port: 8091,
                allowNonLoopback: true
            });
            expect(bridge.getStatus().host).toBe('127.0.0.1');
        });

        it('should reject hostname with consecutive dots', () => {
            const bridge = new AutomationBridge({
                host: 'example..com',
                port: 8091,
                allowNonLoopback: true
            });
            expect(bridge.getStatus().host).toBe('127.0.0.1');
        });
    });

    describe('Domain names/hostnames with allowNonLoopback=true', () => {
        it('should accept domain name when allowNonLoopback is true', () => {
            const bridge = new AutomationBridge({
                host: 'example.com',
                port: 8091,
                allowNonLoopback: true
            });
            expect(bridge.getStatus().host).toBe('example.com');
        });

        it('should accept local hostname when allowNonLoopback is true', () => {
            const bridge = new AutomationBridge({
                host: 'unreal-server.local',
                port: 8091,
                allowNonLoopback: true
            });
            expect(bridge.getStatus().host).toBe('unreal-server.local');
        });

        it('should accept subdomain when allowNonLoopback is true', () => {
            const bridge = new AutomationBridge({
                host: 'mcp.unreal.internal',
                port: 8091,
                allowNonLoopback: true
            });
            expect(bridge.getStatus().host).toBe('mcp.unreal.internal');
        });

        it('should accept simple hostname when allowNonLoopback is true', () => {
            const bridge = new AutomationBridge({
                host: 'dev-pc',
                port: 8091,
                allowNonLoopback: true
            });
            expect(bridge.getStatus().host).toBe('dev-pc');
        });
    });
});
