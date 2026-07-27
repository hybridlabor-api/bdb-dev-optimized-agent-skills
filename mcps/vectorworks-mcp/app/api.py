from __future__ import annotations

from pathlib import Path
from typing import Optional

from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from .config import settings
from .embeddings import Embedder
from .indexer import IndexPaths, ensure_index
from .search import Searcher


def create_app() -> FastAPI:
    app = FastAPI(title="Vectorworks Docs RAG")

    templates = Jinja2Templates(directory=str(Path("templates")))

    embedder = Embedder()
    index, meta = ensure_index(embedder)
    searcher = Searcher(index=index, meta=meta, embedder=embedder)

    @app.get("/", response_class=HTMLResponse)
    async def home(request: Request, q: Optional[str] = None, k: int = 6):
        results = searcher.search(q, k=k) if q else []
        return templates.TemplateResponse(
            "index.html",
            {"request": request, "q": q or "", "results": results},
        )

    @app.get("/search")
    async def api_search(q: str = Query(...), k: int = 6):
        return {"query": q, "results": searcher.search(q, k=k)}

    @app.get("/answer")
    async def api_answer(q: str = Query(...), k: int = 6):
        return searcher.answer(q, k=k)

    @app.get("/get")
    async def api_get(doc_id: str, chunk_id: int):
        try:
            return searcher.get(doc_id, chunk_id)
        except KeyError as e:
            raise HTTPException(status_code=404, detail=str(e))

    return app


app = create_app()

