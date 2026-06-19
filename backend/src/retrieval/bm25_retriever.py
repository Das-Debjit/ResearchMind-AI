# src/retrieval/bm25_retriever.py
# BM25 keyword-based retrieval — classic information retrieval

from rank_bm25 import BM25Okapi
from typing import List, Dict, Any
from loguru import logger


class BM25Retriever:   
    def __init__(self):
        self.bm25 = None
        self.chunks = []
    
    def index(self, chunks: List[Dict[str, Any]]):

        if not chunks:
            logger.warning("No chunks to index for BM25")
            return
        
        self.chunks = chunks
        
        # Tokenize — simple whitespace split works well
        tokenized = [
            chunk["text"].lower().split()
            for chunk in chunks
        ]
        
        self.bm25 = BM25Okapi(tokenized)
        logger.info(f"BM25 index built with {len(chunks)} chunks")
    
    def retrieve(
        self,
        query: str,
        top_k: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Retrieve chunks using BM25 keyword matching.
        """
        if self.bm25 is None or not self.chunks:
            logger.warning("BM25 index is empty")
            return []
        
        logger.info(f"BM25 retrieval for: '{query[:50]}'")
        
        # Tokenize query
        tokenized_query = query.lower().split()
        
        # Get BM25 scores
        scores = self.bm25.get_scores(tokenized_query)
        
        # Get top_k indices
        top_k = min(top_k, len(self.chunks))
        top_indices = sorted(
            range(len(scores)),
            key=lambda i: scores[i],
            reverse=True
        )[:top_k]
        
        # Build results
        results = []
        for idx in top_indices:
            if scores[idx] > 0:  # Only return relevant results
                chunk = self.chunks[idx].copy()
                chunk["score"] = float(scores[idx])
                chunk["retrieval_method"] = "bm25"
                results.append(chunk)
        
        logger.info(f"BM25 retrieval returned {len(results)} results")
        return results