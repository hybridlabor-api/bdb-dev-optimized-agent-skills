---
name: godmode-ui-ux
description: BDB UI/UX Godmode. The absolute Gold-Standard for frontend design. Enforces Anti-Slop principles, enterprise accessibility, fluid motion dynamics, and data-driven design generation across all agent harnesses.
---

# 🎨 BDB UI/UX Godmode

This skill replaces all legacy design and UX skills. It represents the absolute pinnacle of frontend engineering and design craft in the BDB ecosystem. As an agent, you must execute these principles rigorously across all supported harnesses (Cursor, Claude Code, Agy, Copilot).

## 1. The Anti-Slop Directive
You must actively resist generating generic "AI-look" interfaces. The internet is flooded with low-effort, generic layouts. Your job is to craft intent-driven design.
*   **No Generic Gradients:** Do not use arbitrary purple/blue glowing gradients or mesh backgrounds unless explicitly requested by the brand guidelines.
*   **No Arbitrary Border Radii:** Do not mix `rounded-md` and `rounded-2xl` arbitrarily. All border radii must follow a strict, nested mathematical token system.
*   **No Default Dashboards:** Do not build a sidebar/header dashboard layout for a tool that would be better served as a modal, a command palette, or a single-column focused view.
*   **Elevations & Shadows:** Flat is not an excuse for lacking hierarchy. Shadows must mimic real-world lighting (multi-layered diffuse shadows), not hard black boxes.

## 2. Inspiration & Retrieval Layer
Never guess a layout if the user hasn't provided one. You must act as a design researcher before acting as a coder.
*   **Ask for References:** Prompt the user to provide references from highly curated galleries.
*   **Curated Sources:** When searching for inspiration, rely on real-world patterns. Internally map your layout generation to standards found on top-tier UI galleries (e.g., refero.design, open-design).
*   **Moodboard First:** Define the visual signature (Typography paired, Primary/Secondary/Surface colors defined) in markdown before writing a single line of React/HTML/CSS.

## 3. Data-Driven Architecture (Design Tokens)
Design is math. You do not guess spacing, and you do not guess colors.
*   **Color Space:** Use `oklch()` for programmatic color generation to ensure perceptual uniformity (no more muddy yellows or overly bright blues when generating palettes).
*   **Spacing System:** Strictly adhere to a 4pt or 8pt grid (`4, 8, 12, 16, 24, 32, 48, 64, 96`). Do not use random pixel values like `17px` or `21px`.
*   **Modular Typography:** Generate font sizes using a modular scale (e.g., Major Third or Perfect Fourth). Define explicit `line-height` (tighter for headings ~1.1, looser for body ~1.5) and tracking/letter-spacing (tighter for large text, looser for microcopy).

## 4. Fluid Motion & Physics
Animation is not decoration; it is spatial orientation.
*   **Interruptible Animations:** State transitions must be fluid. If a user closes a modal while it is still opening, it must smoothly reverse from its current physical state, not snap back to zero.
*   **Spring Physics:** Avoid fixed-duration CSS `ease-in-out` for interactive elements. Use spring physics (Stiffness, Damping, Mass) via tools like Framer Motion or React Spring so elements feel tactile and physically grounded.
*   **Spatial Consistency:** Elements must expand from their origin point (Shared Element Transitions) rather than fading in from nowhere.

## 5. Enterprise Density & Accessibility
An interface that cannot be used by everyone is broken.
*   **High-Density Data:** When building B2B tables or forms, apply strict compact density rules. Minimize padding, use tabular numbers (`font-variant-numeric: tabular-nums;`), and align numerical data to the right.
*   **WCAG 2.1 AA:** Enforce strict contrast ratios (4.5:1 for normal text).
*   **Keyboard Navigation:** Focus states must be highly visible (e.g., `focus-visible:ring-2 focus-visible:ring-offset-2`). Every interactive element must be reachable via `Tab` and executable via `Enter/Space`.

## 6. Creator Extension & BDB MediaStorm Governance
This Godmode extends beyond standard software development. It STRICTLY governs creative-tech and show-control workflows (BDB Creator Extension).
*   **MediaStorm Validations:** When executing `/bdbmediastorm` for TouchDesigner, Unreal Engine, or Adobe Suite workflows, UX principles must translate to operator panels, perform mode interfaces, and VJ dashboards. 
*   **Performance vs UI:** In real-time rendering environments, UI must not block the main render thread. Anti-slop applies to creative tech: avoid generic generative noises and default particle systems. 

## Universal Agent Harness Integration
This Godmode is universally compatible and governs all extensions, including the BDB Creator Engine.
*   **Cursor:** Auto-injected via `.cursor/rules/godmode-ui-ux.mdc`.
*   **Claude Code:** Reads principles via `CLAUDE.md`.
*   **Agy / CLI Agents:** Natively enforced via the prompt orchestrator.
*   **Execution:** You (the AI) must silently validate your planned UI code against these 5 pillars before outputting code to the user.
