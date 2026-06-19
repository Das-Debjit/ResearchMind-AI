# src/retrieval/reranker.py
# Cross-encoder reranking for precision improvement

from sentence_transformers import CrossEncoder
from typing import List, Dict, Any
from loguru import logger


# Global reranker instance
_reranker = None


def get_reranker(
    model_name: str = "cross-encoder/ms-marco-MiniLM-L-6-v2"
) -> CrossEncoder:
    global _reranker
    if _reranker is None:
        logger.info(f"Loading reranker: {model_name}")
        _reranker = CrossEncoder(model_name)
        logger.info("Reranker loaded successfully!")
    return _reranker


def rerank(
    query: str,
    chunks: List[Dict[str, Any]],
    top_k: int = 5,
    model_name: str = "cross-encoder/ms-marco-MiniLM-L-6-v2"
) -> List[Dict[str, Any]]:

    if not chunks:
        logger.warning("No chunks to rerank")
        return []
    
    reranker = get_reranker(model_name)
    
    logger.info(f"Reranking {len(chunks)} chunks for: '{query[:50]}'")
    
    # Create (query, chunk_text) pairs for cross-encoder
    pairs = [(query, chunk["text"]) for chunk in chunks]
    
    # Score all pairs
    scores = reranker.predict(pairs)
    
    # Attach reranking scores
    for chunk, score in zip(chunks, scores):
        chunk["rerank_score"] = float(score)
    
    # Sort by rerank score
    reranked = sorted(
        chunks,
        key=lambda x: x["rerank_score"],
        reverse=True
    )[:top_k]
    
    for chunk in reranked:
        chunk["retrieval_method"] = "reranked"
    
    logger.info(f"Reranking complete. Top score: {reranked[0]['rerank_score']:.4f}")
    return reranked