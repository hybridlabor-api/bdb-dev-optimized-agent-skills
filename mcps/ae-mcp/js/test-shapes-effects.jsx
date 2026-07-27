// AE-MCP Test Script: Shape Layers and Effects
// This script demonstrates the usage of shape layers and effects

// Create a new composition
var compWidth = 1920;
var compHeight = 1080;
var comp = app.project.items.addComp("Shape Effects Demo", compWidth, compHeight, 1, 10, 30);

// Create a black background
var bgLayer = comp.layers.addSolid([0, 0, 0], "Background", compWidth, compHeight, 1);

// Function to create a star shape
function createStar() {
    // Create a shape layer
    var starLayer = comp.layers.addShape();
    starLayer.name = "Star";
    
    // Add a shape group for a star
    var shapeGroup = starLayer.property("ADBE Root Vectors Group").addProperty("ADBE Vector Shape - Star");
    
    // Set star properties
    shapeGroup.property("ADBE Vector Star Type").setValue(2); // Star type
    shapeGroup.property("ADBE Vector Star Points").setValue(5); // 5-pointed star
    shapeGroup.property("ADBE Vector Star Position").setValue([compWidth/2, compHeight/2]);
    shapeGroup.property("ADBE Vector Star Outer Radius").setValue(200);
    shapeGroup.property("ADBE Vector Star Inner Radius").setValue(100);
    shapeGroup.property("ADBE Vector Star Outer Roundness").setValue(0);
    shapeGroup.property("ADBE Vector Star Inner Roundness").setValue(0);
    
    // Add fill and stroke
    var content = starLayer.property("ADBE Root Vectors Group");
    var fillGroup = content.addProperty("ADBE Vector Graphic - Fill");
    var strokeGroup = content.addProperty("ADBE Vector Graphic - Stroke");
    
    // Set the fill color to gold
    fillGroup.property("ADBE Vector Fill Color").setValue([1, 0.8, 0.2, 1]);
    strokeGroup.property("ADBE Vector Stroke Color").setValue([0.8, 0.6, 0.1, 1]);
    strokeGroup.property("ADBE Vector Stroke Width").setValue(5);
    
    return starLayer;
}

// Function to create a custom wave shape
function createWave() {
    // Create a shape layer
    var waveLayer = comp.layers.addShape();
    waveLayer.name = "Wave";
    
    // Add a shape group
    var content = waveLayer.property("ADBE Root Vectors Group");
    var shapeGroup = content.addProperty("ADBE Vector Shape - Group");
    var path = shapeGroup.property("ADBE Vector Shape");
    
    // Create a wave shape
    var shape = new Shape();
    var vertices = [];
    var numPoints = 20;
    var waveHeight = 100;
    var waveWidth = compWidth - 200;
    var startX = 100;
    
    for (var i = 0; i <= numPoints; i++) {
        var x = startX + (i * (waveWidth / numPoints));
        var y = (compHeight / 2) + (Math.sin(i * (Math.PI * 2) / 10) * waveHeight);
        vertices.push([x, y]);
    }
    
    shape.vertices = vertices;
    shape.closed = false;
    
    // Set the path with our wave shape
    path.setValue(shape);
    
    // Add stroke
    var strokeGroup = content.addProperty("ADBE Vector Graphic - Stroke");
    strokeGroup.property("ADBE Vector Stroke Color").setValue([0.2, 0.6, 1, 1]); // Blue
    strokeGroup.property("ADBE Vector Stroke Width").setValue(15);
    
    return waveLayer;
}

// Function to create a rectangle with glow effect
function createGlowingRectangle() {
    // Create a shape layer
    var rectLayer = comp.layers.addShape();
    rectLayer.name = "Glowing Rectangle";
    
    // Add a rectangle shape
    var content = rectLayer.property("ADBE Root Vectors Group");
    var shapeGroup = content.addProperty("ADBE Vector Shape - Rect");
    
    // Set rectangle properties - center in comp
    shapeGroup.property("ADBE Vector Rect Size").setValue([300, 300]);
    shapeGroup.property("ADBE Vector Rect Position").setValue([compWidth/2, compHeight/2 + 250]);
    shapeGroup.property("ADBE Vector Rect Roundness").setValue(25); // Rounded corners
    
    // Add fill
    var fillGroup = content.addProperty("ADBE Vector Graphic - Fill");
    fillGroup.property("ADBE Vector Fill Color").setValue([0.8, 0.2, 0.8, 1]); // Purple
    
    // Apply glow effect
    var glowEffect = rectLayer.Effects.addProperty("ADBE Glo2");
    glowEffect.property("ADBE Glo2-0001").setValue(25); // Glow Threshold
    glowEffect.property("ADBE Glo2-0002").setValue(0.9); // Glow Radius
    glowEffect.property("ADBE Glo2-0003").setValue(1.0); // Glow Intensity
    
    return rectLayer;
}

// Create the shape elements
var star = createStar();
var wave = createWave();
var glowRect = createGlowingRectangle();

// Apply some effects
// Add Gaussian Blur to the wave
var blurEffect = wave.Effects.addProperty("ADBE Gaussian Blur 2");
blurEffect.property("ADBE Gaussian Blur 2-0001").setValue(5); // Blur Radius

// Add Hue/Saturation effect to the star
var hueEffect = star.Effects.addProperty("ADBE HUE SATURATION");
hueEffect.property("ADBE HUE SATURATION-0001").setValue(1); // Color controller = Master
hueEffect.property("ADBE HUE SATURATION-0002").setValue(60); // Hue shift by 60 degrees

// Animate the star rotation
var startTime = 0;
var endTime = 5;
var startRotation = 0;
var endRotation = 2 * Math.PI; // Full rotation (in radians)

star.transform.rotation.setValueAtTime(startTime, startRotation);
star.transform.rotation.setValueAtTime(endTime, endRotation);

// Alert the user when done
alert("Test script completed!\n\nCreated:\n- Star shape with Hue/Saturation effect\n- Wave shape with Gaussian Blur\n- Rectangle with Glow effect"); 