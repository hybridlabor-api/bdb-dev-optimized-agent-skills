const { app, core } = require("photoshop");

const WS_URL = "ws://localhost:8080";
let socket = new WebSocket(WS_URL);

socket.onopen = () => {
    console.log("UXP connected to MCP Proxy");
    socket.send(JSON.stringify({ type: "register", app: "photoshop" }));
};

socket.onmessage = async (event) => {
    const message = JSON.parse(event.data);
    
    if (message.type === "execute_tool") {
        try {
            let result = null;
            
            if (message.tool === "ps_get_active_document") {
                result = app.activeDocument ? app.activeDocument.name : "No active document";
            } else if (message.tool === "ps_add_layer") {
                await core.executeAsModal(async () => {
                    const newLayer = await app.activeDocument.createArtLayer();
                    newLayer.name = message.args.name || "AI Generated Layer";
                    result = `Layer '${newLayer.name}' created.`;
                }, { commandName: "Create Layer via MCP" });
            }
            
            socket.send(JSON.stringify({
                id: message.id,
                status: "success",
                data: result
            }));
        } catch (err) {
            socket.send(JSON.stringify({
                id: message.id,
                status: "error",
                error: err.toString()
            }));
        }
    }
};

socket.onclose = () => {
    console.log("Disconnected. Reconnecting in 5s...");
    setTimeout(() => { 
        socket = new WebSocket(WS_URL);
    }, 5000);
};
