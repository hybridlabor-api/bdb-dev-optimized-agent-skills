from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path
from typing import List, Tuple

import faiss  # type: ignore
import numpy as np

from .chunking import merge_to_chunks, split_paragraphs
from .config import settings
from .embeddings import Embedder
from .utils import iter_text_files


@dataclass
class IndexPaths:
    base: Path
    index_file: Path
    meta_file: Path

    @staticmethod
    def from_settings() -> "IndexPaths":
        base = Path(settings.index_dir)
        return IndexPaths(
            base=base,
            index_file=base / settings.index_file,
            meta_file=base / settings.meta_file,
        )


def build_index(data_dir: Path, index_paths: IndexPaths, embedder: Embedder) -> Tuple[faiss.Index, List[dict]]:
    index_paths.base.mkdir(parents=True, exist_ok=True)

    texts: List[str] = []
    meta: List[dict] = []

    for src in iter_text_files(data_dir):
        rel = src.relative_to(data_dir).as_posix()
        content = src.read_text(encoding="utf-8", errors="ignore")
        paragraphs = split_paragraphs(content)
        chunks = merge_to_chunks(paragraphs, settings.chunk_chars, settings.chunk_overlap)
        for i, chunk in enumerate(chunks):
            texts.append(chunk)
            meta.append({"doc_id": rel, "chunk_id": i, "text": chunk})

    if not texts:
        raise RuntimeError(f"No ingestable files found under {data_dir}")

    vectors = embedder.encode(texts)
    dim = vectors.shape[1]
    index = faiss.IndexFlatIP(dim)
    index.add(vectors)

    # persist
    faiss.write_index(index, str(index_paths.index_file))
    with index_paths.meta_file.open("w", encoding="utf-8") as f:
        for m in meta:
            f.write(json.dumps(m, ensure_ascii=False) + "\n")

    return index, meta


def load_index(index_paths: IndexPaths) -> Tuple[faiss.Index, List[dict]]:
    index = faiss.read_index(str(index_paths.index_file))
    meta: List[dict] = []
    with index_paths.meta_file.open("r", encoding="utf-8") as f:
        for line in f:
            meta.append(json.loads(line))
    return index, meta


def ensure_index(embedder: Embedder) -> Tuple[faiss.Index, List[dict]]:
    data_dir = Path(settings.data_dir)
    index_paths = IndexPaths.from_settings()
    if not index_paths.index_file.exists() or not index_paths.meta_file.exists():
        return build_index(data_dir, index_paths, embedder)
    return load_index(index_paths)


def main():
    parser = argparse.ArgumentParser(description="Build or rebuild FAISS index from data/")
    parser.add_argument(
        "--rebuild",
        action="store_true",
        help="Force rebuild index from scratch (ignores existing index files)",
    )
    args = parser.parse_args()

    emb = Embedder()
    data_dir = Path(settings.data_dir)
    index_paths = IndexPaths.from_settings()

    if args.rebuild:
        index_paths.base.mkdir(parents=True, exist_ok=True)
        idx, meta = build_index(data_dir, index_paths, emb)
    else:
        idx, meta = ensure_index(emb)

    print(f"Indexed {len(meta)} chunks → {settings.index_dir}/{settings.index_file}")


if __name__ == "__main__":
    main()
