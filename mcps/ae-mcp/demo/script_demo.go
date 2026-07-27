package main

import (
	"fmt"
	"log"

	"github.com/sunqirui1987/ae-mcp/pkg/tools"
)

func main() {
	fmt.Println("Starting After Effects script execution demo...")

	// Simple script to get project info
	simpleScript := `
		var project = app.project;
		return {
			name: project.file ? project.file.name : "Untitled Project",
			numItems: project.numItems,
			activeItem: project.activeItem ? project.activeItem.name : null
		};
	`

	result, err := tools.ExecuteScript(simpleScript)
	if err != nil {
		log.Fatalf("Error executing script: %v", err)
	}

	fmt.Println("Script Result:")
	fmt.Printf("  Project Name: %v\n", result["name"])
	fmt.Printf("  Number of Items: %v\n", result["numItems"])
	fmt.Printf("  Active Item: %v\n", result["activeItem"])

	// Example with parameters
	scriptWithParams := `
		// Script with parameters
		// Create a solid layer with the color from params
		var comp = app.project.activeItem;
		if (!(comp && comp instanceof CompItem)) {
			return { error: "No active composition" };
		}
		
		// Create a solid layer with specified parameters
		var solidLayer = comp.layers.addSolid(
			[params.color.r, params.color.g, params.color.b], // RGB color
			params.name,                                       // Layer name
			params.width,                                      // Width
			params.height,                                     // Height
			1,                                                 // Pixel aspect ratio
			params.duration                                    // Duration in seconds
		);
		
		return {
			message: "Created solid layer",
			layerName: solidLayer.name,
			layerId: solidLayer.index
		};
	`

	// Parameters for the script
	params := map[string]interface{}{
		"name":     "Colored Solid",
		"color":    map[string]float64{"r": 0.2, "g": 0.5, "b": 0.8},
		"width":    400,
		"height":   300,
		"duration": 5.0,
	}

	// Execute the script with parameters
	paramsResult, err := tools.ExecuteScriptWithParams(scriptWithParams, params)
	if err != nil {
		log.Fatalf("Error executing script with parameters: %v", err)
	}

	fmt.Println("\nScript with Parameters Result:")
	fmt.Printf("  Message: %v\n", paramsResult["message"])
	fmt.Printf("  Layer Name: %v\n", paramsResult["layerName"])
	fmt.Printf("  Layer ID: %v\n", paramsResult["layerId"])

	// Example of running more complex code
	complexScript := `
		// Create a simple animation
		var comp = app.project.activeItem;
		if (!(comp && comp instanceof CompItem)) {
			return { error: "No active composition" };
		}
		
		// Create a text layer
		var textLayer = comp.layers.addText("Animated Text");
		var textProp = textLayer.property("Source Text");
		
		// Set text properties
		var textDocument = textProp.value;
		textDocument.fontSize = 72;
		textDocument.fillColor = [1, 1, 0]; // Yellow
		textDocument.font = "Arial-Bold";
		textDocument.justification = ParagraphJustification.CENTER_JUSTIFY;
		textProp.setValue(textDocument);
		
		// Position in center
		var position = textLayer.property("Position");
		position.setValue([comp.width/2, comp.height/2]);
		
		// Add scale animation
		var scale = textLayer.property("Scale");
		scale.setValueAtTime(0, [0, 0, 0]);
		scale.setValueAtTime(2, [100, 100, 100]);
		
		// Add rotation animation
		var rotation = textLayer.property("Rotation");
		rotation.setValueAtTime(2, 0);
		rotation.setValueAtTime(4, 360);
		
		// Add easing to animations
		var easeIn = new KeyframeEase(0.5, 80);
		var easeOut = new KeyframeEase(0.5, 40);
		
		scale.setTemporalEaseAtKey(2, [easeIn, easeIn, easeIn]);
		rotation.setTemporalEaseAtKey(2, [easeIn]);
		
		return {
			message: "Created animated text",
			layer: textLayer.name
		};
	`

	complexResult, err := tools.ExecuteScript(complexScript)
	if err != nil {
		log.Fatalf("Error executing complex script: %v", err)
	}

	fmt.Println("\nComplex Script Result:")
	fmt.Printf("  Message: %v\n", complexResult["message"])
	fmt.Printf("  Layer: %v\n", complexResult["layer"])

	fmt.Println("\nScript execution demo completed!")
} 