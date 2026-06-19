# src/retrieval/hybrid_retriever.py
# Combines Dense + BM25 using Reciprocal Rank Fusion (RRF)

from typing import List, Dict, Any
from loguru import logger
from backend.src.retrieval.dense_retriever import dense_retrieve
from backend.src.retrieval.bm25_retriever import BM25Retriever
from backend.src.vectorstore.faiss_store import FAISSVectorStore


def reciprocal_rank_fusion(
    dense_results: List[Dict[str, Any]],
    bm25_results: List[Dict[str, Any]],
    k: int = 60
) -> List[Dict[str, Any]]:

    rrf_scores = {}
    chunk_map = {}
    
    # Score dense results
    for rank, chunk in enumerate(dense_results):
        chunk_id = chunk["chunk_id"]
        rrf_scores[chunk_id] = rrf_scores.get(chunk_id, 0) + 1 / (k + rank + 1)
        chunk_map[chunk_id] = chunk
    
    # Score BM25 results
    for rank, chunk in enumerate(bm25_results):
        chunk_id = chunk["chunk_id"]
        rrf_scores[chunk_id] = rrf_scores.get(chunk_id, 0) + 1 / (k + rank + 1)
        if chunk_id not in chunk_map:
            chunk_map[chunk_id] = chunk
    
    # Sort by RRF score
    sorted_ids = sorted(
        rrf_scores.keys(),
        key=lambda x: rrf_scores[x],
        reverse=True
    )
    
    # Build final results
    results = []
    for chunk_id in sorted_ids:
        chunk = chunk_map[chunk_id].copy()
        chunk["rrf_score"] = rrf_scores[chunk_id]
        chunk["retrieval_method"] = "hybrid_rrf"
        results.append(chunk)
    
    logger.info(f"RRF fusion produced {len(results)} results")
    return results


def hybrid_retrieve(
    query: str,
    vector_store: FAISSVectorStore,
    bm25_retriever: BM25Retriever,
    dense_top_k: int = 10,
    bm25_top_k: int = 10,
    final_top_k: int = 5
) -> List[Dict[str, Any]]:
    logger.info(f"Hybrid retrieval for: '{query[:50]}'")
    
    # Step 1: Dense retrieval
    dense_results = dense_retrieve(query, vector_store, top_k=dense_top_k)
    
    # Step 2: BM25 retrieval
    bm25_results = bm25_retriever.retrieve(query, top_k=bm25_top_k)
    
    # Step 3: RRF fusion
    fused_results = reciprocal_rank_fusion(dense_results, bm25_results)
    
    # Step 4: Return top k
    final_results = fused_results[:final_top_k]
    
    logger.info(f"Hybrid retrieval final results: {len(final_results)}")
    return final_results