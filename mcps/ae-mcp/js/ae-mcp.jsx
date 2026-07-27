// ae-mcp.jsx - ExtendScript file for After Effects
// Adobe After Effects Model Context Protocol Integration
// This script uses file system communication to receive and execute commands from Claude AI

(function() {
    // JSON Polyfill for ExtendScript environments that don't have native JSON support
    if (typeof JSON === 'undefined') {
        JSON = {};
    }
    
    // Implement stringify if not available
    if (typeof JSON.stringify !== 'function') {
        JSON.stringify = function(obj) {
            var t = typeof obj;
            if (t !== "object" || obj === null) {
                // Simple data type
                if (t === "string") return '"' + obj.replace(/\\/g, '\\\\').replace(/"/g, '\\"').replace(/\n/g, '\\n').replace(/\r/g, '\\r') + '"';
                if (t === "number" || t === "boolean" || obj === null) return String(obj);
                return "null";
            }
            
            // Handle Array
            if (Object.prototype.toString.apply(obj) === '[object Array]') {
                var strArr = [];
                for (var i = 0; i < obj.length; i++) {
                    strArr.push(JSON.stringify(obj[i]) || "null");
                }
                return "[" + strArr.join(",") + "]";
            }
            
            // Handle Object
            var string = [];
            for (var property in obj) {
                if (obj.hasOwnProperty(property)) {
                    var propStr = JSON.stringify(property);
                    var valStr = JSON.stringify(obj[property]);
                    if (propStr && valStr) {
                        string.push(propStr + ":" + valStr);
                    }
                }
            }
            return "{" + string.join(",") + "}";
        };
    }
    
    // Implement parse if not available
    if (typeof JSON.parse !== 'function') {
        JSON.parse = function(str) {
            // Warning: This is a very simplified parser and isn't fully JSON compliant
            // It works for basic JSON but may fail on complex cases
            try {
                // Use Function to create a JS expression from the JSON string
                // Note: This is considered a security risk in browser environments
                // but is acceptable in ExtendScript where there's no user-originated content
                return eval('(' + str + ')');
            } catch (e) {
                throw new SyntaxError('JSON Parse Error: ' + e.message);
            }
        };
    }
    
    // Constants
    var VERSION = "1.0.0";
    var DEBUG_LEVELS = ["Info", "Debug", "Verbose"];
    var POLL_INTERVAL = 300; // milliseconds
    
    // Global state
    var isRunning = false;
    var pollTask = null;
    var debugLevel = 0; // 0=Info, 1=Debug, 2=Verbose
    var logMessages = []; // Store log messages in an array
    var requestFolder = null;
    var responseFolder = null;
    
    // Global function to return JSON data from executed scripts
    // Add this to the global scope so scripts can use it
    $.global.returnjson = function(data) {
        try {
            return JSON.stringify(data);
        } catch (e) {
            return '{"error": "Failed to stringify result: ' + e.toString() + '"}';
        }
    };
    
    // Set up UI panel
    var win = new Window("palette", "AE-MCP " + VERSION, undefined);
    win.orientation = "column";
    win.alignChildren = ["fill", "top"];
    win.spacing = 10;
    win.margins = 16;
    
    // Add header with logo/title
    var headerGroup = win.add("group");
    headerGroup.orientation = "row";
    headerGroup.alignChildren = ["left", "center"];
    headerGroup.add("statictext", undefined, "After Effects MCP").graphics.font = ScriptUI.newFont("Arial", "BOLD", 14);
    
    // Add connection status
    var statusGroup = win.add("group");
    statusGroup.orientation = "row";
    statusGroup.alignChildren = ["left", "center"];
    statusGroup.add("statictext", undefined, "Status:").preferredSize.width = 80;
    var statusText = statusGroup.add("statictext", undefined, "Stopped");
    statusText.characters = 20;
    
    // Add folder selection
    var folderGroup = win.add("group");
    folderGroup.orientation = "row";
    folderGroup.alignChildren = ["left", "center"];
    folderGroup.add("statictext", undefined, "Folder:").preferredSize.width = 80;
    var folderInput = folderGroup.add("edittext", undefined, "");
    folderInput.characters = 30;
    var folderBtn = folderGroup.add("button", undefined, "Browse...");
    
    // Add start/stop button
    var startBtn = win.add("button", undefined, "Start Service");
    
    // Add log area with label
    win.add("statictext", undefined, "Log:");
    
    // Create a text area for logging instead of a listbox
    var logText = win.add("edittext", undefined, "", {multiline: true, scrolling: true, readonly: true});
    logText.preferredSize.width = 400;
    logText.preferredSize.height = 300;
    
    // Bottom panel with debug and clear controls
    var bottomGroup = win.add("group");
    bottomGroup.orientation = "row";
    bottomGroup.alignChildren = ["left", "center"];
    
    // Debug level selector
    bottomGroup.add("statictext", undefined, "Debug Level:");
    var debugDropdown = bottomGroup.add("dropdownlist", undefined, DEBUG_LEVELS);
    debugDropdown.selection = 0; // Default to Info level
    
    // Add clear log button
    var clearLogBtn = bottomGroup.add("button", undefined, "Clear Log");
    
    // Add refresh button
    var refreshBtn = bottomGroup.add("button", undefined, "Refresh");
    
    // Logging function
    function log(message, level) {
        level = level || 0; // Default to Info level
        
        // Only show messages at or below current debug level
        if (level > debugLevel) {
            return;
        }
        
        var timestamp = new Date().toLocaleTimeString();
        var prefix = level === 0 ? "INFO" : (level === 1 ? "DEBUG" : "VERBOSE");
        var logMessage = "[" + timestamp + "] [" + prefix + "] " + message;
        
        try {
            // Add to log messages array
            logMessages.push(logMessage);
            
            // Add to text area
            logText.text += logMessage + "\n";
            
            // Auto-scroll to the bottom
            logText.scrollToEnd();
            
            // Also write to ExtendScript console for debugging
            $.writeln(logMessage);
        } catch (e) {
            $.writeln("Error writing to log: " + e.toString());
        }
    }
    
    // Generate a unique ID
    function generateUUID() {
        var d = new Date().getTime();
        return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function(c) {
            var r = (d + Math.random() * 16) % 16 | 0;
            d = Math.floor(d / 16);
            return (c === 'x' ? r : (r & 0x3 | 0x8)).toString(16);
        });
    }
    
    // Create folders for communication
    function setupCommunicationFolders(baseFolder) {
        try {
            log("Setting up communication folders at: " + baseFolder, 0);
            
            // Create main folder if it doesn't exist
            var mainFolder = new Folder(baseFolder);
            if (!mainFolder.exists) {
                var result = mainFolder.create();
                if (!result) {
                    log("Failed to create main folder: " + baseFolder, 0);
                    return false;
                }
                log("Created main folder: " + mainFolder.fsName, 0);
            }
            
            // Create requests folder
            var reqFolder = new Folder(baseFolder + "/requests");
            if (!reqFolder.exists) {
                result = reqFolder.create();
                if (!result) {
                    log("Failed to create requests folder", 0);
                    return false;
                }
                log("Created requests folder: " + reqFolder.fsName, 0);
            }
            
            // Create responses folder
            var respFolder = new Folder(baseFolder + "/responses");
            if (!respFolder.exists) {
                result = respFolder.create();
                if (!result) {
                    log("Failed to create responses folder", 0);
                    return false;
                }
                log("Created responses folder: " + respFolder.fsName, 0);
            }
            
            // Save folder references
            requestFolder = reqFolder;
            responseFolder = respFolder;
            
            log("Communication folders set up successfully", 0);
            log("requestFolder: " + requestFolder.fsName, 1);
            log("responseFolder: " + responseFolder.fsName, 1);
            
            return true;
        } catch (err) {
            log("Error setting up folders: " + err.toString(), 0);
            return false;
        }
    }
    
    // Start/stop the service
    function toggleService() {
        if (isRunning) {
            // Stop the service
            log("Stopping service...", 0);
            try {
                if (pollTask) {
                    app.cancelTask(pollTask);
                    pollTask = null;
                }
                isRunning = false;
                statusText.text = "Stopped";
                startBtn.text = "Start Service";
                folderInput.enabled = true;
                folderBtn.enabled = true;
                log("Service stopped", 0);
            } catch (err) {
                log("Error stopping service: " + err.toString(), 0);
            }
        } else {
            // Start the service
            log("Starting service...", 0);
            try {
                var folder = folderInput.text;
                if (!folder) {
                    log("Please select a folder for communication", 0);
                    return;
                }
                
                if (!setupCommunicationFolders(folder)) {
                    log("Failed to set up communication folders", 0);
                    return;
                }
                
                isRunning = true;
                statusText.text = "Running";
                startBtn.text = "Stop Service";
                folderInput.enabled = false;
                folderBtn.enabled = false;
                
                // Start polling for requests
                pollTask = app.scheduleTask("checkForRequests()", POLL_INTERVAL, true);
                
                // Verify that variables are properly set
                if (!isRunning || !requestFolder) {
                    log("WARNING: Service variables not properly set - isRunning: " + isRunning + 
                        ", requestFolder: " + (requestFolder ? requestFolder.fsName : "missing"), 0);
                }
                
                log("Service started", 0);
                
                // Write service info file for clients
                writeServiceInfoFile(folder);
            } catch (err) {
                log("Error starting service: " + err.toString(), 0);
                isRunning = false;
                statusText.text = "Error";
            }
        }
    }
    
    // Write service info file for clients to discover
    function writeServiceInfoFile(baseFolder) {
        try {
            var infoFile = new File(baseFolder + "/ae-mcp-info.json");
            infoFile.encoding = "UTF-8";
            if (infoFile.open("w")) {
                var info = {
                    version: VERSION,
                    status: "running",
                    timestamp: new Date().getTime(),
                    afterEffects: app.version,
                    protocol: "file"
                };
                infoFile.write(JSON.stringify(info, null, 2));
                infoFile.close();
                log("Service info file written", 1);
            }
        } catch (err) {
            log("Error writing service info: " + err.toString(), 0);
        }
    }
    
    // Check for request files
    function checkForRequests() {
        if (!isRunning || !requestFolder) {
            log("Service not running properly - isRunning: " + isRunning + ", requestFolder: " + (requestFolder ? "exists" : "missing"), 1);
            return;
        }
        
        try {
            // Confirm request and response folders exist
            if (!requestFolder.exists) {
                log("WARNING: Request folder does not exist, trying to recreate", 0);
                requestFolder.create();
            }
            
            if (!responseFolder || !responseFolder.exists) {
                log("WARNING: Response folder does not exist, trying to recreate", 0);
                if (responseFolder) {
                    responseFolder.create();
                } else {
                    log("ERROR: responseFolder is undefined", 0);
                    return;
                }
            }
            
            // Get all request files
            var requestFiles = requestFolder.getFiles("*.json");
          
            for (var i = 0; i < requestFiles.length; i++) {
                var file = requestFiles[i];
                log("Found request file: " + file.name, 0);
                
                // Ensure file is readable
                if (!(file instanceof File)) {
                    log("WARNING: Skipping non-file object: " + file, 0);
                    continue;
                }
                
                // Process the request
                processRequestFile(file);
                
                // Delete the request file
                try {
                    file.remove();
                    log("Deleted request file: " + file.name, 1);
                } catch (e) {
                    log("Failed to delete request file: " + e.toString(), 0);
                }
            }
        } catch (err) {
            log("Error checking for requests: " + err.toString(), 0);
        }
        
        // Reschedule the task
        pollTask = app.scheduleTask("checkForRequests()", POLL_INTERVAL, true);
    }
    
    // Process a request file
    function processRequestFile(file) {
        try {
            file.encoding = "UTF-8";
            if (file.open("r")) {
                var content = file.read();
                file.close();
                
                log("Read request content: " + content.substring(0, 100) + (content.length > 100 ? "..." : ""), 1);
                
                // Parse the request
                var request;
                try {
                    request = JSON.parse(content);
                    log("Parsed JSON request successfully", 1);
                    log("Request command: " + request.command + ", ID: " + request.id, 1);
                } catch (jsonErr) {
                    log("ERROR parsing JSON: " + jsonErr.toString(), 0);
                    log("Content causing error: " + content, 0);
                    throw jsonErr;
                }
                
                log("Processing request: " + request.command, 0);
                
                // Create the response
                var response = {
                    id: request.id || generateUUID(),
                    timestamp: new Date().getTime(),
                    status: "ok"
                };
                
                // Handle different commands
                if (request.command === "execute") {
                    // Execute JavaScript code
                    try {
                        log("Executing script: " + request.script.substring(0, 100) + (request.script.length > 100 ? "..." : ""), 1);
                        
                        // Check if script is a string
                        if (typeof request.script !== "string") {
                            throw new Error("Script must be a string, got: " + typeof request.script);
                        }
                        
                        // Simplified script execution
                        var scriptToExecute = String(request.script); // Ensure it's a string
            
                        // Execute script and get result
                        log("Evaluating script...", 1);
                        
                        // Always wrap script in a function for proper execution context and 
                        // capture its return value in our global variable
                        scriptToExecute = "__mcp_return_value = (function() { "+scriptToExecute+" })(); ";
                        
                        // Execute the script
                        var result = eval(scriptToExecute);
                        
              
                        log("result: " + result, 1);
                        response.result = result;
                        log("Executed script successfully with result type: " + typeof response.result, 0);
                    } catch (err) {
                        response.status = "error";
                        response.message = err.toString();
                        log("Script execution error: " + err.toString(), 0);
                    }
                } else if (request.command === "ping") {
                    // Simple ping command for testing connection
                    response.result = "pong";
                    log("Ping received", 1);
                } else {
                    // Unknown command
                    response.status = "error";
                    response.message = "Unknown command: " + request.command;
                    log("Unknown command: " + request.command, 0);
                }
                
                // Write the response
                writeResponseFile(response, request.id);
            }
        } catch (err) {
            log("Error processing request file: " + err.toString(), 0);
            
            // Try to write an error response
            try {
                var errorId = file.name.replace(".json", "");
                var errorResponse = {
                    id: errorId,
                    timestamp: new Date().getTime(),
                    status: "error",
                    message: "Failed to process request: " + err.toString()
                };
                log("Writing error response with ID: " + errorId, 1);
                writeResponseFile(errorResponse, errorId);
            } catch (e) {
                log("Failed to write error response: " + e.toString(), 0);
            }
        }
    }
    
    // Write a response file
    function writeResponseFile(response, id) {
        try {
            if (!id) {
                id = generateUUID();
            }
            
            // Ensure responseFolder is properly set
            if (!responseFolder || !(responseFolder instanceof Folder)) {
                log("ERROR: responseFolder is not properly set or is not a valid Folder object", 0);
                return;
            }
            
            // Use File.encode to ensure the file path is correct
            var responseFilePath = responseFolder.fsName + "/" + id + ".json";
            var responseFile = new File(responseFilePath);
            
            log("Attempting to write response file: " + responseFilePath, 1);
            
            responseFile.encoding = "UTF-8";
            if (responseFile.open("w")) {
                var jsonContent = JSON.stringify(response, null, 2);
                responseFile.write(jsonContent);
                responseFile.close();
                log("Response written to: " + responseFile.name, 0);
            } else {
                log("Failed to open response file for writing: " + responseFile.error, 0);
            }
        } catch (err) {
            log("Error writing response: " + err.toString() + ", Stack: " + err.stack, 0);
        }
    }
    
    // Get After Effects version info
    function getAEVersionInfo() {
        try {
            var versionInfo = {
                version: app.version,
                buildNumber: app.buildName,
                language: $.locale
            };
            log("After Effects " + versionInfo.version + " (" + versionInfo.buildNumber + ")", 0);
            log("Language: " + versionInfo.language, 0);
            log("ExtendScript Version: " + $.version, 0);
            
            return versionInfo;
        } catch (err) {
            log("Error getting version info: " + err.toString(), 0);
            return null;
        }
    }
    
    // Attach event handlers
    startBtn.onClick = function() {
        toggleService();
    };
    
    folderBtn.onClick = function() {
        var folder = Folder.selectDialog("Select folder for communication");
        if (folder) {
            folderInput.text = folder.fsName;
        }
    };
    
    clearLogBtn.onClick = function() {
        // Clear the text area
        logText.text = "";
        
        // Clear the log messages array
        logMessages = [];
        
        log("Log cleared");
    };
    
    refreshBtn.onClick = function() {
        log("Manually refreshing service state...", 0);
        if (isRunning && folderInput.text) {
            // Re-setup communication folders to ensure they exist
            setupCommunicationFolders(folderInput.text);
            log("Service state: isRunning=" + isRunning + ", requestFolder=" + 
                (requestFolder ? requestFolder.fsName : "missing"), 0);
            
            // Schedule an immediate check
            if (pollTask) {
                app.cancelTask(pollTask);
            }
            checkForRequests();
        } else {
            log("Service is not running. Please start the service first.", 0);
        }
    };
    
    debugDropdown.onChange = function() {
        debugLevel = debugDropdown.selection.index;
        log("Debug level set to: " + DEBUG_LEVELS[debugLevel]);
    };
    
    // Make function available globally for scheduled tasks
    $.global.checkForRequests = checkForRequests;
    
    // Set default folder path (user documents folder)
    try {
        var defaultFolder = Folder.myDocuments.fsName + "/AE-MCP";
        folderInput.text = defaultFolder;
    } catch (e) {
        // Use desktop as fallback
        try {
            folderInput.text = Folder.desktop.fsName + "/AE-MCP";
        } catch (e2) {
            folderInput.text = "";
        }
    }
    
    // Show the UI
    win.center();
    win.show();
    
    // Log startup info
    log("-----------------------------", 0);
    log("AE-MCP File Protocol v" + VERSION, 0);
    log("-----------------------------", 0);
    
    // Get AE version info
    getAEVersionInfo();
    
    // Final message
    log("Please start the service to begin using Claude with After Effects.", 0);
})(); 