// ae/utils.go provides utility functions for communicating with After Effects
package ae

import (
    "encoding/json"
    "fmt"
    "os"
    "path/filepath"
    "time"
    "io/ioutil"

    "errors"
)

// MCPFolders holds the paths for MCP communication
type MCPFolders struct {
    BaseFolder     string
    RequestsFolder string
    ResponsesFolder string
    InfoFile       string
}

// GetMCPFolders returns the default folders for MCP communication
func GetMCPFolders() (MCPFolders, error) {
    // Default location is in user's documents folder
    homeDir, err := os.UserHomeDir()
    if err != nil {
        return MCPFolders{}, fmt.Errorf("failed to get user home directory: %w", err)
    }

    // Build paths
    baseFolder := filepath.Join(homeDir, "Documents", "AE-MCP")
    
    // Allow override via environment variable
    if envFolder := os.Getenv("AE_MCP_FOLDER"); envFolder != "" {
        baseFolder = envFolder
    }
    
    folders := MCPFolders{
        BaseFolder:      baseFolder,
        RequestsFolder:  filepath.Join(baseFolder, "requests"),
        ResponsesFolder: filepath.Join(baseFolder, "responses"),
        InfoFile:        filepath.Join(baseFolder, "ae-mcp-info.json"),
    }
    
    return folders, nil
}

// EnsureFoldersExist creates the required folders if they don't exist
func EnsureFoldersExist(folders MCPFolders) error {
    // Create base folder if it doesn't exist
    if _, err := os.Stat(folders.BaseFolder); os.IsNotExist(err) {
        if err := os.MkdirAll(folders.BaseFolder, 0755); err != nil {
            return fmt.Errorf("failed to create base folder: %w", err)
        }
    }
    
    // Create requests folder if it doesn't exist
    if _, err := os.Stat(folders.RequestsFolder); os.IsNotExist(err) {
        if err := os.MkdirAll(folders.RequestsFolder, 0755); err != nil {
            return fmt.Errorf("failed to create requests folder: %w", err)
        }
    }
    
    // Create responses folder if it doesn't exist
    if _, err := os.Stat(folders.ResponsesFolder); os.IsNotExist(err) {
        if err := os.MkdirAll(folders.ResponsesFolder, 0755); err != nil {
            return fmt.Errorf("failed to create responses folder: %w", err)
        }
    }
    
    return nil
}

// CheckMCPRunning checks if After Effects MCP service is running
func CheckMCPRunning(folders MCPFolders) (bool, error) {
    // Check if info file exists
    infoData, err := ioutil.ReadFile(folders.InfoFile)
    if err != nil {
        if os.IsNotExist(err) {
            return false, nil // Info file doesn't exist, service not running
        }
        return false, fmt.Errorf("failed to read info file: %w", err)
    }
    
    // Parse info file
    var info map[string]interface{}
    if err := json.Unmarshal(infoData, &info); err != nil {
        return false, fmt.Errorf("failed to parse info file: %w", err)
    }
    
    // Check if status is running
    if status, ok := info["status"].(string); ok && status == "running" {
        return true, nil
    }
    
    return false, nil
}

// SendCommand sends a command to After Effects using file-based communication
func SendCommand(cmd map[string]interface{}) (map[string]interface{}, error) {
    // Get MCP folders
    folders, err := GetMCPFolders()
    if err != nil {
        return nil, err
    }
    
    // Ensure folders exist
    if err := EnsureFoldersExist(folders); err != nil {
        return nil, err
    }
    
    // Check if MCP is running
    running, err := CheckMCPRunning(folders)
    if err != nil {
        return nil, err
    }
    if !running {
        return nil, errors.New("After Effects MCP service is not running")
    }
    
    // Generate a unique ID for this command
    requestID := fmt.Sprintf("go_%d_%d", time.Now().UnixNano(), os.Getpid())
    cmd["id"] = requestID
    cmd["timestamp"] = time.Now().UnixMilli()
    
    // Convert command to JSON
    cmdBytes, err := json.MarshalIndent(cmd, "", "  ")
    if err != nil {
        return nil, fmt.Errorf("failed to marshal command: %w", err)
    }
    
    // Write command to request file
    requestFile := filepath.Join(folders.RequestsFolder, requestID+".json")
    if err := ioutil.WriteFile(requestFile, cmdBytes, 0644); err != nil {
        return nil, fmt.Errorf("failed to write request file: %w", err)
    }
    
    // Wait for response file (with timeout)
    responseFile := filepath.Join(folders.ResponsesFolder, requestID+".json")
    timeout := time.After(30 * time.Second)
    tick := time.Tick(100 * time.Millisecond)
    
    for {
        select {
        case <-timeout:
            return nil, errors.New("timeout waiting for After Effects response")
        case <-tick:
            // Check if response file exists
            if _, err := os.Stat(responseFile); err == nil {
                // Response file exists, read it
                responseData, err := ioutil.ReadFile(responseFile)
                if err != nil {
                    return nil, fmt.Errorf("failed to read response file: %w", err)
                }
                
                // Parse response
                var result map[string]interface{}
                if err := json.Unmarshal(responseData, &result); err != nil {
                    return nil, fmt.Errorf("failed to parse response: %w", err)
                }
                
                // Check for error in response
                if status, ok := result["status"].(string); ok && status == "error" {
                    if message, ok := result["message"].(string); ok {
                        return nil, fmt.Errorf("After Effects error: %s", message)
                    }
                    return nil, errors.New("unknown After Effects error")
                }
                
                // Delete response file (cleanup)
                os.Remove(responseFile)
                
                return result, nil
            }
        }
    }
}

// ExecuteScript executes a script in After Effects
func ExecuteScript(script string) (interface{}, error) {

    // Create command
    cmd := map[string]interface{}{
        "command": "execute",
        "script":  script,
    }
    
    // Send command
    response, err := SendCommand(cmd)
    if err != nil {
        return nil, err
    }
    
    // Return result
    return response["result"], nil
} 