import os
import json
import sqlite3
import numpy as np
from typing import List, Dict, Any, Optional
from memb.vector_stores.base import VectorStoreBase

class NumPyFlat(VectorStoreBase):
    def __init__(
        self,
        collection_name: str = "memb",
        path: Optional[str] = None,
        distance_strategy: str = "cosine"
    ):
        self.collection_name = collection_name
        self.db_path = path if path else os.path.expanduser("~/.MemBDB/memb.db")
        
        # Ensure parent folder exists
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        
        # Initialize Database table
        self._init_db()

    def _init_db(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS memb_vectors (
                id TEXT PRIMARY KEY,
                collection TEXT,
                vector BLOB,
                payload TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        conn.commit()
        conn.close()

    def create_col(self, name, vector_size, distance):
        # Collections are isolated by the 'collection' column in the table.
        # No extra table required.
        pass

    def insert(self, vectors, payloads=None, ids=None):
        if not ids:
            raise ValueError("IDs must be provided for insertion in NumPyFlat.")
            
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        for idx, vec in enumerate(vectors):
            id_val = ids[idx]
            payload = payloads[idx] if payloads else {}
            
            # Serialize payload to JSON and vector to BLOB (numpy float32 array)
            payload_str = json.dumps(payload)
            vec_blob = np.array(vec, dtype=np.float32).tobytes()
            
            cursor.execute(
                """
                INSERT OR REPLACE INTO memb_vectors (id, collection, vector, payload)
                VALUES (?, ?, ?, ?)
                """,
                (id_val, self.collection_name, vec_blob, payload_str)
            )
            
        conn.commit()
        conn.close()

    def search(self, query, vectors, top_k=5, filters=None):
        # Fetch all vectors and payloads from SQLite for this collection
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id, vector, payload FROM memb_vectors WHERE collection = ?",
            (self.collection_name,)
        )
        rows = cursor.fetchall()
        conn.close()
        
        if not rows:
            return []
            
        # Parse inputs
        query_vector = np.array(vectors, dtype=np.float32)
        
        results = []
        for row_id, vec_bytes, payload_str in rows:
            payload = json.loads(payload_str)
            
            # Apply metadata filters in-memory
            if filters:
                match = True
                for k, v in filters.items():
                    if payload.get(k) != v:
                        match = False
                        break
                if not match:
                    continue
                    
            db_vector = np.frombuffer(vec_bytes, dtype=np.float32)
            
            # Cosine Similarity: dot(A, B) / (norm(A) * norm(B))
            dot_prod = np.dot(query_vector, db_vector)
            norm_q = np.linalg.norm(query_vector)
            norm_db = np.linalg.norm(db_vector)
            
            score = dot_prod / (norm_q * norm_db) if (norm_q * norm_db) > 0 else 0.0
            
            # Normalize to 0-1
            score = float(max(0.0, min(1.0, score)))
            
            # Wrap in structure mapping upstream expected properties
            class SearchResult:
                def __init__(self, id_val, score_val, payload_val):
                    self.id = id_val
                    self.score = score_val
                    self.payload = payload_val
            
            results.append(SearchResult(row_id, score, payload))
            
        # Sort by similarity score descending
        results.sort(key=lambda x: x.score, reverse=True)
        return results[:top_k]

    def delete(self, vector_id):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM memb_vectors WHERE id = ?", (vector_id,))
        conn.commit()
        conn.close()

    def update(self, vector_id, vector=None, payload=None):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        if vector is not None:
            vec_blob = np.array(vector, dtype=np.float32).tobytes()
            cursor.execute(
                "UPDATE memb_vectors SET vector = ? WHERE id = ?",
                (vec_blob, vector_id)
            )
            
        if payload is not None:
            # Merge or overwrite payload? We fetch and merge
            cursor.execute("SELECT payload FROM memb_vectors WHERE id = ?", (vector_id,))
            row = cursor.fetchone()
            if row:
                existing_payload = json.loads(row[0])
                existing_payload.update(payload)
                cursor.execute(
                    "UPDATE memb_vectors SET payload = ? WHERE id = ?",
                    (json.dumps(existing_payload), vector_id)
                )
                
        conn.commit()
        conn.close()

    def get(self, vector_id):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id, vector, payload FROM memb_vectors WHERE id = ?",
            (vector_id,)
        )
        row = cursor.fetchone()
        conn.close()
        
        if not row:
            return None
            
        db_vector = np.frombuffer(row[1], dtype=np.float32).tolist()
        payload = json.loads(row[2])
        
        # Wrap in structure mapping upstream expected properties
        class GetResult:
            def __init__(self, id_val, vector_val, payload_val):
                self.id = id_val
                self.vector = vector_val
                self.payload = payload_val
                
        return GetResult(row[0], db_vector, payload)

    def list_cols(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT DISTINCT collection FROM memb_vectors")
        cols = [r[0] for r in cursor.fetchall()]
        conn.close()
        return cols

    def delete_col(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM memb_vectors WHERE collection = ?", (self.collection_name,))
        conn.commit()
        conn.close()

    def col_info(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM memb_vectors WHERE collection = ?", (self.collection_name,))
        count = cursor.fetchone()[0]
        conn.close()
        return {"count": count}

    def list(self, filters=None, top_k=None):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id, vector, payload FROM memb_vectors WHERE collection = ?",
            (self.collection_name,)
        )
        rows = cursor.fetchall()
        conn.close()
        
        results = []
        for row_id, vec_bytes, payload_str in rows:
            payload = json.loads(payload_str)
            
            # Apply metadata filters
            if filters:
                match = True
                for k, v in filters.items():
                    if payload.get(k) != v:
                        match = False
                        break
                if not match:
                    continue
                    
            db_vector = np.frombuffer(vec_bytes, dtype=np.float32).tolist()
            
            # Wrap in structure mapping upstream expected properties
            class ListResult:
                def __init__(self, id_val, vector_val, payload_val):
                    self.id = id_val
                    self.vector = vector_val
                    self.payload = payload_val
                    
            results.append(ListResult(row_id, db_vector, payload))
            
        if top_k:
            results = results[:top_k]
        return results

    def reset(self):
        self.delete_col()
