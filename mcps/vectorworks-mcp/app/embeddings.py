from __future__ import annotations

from dataclasses import dataclass
from typing import List

import numpy as np
from sentence_transformers import SentenceTransformer

from .config import settings


@dataclass
class Embedder:
    model_name: str = settings.model_name
    batch_size: int = settings.batch_size

    def __post_init__(self):
        self.model = SentenceTransformer(self.model_name, device="cpu")

    def encode(self, texts: List[str]) -> np.ndarray:
        vectors = self.model.encode(
            texts,
            batch_size=self.batch_size,
            show_progress_bar=False,
            normalize_embeddings=True,  # cosine via dot product
        )
        return np.asarray(vectors, dtype=np.float32)

