import os
import numpy as np
import onnxruntime as ort
from tokenizers import Tokenizer
from typing import Literal, Optional, List
from memb.embeddings.base import EmbeddingBase
from memb.configs.embeddings.base import BaseEmbedderConfig

class LocalONNXEmbedding(EmbeddingBase):
    def __init__(self, config: Optional[BaseEmbedderConfig] = None):
        super().__init__(config)
        
        # Determine model paths relative to this file
        current_dir = os.path.dirname(os.path.abspath(__file__))
        model_dir = os.path.join(os.path.dirname(current_dir), "models", "all-MiniLM-L6-v2")
        
        model_path = os.path.join(model_dir, "model_quantized.onnx")
        tokenizer_path = os.path.join(model_dir, "tokenizer.json")
        
        if not os.path.exists(model_path) or not os.path.exists(tokenizer_path):
            raise FileNotFoundError(
                f"Bundled ONNX model assets not found in {model_dir}. Please verify installation."
            )
            
        # Load Tokenizer & ONNX Session
        self.tokenizer = Tokenizer.from_file(tokenizer_path)
        
        # Configure CPU session options
        sess_options = ort.SessionOptions()
        sess_options.graph_optimization_level = ort.GraphOptimizationLevel.ORT_ENABLE_ALL
        self.session = ort.InferenceSession(model_path, sess_options, providers=["CPUExecutionProvider"])
        
        self.config.embedding_dims = self.config.embedding_dims or 384 # all-MiniLM-L6-v2 has 384 dimensions

    def _mean_pooling(self, model_output, attention_mask):
        token_embeddings = model_output[0] # First element of model_output contains all token embeddings
        input_mask_expanded = np.expand_dims(attention_mask, -1).astype(float)
        sum_embeddings = np.sum(token_embeddings * input_mask_expanded, 1)
        sum_mask = np.clip(input_mask_expanded.sum(1), a_min=1e-9, a_max=None)
        return sum_embeddings / sum_mask

    def _normalize(self, v):
        norm = np.linalg.norm(v, axis=-1, keepdims=True)
        return (v / np.clip(norm, a_min=1e-9, a_max=None)).tolist()

    def embed(self, text: str, memory_action: Optional[Literal["add", "search", "update"]] = None) -> List[float]:
        # Tokenize inputs
        encoded = self.tokenizer.encode(text)
        
        input_ids = np.array([encoded.ids], dtype=np.int64)
        attention_mask = np.array([encoded.attention_mask], dtype=np.int64)
        
        # For compatibility with MiniLM onnx models: some require token_type_ids
        inputs = {
            "input_ids": input_ids,
            "attention_mask": attention_mask
        }
        
        # Check if model inputs require token_type_ids
        model_inputs = [i.name for i in self.session.get_inputs()]
        if "token_type_ids" in model_inputs:
            inputs["token_type_ids"] = np.array([encoded.type_ids], dtype=np.int64)
            
        outputs = self.session.run(None, inputs)
        
        # Mean Pooling + Normalize
        pooled = self._mean_pooling(outputs, attention_mask)
        normalized = self._normalize(pooled)
        return normalized[0]

    def embed_batch(self, texts: List[str], memory_action="add") -> List[List[float]]:
        if not texts:
            return []
            
        embeddings = []
        for text in texts:
            embeddings.append(self.embed(text, memory_action))
        return embeddings
