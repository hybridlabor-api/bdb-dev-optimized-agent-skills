package main

import (
	"fmt"
	"log"
	"time"

	"github.com/sunqirui1987/ae-mcp/pkg/tools"
)

func main() {
	fmt.Println("Starting comprehensive After Effects demo...")

	// Create a composition to work with
	compName := "Comprehensive Demo"
	width := 1920
	height := 1080
	duration := 30.0
	frameRate := 30.0

	_, err := tools.CreateComposition(compName, width, height, duration, frameRate)
	if err != nil {
		log.Fatalf("Error creating composition: %v", err)
	}
	fmt.Printf("Created composition: %s\n", compName)

	// Add a background layer
	fmt.Println("\n=== Adding Background Layer ===")
	bgColor := tools.ColorRGB{0.05, 0.1, 0.2} // Dark blue-ish
	bgLayer, err := tools.AddSolidLayer(compName, "Background", bgColor, width, height, false)
	if err != nil {
		log.Fatalf("Error adding background layer: %v", err)
	}
	fmt.Printf("Added background layer: %s (Index: %v)\n", bgLayer["name"], bgLayer["index"])

	// Add a shape layer
	fmt.Println("\n=== Adding Shape Layers ===")
	
	// Custom Path Shape - 坐标以左上角(0,0)为原点
	vertices := []tools.ShapeVertex{
		{float64(50), float64(50)},   // 左上角顶点
		{float64(250), float64(50)},  // 右上角顶点
		{float64(250), float64(250)}, // 右下角顶点
		{float64(50), float64(250)},  // 左下角顶点
	}
	
	// Create shape data
	shapeData := tools.ShapeData{
		Vertices: vertices,
		Closed:   true,
	}
	
	// Add custom shape layer
	customShape, err := tools.AddShapeLayer(compName, "Custom Shape", shapeData)
	if err != nil {
		log.Fatalf("Error adding custom shape layer: %v", err)
	}
	fmt.Printf("Added custom shape layer: %s (Index: %v)\n", customShape["name"], customShape["index"])
	
	// Add a preset shape (rectangle)
	rectangleShape, err := tools.AddPresetShapeLayer(compName, "Rectangle Shape", "rectangle", 400, 300)
	if err != nil {
		log.Fatalf("Error adding rectangle shape layer: %v", err)
	}
	fmt.Printf("Added rectangle shape layer: %s (Index: %v)\n", rectangleShape["name"], rectangleShape["index"])
	
	// Add a preset shape (ellipse)
	ellipseShape, err := tools.AddPresetShapeLayer(compName, "Ellipse Shape", "ellipse", 200, 200)
	if err != nil {
		log.Fatalf("Error adding ellipse shape layer: %v", err)
	}
	fmt.Printf("Added ellipse shape layer: %s (Index: %v)\n", ellipseShape["name"], ellipseShape["index"])

	// Add a text layer
	fmt.Println("\n=== Adding Text Layer ===")
	textContent := "AE-MCP Demo"
	textLayer, err := tools.AddTextLayer(compName, "Title Text", textContent, nil)
	if err != nil {
		log.Fatalf("Error adding text layer: %v", err)
	}
	fmt.Printf("Added text layer: %s (Index: %v)\n", textLayer["name"], textLayer["index"])

	// Modify text properties
	textProps := map[string]interface{}{
		"fontSize": 72,
		"fillColor": tools.ColorRGB{1.0, 0.8, 0.2}, // Yellow-gold
		"position": []interface{}{float64(width) / 2, 200.0, 0.0},
		"justification": "CENTER",
	}
	_, err = tools.ModifyTextLayer(compName, "Title Text", textProps)
	if err != nil {
		log.Fatalf("Error modifying text layer: %v", err)
	}
	fmt.Println("Modified text layer properties")

	// Add a camera
	fmt.Println("\n=== Adding Camera Layer ===")
	cameraLayer, err := tools.AddCameraLayer(compName, "Main Camera", "Two-Node Camera")
	if err != nil {
		log.Fatalf("Error adding camera layer: %v", err)
	}
	fmt.Printf("Added camera layer: %s (Index: %v)\n", cameraLayer["name"], cameraLayer["index"])
	
	// Modify camera properties
	cameraOptions := map[string]interface{}{
		"position": []float64{960, 540, -1500},
		"pointOfInterest": []float64{960, 540, 0},
		"zoom": 1000, // Adjust as needed
		"depthOfField": true,
		"focusDistance": 1500,
		"aperture": 25,
	}
	modifiedCamera, err := tools.ModifyCameraProperties(compName, "Main Camera", cameraOptions)
	if err != nil {
		log.Fatalf("Error modifying camera properties: %v", err)
	}
	fmt.Printf("Modified camera properties: %s\n", modifiedCamera["name"])

	// Add light layers
	fmt.Println("\n=== Adding Light Layers ===")
	
	// Add spot light
	spotColor := [3]float64{1.0, 0.9, 0.8} // Warm white
	spotLight, err := tools.AddLightLayer(compName, "Spot Light", "Spot", spotColor)
	if err != nil {
		log.Fatalf("Error adding spot light: %v", err)
	}
	fmt.Printf("Added spot light: %s (Index: %v)\n", spotLight["name"], spotLight["index"])
	
	// Add point light
	pointColor := [3]float64{0.2, 0.4, 1.0} // Blue
	pointLight, err := tools.AddLightLayer(compName, "Point Light", "Point", pointColor)
	if err != nil {
		log.Fatalf("Error adding point light: %v", err)
	}
	fmt.Printf("Added point light: %s (Index: %v)\n", pointLight["name"], pointLight["index"])
	
	// Add ambient light
	ambientColor := [3]float64{0.5, 0.5, 0.5} // Gray
	ambientLight, err := tools.AddLightLayer(compName, "Ambient Light", "Ambient", ambientColor)
	if err != nil {
		log.Fatalf("Error adding ambient light: %v", err)
	}
	fmt.Printf("Added ambient light: %s (Index: %v)\n", ambientLight["name"], ambientLight["index"])

	// Enable 3D for shape layers
	fmt.Println("\n=== Making Layers 3D ===")
	
	// Make rectangle shape 3D
	rectLayerID := tools.LayerIdentifier{Name: "Rectangle Shape"}
	_, err = tools.ModifyLayer(compName, rectLayerID, map[string]interface{}{
		"threeDLayer": true,
		"position": []interface{}{float64(width)/2 - 300, float64(height)/2, 200.0},
	})
	if err != nil {
		log.Fatalf("Error making rectangle 3D: %v", err)
	}
	fmt.Println("Made rectangle layer 3D")
	
	// Make ellipse shape 3D
	ellipseLayerID := tools.LayerIdentifier{Name: "Ellipse Shape"}
	_, err = tools.ModifyLayer(compName, ellipseLayerID, map[string]interface{}{
		"threeDLayer": true,
		"position": []interface{}{float64(width)/2 + 300, float64(height)/2, 200.0},
	})
	if err != nil {
		log.Fatalf("Error making ellipse 3D: %v", err)
	}
	fmt.Println("Made ellipse layer 3D")

	// Apply effects to layers
	fmt.Println("\n=== Applying Effects ===")
	
	// Apply glow effect to text layer
	glowParams := tools.EffectParameters{
		"Glow Threshold": 50,
		"Glow Radius": 20,
		"Glow Intensity": 2,
	}
	glowEffect, err := tools.ApplyEffect(compName, "Title Text", "ADBE Glo2", glowParams)
	if err != nil {
		log.Fatalf("Error applying glow effect: %v", err)
	}
	fmt.Printf("Applied glow effect to text layer: %v\n", glowEffect["name"])
	
	// Apply color correction to ellipse
	colorParams := tools.EffectParameters{
		"Hue": 180,      // Adjust hue
		"Saturation": 50, // Increase saturation
	}
	colorEffect, err := tools.ApplyEffect(compName, "Ellipse Shape", "ADBE HUE SATURATION", colorParams)
	if err != nil {
		log.Fatalf("Error applying color effect: %v", err)
	}
	fmt.Printf("Applied color effect to ellipse: %v\n", colorEffect["name"])
	
	// Apply blur to rectangle
	blurParams := tools.EffectParameters{
		"Blurriness": 15,
	}
	blurEffect, err := tools.ApplyEffect(compName, "Rectangle Shape", "ADBE Gaussian Blur 2", blurParams)
	if err != nil {
		log.Fatalf("Error applying blur effect: %v", err)
	}
	fmt.Printf("Applied blur effect to rectangle: %v\n", blurEffect["name"])

	// Get layer information
	fmt.Println("\n=== Getting Layer Information ===")
	
	customShapeInfo, err := tools.GetLayerInfo(compName, tools.LayerIdentifier{Name: "Custom Shape"})
	if err != nil {
		log.Fatalf("Error getting custom shape info: %v", err)
	}
	fmt.Printf("Custom Shape Info: Type=%v, Enabled=%v\n", customShapeInfo["type"], customShapeInfo["enabled"])
	
	cameraInfo, err := tools.GetCameraLayerInfo(compName, "Main Camera")
	if err != nil {
		log.Fatalf("Error getting camera info: %v", err)
	}
	fmt.Printf("Camera Info: Type=%v, Zoom=%v\n", cameraInfo["cameraType"], cameraInfo["cameraOptions"].(map[string]interface{})["zoom"])

	// Wait a moment to make sure changes are applied
	time.Sleep(2 * time.Second)

	fmt.Println("\nComprehensive demo completed successfully!")
} 