// package tools provides the implementation of After Effects operations
package tools

import (
	"encoding/json"
	"github.com/sunqirui1987/ae-mcp/pkg/ae"
)

// ProjectInfo represents information about an After Effects project
type ProjectInfo map[string]interface{}

// GetProjectInfo retrieves information about the current After Effects project
func GetProjectInfo() (ProjectInfo, error) {
	// Execute JavaScript to get project information
	script := `
	try {
		var project = app.project;
		var result = {
			name: project.file ? project.file.name : "Untitled Project",
			path: project.file ? project.file.fsName : "",
			numItems: project.numItems,
			bitsPerChannel: project.bitsPerChannel,
			frameRate: project.frameRate,
			activeItem: project.activeItem ? project.activeItem.name : null,
			workingSpace: project.workingSpace
		};
		
		// Get composition list
		result.compositions = [];
		for (var i = 1; i <= project.numItems; i++) {
			var item = project.item(i);
			if (item instanceof CompItem) {
				result.compositions.push({
					name: item.name,
					id: i,
					duration: item.duration,
					width: item.width,
					height: item.height,
					frameRate: item.frameRate
				});
			}
		}
		
		// Use the new returnjson function to properly return JSON data
		var jsonstr =  returnjson(result);
		//alert(jsonstr);
		return jsonstr;
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
		var projectInfo ProjectInfo
		if err := json.Unmarshal([]byte(resultStr), &projectInfo); err != nil {
			return nil, err
		}
		
		return projectInfo, nil
	}

	return nil, ErrInvalidResponse
} 