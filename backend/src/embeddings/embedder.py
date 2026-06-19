# src/embeddings/embedder.py
# Converts text chunks into vector embeddings using Sentence Transformers

from sentence_transformers import SentenceTransformer
from typing import List, Dict, Any
from loguru import logger
import numpy as np


# Global model instance — loaded once, reused everywhere
_model = None


def get_embedding_model(model_name: str = "all-MiniLM-L6-v2") -> SentenceTransformer:

    global _model
    if _model is None:
        logger.info(f"Loading embedding model: {model_name}")
        _model = SentenceTransformer(model_name)
        logger.info("Embedding model loaded successfully!")
    return _model


def embed_text(text: str, model_name: str = "all-MiniLM-L6-v2") -> np.ndarray:

    model = get_embedding_model(model_name)
    embedding = model.encode(text, convert_to_numpy=True)
    return embedding


def embed_chunks(
    chunks: List[Dict[str, Any]],
    model_name: str = "all-MiniLM-L6-v2",
    batch_size: int = 32
) -> List[Dict[str, Any]]:

    model = get_embedding_model(model_name)
    
    # Extract just the text for batch encoding
    texts = [chunk["text"] for chunk in chunks]
    
    logger.info(f"Embedding {len(texts)} chunks in batches of {batch_size}")
    
    # Batch encode — much faster than one by one
    embeddings = model.encode(
        texts,
        batch_size=batch_size,
        show_progress_bar=True,
        convert_to_numpy=True
    )
    
    # Attach embeddings back to chunks
    embedded_chunks = []
    for chunk, embedding in zip(chunks, embeddings):
        chunk_with_embedding = chunk.copy()
        chunk_with_embedding["embedding"] = embedding
        embedded_chunks.append(chunk_with_embedding)
    
    logger.info(f"Successfully embedded {len(embedded_chunks)} chunks")
    logger.info(f"Embedding dimension: {embeddings.shape[1]}")
    
    return embedded_chunks


def embed_query(
    query: str,
    model_name: str = "all-MiniLM-L6-v2"
) -> np.ndarray:

    model = get_embedding_model(model_name)
    query_embedding = model.encode(
        query,
        convert_to_numpy=True
    )
    logger.info(f"Query embedded: '{query[:50]}...'")
    return query_embedding