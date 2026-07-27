package tools

import (
	"encoding/json"
	"fmt"
	"github.com/sunqirui1987/ae-mcp/pkg/ae"
)

// CompositionDetails represents the details of an After Effects composition
type CompositionDetails map[string]interface{}


// CreateComposition creates a new composition in After Effects
func CreateComposition(name string, width int, height int, duration float64, frameRate float64) (CompositionDetails, error) {
	// Execute JavaScript to create composition
	script := `
	try {
		var name = "` + name + `";
		var width = ` + fmt.Sprintf("%d", width) + `;
		var height = ` + fmt.Sprintf("%d", height) + `;
		var duration = ` + fmt.Sprintf("%f", duration) + `;
		var frameRate = ` + fmt.Sprintf("%f", frameRate) + `;
		
		// Create the composition
		var project = app.project;
		var comp = project.items.addComp(name, width, height, 1, duration, frameRate);
		
		// Return the new composition details
		var result = {
			name: comp.name,
			id: comp.id,
			duration: comp.duration,
			width: comp.width,
			height: comp.height,
			frameRate: comp.frameRate
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
		var compDetails CompositionDetails
		if err := json.Unmarshal([]byte(resultStr), &compDetails); err != nil {
			return nil, err
		}
		
		return compDetails, nil
	}

	return nil, ErrInvalidResponse
}
