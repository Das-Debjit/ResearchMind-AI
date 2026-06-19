# src/features/gap_analyzer.py
# Research gap analysis across papers

from typing import List, Dict, Any
from loguru import logger
from backend.src.llm.gemini_client import generate_response
from backend.src.llm.prompts import gap_analysis_prompt
from backend.src.vectorstore.faiss_store import FAISSVectorStore


def analyze_gaps(
    paper_names: List[str],
    vector_store: FAISSVectorStore
) -> Dict[str, Any]:

    logger.info(f"Analyzing research gaps for: {paper_names}")

    all_chunks = vector_store.get_all_chunks()
    combined_chunks = []

    for paper_name in paper_names:
        paper_chunks = [
            chunk for chunk in all_chunks
            if chunk["source"] == paper_name
        ][:10]
        combined_chunks.extend(paper_chunks)

    if not combined_chunks:
        return {
            "gaps": "No content found.",
            "papers": paper_names
        }

    prompt = gap_analysis_prompt(combined_chunks, paper_names)
    gaps = generate_response(prompt, temperature=0.4, max_tokens=2048)

    return {
        "gaps": gaps,
        "papers": paper_names,
        "chunks_analyzed": len(combined_chunks)
    }