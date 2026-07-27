package tools

import (
	"encoding/json"
	"fmt"
	"github.com/sunqirui1987/ae-mcp/pkg/ae"
)

// TextLayerInfo represents information about a text layer
type TextLayerInfo map[string]interface{}

// TextOptions represents options for text layer creation or modification
type TextOptions struct {
	// Text appearance
	FontSize      float64   `json:"fontSize,omitempty"`
	FontName      string    `json:"fontName,omitempty"`
	FontFamily    string    `json:"fontFamily,omitempty"`
	FontStyle     string    `json:"fontStyle,omitempty"`
	Color         ColorRGB  `json:"color,omitempty"`
	FillColor     ColorRGB  `json:"fillColor,omitempty"`
	StrokeColor   ColorRGB  `json:"strokeColor,omitempty"`
	StrokeWidth   float64   `json:"strokeWidth,omitempty"`
	ApplyFill     *bool     `json:"applyFill,omitempty"`
	ApplyStroke   *bool     `json:"applyStroke,omitempty"`
	Tracking      float64   `json:"tracking,omitempty"`
	Leading       float64   `json:"leading,omitempty"`
	
	// Text positioning
	Position      [2]float64 `json:"position,omitempty"`
	Justification string    `json:"justification,omitempty"`
	
	// Text styling
	FauxBold     *bool    `json:"fauxBold,omitempty"`
	FauxItalic   *bool    `json:"fauxItalic,omitempty"`
	AllCaps      *bool    `json:"allCaps,omitempty"`
	SmallCaps    *bool    `json:"smallCaps,omitempty"`
}

// TextModifications represents modifications to be applied to a text layer
type TextModifications map[string]interface{}

// AddTextLayer adds a text layer to a composition
func AddTextLayer(compName string, layerName string, text string, options *TextOptions) (TextLayerInfo, error) {
	// Default options
	fontSize := 72.0
	fontName := "Arial"
	color := [3]float64{1.0, 1.0, 1.0} // White
	position := [2]float64{0.0, 0.0}    // Center
	justification := "CENTER_JUSTIFY" // Valid values: LEFT_JUSTIFY, CENTER_JUSTIFY, RIGHT_JUSTIFY
	applyFill := true
	tracking := 0.0
	
	// Apply provided options if available
	if options != nil {
		if options.FontSize > 0 {
			fontSize = options.FontSize
		}
		if options.FontName != "" {
			fontName = options.FontName
		}
		if options.FontFamily != "" {
			fontName = options.FontFamily // Use fontFamily if provided
		}
		if options.Color != [3]float64{0, 0, 0} {
			color = options.Color
		}
		if options.FillColor != [3]float64{0, 0, 0} {
			color = options.FillColor // Use fillColor if provided
		}
		if options.Position != [2]float64{0, 0} {
			position = options.Position
		}
		if options.Justification != "" {
			// Make sure the justification has _JUSTIFY suffix
			if options.Justification == "LEFT" {
				justification = "LEFT_JUSTIFY"
			} else if options.Justification == "CENTER" {
				justification = "CENTER_JUSTIFY"
			} else if options.Justification == "RIGHT" {
				justification = "RIGHT_JUSTIFY"
			} else {
				justification = options.Justification
			}
		}
		if options.ApplyFill != nil {
			applyFill = *options.ApplyFill
		}
		if options.Tracking != 0 {
			tracking = options.Tracking
		}
	}

	// Construct the script to add a text layer
	script := `
	try {
		var compName = "` + compName + `";
		var layerName = "` + layerName + `";
		var textContent = "` + escapeJSString(text) + `";
		var fontSize = ` + fmt.Sprintf("%f", fontSize) + `;
		var fontName = "` + fontName + `";
		var color = [` + fmt.Sprintf("%f, %f, %f", color[0], color[1], color[2]) + `];
		var position = [` + fmt.Sprintf("%f, %f", position[0], position[1]) + `];
		var justification = ParagraphJustification.` + justification + `;
		var applyFill = ` + fmt.Sprintf("%t", applyFill) + `;
		var tracking = ` + fmt.Sprintf("%f", tracking) + `;
		
		// Find the composition
		var comp = null;
		for (var i = 1; i <= app.project.numItems; i++) {
			var item = app.project.item(i);
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
		
		// Add the text layer
		var textLayer = comp.layers.addText(textContent);
		textLayer.name = layerName;
		var textProp = textLayer.property("Source Text");
		var textDocument = textProp.value;
		
		// Set text properties
		textDocument.fontSize = fontSize;
		textDocument.font = fontName;
		textDocument.applyFill = applyFill;
		textDocument.fillColor = color;
		textDocument.justification = justification;
		textDocument.tracking = tracking;
		
		// Apply additional properties if provided
		` + getAdditionalTextProperties(options) + `
		
		// Apply the text document
		textProp.setValue(textDocument);
		
		// Set position if specified
		if (position[0] !== 0 || position[1] !== 0) {
			textLayer.position.setValue([position[0], position[1], 0]);
		} else {
			// Center the text in the composition
			textLayer.position.setValue([comp.width/2, comp.height/2, 0]);
		}
		
		// Return information about the created text layer
		var result = {
			name: textLayer.name,
			index: textLayer.index,
			id: textLayer.index,
			text: textContent,
			fontSize: fontSize,
			fontName: fontName
		};
		
		return returnjson(result);
	} catch (err) {
		return "ERROR: " + err.toString();
	}
	`

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
		var textLayerDetails TextLayerInfo
		if err := json.Unmarshal([]byte(resultStr), &textLayerDetails); err != nil {
			return nil, err
		}
		
		// Check for error in result
		if errMsg, hasErr := textLayerDetails["error"].(string); hasErr {
			return nil, fmt.Errorf("%s", errMsg)
		}
		
		return textLayerDetails, nil
	}

	return nil, ErrInvalidResponse
}

// Helper function to generate additional text property settings based on options
func getAdditionalTextProperties(options *TextOptions) string {
	if options == nil {
		return ""
	}
	
	var script string
	
	// Font style - handle it by using fauxBold and fauxItalic
	if options.FontStyle != "" {
		if options.FontStyle == "Bold" || options.FontStyle == "bold" {
			script += `
		textDocument.fauxBold = true;`
		} else if options.FontStyle == "Italic" || options.FontStyle == "italic" {
			script += `
		textDocument.fauxItalic = true;`
		} else if options.FontStyle == "Bold Italic" || options.FontStyle == "bold italic" || options.FontStyle == "Bold-Italic" {
			script += `
		textDocument.fauxBold = true;
		textDocument.fauxItalic = true;`
		}
		// Otherwise, use regular font weight (no need to set anything)
	}
	
	// Stroke properties
	if options.ApplyStroke != nil {
		script += `
		textDocument.applyStroke = ` + fmt.Sprintf("%t", *options.ApplyStroke) + `;`
	}
	
	if options.StrokeColor != [3]float64{0, 0, 0} {
		script += `
		textDocument.strokeColor = [` + fmt.Sprintf("%f, %f, %f", options.StrokeColor[0], options.StrokeColor[1], options.StrokeColor[2]) + `];`
	}
	
	if options.StrokeWidth > 0 {
		script += `
		textDocument.strokeWidth = ` + fmt.Sprintf("%f", options.StrokeWidth) + `;`
	}
	
	// Text styling
	if options.FauxBold != nil {
		script += `
		textDocument.fauxBold = ` + fmt.Sprintf("%t", *options.FauxBold) + `;`
	}
	
	if options.FauxItalic != nil {
		script += `
		textDocument.fauxItalic = ` + fmt.Sprintf("%t", *options.FauxItalic) + `;`
	}
	
	if options.AllCaps != nil {
		script += `
		textDocument.allCaps = ` + fmt.Sprintf("%t", *options.AllCaps) + `;`
	}
	
	if options.SmallCaps != nil {
		script += `
		textDocument.smallCaps = ` + fmt.Sprintf("%t", *options.SmallCaps) + `;`
	}
	
	if options.Leading > 0 {
		script += `
		textDocument.leading = ` + fmt.Sprintf("%f", options.Leading) + `;`
	}
	
	return script
}

// ModifyTextLayer modifies an existing text layer in a composition
func ModifyTextLayer(compName string, layerName string, modifications TextModifications) (TextLayerInfo, error) {
	// Build the script
	script := `
	try {
		var compName = "` + compName + `";
		var layerName = "` + layerName + `";
		
		// Find the composition
		var comp = null;
		for (var i = 1; i <= app.project.numItems; i++) {
			var item = app.project.item(i);
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
		
		// Find the text layer
		var textLayer = null;
		for (var i = 1; i <= comp.numLayers; i++) {
			var layer = comp.layer(i);
			if (layer.name === layerName) {
				textLayer = layer;
				break;
			}
		}
		
		if (!textLayer) {
			return JSON.stringify({
				error: "Layer not found: " + layerName
			});
		}
		
		// Check if this is actually a text layer
		if (!textLayer.property("Source Text")) {
			return JSON.stringify({
				error: "Layer is not a text layer: " + layerName
			});
		}
		
		// Get the text document
		var textProp = textLayer.property("Source Text");
		var textDocument = textProp.value;
		
		// Apply modifications
		var modified = false;
	`

	// Add modifications to the script
	if text, ok := modifications["text"].(string); ok {
		script += `
		textDocument.text = "` + escapeJSString(text) + `";
		modified = true;
		`
	}

	if fontSize, ok := modifications["fontSize"].(float64); ok {
		script += `
		textDocument.fontSize = ` + fmt.Sprintf("%f", fontSize) + `;
		modified = true;
		`
	}

	if fontName, ok := modifications["fontName"].(string); ok {
		script += `
		textDocument.font = "` + fontName + `";
		modified = true;
		`
	}
	
	// Handle fontFamily as an alias for font
	if fontFamily, ok := modifications["fontFamily"].(string); ok {
		script += `
		textDocument.font = "` + fontFamily + `";
		modified = true;
		`
	}
	
	// Handle fontStyle by converting it to fauxBold and fauxItalic
	if fontStyle, ok := modifications["fontStyle"].(string); ok {
		// Instead of trying to set read-only fontStyle property directly,
		// we use fauxBold and fauxItalic based on the style name
		if fontStyle == "Bold" || fontStyle == "bold" {
			script += `
			textDocument.fauxBold = true;
			modified = true;
			`
		} else if fontStyle == "Italic" || fontStyle == "italic" {
			script += `
			textDocument.fauxItalic = true;
			modified = true;
			`
		} else if fontStyle == "Bold Italic" || fontStyle == "bold italic" || fontStyle == "Bold-Italic" {
			script += `
			textDocument.fauxBold = true;
			textDocument.fauxItalic = true;
			modified = true;
			`
		}
		// Otherwise, do nothing as we can't directly set fontStyle
	}

	// Handle color object or fillColor
	if color, ok := modifications["color"].([]interface{}); ok && len(color) >= 3 {
		r, _ := color[0].(float64)
		g, _ := color[1].(float64)
		b, _ := color[2].(float64)
		script += `
		textDocument.fillColor = [` + fmt.Sprintf("%f, %f, %f", r, g, b) + `];
		modified = true;
		`
	}
	
	if fillColor, ok := modifications["fillColor"].(ColorRGB); ok {
		script += `
		textDocument.fillColor = [` + fmt.Sprintf("%f, %f, %f", fillColor[0], fillColor[1], fillColor[2]) + `];
		modified = true;
		`
	}
	
	// Handle applyFill
	if applyFill, ok := modifications["applyFill"].(bool); ok {
		script += `
		textDocument.applyFill = ` + fmt.Sprintf("%t", applyFill) + `;
		modified = true;
		`
	}
	
	// Handle stroke properties
	if applyStroke, ok := modifications["applyStroke"].(bool); ok {
		script += `
		textDocument.applyStroke = ` + fmt.Sprintf("%t", applyStroke) + `;
		modified = true;
		`
	}
	
	if strokeColor, ok := modifications["strokeColor"].(ColorRGB); ok {
		script += `
		textDocument.strokeColor = [` + fmt.Sprintf("%f, %f, %f", strokeColor[0], strokeColor[1], strokeColor[2]) + `];
		modified = true;
		`
	}
	
	if strokeWidth, ok := modifications["strokeWidth"].(float64); ok {
		script += `
		textDocument.strokeWidth = ` + fmt.Sprintf("%f", strokeWidth) + `;
		modified = true;
		`
	}

	if justification, ok := modifications["justification"].(string); ok {
		// Make sure the justification has _JUSTIFY suffix
		var justificationValue string
		if justification == "LEFT" {
			justificationValue = "LEFT_JUSTIFY"
		} else if justification == "CENTER" {
			justificationValue = "CENTER_JUSTIFY"
		} else if justification == "RIGHT" {
			justificationValue = "RIGHT_JUSTIFY"
		} else {
			justificationValue = justification
		}
		
		script += `
		textDocument.justification = ParagraphJustification.` + justificationValue + `;
		modified = true;
		`
	}

	if position, ok := modifications["position"].([]interface{}); ok && len(position) >= 2 {
		x, _ := position[0].(float64)
		y, _ := position[1].(float64)
		script += `
		textLayer.position.setValue([` + fmt.Sprintf("%f, %f, 0", x, y) + `]);
		modified = true;
		`
	}
	
	// Handle tracking (letter spacing)
	if tracking, ok := modifications["tracking"].(float64); ok {
		script += `
		textDocument.tracking = ` + fmt.Sprintf("%f", tracking) + `;
		modified = true;
		`
	}
	
	// Handle leading (line spacing)
	if leading, ok := modifications["leading"].(float64); ok {
		script += `
		textDocument.leading = ` + fmt.Sprintf("%f", leading) + `;
		modified = true;
		`
	}
	
	// Handle text styling options
	if fauxBold, ok := modifications["fauxBold"].(bool); ok {
		script += `
		textDocument.fauxBold = ` + fmt.Sprintf("%t", fauxBold) + `;
		modified = true;
		`
	}
	
	if fauxItalic, ok := modifications["fauxItalic"].(bool); ok {
		script += `
		textDocument.fauxItalic = ` + fmt.Sprintf("%t", fauxItalic) + `;
		modified = true;
		`
	}
	
	if allCaps, ok := modifications["allCaps"].(bool); ok {
		script += `
		textDocument.allCaps = ` + fmt.Sprintf("%t", allCaps) + `;
		modified = true;
		`
	}
	
	if smallCaps, ok := modifications["smallCaps"].(bool); ok {
		script += `
		textDocument.smallCaps = ` + fmt.Sprintf("%t", smallCaps) + `;
		modified = true;
		`
	}

	// Complete the script
	script += `
		// Apply the text document if modified
		if (modified) {
			textProp.setValue(textDocument);
		}
		
		// Return information about the modified text layer
		var result = {
			name: textLayer.name,
			index: textLayer.index,
			id: textLayer.index,
			text: textDocument.text,
			fontSize: textDocument.fontSize,
			fontName: textDocument.font
		};
		
		return returnjson(result);
	} catch (err) {
		return "ERROR: " + err.toString();
	}
	`

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
		var textLayerDetails TextLayerInfo
		if err := json.Unmarshal([]byte(resultStr), &textLayerDetails); err != nil {
			return nil, err
		}
		
		// Check for error in result
		if errMsg, hasErr := textLayerDetails["error"].(string); hasErr {
			return nil, fmt.Errorf("%s", errMsg)
		}
		
		return textLayerDetails, nil
	}

	return nil, ErrInvalidResponse
}

// Helper function to escape special characters in JS strings
func escapeJSString(s string) string {
	// Implement string escaping for JavaScript
	// This is a simple implementation; you might want to make it more robust
	result := ""
	for _, c := range s {
		switch c {
		case '\\':
			result += "\\\\"
		case '"':
			result += "\\\""
		case '\'':
			result += "\\'"
		case '\n':
			result += "\\n"
		case '\r':
			result += "\\r"
		case '\t':
			result += "\\t"
		default:
			result += string(c)
		}
	}
	return result
} 