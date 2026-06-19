# src/retrieval/dense_retriever.py
# Dense retrieval using FAISS vector similarity search

from typing import List, Dict, Any
from loguru import logger
from backend.src.embeddings.embedder import embed_query
from backend.src.vectorstore.faiss_store import FAISSVectorStore


def dense_retrieve(
    query: str,
    vector_store: FAISSVectorStore,
    top_k: int = 10
) -> List[Dict[str, Any]]:

    logger.info(f"Dense retrieval for: '{query[:50]}'")
    
    # Embed the query
    query_embedding = embed_query(query)
    
    # Search FAISS
    results = vector_store.search(query_embedding, top_k=top_k)
    
    logger.info(f"Dense retrieval returned {len(results)} results")
    return results