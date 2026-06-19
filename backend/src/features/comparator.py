# src/features/comparator.py
# Compare multiple research papers

from typing import List, Dict, Any
from loguru import logger
from backend.src.llm.gemini_client import generate_response
from backend.src.llm.prompts import compare_papers_prompt
from backend.src.vectorstore.faiss_store import FAISSVectorStore


def compare_papers(
    paper_names: List[str],
    vector_store: FAISSVectorStore
) -> Dict[str, Any]:
  
    if len(paper_names) < 2:
        return {
            "comparison": "Please provide at least 2 papers to compare.",
            "papers": paper_names
        }

    logger.info(f"Comparing papers: {paper_names}")

    # Get chunks from all papers
    all_chunks = vector_store.get_all_chunks()
    combined_chunks = []

    for paper_name in paper_names:
        paper_chunks = [
            chunk for chunk in all_chunks
            if chunk["source"] == paper_name
        ][:10]  # 10 chunks per paper
        combined_chunks.extend(paper_chunks)

    if not combined_chunks:
        return {
            "comparison": "No content found for the specified papers.",
            "papers": paper_names
        }

    prompt = compare_papers_prompt(combined_chunks, paper_names)
    comparison = generate_response(prompt, temperature=0.3, max_tokens=3000)

    return {
        "comparison": comparison,
        "papers": paper_names,
        "chunks_used": len(combined_chunks)
    }