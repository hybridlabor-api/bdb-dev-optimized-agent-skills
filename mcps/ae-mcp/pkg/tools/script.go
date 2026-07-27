package tools

import (
	"encoding/json"
	"github.com/sunqirui1987/ae-mcp/pkg/ae"
)

// ScriptResult represents the result of an executed script
type ScriptResult map[string]interface{}

// ExecuteScript executes arbitrary JavaScript code in After Effects
func ExecuteScript(script string) (ScriptResult, error) {
	// Wrap the provided script in a try-catch block to handle errors
	wrappedScript := `
	try {
		// Execute the user's script
		var result = (function() {
			` + script + `
		})();
		
		// If the result is already a string, return it directly
		if (typeof result === "string") {
			return result;
		}
		
		// Otherwise, convert it to JSON
		return returnjson(result || {});
	} catch (err) {
		return "ERROR: " + err.toString();
	}
	`

	// Execute the script using the ae package's ExecuteScript function
	result, err := ae.ExecuteScript(wrappedScript)
	if err != nil {
		return nil, err
	}

	// Extract result
	if resultStr, ok := result.(string); ok {
		// Check if the result indicates an error
		if len(resultStr) > 7 && resultStr[:7] == "ERROR: " {
			return nil, ErrAEScriptError(resultStr[7:])
		}
		
		// Try to parse the JSON result into a structured object
		var scriptResult ScriptResult
		if err := json.Unmarshal([]byte(resultStr), &scriptResult); err != nil {
			// If it's not valid JSON, return a result with the raw string
			return ScriptResult{"rawResult": resultStr}, nil
		}
		
		return scriptResult, nil
	}

	return nil, ErrInvalidResponse
}
