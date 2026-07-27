# GOLEM-3DMCP — Troubleshooting

This guide covers the most common problems encountered when setting up and running GOLEM-3DMCP. Work through the relevant section top-to-bottom; each solution is ordered from most likely to least likely.

---

## Problem: "Connection refused" when using a GOLEM tool

**Symptom:** Claude Code calls a tool and returns an error like `RhinoConnectionError: Cannot connect to Rhino plugin at 127.0.0.1:9876`.

**Causes and solutions:**

### 1. The Rhino plugin is not running

The most common cause. The Rhino plugin server must be started manually (or via the startup scripts configuration) every time Rhino opens.

**Check:** Open Rhino's Python Script Editor (`Tools > Python Script > Edit`). Look for a message like:
```
GOLEM-3DMCP: Server listening on 127.0.0.1:9876
```
in the Rhino command history panel.

**Fix:** Run `rhino_plugin/startup.py` from the Rhino Python Script Editor. You should see the server start message and a list of registered methods.

**Permanent fix:** Add `startup.py` to Rhino's startup scripts:
1. `Tools > Options > RhinoScript`
2. Click **Add** under "Startup scripts"
3. Select `rhino_plugin/startup.py`
4. Restart Rhino

### 2. Rhino is not open

The plugin runs inside Rhino. Rhino must be open and running before Claude Code can connect.

### 3. The plugin crashed after starting

If the plugin started but then crashed (e.g., an unhandled exception in a handler), the server thread may have exited.

**Check:** Run `list_methods` from the test script:
```bash
.venv/bin/python scripts/test_connection.py
```
If this fails but the plugin appeared to start, the server thread has died.

**Fix:** Restart the server from Rhino's Python console:
```python
import rhino_plugin.startup as golem
golem.restart_golem()
```

### 4. Wrong port

The MCP server and Rhino plugin must use the same port. The default is `9876`.

**Check `.mcp.json`:**
```json
"GOLEM_RHINO_PORT": "9876"
```

**Check `rhino_plugin/startup.py`:**
```python
_PORT = 9876
```

Both must match.

---

## Problem: "Port already in use" — cannot start the plugin

**Symptom:** When running `startup.py`, Rhino prints:
```
GOLEM-3DMCP: ERROR — Could not bind 127.0.0.1:9876.
  The port may already be in use by another process.
```

**Solutions:**

### 1. A previous server instance is still running

If Rhino was closed without stopping the server, the socket may still be in TIME_WAIT. The server uses `SO_REUSEADDR`, so this usually resolves immediately. However, if another process is actively listening:

**Find the process using port 9876:**
```bash
lsof -i :9876
```

Expected output (the Rhino plugin server):
```
COMMAND   PID     USER   FD   TYPE             DEVICE SIZE/OFF NODE NAME
Python   12345  yourname  4u  IPv4 ...  TCP 127.0.0.1:9876 (LISTEN)
```

If it is a leftover Rhino process, you can kill it:
```bash
kill -9 12345
```

### 2. A previous test or debug session left the port occupied

Same approach: `lsof -i :9876` to find the PID, then `kill -9 <PID>`.

### 3. Use a different port

If port 9876 is permanently occupied by another service, change the port in both places:

In `rhino_plugin/startup.py`:
```python
_PORT = 9878   # choose any available port
```

In `.mcp.json`:
```json
"GOLEM_RHINO_PORT": "9878"
```

Then restart both.

---

## Problem: The MCP server does not appear in Claude Code

**Symptom:** Claude Code does not list any GOLEM-3DMCP tools, or the server appears as disconnected.

**Solutions:**

### 1. The `.mcp.json` was not loaded

Claude Code reads `.mcp.json` at session start. If you added it after the session opened, restart Claude Code or reload the project.

**Verify it was loaded:**
```bash
claude mcp list
```
You should see `golem-3dmcp` in the output.

**Re-register if missing:**
```bash
claude mcp add --config /Users/kinghippo/Documents/GOLEM-3DMCP/.mcp.json
```

### 2. The Python path in `.mcp.json` is wrong

`.mcp.json` references the venv Python interpreter by absolute path:
```json
"command": "/Users/kinghippo/Documents/GOLEM-3DMCP/.venv/bin/python"
```

This path must match your actual installation. If you cloned to a different location, update the path.

**Check the path exists:**
```bash
ls -la /Users/kinghippo/Documents/GOLEM-3DMCP/.venv/bin/python
```

If it does not exist, run `setup.sh` from the project directory.

### 3. The MCP server process is crashing on startup

Claude Code spawns the MCP server as a subprocess. If it crashes immediately, no tools will appear.

**Test the MCP server manually:**
```bash
cd /Users/kinghippo/Documents/GOLEM-3DMCP
.venv/bin/python -m mcp_server.server
```

This should start without output (it reads from stdin). If it crashes, the error will be printed. Common causes:
- Missing dependencies (run `setup.sh` again)
- Import error in a tool module
- Syntax error from a recent edit

---

## Problem: Grasshopper tools return "GH not available"

**Symptom:** `grasshopper.open_definition` or any other Grasshopper tool returns an error like `"Grasshopper is not available in this Rhino session"`.

**Solutions:**

### 1. Grasshopper is not loaded

In Rhino, open Grasshopper at least once before using the Grasshopper tools:
- Type `Grasshopper` in the Rhino command line and press Enter, or
- Click `Tools > Grasshopper`

The plugin checks `_GH_AVAILABLE` at module import time. If Grasshopper was not loaded when `startup.py` ran, the handlers return unavailable errors.

**Fix:** After loading Grasshopper, restart the GOLEM-3DMCP plugin server:
```python
import rhino_plugin.startup as golem
golem.restart_golem()
```
This re-imports the handler modules, which will now find Grasshopper available.

### 2. Grasshopper is installed but not loading

Check that Grasshopper is installed in Rhino:
- `Tools > Options > Plug-ins`
- Verify "Grasshopper" is present and enabled

If it shows as disabled or not installed, you may need to repair the Rhino installation.

---

## Problem: Python version error during setup

**Symptom:** `setup.sh` fails with:
```
[ERROR] Could not find Python 3.10 or newer.
```

**Solutions:**

### 1. Install Python 3.10 or newer

**Via Homebrew (recommended on macOS):**
```bash
brew install python@3.12
```

**Via pyenv:**
```bash
pyenv install 3.12.4
pyenv global 3.12.4
```

**Direct download:** https://www.python.org/downloads/

### 2. The Python binary is not on PATH

If Python 3.10+ is installed but not found by `setup.sh`, add it to your PATH:
```bash
# For Homebrew on Apple Silicon:
export PATH="/opt/homebrew/bin:$PATH"
echo 'export PATH="/opt/homebrew/bin:$PATH"' >> ~/.zshrc

# Then re-run:
bash setup.sh
```

### 3. Run setup.sh with an explicit Python path

```bash
PYTHON=/usr/local/bin/python3.12 bash setup.sh
```
(The script uses `PYTHON_BIN` internally but you can also edit the candidates list at the top of `setup.sh`.)

---

## Problem: macOS permission errors

**Symptom:** Permission denied when trying to bind port 9876, or when Rhino tries to write files.

**Solutions:**

### 1. Port binding permission (ports below 1024)

Port 9876 is above 1024 and does not require root privileges on macOS. If you are seeing a permission denied error on port 9876, it is likely a firewall or security software issue.

**Check macOS Firewall:**
- `System Settings > Network > Firewall`
- Ensure that Rhino and Python are allowed to accept incoming connections

**Check Little Snitch or similar:** If you have firewall software installed, add an exception for Python (the MCP server) to connect to `127.0.0.1:9876`.

### 2. Gatekeeper blocking the Python interpreter

On macOS, unsigned binaries may be blocked by Gatekeeper. If `.venv/bin/python` is blocked:
```bash
xattr -dr com.apple.quarantine /Users/kinghippo/Documents/GOLEM-3DMCP/.venv
```

### 3. Rhino cannot read/write files in sandboxed locations

Rhino 8 for macOS has file system access controls. If file import/export operations fail with permission errors, try using paths in your home directory rather than system directories.

---

## Problem: Tools time out on complex geometry operations

**Symptom:** A tool returns `RhinoTimeoutError` after 30 seconds.

**Solutions:**

### 1. Increase the command timeout

The default timeout is 30 seconds (set in `.mcp.json` as `GOLEM_TIMEOUT`). For complex boolean operations or large mesh generations, increase it:

In `.mcp.json`:
```json
"GOLEM_TIMEOUT": "120"
```

Restart Claude Code after editing `.mcp.json`.

### 2. Rhino is busy with another operation

`run_on_ui_thread()` waits up to 30 seconds for Rhino's UI thread. If Rhino is showing a progress bar, modal dialog, or file import, the UI thread is blocked. Wait for Rhino to become idle and retry.

### 3. The operation itself is too complex

Some operations (very dense mesh from Brep, large boolean operations) can take more than a minute. For Grasshopper-heavy workflows, consider using `grasshopper.run_definition` with a longer timeout rather than individual parameter-set/recompute steps.

---

## Problem: A tool returns "OBJECT_NOT_FOUND"

**Symptom:** A tool call returns `{"code": "OBJECT_NOT_FOUND", "message": "Object not found ..."}`.

**Causes:**

1. **The GUID is from a previous Rhino session.** GUIDs are only valid within the current Rhino document. If Rhino was restarted or a new document was opened, old GUIDs are no longer valid.

2. **The object was deleted.** Boolean operations and some other tools delete their input objects on success. Do not reuse the GUIDs of consumed inputs.

3. **The GUID was typed incorrectly.** Check for extra braces, whitespace, or truncation.

**Fix:** Use `scene.list_objects` or `scene.get_selected_objects` to get fresh GUIDs from the current document.

---

## How to Check Logs

### MCP Server logs

The MCP server writes to stderr, which Claude Code captures. To see the logs directly:
```bash
cd /Users/kinghippo/Documents/GOLEM-3DMCP
.venv/bin/python -m mcp_server.server 2>mcp_server.log &
tail -f mcp_server.log
```

### Rhino Plugin logs

The Rhino plugin logs to the Rhino command history window via `Rhino.RhinoApp.WriteLine`. Every startup message, registered method, and error is visible there. To see more detail:

1. Open `rhino_plugin/server.py`
2. Add `_log()` calls in the sections you want to trace
3. Restart the server with `golem.restart_golem()`

---

## How to Test the Connection Manually

### Quick ping test

```bash
cd /Users/kinghippo/Documents/GOLEM-3DMCP
.venv/bin/python scripts/test_connection.py
```

Expected output:
```
Connecting to 127.0.0.1:9876...
Ping: {'alive': True}
Connection OK.
```

### Manual TCP test with Python

```python
import socket, json, struct

HOST, PORT = "127.0.0.1", 9876

def send_recv(sock, data):
    payload = json.dumps(data).encode("utf-8")
    sock.sendall(struct.pack("!I", len(payload)) + payload)
    (length,) = struct.unpack("!I", sock.recv(4))
    return json.loads(sock.recv(length).decode("utf-8"))

with socket.socket() as s:
    s.connect((HOST, PORT))
    resp = send_recv(s, {"id": "test-1", "method": "ping", "params": {}})
    print(resp)
    resp = send_recv(s, {"id": "test-2", "method": "list_methods", "params": {}})
    print(f"Registered methods: {len(resp['result']['methods'])}")
```

Run this with the `.venv` Python while Rhino and the plugin are running. You should see `{'id': 'test-1', 'result': {'alive': True}, 'error': None}` and the count of registered methods.

---

## Getting More Help

If none of the above resolves your issue:

1. Run `list_methods` and verify the method you are calling is in the list.
2. Check the Rhino command history window for any error output from the plugin.
3. Check that your Rhino 8 installation is up to date (`Help > Check for Updates`).
4. Open an issue on the GOLEM-3DMCP GitHub repository with:
   - The exact error message
   - The output of `scripts/test_connection.py`
   - Your Rhino version (`Rhino.RhinoApp.ExeVersion` from the Python console)
   - Your Python version (`.venv/bin/python --version`)
