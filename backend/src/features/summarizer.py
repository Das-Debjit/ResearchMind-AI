# src/features/summarizer.py
# Research paper summarization

from typing import List, Dict, Any
from loguru import logger
from backend.src.llm.gemini_client import generate_response
from backend.src.llm.prompts import summarize_prompt
from backend.src.vectorstore.faiss_store import FAISSVectorStore


def summarize_paper(
    paper_name: str,
    vector_store: FAISSVectorStore
) -> Dict[str, Any]:
 
    logger.info(f"Summarizing paper: {paper_name}")

    # Get all chunks for this paper
    all_chunks = vector_store.get_all_chunks()
    paper_chunks = [
        chunk for chunk in all_chunks
        if chunk["source"] == paper_name
    ]

    if not paper_chunks:
        return {
            "summary": f"No content found for paper: {paper_name}",
            "paper": paper_name,
            "total_chunks": 0
        }

    # Use first 20 chunks for summary (covers most of paper)
    chunks_to_use = paper_chunks[:20]

    # Generate summary
    prompt = summarize_prompt(chunks_to_use, paper_name)
    summary = generate_response(prompt, temperature=0.3, max_tokens=2048)

    logger.info(f"Summary generated for {paper_name}")

    return {
        "summary": summary,
        "paper": paper_name,
        "total_chunks": len(paper_chunks),
        "chunks_used": len(chunks_to_use)
    }