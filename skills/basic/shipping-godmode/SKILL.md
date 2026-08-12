---
name: shipping-godmode
description: Release management and workflow discipline based on Addy Osmani's agent-skills. Enforces pre-launch checklists, rollback strategies, and safe deployments.
---

# Shipping Godmode

This skill is the final gatekeeper. No code reaches production without passing these rigorous checks.

## 1. Spec-Driven Development
- Every major change must begin with a clear spec (`/spec`).
- Document boundaries, constraints, and success criteria.

## 2. Pre-Launch Checklists
Before deploying, confirm:
- [ ] All tests pass (Unit, E2E).
- [ ] No `.skip` or `.only` test blocks remain.
- [ ] No `console.log` debugging left in production code.
- [ ] Accessibility (WCAG 2.1 AA) and Core Web Vitals audited.
- [ ] Security boundaries validated.

## 3. Safe Rollouts & Feature Flags
- Ship behind Feature Flags where possible.
- Decouple deployment from release.
- Define a Staged Rollout sequence (Team -> 5% -> 50% -> 100%).

## 4. Rollback Strategy
- NEVER launch without a documented, verified Rollback Plan.
- Define trigger conditions for automatic rollback (e.g., error rate > 2x baseline).

## Workflow Execution
1. Verify CI/CD pipeline green.
2. Run Pre-Launch Checklist.
3. Document Rollback trigger.
4. Execute Deployment.
