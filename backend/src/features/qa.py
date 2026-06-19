# src/features/qa.py
# Question Answering over research papers

from typing import List, Dict, Any, Optional
from loguru import logger
from backend.src.retrieval.hybrid_retriever import hybrid_retrieve
from backend.src.retrieval.reranker import rerank
from backend.src.llm.gemini_client import generate_response
from backend.src.llm.prompts import qa_prompt
from backend.src.vectorstore.faiss_store import FAISSVectorStore
from backend.src.retrieval.bm25_retriever import BM25Retriever


def answer_question(
    query: str,
    vector_store: FAISSVectorStore,
    bm25_retriever: BM25Retriever,
    top_k: int = 5,
    paper_filter: Optional[List[str]] = None
) -> Dict[str, Any]:

    logger.info(f"Answering question: '{query}' | Filter: {paper_filter}")

    # Step 1: Hybrid retrieval (get more results since we'll filter)
    retrieved_chunks = hybrid_retrieve(
        query=query,
        vector_store=vector_store,
        bm25_retriever=bm25_retriever,
        dense_top_k=20,
        bm25_top_k=20,
        final_top_k=20
    )

    # Step 2: Filter by selected papers if specified
    if paper_filter:
        retrieved_chunks = [
            chunk for chunk in retrieved_chunks
            if chunk["source"] in paper_filter
        ]

    if not retrieved_chunks:
        return {
            "answer": "No relevant content found in the selected papers.",
            "sources": [],
            "chunks_used": 0
        }

    # Step 3: Rerank for precision
    reranked_chunks = rerank(
        query=query,
        chunks=retrieved_chunks,
        top_k=top_k
    )

    # Step 4: Generate answer with Gemini
    prompt = qa_prompt(query, reranked_chunks)
    answer = generate_response(prompt, temperature=0.3)

    # Step 5: Build citations
    sources = []
    for chunk in reranked_chunks:
        source = {
            "document": chunk["source"],
            "page": chunk["page_number"],
            "snippet": chunk["text"][:200] + "...",
            "relevance_score": chunk.get("rerank_score", 0)
        }
        if source not in sources:
            sources.append(source)

    logger.info(f"Answer generated with {len(sources)} citations")

    return {
        "answer": answer,
        "sources": sources,
        "chunks_used": len(reranked_chunks)
    }