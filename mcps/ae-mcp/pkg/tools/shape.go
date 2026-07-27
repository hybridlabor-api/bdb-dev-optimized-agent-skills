package tools

import (
	"encoding/json"
	"fmt"
	"github.com/sunqirui1987/ae-mcp/pkg/ae"
)

// ShapeVertex represents a point in a shape
type ShapeVertex [2]float64

// ShapeTangent represents a direction handle/tangent vector
type ShapeTangent [2]float64

// ShapeData represents the data needed to define a shape
type ShapeData struct {
	Vertices     []ShapeVertex  `json:"vertices"`
	InTangents   []ShapeTangent `json:"inTangents,omitempty"`
	OutTangents  []ShapeTangent `json:"outTangents,omitempty"`
	Closed       bool           `json:"closed"`
	FeatherRadii []float64      `json:"featherRadii,omitempty"`
	FeatherSegLocs []int        `json:"featherSegLocs,omitempty"`
	FeatherRelSegLocs []float64 `json:"featherRelSegLocs,omitempty"`
	FeatherTypes []int          `json:"featherTypes,omitempty"` // 0 for outer, 1 for inner
	FeatherInterps []int        `json:"featherInterps,omitempty"` // 0 for non-Hold, 1 for Hold
	FeatherTensions []float64   `json:"featherTensions,omitempty"`
	FeatherRelCornerAngles []float64 `json:"featherRelCornerAngles,omitempty"`
}

// AddShapeLayer adds a shape layer to a composition
func AddShapeLayer(compositionName string, layerName string, shapeData ShapeData) (LayerInfo, error) {
	// Convert shape data to JSON for passing to JavaScript
	shapeJSON, err := json.Marshal(shapeData)
	if err != nil {
		return nil, fmt.Errorf("failed to serialize shape data: %w", err)
	}
	
	// Execute JavaScript to add shape layer
	script := `
	try {
		var compName = "` + compositionName + `";
		var layerName = "` + layerName + `";
		var shapeData = ` + string(shapeJSON) + `;
		
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
		
		// Create shape layer
		var shapeLayer = comp.layers.addShape();
		shapeLayer.name = layerName;
		
		// Get the contents property (shape group)
		var contents = shapeLayer.property("Contents");
		
		// Add a new shape group
		var shapeGroup = contents.addProperty("ADBE Vector Group");
		shapeGroup.name = "Shape";
		
		// Add a shape path to the group
		var pathGroup = shapeGroup.property("Contents").addProperty("ADBE Vector Shape - Group");
		var shapePath = pathGroup.property("Path");
		
		// Create shape
		var shape = new Shape();
		
		// Convert vertices array to the format After Effects expects
		var vertices = [];
		for (var i = 0; i < shapeData.vertices.length; i++) {
			var x = shapeData.vertices[i][0];
			var y = shapeData.vertices[i][1];
			vertices.push([x, y]);
		}
		
		shape.vertices = vertices;
		
		// Set closed property
		shape.closed = shapeData.closed;
		
		// Set in/out tangents if provided
		if (shapeData.inTangents && shapeData.inTangents.length > 0) {
			var inTangents = [];
			for (var i = 0; i < shapeData.inTangents.length; i++) {
				inTangents.push([shapeData.inTangents[i][0], shapeData.inTangents[i][1]]);
			}
			shape.inTangents = inTangents;
		}
		
		if (shapeData.outTangents && shapeData.outTangents.length > 0) {
			var outTangents = [];
			for (var i = 0; i < shapeData.outTangents.length; i++) {
				outTangents.push([shapeData.outTangents[i][0], shapeData.outTangents[i][1]]);
			}
			shape.outTangents = outTangents;
		}
		
		// Set feather properties if provided
		if (shapeData.featherRadii && shapeData.featherRadii.length > 0) {
			shape.featherRadii = shapeData.featherRadii;
		}
		
		if (shapeData.featherSegLocs && shapeData.featherSegLocs.length > 0) {
			shape.featherSegLocs = shapeData.featherSegLocs;
		}
		
		if (shapeData.featherRelSegLocs && shapeData.featherRelSegLocs.length > 0) {
			shape.featherRelSegLocs = shapeData.featherRelSegLocs;
		}
		
		if (shapeData.featherTypes && shapeData.featherTypes.length > 0) {
			shape.featherTypes = shapeData.featherTypes;
		}
		
		if (shapeData.featherInterps && shapeData.featherInterps.length > 0) {
			shape.featherInterps = shapeData.featherInterps;
		}
		
		if (shapeData.featherTensions && shapeData.featherTensions.length > 0) {
			shape.featherTensions = shapeData.featherTensions;
		}
		
		if (shapeData.featherRelCornerAngles && shapeData.featherRelCornerAngles.length > 0) {
			shape.featherRelCornerAngles = shapeData.featherRelCornerAngles;
		}
		
		// Apply the shape to the path property
		shapePath.setValue(shape);
		
		// 添加完成形状后，将图层移动到合成的左上角
		shapeLayer.transform.position.setValue([0, 0, 0]);
		
		// 使用锚点来调整图形位置，使它们相对于左上角定位
		var shapeBounds = shapeLayer.sourceRectAtTime(0, false);
		shapeLayer.transform.anchorPoint.setValue([shapeBounds.left, shapeBounds.top, 0]);
		
		// Return layer info
		var result = {
			name: shapeLayer.name,
			index: shapeLayer.index,
			enabled: shapeLayer.enabled,
			shapeType: "custom",
			vertices: shape.vertices.length
		};
		
		return returnjson(result);
	} catch (err) {
		// Get the error message and stack trace
		var errorMsg = "ERROR: " + err.toString();
		
		// Add stack trace if available
		if (err.stack) {
			errorMsg += "\nStack: " + err.stack;
		}
		
		// Add debugging info about shape data
		try {
			errorMsg += "\nShape Vertices Count: " + (shapeData.vertices ? shapeData.vertices.length : "undefined");
			if (shapeData.vertices && shapeData.vertices.length > 0) {
				errorMsg += "\nFirst Vertex: " + JSON.stringify(shapeData.vertices[0]);
			}
		} catch (debugErr) {
			errorMsg += "\nError getting debug info: " + debugErr.toString();
		}
		
		return errorMsg;
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

// AddPresetShapeLayer adds a preset shape (rectangle, oval, etc.) as a shape layer
func AddPresetShapeLayer(compositionName string, layerName string, shapeType string, width float64, height float64) (LayerInfo, error) {
	// Execute JavaScript to add a preset shape layer
	script := `
	try {
		var compName = "` + compositionName + `";
		var layerName = "` + layerName + `";
		var shapeType = "` + shapeType + `";
		var width = ` + fmt.Sprintf("%f", width) + `;
		var height = ` + fmt.Sprintf("%f", height) + `;
		
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
		
		// Create shape layer
		var shapeLayer = comp.layers.addShape();
		shapeLayer.name = layerName;
		
		// Get the contents property
		var contents = shapeLayer.property("Contents");
		
		// Create a shape group
		var shapeGroup = contents.addProperty("ADBE Vector Group");
		shapeGroup.name = shapeType;
		var shapeContents = shapeGroup.property("Contents");
		
		// Add the appropriate shape based on type
		if (shapeType === "rectangle") {
			var rectGroup = shapeContents.addProperty("ADBE Vector Shape - Rect");
			
			// 设置矩形尺寸
			var rectSize = [width, height];
			// 将位置放在左上角(已经考虑了形状大小的一半)
			var rectPosition = [width/2, height/2]; 
			
			rectGroup.property("Size").setValue(rectSize);
			rectGroup.property("Position").setValue(rectPosition);
		} 
		else if (shapeType === "ellipse") {
			var ellipseGroup = shapeContents.addProperty("ADBE Vector Shape - Ellipse");
			
			// 设置椭圆尺寸
			var ellipseSize = [width, height];
			// 将位置放在左上角(已经考虑了形状大小的一半)
			var ellipsePosition = [width/2, height/2];
			
			ellipseGroup.property("Size").setValue(ellipseSize);
			ellipseGroup.property("Position").setValue(ellipsePosition);
		}
		else if (shapeType === "polygon") {
			var polygonGroup = shapeContents.addProperty("ADBE Vector Shape - Star");
			
			// 将位置放在左上角，考虑半径
			var position = [width/2, height/2];
			
			polygonGroup.property("Type").setValue(1); // Polygon type
			polygonGroup.property("Points").setValue(6); // 6-sided polygon by default
			polygonGroup.property("Position").setValue(position);
			polygonGroup.property("Outer Radius").setValue(width/2);
			polygonGroup.property("Outer Roundness").setValue(0);
		}
		else if (shapeType === "star") {
			var starGroup = shapeContents.addProperty("ADBE Vector Shape - Star");
			
			// 将位置放在左上角，考虑半径
			var position = [width/2, height/2];
			
			starGroup.property("Type").setValue(2); // Star type
			starGroup.property("Points").setValue(5); // 5-pointed star by default
			starGroup.property("Position").setValue(position);
			starGroup.property("Outer Radius").setValue(width/2);
			starGroup.property("Inner Radius").setValue(width/4);
			starGroup.property("Outer Roundness").setValue(0);
			starGroup.property("Inner Roundness").setValue(0);
		}
		else {
			return JSON.stringify({
				error: "Unsupported shape type: " + shapeType
			});
		}
		
		// Add fill to the shape group
		var fillGroup = shapeContents.addProperty("ADBE Vector Graphic - Fill");
		fillGroup.property("Color").setValue([1, 1, 1, 1]); // White
		
		// Add stroke to the shape group
		var strokeGroup = shapeContents.addProperty("ADBE Vector Graphic - Stroke");
		strokeGroup.property("Color").setValue([0, 0, 0, 1]); // Black
		strokeGroup.property("Stroke Width").setValue(2);
		
		// 添加完成形状后，将图层移动到合成的左上角
		shapeLayer.transform.position.setValue([0, 0, 0]);
		
		// 使用锚点来调整图形位置，使它们相对于左上角定位
		var shapeBounds = shapeLayer.sourceRectAtTime(0, false);
		shapeLayer.transform.anchorPoint.setValue([shapeBounds.left, shapeBounds.top, 0]);
		
		// Return layer info
		var result = {
			name: shapeLayer.name,
			index: shapeLayer.index,
			enabled: shapeLayer.enabled,
			shapeType: shapeType
		};
		
		return JSON.stringify(result);
	} catch (err) {
		// Get the error message and stack trace
		var errorMsg = "ERROR: " + err.toString();
		
		// Add stack trace if available
		if (err.stack) {
			errorMsg += "\nStack: " + err.stack;
		}
		
		// Add debugging info 
		try {
			errorMsg += "\nShape Type: " + shapeType;
			errorMsg += "\nWidth: " + width;
			errorMsg += "\nHeight: " + height;
		} catch (debugErr) {
			errorMsg += "\nError getting debug info: " + debugErr.toString();
		}
		
		return errorMsg;
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

// MCP Function Definitions

// MCPAddCustomShapeLayer adds a custom shape layer to a composition via MCP
func MCPAddCustomShapeLayer(args map[string]interface{}) (interface{}, error) {
	// Get required parameters
	compositionName, ok := args["composition_name"].(string)
	if !ok || compositionName == "" {
		return nil, ErrInvalidParams
	}
	
	layerName, ok := args["layer_name"].(string)
	if !ok || layerName == "" {
		return nil, ErrInvalidParams
	}
	
	// Get vertices from args
	verticesRaw, ok := args["vertices"].([]interface{})
	if !ok {
		return nil, fmt.Errorf("vertices parameter is required")
	}
	
	vertices := make([]ShapeVertex, len(verticesRaw))
	for i, v := range verticesRaw {
		if point, ok := v.([]interface{}); ok && len(point) == 2 {
			x, xOk := point[0].(float64)
			y, yOk := point[1].(float64)
			
			if xOk && yOk {
				vertices[i] = ShapeVertex{x, y}
			} else {
				return nil, fmt.Errorf("invalid vertex format at index %d", i)
			}
		} else {
			return nil, fmt.Errorf("invalid vertex format at index %d", i)
		}
	}
	
	// Create shape data with mandatory fields
	shapeData := ShapeData{
		Vertices: vertices,
		Closed:   true, // default to closed shape
	}
	
	// Check if closed property is provided
	if closed, ok := args["closed"].(bool); ok {
		shapeData.Closed = closed
	}
	
	// Handle optional in tangents
	if inTangentsRaw, ok := args["in_tangents"].([]interface{}); ok {
		inTangents := make([]ShapeTangent, len(inTangentsRaw))
		for i, t := range inTangentsRaw {
			if point, ok := t.([]interface{}); ok && len(point) == 2 {
				x, xOk := point[0].(float64)
				y, yOk := point[1].(float64)
				
				if xOk && yOk {
					inTangents[i] = ShapeTangent{x, y}
				} else {
					return nil, fmt.Errorf("invalid in_tangent format at index %d", i)
				}
			} else {
				return nil, fmt.Errorf("invalid in_tangent format at index %d", i)
			}
		}
		shapeData.InTangents = inTangents
	}
	
	// Handle optional out tangents
	if outTangentsRaw, ok := args["out_tangents"].([]interface{}); ok {
		outTangents := make([]ShapeTangent, len(outTangentsRaw))
		for i, t := range outTangentsRaw {
			if point, ok := t.([]interface{}); ok && len(point) == 2 {
				x, xOk := point[0].(float64)
				y, yOk := point[1].(float64)
				
				if xOk && yOk {
					outTangents[i] = ShapeTangent{x, y}
				} else {
					return nil, fmt.Errorf("invalid out_tangent format at index %d", i)
				}
			} else {
				return nil, fmt.Errorf("invalid out_tangent format at index %d", i)
			}
		}
		shapeData.OutTangents = outTangents
	}
	
	// Handle feather properties (advanced)
	if featherRadiiRaw, ok := args["feather_radii"].([]interface{}); ok {
		featherRadii := make([]float64, len(featherRadiiRaw))
		for i, r := range featherRadiiRaw {
			if radius, ok := r.(float64); ok {
				featherRadii[i] = radius
			} else {
				return nil, fmt.Errorf("invalid feather radius at index %d", i)
			}
		}
		shapeData.FeatherRadii = featherRadii
	}
	
	// Add the shape layer
	return AddShapeLayer(compositionName, layerName, shapeData)
}

// MCPAddPresetShapeLayer adds a preset shape layer to a composition via MCP
func MCPAddPresetShapeLayer(args map[string]interface{}) (interface{}, error) {
	// Get required parameters
	compositionName, ok := args["composition_name"].(string)
	if !ok || compositionName == "" {
		return nil, ErrInvalidParams
	}
	
	layerName, ok := args["layer_name"].(string)
	if !ok || layerName == "" {
		return nil, ErrInvalidParams
	}
	
	shapeType, ok := args["shape_type"].(string)
	if !ok || shapeType == "" {
		return nil, fmt.Errorf("shape_type parameter is required")
	}
	
	// Validate shape type
	validShapeTypes := map[string]bool{
		"rectangle": true,
		"ellipse":   true,
		"polygon":   true,
		"star":      true,
	}
	
	if !validShapeTypes[shapeType] {
		return nil, fmt.Errorf("invalid shape type: %s. Must be one of: rectangle, ellipse, polygon, star", shapeType)
	}
	
	// Get dimensions with defaults
	width := float64(100) // Default width
	height := float64(100) // Default height
	
	if widthRaw, ok := args["width"].(float64); ok && widthRaw > 0 {
		width = widthRaw
	}
	
	if heightRaw, ok := args["height"].(float64); ok && heightRaw > 0 {
		height = heightRaw
	}
	
	// Add the preset shape layer
	return AddPresetShapeLayer(compositionName, layerName, shapeType, width, height)
} 