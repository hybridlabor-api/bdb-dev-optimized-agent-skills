package main

import (
	"fmt"
	"log"

	"github.com/sunqirui1987/ae-mcp/pkg/tools"
)

// LayersDemo demonstrates creating and working with different types of layers
// in After Effects, including solid layers, text layers, and shape layers
func main() {
	fmt.Println("Starting layers demo...")

	// Create a composition to work with
	compName := "Layers Demo"
	width := 1920
	height := 1080
	duration := 15.0
	frameRate := 30.0

	_, err := tools.CreateComposition(compName, width, height, duration, frameRate)
	if err != nil {
		log.Fatalf("Error creating composition: %v", err)
	}
	fmt.Printf("Created composition: %s\n", compName)

	// Add a solid color background layer
	bgColor := tools.ColorRGB{0.1, 0.1, 0.3} // Dark blue
	bgLayer, err := tools.AddSolidLayer(compName, "Background", bgColor, width, height, false)
	if err != nil {
		log.Fatalf("Error adding background layer: %v", err)
	}
	fmt.Printf("Added background layer: %s (ID: %v)\n", bgLayer["name"], bgLayer["id"])

	// Add a text layer
	textContent := "Welcome to After Effects!"
	textLayer, err := tools.AddTextLayer(compName, "Title Text", textContent, nil)
	if err != nil {
		log.Fatalf("Error adding text layer: %v", err)
	}
	fmt.Printf("Added text layer: %s (ID: %v)\n", textLayer["name"], textLayer["id"])

	// Modify text properties
	textProps := map[string]interface{}{
		"fontSize": 72,
		"fillColor": tools.ColorRGB{1.0, 0.8, 0.2}, // Yellow-gold
		"position": []interface{}{float64(width) / 2, float64(height) / 3, 0.0}, // Center horizontally, upper third vertically
		"justification": "CENTER",
	}
	_, err = tools.ModifyTextLayer(compName, "Title Text", textProps)
	if err != nil {
		log.Fatalf("Error modifying text layer: %v", err)
	}
	fmt.Println("Modified text layer properties")

	// Instead of using shape layer, we'll create another solid layer 
	// and modify it to look like a rectangle
	rectLayer, err := tools.AddSolidLayer(compName, "Rectangle Shape", 
		tools.ColorRGB{0.2, 0.8, 0.4}, // Green
		400, 200, false)
	if err != nil {
		log.Fatalf("Error adding rectangle layer: %v", err)
	}
	
	// Position the rectangle
	rectLayerID := tools.LayerIdentifier{Name: "Rectangle Shape"}
	_, err = tools.ModifyLayer(compName, rectLayerID, map[string]interface{}{
		"position": []interface{}{float64(width) / 2, float64(height) * 2 / 3, 0.0},
		"borderColor": tools.ColorRGB{1.0, 1.0, 1.0}, // White border
		"borderWidth": 5,
	})
	if err != nil {
		log.Fatalf("Error modifying rectangle layer: %v", err)
	}
	fmt.Printf("Added rectangle layer: %s (ID: %v)\n", rectLayer["name"], rectLayer["id"])

	// Modify layer properties (e.g. opacity)
	bgLayerID := tools.LayerIdentifier{Name: "Background"}
	_, err = tools.ModifyLayer(compName, bgLayerID, map[string]interface{}{
		"opacity": 90, // 90% opacity
	})
	if err != nil {
		log.Fatalf("Error modifying layer opacity: %v", err)
	}
	fmt.Println("Modified background layer opacity")

	fmt.Println("Layers demo completed successfully!")
} 