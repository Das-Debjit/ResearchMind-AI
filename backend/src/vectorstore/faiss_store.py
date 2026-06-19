# src/vectorstore/faiss_store.py
# Stores and retrieves embeddings using FAISS (Meta AI)

import faiss
import numpy as np
import pickle
import os
from typing import List, Dict, Any, Optional
from loguru import logger
from pathlib import Path


class FAISSVectorStore:
    def __init__(self, index_path: str = "./data/faiss_index"):
        self.index_path = index_path
        self.index = None
        self.chunks = []  # Store original chunks with metadata
        self.dimension = 384  # all-MiniLM-L6-v2 outputs 384-dim vectors
        
        # Create directory if it doesn't exist
        Path(index_path).mkdir(parents=True, exist_ok=True)
        
        self.index_file = os.path.join(index_path, "index.faiss")
        self.chunks_file = os.path.join(index_path, "chunks.pkl")
    
    def create_index(self, dimension: int = 384):
        self.dimension = dimension
        # Normalize vectors + inner product = cosine similarity
        self.index = faiss.IndexFlatIP(dimension)
        logger.info(f"Created FAISS index with dimension {dimension}")
    
    def add_chunks(self, embedded_chunks: List[Dict[str, Any]]):
        if not embedded_chunks:
            logger.warning("No chunks to add")
            return
        
        # Get dimension from first embedding
        dimension = len(embedded_chunks[0]["embedding"])
        
        # Create index if it doesn't exist
        if self.index is None:
            self.create_index(dimension)
        
        # Extract embeddings as numpy array
        embeddings = np.array(
            [chunk["embedding"] for chunk in embedded_chunks],
            dtype=np.float32
        )
        
        # Normalize for cosine similarity
        faiss.normalize_L2(embeddings)
        
        # Store chunks without embeddings (save memory)
        chunks_without_embeddings = []
        for chunk in embedded_chunks:
            chunk_copy = {k: v for k, v in chunk.items() if k != "embedding"}
            chunk_copy["faiss_id"] = len(self.chunks) + len(chunks_without_embeddings)
            chunks_without_embeddings.append(chunk_copy)
        
        # Add to FAISS index
        self.index.add(embeddings)
        self.chunks.extend(chunks_without_embeddings)
        
        logger.info(f"Added {len(embedded_chunks)} chunks to FAISS index")
        logger.info(f"Total chunks in index: {self.index.ntotal}")
    
    def search(
        self,
        query_embedding: np.ndarray,
        top_k: int = 10
    ) -> List[Dict[str, Any]]:
        if self.index is None or self.index.ntotal == 0:
            logger.warning("FAISS index is empty")
            return []
        
        # Reshape and normalize query
        query = np.array([query_embedding], dtype=np.float32)
        faiss.normalize_L2(query)
        
        # Search
        top_k = min(top_k, self.index.ntotal)
        scores, indices = self.index.search(query, top_k)
        
        # Build results
        results = []
        for score, idx in zip(scores[0], indices[0]):
            if idx == -1:  # FAISS returns -1 for empty slots
                continue
            chunk = self.chunks[idx].copy()
            chunk["score"] = float(score)
            chunk["retrieval_method"] = "dense"
            results.append(chunk)
        
        logger.info(f"FAISS search returned {len(results)} results")
        return results
    
    def save(self):
        if self.index is None:
            logger.warning("No index to save")
            return
        
        faiss.write_index(self.index, self.index_file)
        
        with open(self.chunks_file, "wb") as f:
            pickle.dump(self.chunks, f)
        
        logger.info(f"Saved FAISS index to {self.index_path}")
    
    def load(self) -> bool:
        if not os.path.exists(self.index_file):
            logger.info("No existing FAISS index found")
            return False
        
        self.index = faiss.read_index(self.index_file)
        
        with open(self.chunks_file, "rb") as f:
            self.chunks = pickle.load(f)
        
        logger.info(
            f"Loaded FAISS index: {self.index.ntotal} vectors"
        )
        return True
    
    def clear(self):
        self.index = None
        self.chunks = []
        
        if os.path.exists(self.index_file):
            os.remove(self.index_file)
        if os.path.exists(self.chunks_file):
            os.remove(self.chunks_file)
        
        logger.info("FAISS index cleared")
    
    def get_all_chunks(self) -> List[Dict[str, Any]]:
        return self.chunks
    
    @property
    def total_chunks(self) -> int:
        return len(self.chunks)