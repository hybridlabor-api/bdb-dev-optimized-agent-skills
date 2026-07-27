package main

import (
	"fmt"
	"github.com/sunqirui1987/ae-mcp/pkg/tools"
	"os"
)

func main() {
	fmt.Println("Starting 3D Eclipse Relationship Demo...")
	
	err := Eclipse3DDemo()
	if err != nil {
		fmt.Printf("Error: %v\n", err)
		os.Exit(1)
	}
	
	fmt.Println("Demo completed successfully!")
}

// Eclipse3DDemo creates a 3D animation showing the relationship between solar and lunar eclipses
func Eclipse3DDemo() error {

	// Create main composition
	comp, err := tools.CreateComposition("Eclipse Animation", 1920, 1080, 20, 30)
	if err != nil {
		return fmt.Errorf("failed to create composition: %w", err)
	}

	// Get composition name and dimensions
	compName, _ := comp["name"].(string)
	compWidth, _ := comp["width"].(float64)
	compHeight, _ := comp["height"].(float64)

	// Add a solid black background
	_, err = tools.AddSolidLayer(compName, "Background", tools.ColorRGB{0, 0, 0}, 1920, 1080, true)
	if err != nil {
		return fmt.Errorf("failed to add background: %w", err)
	}

	// Create celestial bodies
	// Sun - Large yellow sphere using solid layer
	_, err = tools.AddSolidLayer(compName, "Sun", tools.ColorRGB{1, 0.8, 0}, 300, 300, true)
	if err != nil {
		return fmt.Errorf("failed to create sun layer: %w", err)
	}

	// Make sun 3D and position it
	layerID := tools.LayerIdentifier{Name: "Sun"}
	_, err = tools.ModifyLayer(compName, layerID, tools.LayerProperties{
		"threeDLayer": true,
		"position":    [3]float64{1920/2 - 600, 1080/2, 0},
		"material":    map[string]interface{}{"castsShadows": true}, // Ensure 3D properties are set
	})
	if err != nil {
		return fmt.Errorf("failed to modify sun layer: %w", err)
	}

	// Add spherize effect to sun
	_, err = tools.ApplyEffect(compName, "Sun", "Spherize", map[string]interface{}{
		"Amount": 100,
	})
	if err != nil {
		return fmt.Errorf("failed to apply spherize to sun: %w", err)
	}

	// Add glow effect to sun
	_, err = tools.ApplyEffect(compName, "Sun", "Glow", map[string]interface{}{
		"Threshold": 10,
		"Radius":    90,
		"Intensity": 3,
	})
	if err != nil {
		return fmt.Errorf("failed to apply glow to sun: %w", err)
	}
	
	// Add label to Sun
	sunLabelOpts := &tools.TextOptions{
		FontSize:      30,
		Color:         tools.ColorRGB{1, 1, 1},
		Position:      [2]float64{1920/2 - 600, 1080/2 - 180},
		Justification: "CENTER",
	}
	
	_, err = tools.AddTextLayer(compName, "Sun Label", "太阳 (Sun)", sunLabelOpts)
	if err != nil {
		return fmt.Errorf("failed to add sun label: %w", err)
	}
	
	// Make Sun label 3D and add stroke
	sunLabelID := tools.LayerIdentifier{Name: "Sun Label"}
	_, err = tools.ModifyLayer(compName, sunLabelID, tools.LayerProperties{
		"threeDLayer": true,
	})
	if err != nil {
		return fmt.Errorf("failed to make sun label 3D: %w", err)
	}
	
	// Add stroke to Sun label
	_, err = tools.ApplyEffect(compName, "Sun Label", "ADBE Stroke", map[string]interface{}{
		"Color": [4]float64{0, 0, 0, 1}, // Black stroke
		"Stroke Width": 3,
	})
	if err != nil {
		return fmt.Errorf("failed to add stroke to sun label: %w", err)
	}

	// Earth - Blue sphere
	_, err = tools.AddSolidLayer(compName, "Earth", tools.ColorRGB{0.1, 0.3, 0.8}, 150, 150, true)
	if err != nil {
		return fmt.Errorf("failed to create earth layer: %w", err)
	}

	// Make earth 3D and position it
	earthLayerID := tools.LayerIdentifier{Name: "Earth"}
	_, err = tools.ModifyLayer(compName, earthLayerID, tools.LayerProperties{
		"threeDLayer": true,
		"position":    [3]float64{1920/2, 1080/2, 0},
		"blendingMode": "OVERLAY", 
		"material":    map[string]interface{}{"castsShadows": true, "acceptsShadows": true}, // Enhanced 3D properties
	})
	if err != nil {
		return fmt.Errorf("failed to modify earth layer: %w", err)
	}

	// Add spherize effect to earth
	_, err = tools.ApplyEffect(compName, "Earth", "Spherize", map[string]interface{}{
		"Amount": 100,
	})
	if err != nil {
		return fmt.Errorf("failed to apply spherize to earth: %w", err)
	}

	// Add fractal noise effect to earth for texture
	_, err = tools.ApplyEffect(compName, "Earth", "ADBE Fractal Noise", map[string]interface{}{
		"Fractal Type": 6,
		"Noise Type":   50,
		"Contrast":     80,
		"Brightness":   3,
		"Complexity":   1.5,
	})
	if err != nil {
		return fmt.Errorf("failed to apply texture to earth: %w", err)
	}
	
	// Add label to Earth
	earthLabelOpts := &tools.TextOptions{
		FontSize:      30,
		Color:         tools.ColorRGB{1, 1, 1},
		Position:      [2]float64{1920/2, 1080/2 - 100},
		Justification: "CENTER",
	}
	
	_, err = tools.AddTextLayer(compName, "Earth Label", "地球 (Earth)", earthLabelOpts)
	if err != nil {
		return fmt.Errorf("failed to add earth label: %w", err)
	}
	
	// Make Earth label 3D and add stroke
	earthLabelID := tools.LayerIdentifier{Name: "Earth Label"}
	_, err = tools.ModifyLayer(compName, earthLabelID, tools.LayerProperties{
		"threeDLayer": true,
	})
	if err != nil {
		return fmt.Errorf("failed to make earth label 3D: %w", err)
	}
	
	// Add stroke to Earth label
	_, err = tools.ApplyEffect(compName, "Earth Label", "ADBE Stroke", map[string]interface{}{
		"Color": [4]float64{0, 0, 0, 1}, // Black stroke
		"Stroke Width": 3,
	})
	if err != nil {
		return fmt.Errorf("failed to add stroke to earth label: %w", err)
	}

	// Moon - Gray sphere
	_, err = tools.AddSolidLayer(compName, "Moon", tools.ColorRGB{0.7, 0.7, 0.7}, 50, 50, true)
	if err != nil {
		return fmt.Errorf("failed to create moon layer: %w", err)
	}

	// Make moon 3D and position it
	moonLayerID := tools.LayerIdentifier{Name: "Moon"}
	_, err = tools.ModifyLayer(compName, moonLayerID, tools.LayerProperties{
		"threeDLayer": true,
		"position":    [3]float64{1920/2 + 250, 1080/2, 0},
		"material":    map[string]interface{}{"castsShadows": true, "acceptsShadows": true}, // Enhanced 3D properties
	})
	if err != nil {
		return fmt.Errorf("failed to modify moon layer: %w", err)
	}

	// Add spherize effect to moon
	_, err = tools.ApplyEffect(compName, "Moon", "Spherize", map[string]interface{}{
		"Amount": 100,
	})
	if err != nil {
		return fmt.Errorf("failed to apply spherize to moon: %w", err)
	}

	// Add fractal noise effect to moon for texture
	_, err = tools.ApplyEffect(compName, "Moon", "ADBE Fractal Noise", map[string]interface{}{
		"Fractal Type": 6,
		"Noise Type":   50,
		"Contrast":     60,
		"Brightness":   2,
		"Complexity":   1.2,
	})
	if err != nil {
		return fmt.Errorf("failed to apply texture to moon: %w", err)
	}
	
	// Add label to Moon
	moonLabelOpts := &tools.TextOptions{
		FontSize:      30,
		Color:         tools.ColorRGB{1, 1, 1},
		Position:      [2]float64{1920/2 + 250, 1080/2 - 50},
		Justification: "CENTER",
	}
	
	_, err = tools.AddTextLayer(compName, "Moon Label", "月球 (Moon)", moonLabelOpts)
	if err != nil {
		return fmt.Errorf("failed to add moon label: %w", err)
	}
	
	// Make Moon label 3D and add stroke
	moonLabelID := tools.LayerIdentifier{Name: "Moon Label"}
	_, err = tools.ModifyLayer(compName, moonLabelID, tools.LayerProperties{
		"threeDLayer": true,
	})
	if err != nil {
		return fmt.Errorf("failed to make moon label 3D: %w", err)
	}
	
	// Add stroke to Moon label
	_, err = tools.ApplyEffect(compName, "Moon Label", "ADBE Stroke", map[string]interface{}{
		"Color": [4]float64{0, 0, 0, 1}, // Black stroke
		"Stroke Width": 3,
	})
	if err != nil {
		return fmt.Errorf("failed to add stroke to moon label: %w", err)
	}

	// Add a 3D camera using camera.go functionality
	_, err = tools.AddCameraLayer(compName, "Main Camera", "Two-Node Camera")
	if err != nil {
		return fmt.Errorf("failed to create camera: %w", err)
	}
	
	// Modify camera properties for a good view of the system
	cameraOptions := map[string]interface{}{
		"position": [3]float64{compWidth/2, compHeight/2, -1500},
		"zoom":     1000,
	}
	
	_, err = tools.ModifyCameraProperties(compName, "Main Camera", cameraOptions)
	if err != nil {
		return fmt.Errorf("failed to configure camera: %w", err)
	}

	// Add text explanations with stroke effects
	textTitleOpts := &tools.TextOptions{
		FontSize:      60,
		Color:         tools.ColorRGB{1, 1, 1},
		Position:      [2]float64{compWidth / 2, 80},
		Justification: "CENTER",
	}
	_, err = tools.AddTextLayer(compName, "Eclipse Relationship", "日食与月食的关系 (Eclipse Relationship)", textTitleOpts)
	if err != nil {
		return fmt.Errorf("failed to add title: %w", err)
	}
	
	// Add stroke to title text
	_, err = tools.ApplyEffect(compName, "Eclipse Relationship", "ADBE Stroke", map[string]interface{}{
		"Color": [4]float64{0, 0, 0, 1}, // Black stroke
		"Stroke Width": 5,
	})
	if err != nil {
		return fmt.Errorf("failed to add stroke to title: %w", err)
	}

	// Add explanation text layers with stroke effects
	solarTextOpts := &tools.TextOptions{
		FontSize:      40,
		Color:         tools.ColorRGB{1, 1, 1},
		Position:      [2]float64{compWidth / 2, compHeight - 200},
		Justification: "CENTER",
	}
	_, err = tools.AddTextLayer(compName, "Solar Eclipse Text", "日食：月球挡住太阳光到达地球 (Solar Eclipse: Moon blocks Sun's light from reaching Earth)", solarTextOpts)
	if err != nil {
		return fmt.Errorf("failed to add solar explanation: %w", err)
	}
	
	// Add stroke to solar eclipse text
	_, err = tools.ApplyEffect(compName, "Solar Eclipse Text", "ADBE Stroke", map[string]interface{}{
		"Color": [4]float64{0, 0, 0, 1}, // Black stroke
		"Stroke Width": 4,
	})
	if err != nil {
		return fmt.Errorf("failed to add stroke to solar eclipse text: %w", err)
	}

	lunarTextOpts := &tools.TextOptions{
		FontSize:      40,
		Color:         tools.ColorRGB{1, 1, 1},
		Position:      [2]float64{compWidth / 2, compHeight - 140},
		Justification: "CENTER",
	}
	_, err = tools.AddTextLayer(compName, "Lunar Eclipse Text", "月食：地球挡住太阳光到达月球 (Lunar Eclipse: Earth blocks Sun's light from reaching Moon)", lunarTextOpts)
	if err != nil {
		return fmt.Errorf("failed to add lunar explanation: %w", err)
	}
	
	// Add stroke to lunar eclipse text
	_, err = tools.ApplyEffect(compName, "Lunar Eclipse Text", "ADBE Stroke", map[string]interface{}{
		"Color": [4]float64{0, 0, 0, 1}, // Black stroke
		"Stroke Width": 4,
	})
	if err != nil {
		return fmt.Errorf("failed to add stroke to lunar eclipse text: %w", err)
	}

	// Hide explanations initially
	solarTextLayerID := tools.LayerIdentifier{Name: "Solar Eclipse Text"}
	_, err = tools.ModifyLayer(compName, solarTextLayerID, tools.LayerProperties{
		"opacity": 0,
	})
	if err != nil {
		return fmt.Errorf("failed to set solar text opacity: %w", err)
	}

	lunarTextLayerID := tools.LayerIdentifier{Name: "Lunar Eclipse Text"}
	_, err = tools.ModifyLayer(compName, lunarTextLayerID, tools.LayerProperties{
		"opacity": 0,
	})
	if err != nil {
		return fmt.Errorf("failed to set lunar text opacity: %w", err)
	}
	
	// Add additional explanation text for more detailed information
	solarDetailTextOpts := &tools.TextOptions{
		FontSize:      30,
		Color:         tools.ColorRGB{1, 0.9, 0.4}, // Light yellow
		Position:      [2]float64{compWidth / 2, compHeight - 240},
		Justification: "CENTER",
	}
	_, err = tools.AddTextLayer(compName, "Solar Detail Text", "当月球位于太阳和地球之间，会挡住阳光，地球上会出现日食现象 (When the Moon is between the Sun and Earth, it blocks sunlight, causing a solar eclipse)", solarDetailTextOpts)
	if err != nil {
		return fmt.Errorf("failed to add solar detail: %w", err)
	}
	
	// Add stroke to solar detail text
	_, err = tools.ApplyEffect(compName, "Solar Detail Text", "ADBE Stroke", map[string]interface{}{
		"Color": [4]float64{0.2, 0.2, 0.2, 1}, // Dark gray stroke
		"Stroke Width": 3,
	})
	if err != nil {
		return fmt.Errorf("failed to add stroke to solar detail text: %w", err)
	}
	
	// Hide solar detail initially
	solarDetailID := tools.LayerIdentifier{Name: "Solar Detail Text"}
	_, err = tools.ModifyLayer(compName, solarDetailID, tools.LayerProperties{
		"opacity": 0,
		"threeDLayer": true,
	})
	if err != nil {
		return fmt.Errorf("failed to set solar detail opacity: %w", err)
	}
	
	lunarDetailTextOpts := &tools.TextOptions{
		FontSize:      30,
		Color:         tools.ColorRGB{0.7, 0.7, 1}, // Light blue
		Position:      [2]float64{compWidth / 2, compHeight - 80},
		Justification: "CENTER",
	}
	_, err = tools.AddTextLayer(compName, "Lunar Detail Text", "当地球位于太阳和月球之间，地球的阴影会落在月球上，发生月食现象 (When Earth is between the Sun and Moon, Earth's shadow falls on the Moon, causing a lunar eclipse)", lunarDetailTextOpts)
	if err != nil {
		return fmt.Errorf("failed to add lunar detail: %w", err)
	}
	
	// Add stroke to lunar detail text
	_, err = tools.ApplyEffect(compName, "Lunar Detail Text", "ADBE Stroke", map[string]interface{}{
		"Color": [4]float64{0.2, 0.2, 0.2, 1}, // Dark gray stroke
		"Stroke Width": 3,
	})
	if err != nil {
		return fmt.Errorf("failed to add stroke to lunar detail text: %w", err)
	}
	
	// Hide lunar detail initially
	lunarDetailID := tools.LayerIdentifier{Name: "Lunar Detail Text"}
	_, err = tools.ModifyLayer(compName, lunarDetailID, tools.LayerProperties{
		"opacity": 0,
		"threeDLayer": true,
	})
	if err != nil {
		return fmt.Errorf("failed to set lunar detail opacity: %w", err)
	}

	// At 11 seconds, camera moves to show another angle
	cameraKeyframeScript := `
	try {
		var comp = app.project.activeItem;
		var camera = comp.layer("Main Camera");
		
		// Set keyframes for camera position
		camera.position.setValueAtTime(11, [comp.width/2, comp.height/2, -1500]);
		camera.position.setValueAtTime(15, [comp.width/2, comp.height/2 - 500, -1200]);
		
		// Set keyframes for camera rotation
		camera.xRotation.setValueAtTime(11, 0);
		camera.xRotation.setValueAtTime(15, degreesToRadians(30));
		
		// Apply easing to camera keyframes
		easeKeyframes(camera.position);
		easeKeyframes(camera.xRotation);
		
		return returnjson({"result": "Camera animation keyframes created successfully"});
		
		function degreesToRadians(degrees) {
			return degrees * Math.PI / 180;
		}
		
		function easeKeyframes(prop) {
			if (prop.numKeys > 0) {
				for (var i = 1; i <= prop.numKeys; i++) {
					var easeIn = new KeyframeEase(0.5, 50);
					var easeOut = new KeyframeEase(0.5, 50);
					if (prop.propertyValueType == PropertyValueType.TwoD_SPATIAL ||
						prop.propertyValueType == PropertyValueType.ThreeD_SPATIAL) {
						prop.setSpatialTangentsAtKey(i, [0,0,0], [0,0,0]);
					} else {
						prop.setTemporalEaseAtKey(i, [easeIn], [easeOut]);
					}
				}
			}
		}
	} catch (err) {
		return returnjson({"error": err.toString()});
	}
	`;
	
	_, err = tools.ExecuteScript(cameraKeyframeScript)
	if err != nil {
		return fmt.Errorf("failed to create camera animation: %w", err)
	}
	
	// Continue with the rest of the animations for other elements including the new text layers
	animScript := `
	try {
		var comp = app.project.activeItem;
		var moonLayer = comp.layer("Moon");
		var solarText = comp.layer("Solar Eclipse Text");
		var lunarText = comp.layer("Lunar Eclipse Text");
		var solarDetail = comp.layer("Solar Detail Text");
		var lunarDetail = comp.layer("Lunar Detail Text");
		
		// At 3 seconds, moon moves between sun and earth (solar eclipse)
		moonLayer.position.setValueAtTime(3, [comp.width/2 - 300, comp.height/2, 0]);
		
		// Fade in solar eclipse explanation
		solarText.opacity.setValueAtTime(2.5, 0);
		solarText.opacity.setValueAtTime(3.5, 100);
		
		// Fade in solar detail
		solarDetail.opacity.setValueAtTime(3, 0);
		solarDetail.opacity.setValueAtTime(4, 100);
		
		// At 7 seconds, move to show lunar eclipse alignment
		// Moon moves to opposite side of earth from sun
		moonLayer.position.setValueAtTime(7, [comp.width/2 + 300, comp.height/2, 0]);
		
		// Fade out solar eclipse explanation
		solarText.opacity.setValueAtTime(6.5, 100);
		solarText.opacity.setValueAtTime(7.5, 0);
		
		// Fade out solar detail
		solarDetail.opacity.setValueAtTime(6.5, 100);
		solarDetail.opacity.setValueAtTime(7.5, 0);
		
		// Fade in lunar eclipse explanation
		lunarText.opacity.setValueAtTime(7, 0);
		lunarText.opacity.setValueAtTime(8, 100);
		
		// Fade in lunar detail
		lunarDetail.opacity.setValueAtTime(7.5, 0);
		lunarDetail.opacity.setValueAtTime(8.5, 100);
		
		// Apply easing to all animations
		easyEaseAllKeyframes(comp);
		
		return returnjson({"result": "Animation keyframes created successfully"});
	} catch (err) {
		return returnjson({"error": err.toString()});
	}
	
	function easyEaseAllKeyframes(comp) {
		for (var i = 1; i <= comp.numLayers; i++) {
			var layer = comp.layer(i);
			// Skip the camera layer as we've already handled it
			if (layer.name !== "Main Camera") {
				easeLayerProperties(layer);
			}
		}
	}
	
	function easeLayerProperties(layer) {
		// Get all properties that can have keyframes
		var props = layer.Properties;
		for (var i = 1; i <= props.numProperties; i++) {
			var prop = props.property(i);
			if (prop.canSetExpression) {
				applyEaseToProperty(prop);
			}
		}
	}
	
	function applyEaseToProperty(prop) {
		if (prop.numKeys > 0) {
			for (var i = 1; i <= prop.numKeys; i++) {
				var easeIn = new KeyframeEase(0.5, 50);
				var easeOut = new KeyframeEase(0.5, 50);
				if (prop.propertyValueType == PropertyValueType.TwoD_SPATIAL ||
					prop.propertyValueType == PropertyValueType.ThreeD_SPATIAL) {
					prop.setSpatialTangentsAtKey(i, [0,0,0], [0,0,0]);
				} else {
					prop.setTemporalEaseAtKey(i, [easeIn], [easeOut]);
				}
			}
		}
	}
	`;
	
	_, err = tools.ExecuteScript(animScript)
	if err != nil {
		return fmt.Errorf("failed to create animation: %w", err)
	}

	// Add lighting to enhance 3D effect
	lightScript := `
	try {
		var comp = app.project.activeItem;
		
		// Add main directional light
		var light = comp.layers.addLight("Main Light", [comp.width/2, comp.height/2]);
		light.position.setValue([comp.width/2 - 800, comp.height/2 - 500, -800]);
		light.intensity.setValue(150);
		
		// Add ambient light for overall scene illumination
		var ambientLight = comp.layers.addLight("Ambient Light", [comp.width/2, comp.height/2]);
		ambientLight.lightType = LightType.AMBIENT;
		ambientLight.intensity.setValue(30);
		
		// Add a rim light to enhance 3D appearance
		var rimLight = comp.layers.addLight("Rim Light", [comp.width/2, comp.height/2]);
		rimLight.position.setValue([comp.width/2 + 600, comp.height/2 - 300, -600]);
		rimLight.intensity.setValue(80);
		
		return returnjson({"result": "Lights added successfully"});
	} catch (err) {
		return returnjson({"error": err.toString()});
	}
	`
	_, err = tools.ExecuteScript(lightScript)
	if err != nil {
		return fmt.Errorf("failed to add lighting: %w", err)
	}

	// Add shadows for 3D effect
	_, err = tools.ModifyLayer(compName, earthLayerID, tools.LayerProperties{
		"castsShadows":  1,
		"acceptsShadows": 1,
	})
	if err != nil {
		return fmt.Errorf("failed to configure earth shadows: %w", err)
	}

	_, err = tools.ModifyLayer(compName, moonLayerID, tools.LayerProperties{
		"castsShadows":  1,
		"acceptsShadows": 1,
	})
	if err != nil {
		return fmt.Errorf("failed to configure moon shadows: %w", err)
	}

	// Use shape layers for orbit paths for visual enhancement
	_, err = tools.AddPresetShapeLayer(compName, "Earth Orbit Path", "ellipse", 1200, 1200)
	if err != nil {
		return fmt.Errorf("failed to create earth orbit path: %w", err)
	}

	// Center the orbit and make it 3D
	earthOrbitLayerID := tools.LayerIdentifier{Name: "Earth Orbit Path"}
	_, err = tools.ModifyLayer(compName, earthOrbitLayerID, tools.LayerProperties{
		"threeDLayer": true,
		"position":    [3]float64{1920/2, 1080/2, 0},
		"opacity":     50,
		"scale":       [3]float64{100, 25, 100}, // Flatten to create elliptical orbit appearance
	})
	if err != nil {
		return fmt.Errorf("failed to modify earth orbit path: %w", err)
	}

	// Apply stroke effect to orbit path
	_, err = tools.ApplyEffect(compName, "Earth Orbit Path", "ADBE Stroke", map[string]interface{}{
		"Color": [4]float64{0.5, 0.5, 1, 1}, // Light blue
		"Stroke Width": 2,
	})
	if err != nil {
		return fmt.Errorf("failed to apply stroke to earth orbit: %w", err)
	}

	// Create a moon orbit path
	_, err = tools.AddPresetShapeLayer(compName, "Moon Orbit Path", "ellipse", 500, 500)
	if err != nil {
		return fmt.Errorf("failed to create moon orbit path: %w", err)
	}

	// Position moon orbit and make it 3D
	moonOrbitLayerID := tools.LayerIdentifier{Name: "Moon Orbit Path"}
	_, err = tools.ModifyLayer(compName, moonOrbitLayerID, tools.LayerProperties{
		"threeDLayer": true,
		"position":    [3]float64{1920/2, 1080/2, 0},
		"opacity":     40,
		"scale":       [3]float64{100, 40, 100}, // Flatten to create elliptical orbit appearance
	})
	if err != nil {
		return fmt.Errorf("failed to modify moon orbit path: %w", err)
	}

	// Apply stroke effect to moon orbit path
	_, err = tools.ApplyEffect(compName, "Moon Orbit Path", "ADBE Stroke", map[string]interface{}{
		"Color": [4]float64{0.8, 0.8, 0.8, 1}, // Light gray
		"Stroke Width": 1,
	})
	if err != nil {
		return fmt.Errorf("failed to apply stroke to moon orbit: %w", err)
	}

	fmt.Println("3D Eclipse relationship animation created successfully!")
	return nil
}