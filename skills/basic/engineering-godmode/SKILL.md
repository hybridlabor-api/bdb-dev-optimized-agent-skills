---
name: engineering-godmode
description: Engineering and Architecture master skill based on Matt Pocock's standards. Enforces strict TypeScript domain modeling, codebase design, and systematic debugging triage.
---

# Engineering Godmode

This skill orchestrates the core logic, domain modeling, and typing constraints of the codebase. It replaces scattershot coding with rigorous, structured engineering.

## 1. Codebase Design & Domain Modeling (Matt Pocock)
- Before writing implementation logic, define the Domain Model using strict TypeScript types/interfaces.
- Enforce immutability and pure functions where applicable.
- Types should represent the domain truthfully; use Discriminated Unions for state machines.
- Avoid `any` at all costs.

## 2. Systematic Triage & Debugging
- Do not guess fixes based on error logs.
- Use the 5-step triage method: Reproduce -> Localize -> Reduce -> Fix -> Guard.
- Write a failing test (TDD) that reproduces the bug before implementing the fix.

## 3. Clean Architecture
- Separate business logic from UI/Framework details.
- Adhere to DAMP over DRY in tests.
- Every architectural decision should be justifiable and documented (ADR).

## Workflow Execution
1. Type the boundaries.
2. Write the failing test.
3. Implement the pure logic.
4. Integrate with the framework.
