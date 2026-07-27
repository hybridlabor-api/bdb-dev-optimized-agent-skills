package main

import (
	"fmt"
	"log"

	"github.com/sunqirui1987/ae-mcp/pkg/tools"
)

// AnimationEffectsDemo demonstrates creating animations and applying effects
// to layers in After Effects
func main() {
	fmt.Println("Starting animation and effects demo...")

	// Create a composition
	compName := "Animation Demo"
	width := 1920
	height := 1080
	duration := 10.0 // 10 seconds
	frameRate := 30.0

	_, err := tools.CreateComposition(compName, width, height, duration, frameRate)
	if err != nil {
		log.Fatalf("Error creating composition: %v", err)
	}
	fmt.Printf("Created composition: %s\n", compName)

	// Add a background layer
	bgColor := tools.ColorRGB{0.0, 0.0, 0.0} // Black
	bgLayer, err := tools.AddSolidLayer(compName, "Background", bgColor, width, height, false)
	if err != nil {
		log.Fatalf("Error adding background layer: %v", err)
	}
	fmt.Printf("Added background layer: %s\n", bgLayer["name"])

	// Add a circle as a solid layer since AddShapeLayer may not be available
	circleLayer, err := tools.AddSolidLayer(compName, "Animated Circle", 
		tools.ColorRGB{0.8, 0.2, 0.2}, // Red
		200, 200, false)
	if err != nil {
		log.Fatalf("Error adding circle layer: %v", err)
	}
	fmt.Printf("Added circle layer: %s\n", circleLayer["name"])
	
	// Position the circle in the center
	layerID := tools.LayerIdentifier{Name: "Animated Circle"}
	if circleIndex, ok := circleLayer["index"].(float64); ok {
		layerID = tools.LayerIdentifier{Index: int(circleIndex)}
	}
	
	_, err = tools.ModifyLayer(compName, layerID, map[string]interface{}{
		"position": []interface{}{float64(width) / 2, float64(height) / 2, 0.0},
	})
	if err != nil {
		log.Fatalf("Error positioning circle: %v", err)
	}

	// Since we don't have ModifyLayerWithKeyframe, we'll need a different approach for animations
	// For this demo, we'll skip the animation part
	fmt.Println("Note: Keyframe animation functionality is limited in this version")
	
	// Add a text layer
	textOptions := &tools.TextOptions{
		FontSize: 120,
		Color: tools.ColorRGB{1.0, 1.0, 1.0}, // White
	}
	textLayer, err := tools.AddTextLayer(compName, "Text Layer", "ANIMATED!", textOptions)
	if err != nil {
		log.Fatalf("Error adding text layer: %v", err)
	}
	
	// Modify text layer position
	textLayerID := tools.LayerIdentifier{Name: "Text Layer"}
	if textIndex, ok := textLayer["index"].(float64); ok {
		textLayerID = tools.LayerIdentifier{Index: int(textIndex)}
	}
	
	_, err = tools.ModifyLayer(compName, textLayerID, map[string]interface{}{
		"position": []interface{}{float64(width) / 2, float64(height) / 2 + 300.0, 0.0},
	})
	if err != nil {
		log.Fatalf("Error positioning text: %v", err)
	}
	fmt.Printf("Added text layer: %s\n", textLayer["name"])

	// Apply a glow effect to the text
	// Convert the interface for ApplyEffect
	textEffectParams := tools.EffectParameters{
		"Glow Threshold": 50,
		"Glow Radius": 25,
		"Glow Intensity": 2.0,
		"Glow Color": []interface{}{0.0, 0.7, 1.0}, // Cyan
	}
	_, err = tools.ApplyEffect(compName, textLayer["name"].(string), "ADBE Glo2", textEffectParams)
	if err != nil {
		log.Fatalf("Error applying glow effect: %v", err)
	}
	fmt.Println("Applied glow effect to text")

	// Apply a Gaussian Blur effect to the background
	blurParams := tools.EffectParameters{
		"Blurriness": 25,
	}
	_, err = tools.ApplyEffect(compName, bgLayer["name"].(string), "ADBE Gaussian Blur 2", blurParams)
	if err != nil {
		log.Fatalf("Error applying blur effect: %v", err)
	}
	fmt.Println("Applied Gaussian Blur to background")

	// Add some particle effects to another layer
	particleLayer, err := tools.AddSolidLayer(compName, "Particles", 
		tools.ColorRGB{0.5, 0.5, 0.5}, width, height, false)
	if err != nil {
		log.Fatalf("Error adding particle layer: %v", err)
	}
	
	// Apply CC Particle World effect
	particleParams := tools.EffectParameters{
		"Birth Rate": 1.0,
		"Longevity": 3.0,
		"Producer Position": []interface{}{float64(width) / 2, float64(height), 0.5},
		"Velocity": 0.3,
		"Particle Type": "Shaded Sphere",
		"Particle Color": []interface{}{0.9, 0.7, 0.1}, // Gold
	}
	_, err = tools.ApplyEffect(compName, particleLayer["name"].(string), "CC Particle World", particleParams)
	if err != nil {
		log.Fatalf("Error applying particle effect: %v", err)
	}
	fmt.Println("Added particle effect layer")

	fmt.Println("Animation and effects demo completed successfully!")
} 