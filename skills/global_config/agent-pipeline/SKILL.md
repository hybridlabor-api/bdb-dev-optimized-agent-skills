---
name: agent-pipeline
description: Defines the 6-stage BDB Software Engineering Pipeline (DEFINE, PLAN, BUILD, VERIFY, REVIEW, SHIP) with corresponding slash commands (/spec, /plan, /build, /test, /review, /ship) for AI agent orchestration.
---

# 🔄 BDB Software Engineering Pipeline

When orchestrating or executing software development, AI agents MUST follow the 6-stage lifecycle pipeline.

```
DEFINE          PLAN           BUILD          VERIFY         REVIEW          SHIP
 ┌──────┐      ┌──────┐      ┌──────┐      ┌──────┐      ┌──────┐      ┌──────┐
 │ Idea │ ───▶ │ Spec │ ───▶ │ Code │ ───▶ │ Test │ ───▶ │  QA  │ ───▶ │  Go  │
 │Refine│      │  PRD │      │ Impl │      │Debug │      │ Gate │      │ Live │
 └──────┘      └──────┘      └──────┘      └──────┘      └──────┘      └──────┘
  /spec          /plan          /build        /test         /review       /ship
```

---

## 📌 Pipeline Stages & Slash Command Triggers

### 1. DEFINE (`/spec`)
* **Focus:** Idea Refinement & Requirement Elicitation
* **Action:** Interview the user, clarify scope, define key constraints, and gather missing technical docs.
* **Output:** User Stories, Scope Boundaries, and Spec RFCs.

### 2. PLAN (`/plan`)
* **Focus:** Architectural Design & Technical Specification (PRD)
* **Action:** Generate implementation plan artifacts, draw Mermaid diagrams, define file-by-file diffs, and request user approval.
* **Output:** Approved Implementation Plan Artifact (`<plan_name>.md`).

### 3. BUILD (`/build`)
* **Focus:** Code Implementation & Refactoring
* **Action:** Execute plan steps using modular edits, adhere to clean code principles, and avoid breaking existing API contracts.
* **Output:** Functional codebase modifications & newly created components.

### 4. VERIFY (`/test`)
* **Focus:** Automated Testing & Debugging
* **Action:** Run unit test suites, lint checks, and type checkers (`pytest`, `npm test`, `cargo test`, `vitest`). Inspect runtime logs upon failure.
* **Output:** Verified test run outputs (100% green build status).

### 5. REVIEW (`/review`)
* **Focus:** QA Gate & Code Review
* **Action:** Perform architectural reviews, security scans for hardcoded secrets, UI/UX compliance audits (`ui-ux-pro-max`), and code simplification passes.
* **Output:** Code review summary & QA gate approval.

### 6. SHIP (`/ship`)
* **Focus:** Production Deployment & Release
* **Action:** Take git snapshots, push commits to remote repositories (Private by default), update documentation/OpenWiki release notes, and deploy daemons/executables.
* **Output:** Live deployment confirmation & release notes entry.
