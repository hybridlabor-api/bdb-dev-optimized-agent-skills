package tools

import (
	"encoding/json"
	"fmt"
	"github.com/sunqirui1987/ae-mcp/pkg/ae"
)

// AddCameraLayer adds a camera layer to a composition
func AddCameraLayer(compositionName, layerName, cameraType string) (map[string]interface{}, error) {
	if compositionName == "" {
		return nil, fmt.Errorf("composition name is required")
	}
	if layerName == "" {
		return nil, fmt.Errorf("layer name is required")
	}
	
	// Validate camera type
	validCameraTypes := map[string]bool{
		"One-Node Camera": true,
		"Two-Node Camera": true,
		"": true, // Default camera type
	}
	
	if !validCameraTypes[cameraType] {
		return nil, fmt.Errorf("invalid camera type: %s. Valid types are 'One-Node Camera' or 'Two-Node Camera'", cameraType)
	}
	
	// If camera type is empty, use default "Two-Node Camera"
	if cameraType == "" {
		cameraType = "Two-Node Camera"
	}
	
	// Create JavaScript to add camera layer
	script := `
	try {
		// Find the composition
		var comp = null;
		for (var i = 1; i <= app.project.numItems; i++) {
			if (app.project.item(i) instanceof CompItem && app.project.item(i).name === "` + compositionName + `") {
				comp = app.project.item(i);
				break;
			}
		}
		
		if (!comp) {
			return returnjson({
				error: "Composition not found: " + "` + compositionName + `"
			});
		}
		
		// Define the center point for the camera in the middle of the composition
		var centerPoint = [comp.width/2, comp.height/2];
		
		// Add camera layer - this creates a Two-Node Camera by default
		var cameraLayer = comp.layers.addCamera("` + layerName + `", centerPoint);
		
		// Set up camera based on requested type
		if ("` + cameraType + `" === "One-Node Camera") {
			// For one-node camera, we need to remove the Point of Interest
			if (cameraLayer.transform.pointOfInterest) {
				try {
					// Attempt to detach the point of interest to make it a One-Node Camera
					cameraLayer.transform.pointOfInterest.expression = "// No point of interest for one-node camera";
					cameraLayer.transform.pointOfInterest.expressionEnabled = true;
					// Alternatively in some versions we might need to disable it:
					// cameraLayer.transform.pointOfInterest.enabled = false;
				} catch(e) {
					// If we can't modify it, log the error but continue
				}
			}
		} else {
			// For Two-Node Camera, make sure the point of interest is positioned at the center
			if (cameraLayer.transform.pointOfInterest) {
				cameraLayer.transform.pointOfInterest.setValue(centerPoint.concat(0)); // [x, y, 0]
			}
		}
		
		// Return information about the camera layer
		var layerInfo = {
			index: cameraLayer.index,
			name: cameraLayer.name,
			type: "Camera",
			cameraType: "` + cameraType + `",
			enabled: cameraLayer.enabled,
			threeDLayer: true,
			transform: {
				position: cameraLayer.transform.position.value,
				pointOfInterest: cameraLayer.transform.pointOfInterest ? cameraLayer.transform.pointOfInterest.value : null,
				orientation: cameraLayer.transform.orientation ? cameraLayer.transform.orientation.value : null
			},
			cameraOptions: {
				zoom: cameraLayer.cameraOption.zoom.value,
				depthOfField: cameraLayer.cameraOption.depthOfField.value,
				focusDistance: cameraLayer.cameraOption.focusDistance.value,
				aperture: cameraLayer.cameraOption.aperture.value,
				blurLevel: cameraLayer.cameraOption.blurLevel.value
			}
		};
		
		return returnjson({ success: true, layer: layerInfo });
	} catch (e) {
		return returnjson({ error: "Error adding camera layer: " + e.toString() });
	}
	`
	
	// Execute the script
	result, err := ae.ExecuteScript(script)
	if err != nil {
		return nil, fmt.Errorf("error executing script: %v", err)
	}
	
	// Parse the result
	var response map[string]interface{}
	if resultStr, ok := result.(string); ok {
		// Log the raw result for debugging
		fmt.Printf("Raw camera script result: %s\n", resultStr)
		
		if err := json.Unmarshal([]byte(resultStr), &response); err != nil {
			return nil, fmt.Errorf("error parsing script response: %v, raw response: %s", err, resultStr)
		}
	} else {
		return nil, fmt.Errorf("unexpected script response type: %T", result)
	}
	
	if errMsg, ok := response["error"].(string); ok {
		return nil, fmt.Errorf(errMsg)
	}
	
	if layer, ok := response["layer"].(map[string]interface{}); ok {
		return layer, nil
	}
	
	return nil, fmt.Errorf("unexpected script response format")
}

// ModifyCameraProperties modifies properties of an existing camera layer
func ModifyCameraProperties(compositionName, layerName string, options map[string]interface{}) (map[string]interface{}, error) {
	if compositionName == "" {
		return nil, fmt.Errorf("composition name is required")
	}
	if layerName == "" {
		return nil, fmt.Errorf("layer name is required")
	}
	if options == nil {
		return nil, fmt.Errorf("camera options are required")
	}
	
	// Convert options to JSON
	optionsJSON, err := json.Marshal(options)
	if err != nil {
		return nil, fmt.Errorf("error encoding camera options: %v", err)
	}
	
	// Create JavaScript to modify camera properties
	script := `
	try {
		// Find the composition
		var comp = null;
		for (var i = 1; i <= app.project.numItems; i++) {
			if (app.project.item(i) instanceof CompItem && app.project.item(i).name === "` + compositionName + `") {
				comp = app.project.item(i);
				break;
			}
		}
		
		if (!comp) {
			return returnjson({
				error: "Composition not found: " + "` + compositionName + `"
			});
		}
		
		// Find the camera layer
		var cameraLayer = null;
		for (var i = 1; i <= comp.numLayers; i++) {
			if (comp.layer(i).name === "` + layerName + `") {
				cameraLayer = comp.layer(i);
				break;
			}
		}
		
		if (!cameraLayer) {
			return returnjson({
				error: "Camera layer not found: " + "` + layerName + `"
			});
		}
		
		// Check if it's actually a camera layer
		if (!(cameraLayer instanceof CameraLayer)) {
			return returnjson({
				error: "Layer is not a camera layer: " + "` + layerName + `"
			});
		}
		
		var options = ` + string(optionsJSON) + `;
		
		// Apply transform properties
		if (options.position) {
			cameraLayer.transform.position.setValue(options.position);
		}
		
		if (options.pointOfInterest && cameraLayer.transform.pointOfInterest) {
			cameraLayer.transform.pointOfInterest.setValue(options.pointOfInterest);
		}
		
		if (options.orientation && cameraLayer.transform.orientation) {
			cameraLayer.transform.orientation.setValue(options.orientation);
		}
		
		// Apply camera options
		if (options.zoom) {
			cameraLayer.cameraOption.zoom.setValue(options.zoom);
		}
		
		if (options.depthOfField !== undefined) {
			cameraLayer.cameraOption.depthOfField.setValue(options.depthOfField);
		}
		
		if (options.focusDistance) {
			cameraLayer.cameraOption.focusDistance.setValue(options.focusDistance);
		}
		
		if (options.aperture) {
			cameraLayer.cameraOption.aperture.setValue(options.aperture);
		}
		
		if (options.blurLevel) {
			cameraLayer.cameraOption.blurLevel.setValue(options.blurLevel);
		}
		
		// Return updated camera information
		var cameraInfo = {
			index: cameraLayer.index,
			name: cameraLayer.name,
			type: "Camera",
			enabled: cameraLayer.enabled,
			transform: {
				position: cameraLayer.transform.position.value,
				pointOfInterest: cameraLayer.transform.pointOfInterest ? cameraLayer.transform.pointOfInterest.value : null,
				orientation: cameraLayer.transform.orientation ? cameraLayer.transform.orientation.value : null
			},
			cameraOptions: {
				zoom: cameraLayer.cameraOption.zoom.value,
				depthOfField: cameraLayer.cameraOption.depthOfField.value,
				focusDistance: cameraLayer.cameraOption.focusDistance.value,
				aperture: cameraLayer.cameraOption.aperture.value,
				blurLevel: cameraLayer.cameraOption.blurLevel.value
			}
		};
		
		return returnjson({ success: true, camera: cameraInfo });
	} catch (e) {
		return returnjson({ error: "Error modifying camera properties: " + e.toString() });
	}
	`
	
	// Execute the script
	result, err := ae.ExecuteScript(script)
	if err != nil {
		return nil, fmt.Errorf("error executing script: %v", err)
	}
	
	// Parse the result
	var response map[string]interface{}
	if resultStr, ok := result.(string); ok {
		// Log the raw result for debugging
		fmt.Printf("Raw camera modify script result: %s\n", resultStr)
		
		if err := json.Unmarshal([]byte(resultStr), &response); err != nil {
			return nil, fmt.Errorf("error parsing script response: %v, raw response: %s", err, resultStr)
		}
	} else {
		return nil, fmt.Errorf("unexpected script response type: %T", result)
	}
	
	if errMsg, ok := response["error"].(string); ok {
		return nil, fmt.Errorf(errMsg)
	}
	
	if camera, ok := response["camera"].(map[string]interface{}); ok {
		return camera, nil
	}
	
	return nil, fmt.Errorf("unexpected script response format")
}

// GetCameraLayerInfo retrieves information about a camera layer in a composition
func GetCameraLayerInfo(compositionName, layerName string) (map[string]interface{}, error) {
	if compositionName == "" {
		return nil, fmt.Errorf("composition name is required")
	}
	if layerName == "" {
		return nil, fmt.Errorf("layer name is required")
	}
	
	// Create JavaScript to get camera layer info
	script := `
	try {
		// Find the composition
		var comp = null;
		for (var i = 1; i <= app.project.numItems; i++) {
			if (app.project.item(i) instanceof CompItem && app.project.item(i).name === "` + compositionName + `") {
				comp = app.project.item(i);
				break;
			}
		}
		
		if (!comp) {
			return returnjson({
				error: "Composition not found: " + "` + compositionName + `"
			});
		}
		
		// Find the camera layer
		var cameraLayer = null;
		for (var i = 1; i <= comp.numLayers; i++) {
			if (comp.layer(i).name === "` + layerName + `") {
				cameraLayer = comp.layer(i);
				break;
			}
		}
		
		if (!cameraLayer) {
			return returnjson({
				error: "Camera layer not found: " + "` + layerName + `"
			});
		}
		
		// Check if it's actually a camera layer
		if (!(cameraLayer instanceof CameraLayer)) {
			return returnjson({
				error: "Layer is not a camera layer: " + "` + layerName + `"
			});
		}
		
		// Get camera type
		var cameraType = "";
		if (cameraLayer.transform.pointOfInterest) {
			cameraType = "Two-Node Camera";
		} else {
			cameraType = "One-Node Camera";
		}
		
		// Build camera information object
		var cameraInfo = {
			index: cameraLayer.index,
			name: cameraLayer.name,
			type: "Camera",
			cameraType: cameraType,
			enabled: cameraLayer.enabled,
			threeDLayer: true,
			transform: {
				position: cameraLayer.transform.position.value,
				pointOfInterest: cameraLayer.transform.pointOfInterest ? cameraLayer.transform.pointOfInterest.value : null,
				orientation: cameraLayer.transform.orientation ? cameraLayer.transform.orientation.value : null,
				xRotation: cameraLayer.transform.xRotation ? cameraLayer.transform.xRotation.value : null,
				yRotation: cameraLayer.transform.yRotation ? cameraLayer.transform.yRotation.value : null,
				zRotation: cameraLayer.transform.zRotation ? cameraLayer.transform.zRotation.value : null
			},
			cameraOptions: {
				zoom: cameraLayer.cameraOption.zoom.value,
				depthOfField: cameraLayer.cameraOption.depthOfField.value,
				focusDistance: cameraLayer.cameraOption.focusDistance.value,
				aperture: cameraLayer.cameraOption.aperture.value,
				blurLevel: cameraLayer.cameraOption.blurLevel.value
			}
		};
		
		return returnjson({ success: true, camera: cameraInfo });
	} catch (e) {
		return returnjson({ error: "Error getting camera information: " + e.toString() });
	}
	`
	
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
	
	if camera, ok := response["camera"].(map[string]interface{}); ok {
		return camera, nil
	}
	
	return nil, fmt.Errorf("unexpected script response format")
}
