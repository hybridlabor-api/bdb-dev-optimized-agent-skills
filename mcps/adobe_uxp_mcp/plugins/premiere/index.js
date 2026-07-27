const WS_URL = "ws://localhost:8080";
let socket = new WebSocket(WS_URL);

socket.onopen = () => {
    console.log("UXP connected to MCP Proxy");
    socket.send(JSON.stringify({ type: "register", app: "premiere" }));
};

socket.onmessage = async (event) => {
    const message = JSON.parse(event.data);
    
    if (message.type === "execute_tool") {
        try {
            let result = null;
            
            if (message.tool === "pr_get_active_sequence") {
                // app.project.activeSequence doesn't strictly exist in standard UXP without ExtendScript evaluation
                // But this is the entry point
                result = "Active Sequence query via UXP";
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
    setTimeout(() => { socket = new WebSocket(WS_URL); }, 5000);
};
