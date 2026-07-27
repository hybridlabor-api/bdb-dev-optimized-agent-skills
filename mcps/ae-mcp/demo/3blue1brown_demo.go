package main

import (
	"fmt"
	"log"
	"os"
	"path/filepath"
	"strconv"
	"time"

	"github.com/sunqirui1987/ae-mcp/pkg/tools"
)

func main() {
	// Create a timestamped output directory for better organization
	timestamp := time.Now().Format("2006-01-02_15-04-05")
	baseOutputDir := filepath.Join("output", "3blue1brown_"+timestamp)
	
	// Create subdirectories for different outputs
	manimOutputDir := filepath.Join(baseOutputDir, "manim")
	videoOutputDir := filepath.Join(baseOutputDir, "video")
	
	// Create directories if they don't exist
	for _, dir := range []string{baseOutputDir, manimOutputDir, videoOutputDir} {
		err := os.MkdirAll(dir, 0755)
		if err != nil {
			log.Fatalf("Failed to create output directory %s: %v", dir, err)
		}
		fmt.Printf("Created output directory: %s\n", dir)
	}
	
	// Create Manim tool with the new output directory
	manimTool, err := tools.NewManimTool(manimOutputDir)
	if err != nil {
		log.Fatalf("Failed to create Manim tool: %v", err)
	}

	// Get project info first
	projectInfo, err := tools.GetProjectInfo()
	if err != nil {
		log.Fatalf("Failed to get project info: %v", err)
	}
	fmt.Printf("Project info: %+v\n", projectInfo)

	// Create a composition for the 3Blue1Brown video
	comp, err := tools.CreateComposition(
		"3Blue1Brown - Complex Functions", 
		1920,           // width
		1080,           // height
		180.0,          // duration (3 minutes)
		60.0,           // frameRate
	)
	if err != nil {
		log.Fatalf("Failed to create composition: %v", err)
	}
	fmt.Printf("Created composition: %s\n", comp["name"])
	compName := comp["name"].(string)

	// Create placeholder for layers
	type AnimationLayer struct {
		Name   string
		ID     int
		Error  error
	}
	layers := make([]AnimationLayer, 0, 4)
	
	// Helper function to create a manim layer with error handling
	createManimLayerSafe := func(code, name string) AnimationLayer {
		result, err := manimTool.CreateManimLayer(code, name)
		layer := AnimationLayer{Name: name}
		if err != nil {
			fmt.Printf("Warning: Failed to create %s animation: %v\n", name, err)
			layer.Error = err
			return layer
		}
		layerId, _ := strconv.Atoi(result.LayerID)
		layer.ID = layerId
		fmt.Printf("Created %s animation layer: %+v\n", name, result)
		return layer
	}

	// 1. Introduction with title animation
	introCode := `
from manim import *
import os
import platform
import subprocess

# Check if LaTeX is installed
def is_latex_installed():
    try:
        # Try to run a simple latex command to check if it's available
        if platform.system() == "Windows":
            subprocess.run(["where", "latex"], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        else:
            subprocess.run(["which", "latex"], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        return True
    except (subprocess.SubprocessError, FileNotFoundError):
        return False

# Set this config to avoid LaTeX if not installed
if not is_latex_installed():
    config.renderer = "opengl"
    config.text_mode = "pymobject"  # Use Python-based rendering

class Introduction(Scene):
    def construct(self):
        # Title with 3Blue1Brown style
        title = Text("Complex Functions", font_size=72)
        subtitle = Text("Visualizing the Beauty of Mathematics", font_size=48)
        subtitle.next_to(title, DOWN)
        
        # Group title and subtitle
        header = VGroup(title, subtitle)
        
        # Add 3Blue1Brown logo (a circle with color gradient)
        logo = Circle(radius=0.5, color=BLUE)
        logo.set_fill(BLUE, opacity=0.8)
        logo.next_to(header, UP, buff=0.5)
        
        # Animation sequence
        self.play(FadeIn(logo))
        self.wait(0.5)
        self.play(Write(title))
        self.wait(0.5)
        self.play(Write(subtitle))
        self.wait(2)
`
	introLayer := createManimLayerSafe(introCode, "Introduction")
	layers = append(layers, introLayer)

	// Add narration text for introduction
	introNarration := "Welcome to a journey into the fascinating world of complex functions. Today, we'll explore how these mathematical structures can be visualized and understood through geometry and color. Complex numbers and functions are not just abstract concepts, but have beautiful visual representations that help us see their underlying patterns."
	
	// Create text layer with narration
	applyFill := true
	introNarrationLayer, err := tools.AddTextLayer(
		compName,
		"Intro Narration", 
		introNarration, 
		&tools.TextOptions{
			FontName: "Arial",
			FontSize: 18,
			Color:    tools.ColorRGB{1.0, 1.0, 1.0}, // White
			Position: [2]float64{960, 800}, // Bottom center of the screen
			ApplyFill: &applyFill,
		},
	)
	if err != nil {
		log.Printf("Warning: Failed to add intro narration: %v", err)
	} else {
		// Set layer position using layer index
		introNarrationLayerIdx := introNarrationLayer["index"].(float64)
		_, err = tools.ModifyLayer(compName, tools.LayerIdentifier{Index: int(introNarrationLayerIdx)}, 
			tools.LayerProperties{
				"inPoint": 2.0, // Start after the logo appears
				"outPoint": 15.0, // End before the next section
			},
		)
		if err != nil {
			log.Printf("Warning: Failed to set narration timing: %v", err)
		}
	}

	// 2. Complex plane explanation
	complexPlaneCode := `
from manim import *
import os
import platform
import subprocess

# Check if LaTeX is installed
def is_latex_installed():
    try:
        # Try to run a simple latex command to check if it's available
        if platform.system() == "Windows":
            subprocess.run(["where", "latex"], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        else:
            subprocess.run(["which", "latex"], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        return True
    except (subprocess.SubprocessError, FileNotFoundError):
        return False

# Set this config to avoid LaTeX if not installed
if not is_latex_installed():
    config.renderer = "opengl"
    config.text_mode = "pymobject"  # Use Python-based rendering

class ComplexPlaneScene(Scene):
    def construct(self):
        # Create a simpler coordinate system without LaTeX labels
        axes = Axes(
            x_range=[-5, 5, 1],
            y_range=[-5, 5, 1],
            axis_config={
                "color": BLUE_D,
                "stroke_width": 2,
                "stroke_opacity": 0.6,
                "include_numbers": True
            }
        )
        
        # Explanatory text
        title = Text("The Complex Plane", font_size=60)
        title.to_edge(UP)
        
        # Explanation text
        explanation = Text(
            "Complex numbers have a real part and an imaginary part",
            font_size=36
        )
        explanation.next_to(title, DOWN)
        
        # Example point
        point = Dot(axes.c2p(3, 2), color=YELLOW)
        point_coords = Text("3 + 2i", font_size=36)
        point_coords.next_to(point, UP+RIGHT, buff=0.1)
        
        # Draw arrows for the complex number components
        x_arrow = Arrow(
            axes.c2p(0, 0), axes.c2p(3, 0), 
            buff=0, color=GREEN
        )
        y_arrow = Arrow(
            axes.c2p(3, 0), axes.c2p(3, 2), 
            buff=0, color=RED
        )
        
        x_label = Text("3", font_size=36, color=GREEN)
        x_label.next_to(x_arrow, DOWN, buff=0.1)
        
        y_label = Text("2i", font_size=36, color=RED)
        y_label.next_to(y_arrow, RIGHT, buff=0.1)
        
        # Add labels for real and imaginary axes
        real_label = Text("Real axis", font_size=36)
        real_label.next_to(axes.x_axis, DOWN, buff=0.2)
        imag_label = Text("Imaginary axis", font_size=36)
        imag_label.next_to(axes.y_axis, LEFT, buff=0.2).rotate(90 * DEGREES)
        
        # Animation sequence
        self.play(Write(title))
        self.wait(0.5)
        self.play(Create(axes))
        self.wait(0.5)
        self.play(Write(real_label), Write(imag_label))
        self.wait(0.5)
        self.play(Write(explanation))
        self.wait(1)
        self.play(FadeOut(explanation))
        
        # Show the example point
        self.play(Create(point))
        self.play(Write(point_coords))
        self.wait(0.5)
        
        # Show the components
        self.play(Create(x_arrow), Write(x_label))
        self.wait(0.5)
        self.play(Create(y_arrow), Write(y_label))
        self.wait(2)
`
	complexPlaneLayer := createManimLayerSafe(complexPlaneCode, "ComplexPlaneScene")
	layers = append(layers, complexPlaneLayer)

	// Add narration for complex plane
	complexPlaneNarration := "Let's begin by understanding the complex plane. In this two-dimensional space, we represent complex numbers with both real and imaginary components. The horizontal axis represents the real part, while the vertical axis represents the imaginary part. Each point on this plane corresponds to a complex number of the form a + bi. For example, the point at coordinates (3, 2) represents the complex number 3 + 2i. This geometric representation allows us to visualize complex numbers as vectors with magnitude and direction."
	
	complexPlaneNarrationLayer, err := tools.AddTextLayer(
		compName,
		"Complex Plane Narration", 
		complexPlaneNarration, 
		&tools.TextOptions{
			FontName: "Arial",
			FontSize: 18,
			Color:    tools.ColorRGB{1.0, 1.0, 1.0},
			Position: [2]float64{960, 800},
			ApplyFill: &applyFill,
		},
	)
	if err != nil {
		log.Printf("Warning: Failed to add complex plane narration: %v", err)
	} else {
		complexPlaneNarrationLayerIdx := complexPlaneNarrationLayer["index"].(float64)
		_, err = tools.ModifyLayer(compName, tools.LayerIdentifier{Index: int(complexPlaneNarrationLayerIdx)}, 
			tools.LayerProperties{
				"inPoint": 16.0, // Start after transition
				"outPoint": 44.0, // End before the next section
			},
		)
		if err != nil {
			log.Printf("Warning: Failed to set narration timing: %v", err)
		}
	}

	// 3. Function transformation visualization
	transformationCode := `
from manim import *
import os
import platform
import subprocess

# Check if LaTeX is installed
def is_latex_installed():
    try:
        # Try to run a simple latex command to check if it's available
        if platform.system() == "Windows":
            subprocess.run(["where", "latex"], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        else:
            subprocess.run(["which", "latex"], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        return True
    except (subprocess.SubprocessError, FileNotFoundError):
        return False

# Set this config to avoid LaTeX if not installed
if not is_latex_installed():
    config.renderer = "opengl"
    config.text_mode = "pymobject"  # Use Python-based rendering

class ComplexTransformation(Scene):
    def construct(self):
        # Create axes for original plane
        axes = Axes(
            x_range=[-5, 5, 1],
            y_range=[-5, 5, 1],
            axis_config={
                "color": BLUE_D,
                "stroke_width": 2,
                "stroke_opacity": 0.6,
                "include_numbers": True
            }
        )
        
        # Create axes for transformed plane
        transformed_axes = Axes(
            x_range=[-5, 5, 1],
            y_range=[-5, 5, 1],
            axis_config={
                "color": GREEN_D,
                "stroke_width": 2,
                "stroke_opacity": 0.6,
                "include_numbers": True
            }
        )
        
        # Title
        title = Text("Complex Function: f(z) = z²", font_size=60)
        title.to_edge(UP)
        
        # Create a grid of points
        dots = VGroup()
        transformed_dots = VGroup()
        
        vectors = VGroup()
        transformed_vectors = VGroup()
        
        # Create dots and vectors for the grid
        for x in np.arange(-2, 2.1, 0.5):
            for y in np.arange(-2, 2.1, 0.5):
                # Original point
                dot = Dot(axes.c2p(x, y), color=BLUE, radius=0.05)
                dots.add(dot)
                
                # Calculate transformed point (z²)
                # z² = (x + yi)² = (x² - y²) + (2xy)i
                tx = x*x - y*y
                ty = 2*x*y
                transformed_dot = Dot(
                    transformed_axes.c2p(tx, ty), 
                    color=YELLOW, 
                    radius=0.05
                )
                transformed_dots.add(transformed_dot)
                
                # Draw vectors
                vector = Arrow(
                    axes.c2p(0, 0), 
                    axes.c2p(x, y), 
                    buff=0, 
                    color=BLUE_A, 
                    stroke_width=2
                )
                vectors.add(vector)
                
                transformed_vector = Arrow(
                    transformed_axes.c2p(0, 0), 
                    transformed_axes.c2p(tx, ty), 
                    buff=0, 
                    color=YELLOW_A, 
                    stroke_width=2
                )
                transformed_vectors.add(transformed_vector)
        
        # Animation sequence
        self.play(Write(title))
        self.play(Create(axes))
        self.wait(0.5)
        
        # Add labels
        input_label = Text("Input plane (z)", font_size=36)
        input_label.next_to(axes, DOWN)
        self.play(Write(input_label))
        
        # Show the grid of points
        self.play(Create(vectors, lag_ratio=0.05))
        self.play(Create(dots))
        self.wait(1)
        
        # Transform to z²
        transformed_axes.next_to(axes, RIGHT, buff=1)
        self.play(
            Create(transformed_axes),
            run_time=2
        )
        
        # Add output label
        output_label = Text("Output plane (z²)", font_size=36)
        output_label.next_to(transformed_axes, DOWN)
        self.play(Write(output_label))
        
        # Show transformation
        self.play(
            Create(transformed_vectors, lag_ratio=0.05),
            run_time=3
        )
        self.play(
            Create(transformed_dots),
            run_time=2
        )
        self.wait(2)
        
        # Add explanation
        explanation = Text(
            "Notice how angles double and distances square",
            font_size=36
        )
        explanation.to_edge(DOWN)
        self.play(Write(explanation))
        self.wait(3)
`
	transformationLayer := createManimLayerSafe(transformationCode, "ComplexTransformation")
	layers = append(layers, transformationLayer)

	// Add narration for transformation
	transformationNarration := "When we apply functions to complex numbers, we can visualize them as transformations of the complex plane. Let's consider the function f(z) = z². This squares each complex number. Geometrically, we can see how points in the plane move under this transformation. Notice that circles centered at the origin become stretched into ellipses, and straight lines through the origin get mapped to parabolas. The transformation doubles angles and squares distances from the origin. This visual approach gives us deep insights into how complex functions behave, revealing patterns that equations alone might obscure."
	
	transformationNarrationLayer, err := tools.AddTextLayer(
		compName,
		"Transformation Narration", 
		transformationNarration, 
		&tools.TextOptions{
			FontName: "Arial",
			FontSize: 18,
			Color:    tools.ColorRGB{1.0, 1.0, 1.0},
			Position: [2]float64{960, 800},
			ApplyFill: &applyFill,
		},
	)
	if err != nil {
		log.Printf("Warning: Failed to add transformation narration: %v", err)
	} else {
		transformationNarrationLayerIdx := transformationNarrationLayer["index"].(float64)
		_, err = tools.ModifyLayer(compName, tools.LayerIdentifier{Index: int(transformationNarrationLayerIdx)}, 
			tools.LayerProperties{
				"inPoint": 46.0, // Start after transition
				"outPoint": 74.0, // End before the next section
			},
		)
		if err != nil {
			log.Printf("Warning: Failed to set narration timing: %v", err)
		}
	}

	// 4. Euler's formula visualization
	eulersFormulaCode := `
from manim import *
import os
import platform
import subprocess
import numpy as np

# Check if LaTeX is installed
def is_latex_installed():
    try:
        # Try to run a simple latex command to check if it's available
        if platform.system() == "Windows":
            subprocess.run(["where", "latex"], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        else:
            subprocess.run(["which", "latex"], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        return True
    except (subprocess.SubprocessError, FileNotFoundError):
        return False

# Set this config to avoid LaTeX if not installed
if not is_latex_installed():
    config.renderer = "opengl"
    config.text_mode = "pymobject"  # Use Python-based rendering

class EulersFormula(Scene):
    def construct(self):
        # Title
        title = Text("Euler's Formula", font_size=60)
        title.to_edge(UP)
        
        # Create the equation as Text instead of MathTex
        euler_eq = Text(
            "e^(iθ) = cos(θ) + i·sin(θ)",
            font_size=48
        )
        
        # Create a simple coordinate system
        axes = Axes(
            x_range=[-1.5, 1.5, 0.5],
            y_range=[-1.5, 1.5, 0.5],
            axis_config={
                "color": BLUE_D,
                "stroke_width": 2,
                "stroke_opacity": 0.6,
                "include_numbers": True
            }
        ).scale(2)
        
        # Create a unit circle
        circle = Circle(radius=2, color=YELLOW)
        
        # Create a dot that moves around the circle
        dot = Dot(axes.c2p(1, 0), color=RED)
        
        # Create a line from origin to the dot
        line = Line(
            axes.c2p(0, 0), 
            dot.get_center(), 
            color=RED
        )
        
        # Create labels for real and imaginary parts
        cos_label = Text("cos(θ)", font_size=36, color=GREEN)
        sin_label = Text("i·sin(θ)", font_size=36, color=BLUE)
        
        # Create angle label
        angle = Arc(
            start_angle=0,
            angle=0,
            radius=0.5,
            color=WHITE
        ).shift(axes.c2p(0, 0))
        angle_label = Text("θ", font_size=36)
        angle_label.move_to(axes.c2p(0, 0) + 0.7*RIGHT + 0.3*UP)
        
        # Animations
        self.play(Write(title))
        self.wait(0.5)
        self.play(Write(euler_eq))
        self.wait(1)
        
        # Move equation up to make room for visualization
        self.play(euler_eq.animate.next_to(title, DOWN))
        
        # Show the complex plane and unit circle
        self.play(Create(axes))
        self.play(Create(circle))
        self.wait(0.5)
        
        # Show the point and connecting line
        self.play(Create(dot), Create(line))
        self.play(Create(angle), Write(angle_label))
        
        # Add horizontal and vertical components
        x_line = DashedLine(
            dot.get_center(),
            axes.c2p(np.cos(0), 0, 0),
            color=GREEN
        )
        y_line = DashedLine(
            dot.get_center(),
            axes.c2p(np.cos(0), 0, 0),
            color=BLUE
        )
        
        cos_label.next_to(x_line, DOWN)
        sin_label.next_to(y_line, RIGHT)
        
        self.play(
            Create(x_line),
            Create(y_line),
            Write(cos_label),
            Write(sin_label)
        )
        
        # Add axis labels
        x_axis_label = Text("Real", font_size=36)
        x_axis_label.next_to(axes.x_axis, DOWN, buff=0.2)
        y_axis_label = Text("Imaginary", font_size=36)
        y_axis_label.next_to(axes.y_axis, LEFT, buff=0.2).rotate(90 * DEGREES)
        
        self.play(Write(x_axis_label), Write(y_axis_label))
        
        # Animate the point moving around the circle
        def update_point(mob, alpha):
            theta = 2 * PI * alpha
            new_point = axes.c2p(np.cos(theta), np.sin(theta))
            mob.move_to(new_point)
            return mob
            
        def update_line(mob):
            start = axes.c2p(0, 0)
            end = dot.get_center()
            mob.put_start_and_end_on(start, end)
            return mob
            
        def update_x_line(mob):
            start = dot.get_center()
            end = axes.c2p(np.cos(angle.angle), 0, 0)
            mob.put_start_and_end_on(start, end)
            return mob
            
        def update_y_line(mob):
            start = dot.get_center()
            end = axes.c2p(np.cos(angle.angle), 0, 0)
            mob.put_start_and_end_on(end, start)
            return mob
            
        def update_angle(mob, alpha):
            theta = 2 * PI * alpha
            mob.become(
                Arc(
                    start_angle=0,
                    angle=theta,
                    radius=0.5,
                    color=WHITE
                ).shift(axes.c2p(0, 0))
            )
            return mob
            
        def update_angle_label(mob, alpha):
            theta = 2 * PI * alpha
            mob.move_to(
                axes.c2p(0, 0) + 0.7 * np.cos(theta/2) * RIGHT + 
                0.7 * np.sin(theta/2) * UP
            )
            return mob
            
        def update_cos_label(mob):
            mob.next_to(x_line, DOWN)
            return mob
            
        def update_sin_label(mob):
            mob.next_to(y_line, RIGHT)
            return mob
        
        self.play(
            UpdateFromAlphaFunc(dot, update_point),
            UpdateFromFunc(line, update_line),
            UpdateFromFunc(x_line, update_x_line),
            UpdateFromFunc(y_line, update_y_line),
            UpdateFromAlphaFunc(angle, update_angle),
            UpdateFromAlphaFunc(angle_label, update_angle_label),
            UpdateFromFunc(cos_label, update_cos_label),
            UpdateFromFunc(sin_label, update_sin_label),
            run_time=8,
            rate_func=linear
        )
        
        self.wait(2)
`
	eulersLayer := createManimLayerSafe(eulersFormulaCode, "EulersFormula")
	layers = append(layers, eulersLayer)

	// Add narration for Euler's formula
	eulersNarration := "One of the most elegant relationships in mathematics is Euler's formula: e to the power of i theta equals cosine theta plus i sine theta. This formula connects exponential functions with trigonometric functions through complex numbers. Geometrically, e raised to the power of i theta traces out the unit circle in the complex plane as theta varies. The real part follows the cosine function, while the imaginary part follows the sine function. This remarkable relationship is the foundation of many advanced concepts in mathematics, physics, and engineering, elegantly demonstrating how complex numbers unify seemingly disparate mathematical ideas."
	
	eulersNarrationLayer, err := tools.AddTextLayer(
		compName,
		"Euler's Formula Narration", 
		eulersNarration, 
		&tools.TextOptions{
			FontName: "Arial",
			FontSize: 18,
			Color:    tools.ColorRGB{1.0, 1.0, 1.0},
			Position: [2]float64{960, 800},
			ApplyFill: &applyFill,
		},
	)
	if err != nil {
		log.Printf("Warning: Failed to add Euler's formula narration: %v", err)
	} else {
		eulersNarrationLayerIdx := eulersNarrationLayer["index"].(float64)
		_, err = tools.ModifyLayer(compName, tools.LayerIdentifier{Index: int(eulersNarrationLayerIdx)}, 
			tools.LayerProperties{
				"inPoint": 76.0, // Start after transition
				"outPoint": 104.0, // End before the next section
			},
		)
		if err != nil {
			log.Printf("Warning: Failed to set narration timing: %v", err)
		}
	}

	// Configure the layering and transitions in After Effects
	// Set layer position in the timeline for Manim layers
	
	// Set animation layer timing, skipping any that failed to generate
	timings := []struct{
		start float64
		end float64
	}{
		{0.0, 15.0},    // Introduction
		{15.0, 45.0},   // Complex Plane
		{45.0, 75.0},   // Transformation
		{75.0, 105.0},  // Euler's Formula
	}
	
	for i, layer := range layers {
		if layer.Error != nil {
			fmt.Printf("Skipping timeline setting for %s due to previous error\n", layer.Name)
			continue
		}
		
		_, err = tools.ModifyLayer(compName, tools.LayerIdentifier{Index: layer.ID}, 
			tools.LayerProperties{
				"inPoint": timings[i].start,
				"outPoint": timings[i].end,
			},
		)
		if err != nil {
			log.Printf("Warning: Failed to set %s layer properties: %v", layer.Name, err)
		}
	}
	
	// Additional layer for a simple background with the 3Blue1Brown style
	backgroundColor := tools.ColorRGB{0.1, 0.1, 0.1} // Dark background typical of 3Blue1Brown videos
	bgLayer, err := tools.AddSolidLayer(compName, "Background", backgroundColor, 1920, 1080, false)
	if err != nil {
		log.Printf("Warning: Failed to add background layer: %v", err)
	} else {
		// Put background at the bottom of the layer stack
		bgLayerIdx := int(bgLayer["index"].(float64))
		_, err = tools.ModifyLayer(compName, tools.LayerIdentifier{Index: bgLayerIdx}, 
			tools.LayerProperties{
				"inPoint": 0.0,
				"outPoint": 180.0, // Full video duration
			},
		)
		if err != nil {
			log.Printf("Warning: Failed to set background layer properties: %v", err)
		}
	}
	
	// Add fallback text for any failed animations
	for i, layer := range layers {
		if layer.Error == nil {
			continue
		}
		
		fallbackText := fmt.Sprintf("[Animation for %s could not be generated]", layer.Name)
		fallbackLayer, err := tools.AddTextLayer(
			compName,
			fmt.Sprintf("Fallback for %s", layer.Name),
			fallbackText,
			&tools.TextOptions{
				FontName: "Arial",
				FontSize: 36,
				Color:    tools.ColorRGB{1.0, 1.0, 1.0},
				Position: [2]float64{960, 540}, // Center of screen
				ApplyFill: &applyFill,
			},
		)
		if err != nil {
			log.Printf("Warning: Failed to add fallback text for %s: %v", layer.Name, err)
			continue
		}
		
		fallbackIdx := int(fallbackLayer["index"].(float64))
		_, err = tools.ModifyLayer(compName, tools.LayerIdentifier{Index: fallbackIdx}, 
			tools.LayerProperties{
				"inPoint": timings[i].start,
				"outPoint": timings[i].end,
			},
		)
		if err != nil {
			log.Printf("Warning: Failed to set fallback layer properties: %v", err)
		}
	}
	
	fmt.Println("\nCompleted creating 3Blue1Brown style video with narration!")
	fmt.Println("Output directory: " + baseOutputDir)
	fmt.Println("The composition is ready in After Effects.")
	fmt.Println("\nNOTE: If you encountered any LaTeX-related errors, the script attempted to work around")
	fmt.Println("these by using simpler text rendering. To fix this permanently, please install LaTeX")
	fmt.Println("(e.g., MiKTeX or TeX Live) and ensure it's in your system PATH.")
}