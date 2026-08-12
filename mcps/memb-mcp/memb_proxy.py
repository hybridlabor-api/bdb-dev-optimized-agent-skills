import os
import sys
import json
import httpx
from fastapi import FastAPI, Request, BackgroundTasks
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
import asyncio

current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

try:
    from memb import Memory
except ImportError:
    print("Error: Could not import memB module.")
    sys.exit(1)

app = FastAPI(title="memB LLM Proxy")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def init_memory():
    if "OPENAI_API_KEY" not in os.environ and "GEMINI_API_KEY" not in os.environ:
        os.environ["OPENAI_API_KEY"] = "sk-dummy-key-for-local-onnx-ingestion"

    db_dir = os.environ.get("MEMB_DATA_DIR") or os.path.expanduser("~/.MemBDB")
    os.makedirs(db_dir, exist_ok=True)
    db_path = os.path.join(db_dir, "memb.db")
    history_db_path = os.path.join(db_dir, "history.db")
    
    memory_config = {
        "embedder": {
            "provider": "local_onnx",
            "config": {}
        },
        "vector_store": {
            "provider": "numpy_flat",
            "config": {
                "collection_name": "bdb_agent_memory",
                "path": db_path
            }
        },
        "history_db_path": history_db_path
    }
    return Memory.from_config(memory_config)

memb = init_memory()
OPENAI_BASE_URL = os.environ.get("OPENAI_BASE_URL", "https://api.openai.com/v1")
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")

def extract_and_store_facts(user_msg: str, assistant_msg: str):
    # Lightweight extraction logic
    # In a real system this would prompt an LLM to extract facts.
    # For now, we will add a dummy check or simply add the conversation context.
    # We will simulate a basic extraction for demonstration.
    if "my name is" in user_msg.lower() or "remember" in user_msg.lower() or "prefer" in user_msg.lower():
        memb.add(user_msg, user_id="default")
        print(f"Captured fact: {user_msg}")

@app.post("/v1/chat/completions")
async def chat_completions(request: Request, background_tasks: BackgroundTasks):
    body = await request.json()
    messages = body.get("messages", [])
    
    user_msgs = [m["content"] for m in messages if m["role"] == "user"]
    last_user_msg = user_msgs[-1] if user_msgs else ""
    
    if last_user_msg:
        # Search memory
        results = memb.search(last_user_msg, user_id="default", limit=3)
        context = "\n".join([r["memory"] for r in results]) if results else ""
        
        if context:
            system_injection = f"Relevant context from memory:\n{context}"
            # Inject into system prompt
            if messages and messages[0]["role"] == "system":
                messages[0]["content"] += f"\n\n{system_injection}"
            else:
                messages.insert(0, {"role": "system", "content": system_injection})
                
    body["messages"] = messages
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {OPENAI_API_KEY}"
    }
    # Pass along authorization if present in request
    auth_header = request.headers.get("Authorization")
    if auth_header:
        headers["Authorization"] = auth_header

    stream = body.get("stream", False)
    
    async def forward_request():
        async with httpx.AsyncClient() as client:
            req = client.build_request("POST", f"{OPENAI_BASE_URL}/chat/completions", json=body, headers=headers)
            r = await client.send(req, stream=stream)
            if stream:
                assistant_response_parts = []
                async def stream_generator():
                    async for chunk in r.aiter_bytes():
                        # Extract chunks to build the full response for background task if needed
                        # Simplistic extraction of assistant response is tricky in streaming without parsing SSE
                        yield chunk
                return StreamingResponse(stream_generator(), status_code=r.status_code, headers=dict(r.headers))
            else:
                data = r.json()
                assistant_msg = ""
                if "choices" in data and len(data["choices"]) > 0:
                    assistant_msg = data["choices"][0].get("message", {}).get("content", "")
                
                background_tasks.add_task(extract_and_store_facts, last_user_msg, assistant_msg)
                return data

    if stream:
        # If streaming, we might not capture the full assistant msg easily for the background task
        # without wrapping the generator.
        async with httpx.AsyncClient() as client:
            req = client.build_request("POST", f"{OPENAI_BASE_URL}/chat/completions", json=body, headers=headers)
            r = await client.send(req, stream=True)
            
            async def stream_and_capture():
                full_response = ""
                async for chunk in r.aiter_bytes():
                    yield chunk
                # Note: To correctly capture assistant msg, we'd parse SSE JSON here.
                # Background capture for streaming is partially stubbed.
                background_tasks.add_task(extract_and_store_facts, last_user_msg, "Streamed response")
                
            return StreamingResponse(stream_and_capture(), status_code=r.status_code, headers=dict(r.headers))
    else:
        async with httpx.AsyncClient() as client:
            resp = await client.post(f"{OPENAI_BASE_URL}/chat/completions", json=body, headers=headers, timeout=60.0)
            data = resp.json()
            assistant_msg = ""
            if "choices" in data and len(data["choices"]) > 0:
                assistant_msg = data["choices"][0].get("message", {}).get("content", "")
            
            background_tasks.add_task(extract_and_store_facts, last_user_msg, assistant_msg)
            return data

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
