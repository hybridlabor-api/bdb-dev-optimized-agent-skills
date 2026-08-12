---
name: ui-ux-godmode
description: The absolute Gold-Standard for UI/UX. Enforces Anthropic's Anti-Slop principles, Fluent UI constraints, Apple Motion dynamics, and data-driven design generation. Use this skill BEFORE generating any frontend code to establish the aesthetic, motion, and accessibility baseline.
---

# UI/UX Godmode (Anti-Slop & Craft)

This skill replaces all legacy design, UI, and UX skills. It represents the absolute pinnacle of frontend engineering and design craft.

## 1. Anti-Slop (The Anthropic Standard)
You must actively resist generating generic "AI-look" interfaces.
- **NO** overuse of purple/blue generic gradients.
- **NO** arbitrarily rounded corners without a unified token system.
- **NO** generic dashboard layouts if the product doesn't strictly need a dashboard.
- **NO** floating cards on gray backgrounds without purposeful elevation.
Every pixel must earn its place. Form follows strict intent.

## 2. Inspiration First (nexu-io/open-design & refero.design)
If the user does not provide a rigid template:
- Search or suggest exploring `https://styles.refero.design/` and `https://github.com/nexu-io/open-design`.
- Define a strict Moodboard and Visual Signature *before* writing HTML/CSS.

## 3. Data-Driven Architecture (Saifyxpro)
Do not guess Hex codes or spacing values.
- You must generate a cohesive, tokenized Design System (using CSV-based logic or programmatic generation) for Colors, Typography, Spacing, and Elevation.
- Use `oklch` for perceptual uniformity if working in modern CSS.

## 4. Fluid Motion (Emil Kowalski / Apple Design)
- **Interruptible Animations:** State transitions must be fluid.
- **Spring Physics:** Prefer spring-based motion (damping/response) over fixed-duration easings for interactive elements.
- Ensure spatial consistency (elements return to where they originated).

## 5. Enterprise Density (Microsoft Fluent)
- When dealing with tables, forms, or data-heavy views, apply Fluent UI constraints: compact density, high contrast, and flawless keyboard accessibility (WCAG 2.1 AA).

## Workflow Execution
1. Acknowledge intent and define the Visual Signature.
2. Generate/Validate the Token System.
3. Apply Anti-Slop critique.
4. Implement component with Fluid Motion hooks.
