package tools

import (
	"encoding/json"
	"fmt"
	"github.com/sunqirui1987/ae-mcp/pkg/ae"
)

// AddLightLayer adds a light layer to a composition
func AddLightLayer(compositionName, layerName, lightType string, color [3]float64) (map[string]interface{}, error) {
	if compositionName == "" {
		return nil, fmt.Errorf("composition name is required")
	}
	if layerName == "" {
		return nil, fmt.Errorf("layer name is required")
	}
	
	// Validate light type
	validLightTypes := map[string]bool{
		"Parallel":  true,
		"Spot":      true,
		"Point":     true,
		"Ambient":   true,
		"": true, // Default light type
	}
	
	if !validLightTypes[lightType] {
		return nil, fmt.Errorf("invalid light type: %s. Valid types are 'Parallel', 'Spot', 'Point', or 'Ambient'", lightType)
	}
	
	// If light type is empty, use default "Parallel"
	if lightType == "" {
		lightType = "Parallel"
	}
	
	// Convert light type to JSON string
	lightTypeJSON, err := json.Marshal(lightType)
	if err != nil {
		return nil, fmt.Errorf("error encoding light type: %v", err)
	}
	
	// Convert color to JSON
	colorJSON, err := json.Marshal(color)
	if err != nil {
		return nil, fmt.Errorf("error encoding color: %v", err)
	}
	
	// Create JavaScript to add light layer
	script := fmt.Sprintf(`
	(function() {
		// Find the composition
		var comp = null;
		for (var i = 1; i <= app.project.numItems; i++) {
			if (app.project.item(i) instanceof CompItem && app.project.item(i).name === "%s") {
				comp = app.project.item(i);
				break;
			}
		}
		
		if (!comp) {
			return { error: "Composition not found: " + "%s" };
		}
		
		// Create color object
		var colorArray = %s;
		var color = [colorArray[0], colorArray[1], colorArray[2], 1];  // Add alpha channel (1)
		
		try {
			// Add light layer
			var lightLayer = comp.layers.addLight(%s, [comp.width/2, comp.height/2]);
			lightLayer.name = "%s";
			
			// Set light color if provided
			if (color) {
				lightLayer.lightOption.color.setValue(color);
			}
			
			// Return information about the light layer
			var layerInfo = {
				index: lightLayer.index,
				name: lightLayer.name,
				type: "Light",
				lightType: %s,
				enabled: lightLayer.enabled,
				threeDLayer: true,
				transform: {
					position: lightLayer.transform.position.value,
					pointOfInterest: lightLayer.transform.pointOfInterest ? lightLayer.transform.pointOfInterest.value : null,
					orientation: lightLayer.transform.orientation ? lightLayer.transform.orientation.value : null
				},
				lightOptions: {
					intensity: lightLayer.lightOption.intensity.value,
					color: lightLayer.lightOption.color.value,
					coneAngle: lightLayer.lightOption.coneAngle ? lightLayer.lightOption.coneAngle.value : null,
					coneFeather: lightLayer.lightOption.coneFeather ? lightLayer.lightOption.coneFeather.value : null,
					shadowDarkness: lightLayer.lightOption.shadowDarkness ? lightLayer.lightOption.shadowDarkness.value : null,
					shadowDiffusion: lightLayer.lightOption.shadowDiffusion ? lightLayer.lightOption.shadowDiffusion.value : null
				}
			};
			
			return { success: true, layer: layerInfo };
		} catch (e) {
			return { error: "Error adding light layer: " + e.toString() };
		}
	})();
	`, compositionName, compositionName, 
	   string(colorJSON), string(lightTypeJSON), layerName, 
	   string(lightTypeJSON))
	
	// Execute the script
	result, err := ae.ExecuteScript(script)
	if err != nil {
		return nil, fmt.Errorf("error executing script: %v", err)
	}
	
	// Parse the result
	var response map[string]interface{}
	if resultStr, ok := result.(string); ok {
		if err := json.Unmarshal([]byte(resultStr), &response); err != nil {
			return nil, fmt.Errorf("error parsing script response: %v", err)
		}
	} else {
		return nil, fmt.Errorf("unexpected script response type")
	}
	
	if errMsg, ok := response["error"].(string); ok {
		return nil, fmt.Errorf(errMsg)
	}
	
	if layer, ok := response["layer"].(map[string]interface{}); ok {
		return layer, nil
	}
	
	return nil, fmt.Errorf("unexpected script response format")
}

