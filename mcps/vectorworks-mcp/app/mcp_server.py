from __future__ import annotations

import asyncio
import json
from dataclasses import dataclass
from typing import Any, Awaitable, Callable, Dict

import websockets

from .config import settings
from .embeddings import Embedder
from .indexer import ensure_index
from .search import Searcher


Json = Dict[str, Any]


@dataclass
class McpServer:
    host: str = settings.mcp_host
    port: int = settings.mcp_port

    def __post_init__(self):
        emb = Embedder()
        index, meta = ensure_index(emb)
        self.searcher = Searcher(index=index, meta=meta, embedder=emb)

    async def handler(self, websocket):
        async for message in websocket:
            try:
                req = json.loads(message)
                if not isinstance(req, dict):
                    raise ValueError("Invalid JSON-RPC request")
                method = req.get("method")
                req_id = req.get("id")
                params = req.get("params", {})

                if method == "vw.search":
                    q = params.get("query")
                    k = int(params.get("k", 6))
                    result = self.searcher.search(q, k=k)
                elif method == "vw.answer":
                    q = params.get("query")
                    k = int(params.get("k", 6))
                    result = self.searcher.answer(q, k=k)
                elif method == "vw.get":
                    doc_id = params.get("doc_id")
                    chunk_id = int(params.get("chunk_id"))
                    result = self.searcher.get(doc_id, chunk_id)
                else:
                    raise ValueError(f"Unknown method: {method}")

                resp: Json = {"jsonrpc": "2.0", "id": req_id, "result": result}
            except Exception as e:  # pragma: no cover - basic error surface
                resp = {
                    "jsonrpc": "2.0",
                    "id": req.get("id") if isinstance(req, dict) else None,
                    "error": {"code": -32000, "message": str(e)},
                }
            await websocket.send(json.dumps(resp, ensure_ascii=False))

    async def run(self):
        async with websockets.serve(self.handler, self.host, self.port):
            await asyncio.Future()  # run forever


async def run_server():
    server = McpServer()
    await server.run()

