from __future__ import annotations

from dataclasses import dataclass
from typing import List, Tuple

import faiss  # type: ignore
import numpy as np

from .embeddings import Embedder


@dataclass
class Searcher:
    index: faiss.Index
    meta: List[dict]
    embedder: Embedder

    def search(self, query: str, k: int = 6) -> List[dict]:
        vec = self.embedder.encode([query])  # normalized
        scores, idxs = self.index.search(vec, k)
        out: List[dict] = []
        for score, idx in zip(scores[0].tolist(), idxs[0].tolist()):
            if idx == -1:
                continue
            m = self.meta[idx]
            out.append({
                "score": float(score),
                "doc_id": m["doc_id"],
                "chunk_id": m["chunk_id"],
                "text": m["text"],
            })
        return out

    def get(self, doc_id: str, chunk_id: int) -> dict:
        # naive lookup by scanning meta (meta is same order as index)
        for m in self.meta:
            if m["doc_id"] == doc_id and m["chunk_id"] == chunk_id:
                return m
        raise KeyError(f"Chunk not found: {doc_id}#{chunk_id}")

    def answer(self, query: str, k: int = 6) -> dict:
        # Simple extractive draft: stitch top-k snippets
        hits = self.search(query, k=k)
        summary_lines: List[str] = []
        for i, h in enumerate(hits, start=1):
            text = h["text"].strip().splitlines()
            lead = " ".join(text[:2])[:400]
            summary_lines.append(f"[{i}] {lead}")
        draft = (
            "以下は関連する資料からの抜粋です。詳細は出典を参照してください。\n\n"
            + "\n".join(summary_lines)
        )
        return {"draft": draft, "sources": hits}

