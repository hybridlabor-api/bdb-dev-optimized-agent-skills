package main

import (
	"fmt"
	"log"
	"path/filepath"

	"github.com/sunqirui1987/ae-mcp/pkg/tools"
)

func main() {
	// Create output directory for Manim videos
	outputDir := filepath.Join("output", "manim")
	
	// Create Manim tool
	manimTool, err := tools.NewManimTool(outputDir)
	if err != nil {
		log.Fatalf("Failed to create Manim tool: %v", err)
	}

	// Example 1: Create a rotating cube animation
	cubeCode := `
from manim import *

class RotatingCube(ThreeDScene):
    def construct(self):
        # Create a cube
        cube = Cube(side_length=2)
        
        # Add axes for reference
        axes = ThreeDAxes()
        
        # Add the cube and axes to the scene
        self.add(axes, cube)
        
        # Rotate the cube
        self.play(Rotate(cube, angle=2*PI, axis=UP), run_time=2)
        self.wait()
        
        # Rotate around different axes
        self.play(Rotate(cube, angle=PI, axis=RIGHT), run_time=1)
        self.wait()
        self.play(Rotate(cube, angle=PI, axis=OUT), run_time=1)
        self.wait()
`

	// Create the rotating cube layer
	cubeResult, err := manimTool.CreateManimLayer(cubeCode, "RotatingCube")
	if err != nil {
		log.Fatalf("Failed to create rotating cube: %v", err)
	}
	fmt.Printf("Created rotating cube layer: %+v\n", cubeResult)

	// Example 2: Create a mathematical equation animation
	equationCode := `
from manim import *

class MathEquation(Scene):
    def construct(self):
        # Create the equation
        equation = MathTex(
            r"e^{i\pi} + 1 = 0",
            font_size=72
        )
        
        # Add the equation to the scene
        self.play(Write(equation))
        self.wait()
        
        # Transform the equation
        new_equation = MathTex(
            r"e^{i\pi} = -1",
            font_size=72
        )
        self.play(Transform(equation, new_equation))
        self.wait()
        
        # Add explanation
        explanation = Text(
            "Euler's Identity",
            font_size=36
        ).next_to(equation, DOWN)
        self.play(Write(explanation))
        self.wait()
`

	// Create the equation animation layer
	equationResult, err := manimTool.CreateManimLayer(equationCode, "MathEquation")
	if err != nil {
		log.Fatalf("Failed to create equation animation: %v", err)
	}
	fmt.Printf("Created equation animation layer: %+v\n", equationResult)

	// Example 3: Create a complex animation with multiple elements
	complexCode := `
from manim import *

class ComplexAnimation(Scene):
    def construct(self):
        # Create a circle
        circle = Circle(radius=2, color=BLUE)
        
        # Create a square
        square = Square(side_length=3, color=RED)
        
        # Create a triangle
        triangle = Triangle(color=GREEN)
        
        # Add shapes to the scene
        self.play(Create(circle))
        self.wait()
        
        # Transform circle to square
        self.play(Transform(circle, square))
        self.wait()
        
        # Transform square to triangle
        self.play(Transform(square, triangle))
        self.wait()
        
        # Add text
        text = Text("Shape Transformations", font_size=36)
        self.play(Write(text))
        self.wait()
`

	// Create the complex animation layer
	complexResult, err := manimTool.CreateManimLayer(complexCode, "ComplexAnimation")
	if err != nil {
		log.Fatalf("Failed to create complex animation: %v", err)
	}
	fmt.Printf("Created complex animation layer: %+v\n", complexResult)

	// Example 4: Update an existing layer
	fmt.Println("\nUpdating the rotating cube animation...")
	updatedCubeCode := `
from manim import *

class UpdatedCube(ThreeDScene):
    def construct(self):
        # Create a cube with different color
        cube = Cube(side_length=2, color=RED)
        
        # Add axes for reference
        axes = ThreeDAxes()
        
        # Add the cube and axes to the scene
        self.add(axes, cube)
        
        # More complex rotation sequence
        self.play(Rotate(cube, angle=2*PI, axis=UP), run_time=2)
        self.wait()
        self.play(Rotate(cube, angle=PI, axis=RIGHT), run_time=1)
        self.wait()
        self.play(Rotate(cube, angle=PI, axis=OUT), run_time=1)
        self.wait()
        self.play(Rotate(cube, angle=PI, axis=UP+RIGHT), run_time=1)
        self.wait()
`

	// Update the rotating cube layer
	updatedResult, err := manimTool.UpdateManimLayer(cubeResult.LayerID, updatedCubeCode, "UpdatedCube")
	if err != nil {
		log.Fatalf("Failed to update rotating cube: %v", err)
	}
	fmt.Printf("Updated rotating cube layer: %+v\n", updatedResult)

	// Get information about all created layers
	fmt.Println("\nLayer Information:")
	
	// Get cube layer info
	cubeInfo, err := manimTool.GetManimLayerInfo(cubeResult.LayerID)
	if err != nil {
		log.Printf("Failed to get cube layer info: %v", err)
	} else {
		fmt.Printf("Cube Layer: %+v\n", cubeInfo)
	}

	// Get equation layer info
	equationInfo, err := manimTool.GetManimLayerInfo(equationResult.LayerID)
	if err != nil {
		log.Printf("Failed to get equation layer info: %v", err)
	} else {
		fmt.Printf("Equation Layer: %+v\n", equationInfo)
	}

	// Get complex animation layer info
	complexInfo, err := manimTool.GetManimLayerInfo(complexResult.LayerID)
	if err != nil {
		log.Printf("Failed to get complex animation layer info: %v", err)
	} else {
		fmt.Printf("Complex Animation Layer: %+v\n", complexInfo)
	}
} 