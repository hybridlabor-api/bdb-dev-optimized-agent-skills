# After Effects MCP Integration Demos

This directory contains demo applications showcasing the capabilities of the After Effects MCP integration.

## Demo Applications

### 1. Basic Project Demo (`basic_project.go`)
A simple demonstration that shows how to:
- Get project information
- Create a composition
- Get composition details

### 2. Layers Demo (`layers_demo.go`)
Demonstrates working with various layer types:
- Creating solid color layers
- Adding text layers with customized properties
- Creating shape layers
- Modifying layer properties

### 3. Animation and Effects Demo (`animation_effects_demo.go`)
Showcases animation and effects capabilities:
- Creating keyframe animations for position and scale
- Setting keyframe interpolation for smooth animations
- Applying effects like glow and blur
- Using particle systems

### 4. Text Animation Demo (`text_animation_demo.go`)
Specialized demo focusing on typography and text animations:
- Character-by-character animations
- Word-by-word reveal effects
- Letter spacing (tracking) animations
- Text countdown sequence with changing content
- Wipe-on text reveals and text effects

### 5. Complete Workflow Demo (`complete_workflow_demo.go`)
A comprehensive end-to-end demo that shows:
- Creating a complete product introduction animation
- Building a multi-layered composition with visual elements
- Configuring complex animations
- Adding text with animations
- Using multiple effects for visual enhancement
- Rendering the final output to a video file

## Running the Demos

To run these demos, After Effects should be running, and the After Effects MCP integration should be set up properly.

1. Make sure After Effects is open
2. Run a demo with:
   ```
   go run basic_project.go
   ```

Each demo is designed to showcase different aspects of the After Effects MCP toolset, building from simple operations to more complex workflows.

## Note on Customization

These demos are meant as starting points. Feel free to modify parameters, colors, timings, and effects to experiment with different results. The code is well-commented to help you understand how each function works.

## Prerequisites

- Adobe After Effects (CC 2020 or later recommended)
- Go compiler
- AE-MCP integration properly set up

## Related Documentation

For more information on available functions and their parameters, please refer to the pkg/tools directory which contains the implementation of all the tools used in these demos. 