package main

import (
	"fmt"
	"log"

	"github.com/sunqirui1987/ae-mcp/pkg/tools"
)

// TextAnimationDemo demonstrates text creation and styling
// for typography in After Effects
func main() {
	fmt.Println("Starting simplified text demo...")

	// Create a composition
	compName := "Typography Demo"
	width := 1920
	height := 1080
	duration := 10.0 // 10 seconds
	frameRate := 30.0

	_, err := tools.CreateComposition(compName, width, height, duration, frameRate)
	if err != nil {
		log.Fatalf("Error creating composition: %v", err)
	}
	fmt.Printf("Created composition: %s\n", compName)

	// Add a dark background
	bgColor := tools.ColorRGB{0.12, 0.12, 0.15} // Dark bluish-gray
	_, err = tools.AddSolidLayer(compName, "Background", bgColor, width, height, false)
	if err != nil {
		log.Fatalf("Error adding background layer: %v", err)
	}
	fmt.Println("Added background layer")

	// Add a fractal noise effect to the background
	noiseParams := tools.EffectParameters{
		"Contrast": 120.0,
		"Brightness": -20.0,
		"Scale": 200.0,
		"Opacity": 15.0,
	}
	_, err = tools.ApplyEffect(compName, "Background", "ADBE Fractal Noise", noiseParams)
	if err != nil {
		log.Fatalf("Error applying fractal noise effect: %v", err)
	}
	fmt.Println("Added texture to background")

	// 1. Create a main headline text
	mainText := "TYPOGRAPHY"
	_, err = tools.AddTextLayer(compName, "Main Headline", mainText, nil)
	if err != nil {
		log.Fatalf("Error adding headline layer: %v", err)
	}

	// Customize text appearance
	headlineProps := map[string]interface{}{
		"fontSize": 120.0,
		"fontFamily": "Arial",
		"fauxBold": true,
		"fillColor": tools.ColorRGB{1.0, 1.0, 1.0}, // White
		"justification": "CENTER",
		"tracking": 50.0, // Wide letter spacing
	}
	_, err = tools.ModifyTextLayer(compName, "Main Headline", headlineProps)
	if err != nil {
		log.Fatalf("Error setting headline properties: %v", err)
	}
	
	// Position the headline using ModifyLayer
	headlineLayerID := tools.LayerIdentifier{Name: "Main Headline"}
	_, err = tools.ModifyLayer(compName, headlineLayerID, map[string]interface{}{
		"position": []interface{}{float64(width) / 2, float64(height) / 2 - 100.0, 0.0},
	})
	if err != nil {
		log.Fatalf("Error positioning headline: %v", err)
	}
	fmt.Println("Added main headline")

	// 2. Add a subtitle
	_, err = tools.AddTextLayer(compName, "Subtitle", "IN MOTION", nil)
	if err != nil {
		log.Fatalf("Error adding subtitle layer: %v", err)
	}

	// Customize subtitle appearance
	subtitleProps := map[string]interface{}{
		"fontSize": 60.0,
		"fontFamily": "Arial",
		"fillColor": tools.ColorRGB{0.8, 0.8, 0.8}, // Light gray
		"justification": "CENTER",
		"tracking": 300.0, // Very wide letter spacing
	}
	_, err = tools.ModifyTextLayer(compName, "Subtitle", subtitleProps)
	if err != nil {
		log.Fatalf("Error setting subtitle properties: %v", err)
	}
	
	// Position the subtitle
	subtitleLayerID := tools.LayerIdentifier{Name: "Subtitle"}
	_, err = tools.ModifyLayer(compName, subtitleLayerID, map[string]interface{}{
		"position": []interface{}{float64(width) / 2, float64(height) / 2 + 50.0, 0.0},
		"opacity": 85.0, // Slightly transparent
	})
	if err != nil {
		log.Fatalf("Error positioning subtitle: %v", err)
	}
	fmt.Println("Added subtitle")

	// 3. Add a quote text
	_, err = tools.AddTextLayer(compName, "Quote", "DESIGN IS THINKING MADE VISUAL", nil)
	if err != nil {
		log.Fatalf("Error adding quote layer: %v", err)
	}

	// Customize quote appearance
	quoteProps := map[string]interface{}{
		"fontSize": 36.0,
		"fontFamily": "Arial",
		"fauxItalic": true,
		"fillColor": tools.ColorRGB{0.9, 0.9, 0.2}, // Yellow
		"justification": "CENTER",
	}
	_, err = tools.ModifyTextLayer(compName, "Quote", quoteProps)
	if err != nil {
		log.Fatalf("Error setting quote properties: %v", err)
	}
	
	// Position the quote
	quoteLayerID := tools.LayerIdentifier{Name: "Quote"}
	_, err = tools.ModifyLayer(compName, quoteLayerID, map[string]interface{}{
		"position": []interface{}{float64(width) / 2, float64(height) / 2 + 200.0, 0.0},
	})
	if err != nil {
		log.Fatalf("Error positioning quote: %v", err)
	}
	fmt.Println("Added quote")

	// 4. Add a stylized number
	_, err = tools.AddTextLayer(compName, "Number", "3", nil)
	if err != nil {
		log.Fatalf("Error adding number layer: %v", err)
	}

	// Customize number appearance
	countdownProps := map[string]interface{}{
		"fontSize": 200.0,
		"fontFamily": "Impact",
		"fillColor": tools.ColorRGB{1.0, 0.3, 0.1}, // Red-orange
		"justification": "CENTER",
	}
	_, err = tools.ModifyTextLayer(compName, "Number", countdownProps)
	if err != nil {
		log.Fatalf("Error setting number properties: %v", err)
	}
	
	// Position the number and make it semi-transparent
	numberLayerID := tools.LayerIdentifier{Name: "Number"}
	_, err = tools.ModifyLayer(compName, numberLayerID, map[string]interface{}{
		"position": []interface{}{float64(width) / 2, float64(height) / 2, 0.0},
		"opacity": 50.0, // Half transparent
		"scale": []interface{}{120.0, 120.0, 100.0}, // Scale up a bit
	})
	if err != nil {
		log.Fatalf("Error positioning number: %v", err)
	}
	fmt.Println("Added stylized number")

	// 5. Add a glow effect to the main headline
	glowParams := tools.EffectParameters{
		"Glow Threshold": 50.0,
		"Glow Radius": 25.0,
		"Glow Intensity": 2.0,
		"Glow Color": []interface{}{0.0, 0.7, 1.0}, // Cyan
	}
	_, err = tools.ApplyEffect(compName, "Main Headline", "ADBE Glo2", glowParams)
	if err != nil {
		log.Fatalf("Error applying glow effect: %v", err)
	}
	fmt.Println("Added glow effect to headline")

	fmt.Println("Text demo completed successfully!")
} 