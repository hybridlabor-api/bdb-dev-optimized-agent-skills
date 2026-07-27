package tools

import (
	"encoding/json"
	"fmt"
	"github.com/sunqirui1987/ae-mcp/pkg/ae"
)

// Layer type constants
const (
	AVLayer       = "ADBE AV Layer"
	CameraLayer   = "ADBE Camera Layer"
	LightLayer    = "ADBE Light Layer"
	ShapeLayer    = "ADBE Vector Layer"
	TextLayer     = "ADBE Text Layer"
)

// Common transform property match names
const (
	TransformGroup  = "ADBE Transform Group"
	AnchorPoint     = "ADBE Anchor Point"
	Position        = "ADBE Position"
	PositionX       = "ADBE Position_0"
	PositionY       = "ADBE Position_1"
	PositionZ       = "ADBE Position_2"
	Scale           = "ADBE Scale"
	Orientation     = "ADBE Orientation"
	RotationX       = "ADBE Rotate X"
	RotationY       = "ADBE Rotate Y"
	RotationZ       = "ADBE Rotate Z" // Also "Rotation" for 2D layers
	Opacity         = "ADBE Opacity"
)

// Common layer property match names
const (
	MarkerProperty      = "ADBE Marker"
	TimeRemap           = "ADBE Time Remapping"
	MotionTrackers      = "ADBE MTrackers"
	MaskGroup           = "ADBE Mask Parade"
	EffectGroup         = "ADBE Effect Parade"
	EssentialProperties = "ADBE Layer Overrides"
)

// 3D Layer specific match names
const (
	// Plane
	PlaneOptions = "ADBE Plane Options Group"
	Curvature    = "ADBE Plane Curvature"
	Segments     = "ADBE Plane Subdivision"
	
	// Extrusion
	ExtrusionOptions = "ADBE Extrsn Options Group"
	BevelDepth       = "ADBE Bevel Depth"
	HoleBevelDepth   = "ADBE Hole Bevel Depth"
	ExtrusionDepth   = "ADBE Extrsn Depth"
	
	// Material
	MaterialOptions    = "ADBE Material Options Group"
	LightTransmission  = "ADBE Light Transmission"
	AmbientCoefficient = "ADBE Ambient Coefficient"
	DiffuseCoefficient = "ADBE Diffuse Coefficient"
	SpecularIntensity  = "ADBE Specular Coefficient"
	SpecularShininess  = "ADBE Shininess Coefficient"
	Metal              = "ADBE Metal Coefficient"
	ReflectionIntensity = "ADBE Reflection Coefficient"
	ReflectionSharpness = "ADBE Glossiness Coefficient"
	ReflectionRolloff   = "ADBE Fresnel Coefficient"
	Transparency        = "ADBE Transparency Coefficient"
	TransparencyRolloff = "ADBE Transp Rolloff"
	IndexOfRefraction   = "ADBE Index of Refraction"
)

// Camera Layer specific match names
const (
	CameraOptions     = "ADBE Camera Options Group"
	CameraZoom        = "ADBE Camera Zoom"
	DepthOfField      = "ADBE Camera Depth of Field"
	FocusDistance     = "ADBE Camera Focus Distance"
	Aperture          = "ADBE Camera Aperture"
	BlurLevel         = "ADBE Camera Blur Level"
	
	// Iris
	IrisShape            = "ADBE Iris Shape"
	IrisRotation         = "ADBE Iris Rotation"
	IrisRoundness        = "ADBE Iris Roundness"
	IrisAspectRatio      = "ADBE Iris Aspect Ratio"
	IrisDiffractionFringe = "ADBE Iris Diffraction Fringe"
	HighlightGain        = "ADBE Iris Highlight Gain"
	HighlightThreshold   = "ADBE Iris Highlight Threshold"
	HighlightSaturation  = "ADBE Iris Hightlight Saturation"
)

// Light Layer specific match names
const (
	LightOptions     = "ADBE Light Options Group"
	LightIntensity   = "ADBE Light Intensity"
	LightColor       = "ADBE Light Color"
	ConeAngle        = "ADBE Light Cone Angle"
	ConeFeather      = "ADBE Light Cone Feather 2"
	
	// Falloff
	FalloffType      = "ADBE Light Falloff Type"
	FalloffStart     = "ADBE Light Falloff Start"
	FalloffDistance  = "ADBE Light Falloff Distance"
	
	// Shadow
	ShadowDarkness   = "ADBE Light Shadow Darkness"
	ShadowDiffusion  = "ADBE Light Shadow Diffusion"
)

// Text Layer specific match names
const (
	TextDocument     = "ADBE Text Document"
	TextSourceText   = "ADBE Text Properties"
	TextPathOptions  = "ADBE Text Path Options"
	TextMoreOptions  = "ADBE Text More Options"
	TextAnimators    = "ADBE Text Animators"
)

// Shape Layer specific match names
const (
	ShapeContents = "ADBE Root Vectors Group"
	ShapeGroup    = "ADBE Vector Group"
	ShapePath     = "ADBE Vector Shape"
	ShapeFill     = "ADBE Vector Graphic - Fill"
	ShapeStroke   = "ADBE Vector Graphic - Stroke"
)

// LayerInfo represents information about a layer in After Effects
type LayerInfo map[string]interface{}

// ColorRGB represents an RGB color with values between 0 and 1
type ColorRGB [3]float64

// LayerIdentifier can be either a name or index
type LayerIdentifier struct {
	Name  string  `json:"name,omitempty"`
	Index int     `json:"index,omitempty"`
}

// LayerProperties represents properties that can be modified on a layer
type LayerProperties map[string]interface{}

// PropertyPath represents a path to a property using match names
type PropertyPath []string

// AddSolidLayer adds a solid layer to a composition
func AddSolidLayer(compositionName string, layerName string, color ColorRGB, width int, height int, is3D bool) (LayerInfo, error) {
	// Execute JavaScript to add solid layer
	script := `
	try {
		var compName = "` + compositionName + `";
		var layerName = "` + layerName + `";
		var color = [` + fmt.Sprintf("%f, %f, %f", color[0], color[1], color[2]) + `];
		var width = ` + fmt.Sprintf("%d", width) + `;
		var height = ` + fmt.Sprintf("%d", height) + `;
		var is3D = ` + fmt.Sprintf("%t", is3D) + `;
		
		// Find the composition
		var project = app.project;
		var comp = null;
		
		for (var i = 1; i <= project.numItems; i++) {
			var item = project.item(i);
			if (item instanceof CompItem && item.name === compName) {
				comp = item;
				break;
			}
		}
		
		if (!comp) {
			return JSON.stringify({
				error: "Composition not found: " + compName
			});
		}
		
		// Use composition dimensions if width/height are not specified
		if (width <= 0) width = comp.width;
		if (height <= 0) height = comp.height;
		
		// Create solid layer directly in the composition
		var layer = comp.layers.addSolid(
			color,               // color array [r, g, b]
			layerName,           // name
			width,               // width
			height,              // height
			1,                   // pixel aspect ratio
			comp.duration        // duration (seconds)
		);
		
		// Set 3D if specified
		if (is3D) {
			layer.threeDLayer = true;
		}
		
		// Return layer info
		var result = {
			name: layer.name,
			index: layer.index,
			enabled: layer.enabled,
			is3D: layer.threeDLayer,
			position: layer.position.value
		};
		
		return returnjson(result);
	} catch (err) {
		return "ERROR: " + err.toString();
	}
	`

	// Execute the script using the new file-based communication method
	result, err := ae.ExecuteScript(script)
	if err != nil {
		return nil, err
	}

	// Extract result
	if resultStr, ok := result.(string); ok {
		// Check if the result indicates an error
		if len(resultStr) > 7 && resultStr[:7] == "ERROR: " {
			return nil, ErrAEScriptError(resultStr[7:])
		}
		
		// Parse the JSON result into a structured object
		var layerInfo LayerInfo
		if err := json.Unmarshal([]byte(resultStr), &layerInfo); err != nil {
			return nil, err
		}
		
		// Check for error in result
		if errMsg, hasErr := layerInfo["error"].(string); hasErr {
			return nil, fmt.Errorf("%s", errMsg)
		}
		
		return layerInfo, nil
	}

	return nil, ErrInvalidResponse
}

// ModifyLayer modifies properties of an existing layer
func ModifyLayer(compositionName string, layerIdentifier LayerIdentifier, properties LayerProperties) (LayerInfo, error) {
	// Convert properties to JavaScript
	propsJSON, err := json.Marshal(properties)
	if err != nil {
		return nil, fmt.Errorf("failed to serialize properties: %w", err)
	}

	// Create layer identification JavaScript code
	var layerIdentifierJS string
	if layerIdentifier.Name != "" {
		layerIdentifierJS = `
		// Find layer by name
		var targetLayer = null;
		for (var i = 1; i <= comp.numLayers; i++) {
			if (comp.layer(i).name === "` + layerIdentifier.Name + `") {
				targetLayer = comp.layer(i);
				break;
			}
		}
		`
	} else if layerIdentifier.Index > 0 {
		layerIdentifierJS = fmt.Sprintf(`
		// Get layer by index
		var targetLayer = comp.layer(%d);
		`, layerIdentifier.Index)
	} else {
		return nil, fmt.Errorf("layer_identifier must have either name or index field: %w", ErrInvalidParams)
	}

	// Execute JavaScript to modify layer
	script := `
	try {
		var compName = "` + compositionName + `";
		var props = ` + string(propsJSON) + `;
		
		// Find the composition
		var project = app.project;
		var comp = null;
		
		for (var i = 1; i <= project.numItems; i++) {
			var item = project.item(i);
			if (item instanceof CompItem && item.name === compName) {
				comp = item;
				break;
			}
		}
		
		if (!comp) {
			return JSON.stringify({
				error: "Composition not found: " + compName
			});
		}
		
		` + layerIdentifierJS + `
		
		if (!targetLayer) {
			return JSON.stringify({
				error: "Layer not found"
			});
		}
		
		// Apply properties
		var result = {
			name: targetLayer.name,
			index: targetLayer.index,
			modified: {}
		};
		
		// Position
		if (props.position) {
			if (targetLayer.position.dimensionsSeparated) {
				// If dimensions are separated, we need to set X, Y, Z separately
				if (props.position[0] !== undefined) {
					targetLayer.transform.xPosition.setValue(props.position[0]);
					result.modified.xPosition = props.position[0];
				}
				if (props.position[1] !== undefined) {
					targetLayer.transform.yPosition.setValue(props.position[1]);
					result.modified.yPosition = props.position[1];
				}
				if (props.position[2] !== undefined && targetLayer.threeDLayer) {
					targetLayer.transform.zPosition.setValue(props.position[2]);
					result.modified.zPosition = props.position[2];
				}
			} else {
				// Set position as array
				targetLayer.position.setValue(props.position);
				result.modified.position = props.position;
			}
		}
		
		// Scale
		if (props.scale) {
			targetLayer.scale.setValue(props.scale);
			result.modified.scale = props.scale;
		}
		
		// Rotation
		if (props.rotation !== undefined) {
			targetLayer.rotation.setValue(props.rotation);
			result.modified.rotation = props.rotation;
		}
		
		// Opacity
		if (props.opacity !== undefined) {
			targetLayer.opacity.setValue(props.opacity);
			result.modified.opacity = props.opacity;
		}
		
		// Enabled
		if (props.enabled !== undefined) {
			targetLayer.enabled = props.enabled;
			result.modified.enabled = props.enabled;
		}
		
		// 3D Layer
		if (props.threeDLayer !== undefined) {
			targetLayer.threeDLayer = props.threeDLayer;
			result.modified.threeDLayer = props.threeDLayer;
		}
		
		return returnjson(result);
	} catch (err) {
		return "ERROR: " + err.toString();
	}
	`

	// Execute the script using the new file-based communication method
	result, err := ae.ExecuteScript(script)
	if err != nil {
		return nil, err
	}

	// Extract result
	if resultStr, ok := result.(string); ok {
		// Check if the result indicates an error
		if len(resultStr) > 7 && resultStr[:7] == "ERROR: " {
			return nil, ErrAEScriptError(resultStr[7:])
		}
		
		// Parse the JSON result into a structured object
		var resultData LayerInfo
		if err := json.Unmarshal([]byte(resultStr), &resultData); err != nil {
			return nil, err
		}
		
		// Check for error in result
		if errMsg, hasErr := resultData["error"].(string); hasErr {
			return nil, fmt.Errorf("%s", errMsg)
		}
		
		return resultData, nil
	}

	return nil, ErrInvalidResponse
}

// ModifyLayerProperty modifies a specific property of a layer using match names
func ModifyLayerProperty(compositionName string, layerIdentifier LayerIdentifier, propertyPath PropertyPath, value interface{}) (LayerInfo, error) {
	// Convert value to JSON string
	valueJSON, err := json.Marshal(value)
	if err != nil {
		return nil, fmt.Errorf("failed to serialize value: %w", err)
	}

	// Convert property path to JSON string
	pathJSON, err := json.Marshal(propertyPath)
	if err != nil {
		return nil, fmt.Errorf("failed to serialize property path: %w", err)
	}

	// Create layer identification JavaScript code
	var layerIdentifierJS string
	if layerIdentifier.Name != "" {
		layerIdentifierJS = `
		// Find layer by name
		var targetLayer = null;
		for (var i = 1; i <= comp.numLayers; i++) {
			if (comp.layer(i).name === "` + layerIdentifier.Name + `") {
				targetLayer = comp.layer(i);
				break;
			}
		}
		`
	} else if layerIdentifier.Index > 0 {
		layerIdentifierJS = fmt.Sprintf(`
		// Get layer by index
		var targetLayer = comp.layer(%d);
		`, layerIdentifier.Index)
	} else {
		return nil, fmt.Errorf("layer_identifier must have either name or index field: %w", ErrInvalidParams)
	}

	script := `
	try {
		var compName = "` + compositionName + `";
		var propPath = ` + string(pathJSON) + `;
		var value = ` + string(valueJSON) + `;
		
		// Find the composition
		var project = app.project;
		var comp = null;
		
		for (var i = 1; i <= project.numItems; i++) {
			var item = project.item(i);
			if (item instanceof CompItem && item.name === compName) {
				comp = item;
				break;
			}
		}
		
		if (!comp) {
			return JSON.stringify({
				error: "Composition not found: " + compName
			});
		}
		
		` + layerIdentifierJS + `
		
		if (!targetLayer) {
			return JSON.stringify({
				error: "Layer not found"
			});
		}
		
		// Navigate to the target property using the property path
		var prop = targetLayer;
		var propNames = [];
		
		for (var i = 0; i < propPath.length; i++) {
			var matchName = propPath[i];
			propNames.push(matchName);
			
			try {
				prop = prop.property(matchName);
			} catch (propErr) {
				return JSON.stringify({
					error: "Property not found: " + propNames.join(" > ")
				});
			}
		}
		
		// Check if we can set this property
		if (!prop.canSetValue) {
			return JSON.stringify({
				error: "Cannot set value for property: " + propNames.join(" > ")
			});
		}
		
		// Set the property value
		prop.setValue(value);
		
		// Return the result
		var result = {
			name: targetLayer.name,
			index: targetLayer.index,
			modified: {
				property: propNames.join(" > "),
				value: value
			}
		};
		
		return returnjson(result);
	} catch (err) {
		return "ERROR: " + err.toString();
	}
	`;

	// Execute the script
	result, err := ae.ExecuteScript(script)
	if err != nil {
		return nil, err
	}

	// Extract result
	if resultStr, ok := result.(string); ok {
		// Check if the result indicates an error
		if len(resultStr) > 7 && resultStr[:7] == "ERROR: " {
			return nil, ErrAEScriptError(resultStr[7:])
		}
		
		// Parse the JSON result into a structured object
		var resultData LayerInfo
		if err := json.Unmarshal([]byte(resultStr), &resultData); err != nil {
			return nil, err
		}
		
		// Check for error in result
		if errMsg, hasErr := resultData["error"].(string); hasErr {
			return nil, fmt.Errorf("%s", errMsg)
		}
		
		return resultData, nil
	}

	return nil, ErrInvalidResponse
}

// GetLayerInfo gets detailed information about a layer
func GetLayerInfo(compositionName string, layerIdentifier LayerIdentifier) (LayerInfo, error) {
	// Create layer identification JavaScript code
	var layerIdentifierJS string
	if layerIdentifier.Name != "" {
		layerIdentifierJS = `
		// Find layer by name
		var targetLayer = null;
		for (var i = 1; i <= comp.numLayers; i++) {
			if (comp.layer(i).name === "` + layerIdentifier.Name + `") {
				targetLayer = comp.layer(i);
				break;
			}
		}
		`
	} else if layerIdentifier.Index > 0 {
		layerIdentifierJS = fmt.Sprintf(`
		// Get layer by index
		var targetLayer = comp.layer(%d);
		`, layerIdentifier.Index)
	} else {
		return nil, fmt.Errorf("layer_identifier must have either name or index field: %w", ErrInvalidParams)
	}

	script := `
	try {
		var compName = "` + compositionName + `";
		
		// Find the composition
		var project = app.project;
		var comp = null;
		
		for (var i = 1; i <= project.numItems; i++) {
			var item = project.item(i);
			if (item instanceof CompItem && item.name === compName) {
				comp = item;
				break;
			}
		}
		
		if (!comp) {
			return JSON.stringify({
				error: "Composition not found: " + compName
			});
		}
		
		` + layerIdentifierJS + `
		
		if (!targetLayer) {
			return JSON.stringify({
				error: "Layer not found"
			});
		}
		
		// Gather layer information
		var layerInfo = {
			name: targetLayer.name,
			index: targetLayer.index,
			enabled: targetLayer.enabled,
			type: getLayerType(targetLayer),
			is3D: targetLayer.threeDLayer,
			transform: {
				position: targetLayer.transform.position.value,
				scale: targetLayer.transform.scale.value,
				rotation: targetLayer.transform.rotation ? targetLayer.transform.rotation.value : null,
				anchor: targetLayer.transform.anchorPoint.value,
				opacity: targetLayer.transform.opacity.value
			}
		};
		
		// Add more specific information based on layer type
		if (targetLayer.parent) {
			layerInfo.parent = {
				index: targetLayer.parent.index,
				name: targetLayer.parent.name
			};
		}
		
		// Get effects
		if (targetLayer.Effects && targetLayer.Effects.numProperties > 0) {
			layerInfo.effects = [];
			for (var i = 1; i <= targetLayer.Effects.numProperties; i++) {
				var effect = targetLayer.Effects.property(i);
				layerInfo.effects.push({
					name: effect.name,
					matchName: effect.matchName,
					enabled: effect.enabled
				});
			}
		}
		
		// Get layer specific info
		if (layerInfo.type === "Text") {
			try {
				var textDocument = targetLayer.property("ADBE Text Properties").property("ADBE Text Document");
				layerInfo.text = {
					value: textDocument.value.text
				};
			} catch (textErr) {
				// Text information not available
			}
		} else if (layerInfo.type === "Shape") {
			// Get shape layer contents
			layerInfo.shapeContents = getShapeContents(targetLayer);
		} else if (layerInfo.type === "Camera") {
			// Get camera properties
			try {
				layerInfo.camera = {
					zoom: targetLayer.property("ADBE Camera Options Group").property("ADBE Camera Zoom").value
				};
			} catch (cameraErr) {
				// Camera information not available
			}
		} else if (layerInfo.type === "Light") {
			// Get light properties
			try {
				layerInfo.light = {
					type: getLightType(targetLayer),
					intensity: targetLayer.property("ADBE Light Options Group").property("ADBE Light Intensity").value,
					color: targetLayer.property("ADBE Light Options Group").property("ADBE Light Color").value
				};
			} catch (lightErr) {
				// Light information not available
			}
		}
		
		return returnjson(layerInfo);
		
		// Helper function to get layer type
		function getLayerType(layer) {
			if (layer instanceof TextLayer) return "Text";
			if (layer instanceof ShapeLayer) return "Shape";
			if (layer instanceof CameraLayer) return "Camera";
			if (layer instanceof LightLayer) return "Light";
			if (layer instanceof AVLayer) {
				if (layer.source && layer.source instanceof CompItem) {
					return "Composition";
				} else if (layer.source && layer.source instanceof SolidSource) {
					return "Solid";
				} else {
					return "AVLayer";
				}
			}
			return "Unknown";
		}
		
		// Helper function to get light type
		function getLightType(lightLayer) {
			var lightType = "Unknown";
			try {
				var coneAngle = lightLayer.property("ADBE Light Options Group").property("ADBE Light Cone Angle");
				if (coneAngle) {
					return "Spot";
				} else {
					// Test for other properties to determine light type
					return "Point"; // Default assumption
				}
			} catch (err) {
				return lightType;
			}
		}
		
		// Helper function to explore shape contents
		function getShapeContents(shapeLayer) {
			var contents = [];
			try {
				var shapesGroup = shapeLayer.property("ADBE Root Vectors Group");
				if (shapesGroup && shapesGroup.numProperties > 0) {
					for (var i = 1; i <= shapesGroup.numProperties; i++) {
						var item = shapesGroup.property(i);
						contents.push({
							name: item.name,
							matchName: item.matchName
						});
					}
				}
			} catch (err) {
				// Error exploring shape contents
			}
			return contents;
		}
	} catch (err) {
		return "ERROR: " + err.toString();
	}
	`;

	// Execute the script
	result, err := ae.ExecuteScript(script)
	if err != nil {
		return nil, err
	}

	// Extract result
	if resultStr, ok := result.(string); ok {
		// Check if the result indicates an error
		if len(resultStr) > 7 && resultStr[:7] == "ERROR: " {
			return nil, ErrAEScriptError(resultStr[7:])
		}
		
		// Parse the JSON result into a structured object
		var layerInfo LayerInfo
		if err := json.Unmarshal([]byte(resultStr), &layerInfo); err != nil {
			return nil, err
		}
		
		// Check for error in result
		if errMsg, hasErr := layerInfo["error"].(string); hasErr {
			return nil, fmt.Errorf("%s", errMsg)
		}
		
		return layerInfo, nil
	}

	return nil, ErrInvalidResponse
}
