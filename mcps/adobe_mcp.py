# /// script
# dependencies = [
#     "mcp[cli]>=1.3.0",
# ]
# ///

from mcp.server.fastmcp import FastMCP
import subprocess
import platform
import tempfile
import os

mcp = FastMCP("BDB Adobe Suite MCP")

def execute_adobe_jsx(app_name: str, jsx_code: str) -> str:
    """Executes JSX code natively on macOS (osascript) or Windows (PowerShell COM)."""
    if platform.system() == "Darwin":
        escaped_jsx = jsx_code.replace('"', '\\"')
        command = "do javascript"
        if "After Effects" in app_name:
            command = "DoScript"
            
        # Version-independent Bundle ID routing
        app_target = f'"{app_name}"'
        if "Photoshop" in app_name:
            app_target = 'id "com.adobe.Photoshop"'
        elif "Illustrator" in app_name:
            app_target = 'id "com.adobe.illustrator"'
        elif "After Effects" in app_name:
            app_target = 'id "com.adobe.AfterEffects"'
            
        apple_script = f'''
        tell application {app_target}
            {command} "{escaped_jsx}"
        end tell
        '''
        
        result = subprocess.run(["osascript", "-e", apple_script], capture_output=True, text=True)
        if result.returncode != 0:
            raise Exception(f"Adobe Script Error: {result.stderr}")
            
        return result.stdout.strip()
        
    elif platform.system() == "Windows":
        # Resolve COM Object ProgID
        prog_id = None
        if "Photoshop" in app_name:
            prog_id = "Photoshop.Application"
        elif "Illustrator" in app_name:
            prog_id = "Illustrator.Application"
        elif "After Effects" in app_name:
            # AE Windows COM
            prog_id = "AfterFX.Application"
        else:
            raise Exception(f"Windows COM execution not yet supported for {app_name}")
            
        # Write JSX to temp file
        fd, temp_path = tempfile.mkstemp(suffix=".jsx")
        with os.fdopen(fd, 'w', encoding='utf-8') as f:
            f.write(jsx_code)
            
        # Execute via PowerShell COM object
        ps_script = f'''
        $ErrorActionPreference = "Stop"
        $app = New-Object -ComObject "{prog_id}"
        # Execute the JSX
        $app.DoJavaScriptFile("{temp_path}")
        '''
        result = subprocess.run(["powershell", "-Command", ps_script], capture_output=True, text=True)
        os.remove(temp_path)
        
        if result.returncode != 0:
            raise Exception(f"Adobe Script Error (Windows): {result.stderr}")
            
        return result.stdout.strip()
    else:
        raise Exception(f"Unsupported OS: {platform.system()}")

@mcp.tool()
def ps_add_text_layer(text: str, font_size: int = 24) -> str:
    """Adds a text layer to the active Photoshop document."""
    jsx = f"""
    if (app.documents.length > 0) {{
        var doc = app.activeDocument;
        var artLayer = doc.artLayers.add();
        artLayer.kind = LayerKind.TEXT;
        var textItem = artLayer.textItem;
        textItem.contents = "{text}";
        textItem.size = {font_size};
        "Success";
    }} else {{
        "Error: No active document";
    }}
    """
    return execute_adobe_jsx("Adobe Photoshop", jsx)

@mcp.tool()
def ae_render_active_comp() -> str:
    """Adds active composition to render queue and renders it in After Effects."""
    jsx = """
    var comp = app.project.activeItem;
    if (comp != null && comp instanceof CompItem) {
        app.project.renderQueue.items.add(comp);
        app.project.renderQueue.render();
        "Render Complete";
    } else {
        "Error: No active comp";
    }
    """
    return execute_adobe_jsx("Adobe After Effects", jsx)

@mcp.tool()
def ai_draw_rectangle(width: float = 200.0, height: float = 150.0, red: int = 255, green: int = 0, blue: int = 0) -> str:
    """Creates a new document in Illustrator (if none exists) and draws a filled rectangle."""
    jsx = f"""
    var doc = app.documents.length > 0 ? app.activeDocument : app.documents.add();
    var rect = doc.pathItems.rectangle(200, 100, {width}, {height});
    var fillColor = new RGBColor();
    fillColor.red = {red};
    fillColor.green = {green};
    fillColor.blue = {blue};
    rect.fillColor = fillColor;
    "Success";
    """
    return execute_adobe_jsx("Adobe Illustrator", jsx)

if __name__ == "__main__":
    mcp.run()
