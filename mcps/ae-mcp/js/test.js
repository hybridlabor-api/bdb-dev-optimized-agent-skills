/**
 * test.js - Simple AE-MCP communication test script
 * 
 * This script is used to test After Effects MCP communication functionality
 * It can directly create request files and wait for responses
 */
// Set up communication folder - this needs to match the path set in After Effects
// Modify this to your AE-MCP folder path
let baseFolder = null;
// Node.js environment
const os = require('os');
const path = require('path');
const fs = require('fs');

// Get user documents directory
const userHome = os.homedir();
baseFolder = path.join(userHome, "Documents", "AE-MCP");
console.log(`Path automatically set: ${baseFolder}`);

// Ensure directories exist
if (!fs.existsSync(baseFolder)) {
    try {
        fs.mkdirSync(baseFolder);
        fs.mkdirSync(path.join(baseFolder, "requests"));
        fs.mkdirSync(path.join(baseFolder, "responses"));
        console.log(`Communication directories created: ${baseFolder}`);
    } catch (err) {
        console.error(`Failed to create directories: ${err.message}`);
    }
}

// Generate a simple unique ID
function generateUID() {
    return 'id_' + Date.now() + '_' + Math.floor(Math.random() * 1000000);
}

// Utility function - Write file
function writeFile(filePath, content) {
    if (typeof process !== 'undefined' && process.versions && process.versions.node) {
        // Node.js environment
        const fs = require('fs');
        try {
            fs.writeFileSync(filePath, content, 'utf8');
            console.log(`Successfully wrote file: ${filePath}`);
            return true;
        } catch (err) {
            console.error(`Failed to write file: ${err.message}`);
            return false;
        }
    } else {
        // Browser environment
        console.log(`[Simulation] Writing file: ${filePath}`);
        console.log(`Content: ${content}`);
        return false;
    }
}

// Utility function - Read file
function readFile(filePath) {
    if (typeof process !== 'undefined' && process.versions && process.versions.node) {
        // Node.js environment
        const fs = require('fs');
        try {
            const content = fs.readFileSync(filePath, 'utf8');
            return content;
        } catch (err) {
            console.error(`Failed to read file: ${err.message}`);
            return null;
        }
    } else {
        // Browser environment
        console.log(`[Simulation] Reading file: ${filePath}`);
        return null;
    }
}

// Utility function - Check if file exists
function fileExists(filePath) {
    if (typeof process !== 'undefined' && process.versions && process.versions.node) {
        // Node.js environment
        const fs = require('fs');
        return fs.existsSync(filePath);
    } else {
        // Browser environment
        console.log(`[Simulation] Checking if file exists: ${filePath}`);
        return false;
    }
}

// Wait for response file to appear
function waitForResponse(responseFilePath, maxWaitTimeMs = 10000, checkIntervalMs = 500) {
    console.log(`Waiting for response file: ${responseFilePath}`);
    
    if (typeof process !== 'undefined' && process.versions && process.versions.node) {
        // Node.js environment - actual waiting
        return new Promise((resolve, reject) => {
            const startTime = Date.now();
            let checkCount = 0;
            
            const checkFile = () => {
                checkCount++;
                const elapsed = Date.now() - startTime;
                
                if (fileExists(responseFilePath)) {
                    const content = readFile(responseFilePath);
                    console.log(`Response file found! Time elapsed: ${elapsed}ms, Checks: ${checkCount}`);
                    console.log(`Response content: ${content}`);
                    
                    try {
                        const response = JSON.parse(content);
                        resolve(response);
                    } catch (err) {
                        reject(new Error(`Failed to parse response JSON: ${err.message}`));
                    }
                    return;
                }
                
                if (elapsed > maxWaitTimeMs) {
                    reject(new Error(`Response timeout, waited ${elapsed}ms`));
                    return;
                }
                
                console.log(`Waiting for response... (${elapsed}ms, Check #${checkCount})`);
                setTimeout(checkFile, checkIntervalMs);
            };
            
            checkFile();
        });
    } else {
        // Browser environment - manual instructions
        console.log("This browser version cannot automatically detect the file system. Please check manually:");
        console.log(`1. Check if the request has been processed in After Effects`);
        console.log(`2. Check if the response file has been created: ${responseFilePath}`);
        console.log(`3. View the response file content`);
    }
}

// Test PING command
async function testPing() {
    console.log("\n=== Testing PING Request ===");
    
    if (!baseFolder) {
        console.log("Error: No folder path provided");
        return;
    }
    
    const requestsFolder = typeof process !== 'undefined' ? require('path').join(baseFolder, "requests") : baseFolder + "/requests";
    const responsesFolder = typeof process !== 'undefined' ? require('path').join(baseFolder, "responses") : baseFolder + "/responses";
    
    // Create ping request
    const requestId = generateUID();
    const request = {
        id: requestId,
        command: "ping",
        timestamp: Date.now()
    };
    
    // Convert to JSON
    const requestJson = JSON.stringify(request, null, 2);
    
    // File paths
    const requestFile = typeof process !== 'undefined' ? 
        require('path').join(requestsFolder, `${requestId}.json`) :
        requestsFolder + "/" + requestId + ".json";
    
    const responseFile = typeof process !== 'undefined' ? 
        require('path').join(responsesFolder, `${requestId}.json`) :
        responsesFolder + "/" + requestId + ".json";
    
    // Output request information
    console.log("Request ID:", requestId);
    console.log("Request JSON:", requestJson);
    console.log("Request File:", requestFile);
    
    // Write request file
    const writeResult = writeFile(requestFile, requestJson);
    
    if (typeof process !== 'undefined' && process.versions && process.versions.node) {
        if (writeResult) {
            try {
                // Wait for response
                console.log("\nWaiting for After Effects response...");
                const response = await waitForResponse(responseFile);
                
                if (response && response.result === "pong") {
                    console.log("✅ PING test successful! After Effects communication is working normally.");
                } else {
                    console.log("❌ PING test failed! Response content is not the expected 'pong'");
                    console.log("Actual response:", response);
                }
            } catch (err) {
                console.error("❌ PING test failed:", err.message);
                console.log("Please ensure the AE-MCP service in After Effects has started correctly");
            }
        }
    } else {
        // Browser environment - manual guidance
        console.log("\nPlease manually perform the following steps:");
        console.log("1. Ensure After Effects is started and running the ae-mcp.jsx script");
        console.log("2. Ensure the service is started in the AE-MCP panel");
        console.log("3. Create the following file in your file system:");
        console.log(`   ${requestFile}`);
        console.log("4. Copy the following content into the file:");
        console.log("----------");
        console.log(requestJson);
        console.log("----------");
        console.log("5. Save the file");
        console.log("6. Wait a few seconds");
        console.log("7. Check the response file:");
        console.log(`   ${responseFile}`);
        console.log("8. Confirm that the content contains 'pong'");
    }
}

// Test creating a composition
async function createCompExample() {
    console.log("\n=== Creating Composition Example Script ===");
    
    if (!baseFolder) {
        console.log("Error: No folder path provided");
        return;
    }
    
    const requestsFolder = typeof process !== 'undefined' ? require('path').join(baseFolder, "requests") : baseFolder + "/requests";
    const responsesFolder = typeof process !== 'undefined' ? require('path').join(baseFolder, "responses") : baseFolder + "/responses";
    
    const requestId = generateUID();
    const script = `(function() {
        // Create a new composition
        var compName = "Test Composition " + new Date().toLocaleTimeString();
        var newComp = app.project.items.addComp(compName, 1920, 1080, 1, 10, 30);
        newComp.openInViewer();
        return "Successfully created new composition: " + compName;
    })()`;
    
    const request = {
        id: requestId,
        command: "execute",
        script: script,
        timestamp: Date.now()
    };
    
    const requestJson = JSON.stringify(request, null, 2);
    const requestFile = typeof process !== 'undefined' ? 
        require('path').join(requestsFolder, `${requestId}.json`) :
        requestsFolder + "/" + requestId + ".json";
    
    const responseFile = typeof process !== 'undefined' ? 
        require('path').join(responsesFolder, `${requestId}.json`) :
        responsesFolder + "/" + requestId + ".json";
    
    console.log("Request ID:", requestId);
    console.log("Script Request JSON:");
    console.log("----------");
    console.log(requestJson);
    console.log("----------");
    
    // Write request file
    const writeResult = writeFile(requestFile, requestJson);
    
    if (typeof process !== 'undefined' && process.versions && process.versions.node) {
        if (writeResult) {
            try {
                // Wait for response
                console.log("\nWaiting for After Effects to execute script...");
                const response = await waitForResponse(responseFile);
                
                if (response && response.status === "ok") {
                    console.log("✅ Composition test successful!");
                    console.log("Result:", response.result);
                    console.log("Please check the new composition in After Effects");
                } else {
                    console.log("❌ Composition test failed!");
                    console.log("Response:", response);
                }
            } catch (err) {
                console.error("❌ Composition test failed:", err.message);
                console.log("Please ensure the AE-MCP service in After Effects has started correctly");
            }
        }
    } else {
        // Browser environment - manual guidance
        console.log("\nPlease manually perform the following steps:");
        console.log("1. Ensure the AE-MCP service in After Effects is started");
        console.log("2. Create the file:", requestFile);
        console.log("3. Copy the above JSON into the file and save");
        console.log("4. Wait a few seconds");
        console.log("5. Check After Effects to see if a new composition is created");
        console.log("6. Check the response file:", responseFile);
    }
}

// Test creating a triangle shape layer
async function createTriangleExample() {
    console.log("\n=== Creating Triangle Shape Layer Test ===");
    
    if (!baseFolder) {
        console.log("Error: No folder path provided");
        return;
    }
    
    const requestsFolder = typeof process !== 'undefined' ? require('path').join(baseFolder, "requests") : baseFolder + "/requests";
    const responsesFolder = typeof process !== 'undefined' ? require('path').join(baseFolder, "responses") : baseFolder + "/responses";
    
    const requestId = generateUID();
    // Simplified triangle script - reduce complexity
    const script = `(function() {
        // Create a new composition
        var compName = "Triangle Composition " + new Date().toLocaleTimeString();
        var comp = app.project.items.addComp(compName, 1920, 1080, 1, 10, 30);
        comp.openInViewer();
        
        // Create a shape layer
        var shapeLayer = comp.layers.addShape();
        shapeLayer.name = "Triangle";
        
        // Create a triangle
        var shapeGroup = shapeLayer.property("Contents").addProperty("ADBE Vector Group");
        var shapePath = shapeGroup.property("Contents").addProperty("ADBE Vector Shape - Group");
        
        // Define triangle vertices (note here using simplified method)
        var path = new Shape();
        path.vertices = [[960, 340], [760, 740], [1160, 740]];
        path.closed = true;
        
        // Apply shape
        shapePath.property("Path").setValue(path);
        
        // Add fill
        var fill = shapeGroup.property("Contents").addProperty("ADBE Vector Graphic - Fill");
        fill.property("Color").setValue([1, 0.5, 0]);
        
        return "Successfully created triangle";
    })()`;
    
    const request = {
        id: requestId,
        command: "execute",
        script: script,
        timestamp: Date.now()
    };
    
    const requestJson = JSON.stringify(request, null, 2);
    const requestFile = typeof process !== 'undefined' ? 
        require('path').join(requestsFolder, `${requestId}.json`) :
        requestsFolder + "/" + requestId + ".json";
    
    const responseFile = typeof process !== 'undefined' ? 
        require('path').join(responsesFolder, `${requestId}.json`) :
        responsesFolder + "/" + requestId + ".json";
    
    console.log("Request ID:", requestId);
    console.log("Script Request JSON:");
    console.log("----------");
    console.log(requestJson);
    console.log("----------");
    
    // Write request file
    const writeResult = writeFile(requestFile, requestJson);
    
    if (typeof process !== 'undefined' && process.versions && process.versions.node) {
        if (writeResult) {
            try {
                // Wait for response
                console.log("\nWaiting for After Effects to create triangle...");
                const response = await waitForResponse(responseFile);
                
                if (response && response.status === "ok") {
                    console.log("✅ Triangle test successful!");
                    console.log("Result:", response.result);
                    console.log("Please check the new triangle shape layer in After Effects");
                } else {
                    console.log("❌ Triangle test failed!");
                    console.log("Response:", response);
                }
            } catch (err) {
                console.error("❌ Triangle test failed:", err.message);
                console.log("Please ensure the AE-MCP service in After Effects has started correctly");
            }
        }
    } else {
        // Browser environment - manual guidance
        console.log("\nPlease manually perform the following steps:");
        console.log("1. Ensure After Effects is started and running the ae-mcp.jsx script");
        console.log("2. Create the file:", requestFile);
        console.log("3. Copy the above JSON into the file and save");
        console.log("4. Wait a few seconds");
        console.log("5. Check After Effects to see if a triangle shape layer is created");
        console.log("6. Check the response file:", responseFile);
    }
}

// Run tests
async function runTests() {
    console.log("AE-MCP Test Tool");
    console.log("This tool is used to test communication with After Effects");
    console.log(`Using communication folder: ${baseFolder}`);
    
    if (typeof process !== 'undefined' && process.versions && process.versions.node) {
        // In Node.js environment, run tests in order
        try {
            await testPing();
            console.log("\n------------------------------");
            await createCompExample();
            console.log("\n------------------------------");
            await createTriangleExample();
        } catch (err) {
            console.error("Error occurred during tests:", err.message);
        }
    } else {
        // In browser environment, provide guidance only
        testPing();
        createCompExample();
        createTriangleExample();
    }
}

// Start tests
runTests();
