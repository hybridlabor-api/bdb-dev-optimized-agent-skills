import os
from dataclasses import dataclass


@dataclass
class Settings:
    # Paths
    data_dir: str = os.getenv("DATA_DIR", "data")
    index_dir: str = os.getenv("INDEX_DIR", "index")
    index_file: str = os.getenv("INDEX_FILE", "vw.faiss")
    meta_file: str = os.getenv("META_FILE", "meta.jsonl")

    # Embeddings
    model_name: str = os.getenv("EMBED_MODEL", "sentence-transformers/all-MiniLM-L6-v2")
    batch_size: int = int(os.getenv("EMBED_BATCH", "32"))

    # Chunking
    chunk_chars: int = int(os.getenv("CHUNK_CHARS", "2800"))
    chunk_overlap: int = int(os.getenv("CHUNK_OVERLAP", "480"))

    # API / MCP
    api_host: str = os.getenv("API_HOST", "0.0.0.0")
    api_port: int = int(os.getenv("API_PORT", "8000"))
    mcp_host: str = os.getenv("MCP_HOST", "0.0.0.0")
    mcp_port: int = int(os.getenv("MCP_PORT", "8765"))


settings = Settings()

