# src/features/extractor.py
# Extract methodology, findings, future work

from typing import List, Dict, Any
from loguru import logger
from backend.src.llm.gemini_client import generate_response
from backend.src.llm.prompts import (
    extract_methodology_prompt,
    extract_findings_prompt,
    extract_future_work_prompt
)
from backend.src.vectorstore.faiss_store import FAISSVectorStore


def get_paper_chunks(
    paper_name: str,
    vector_store: FAISSVectorStore,
    max_chunks: int = 15
) -> List[Dict[str, Any]]:

    all_chunks = vector_store.get_all_chunks()
    paper_chunks = [
        chunk for chunk in all_chunks
        if chunk["source"] == paper_name
    ]
    return paper_chunks[:max_chunks]


def extract_methodology(
    paper_name: str,
    vector_store: FAISSVectorStore
) -> Dict[str, Any]:
  
    logger.info(f"Extracting methodology from: {paper_name}")

    chunks = get_paper_chunks(paper_name, vector_store)
    if not chunks:
        return {"methodology": "No content found.", "paper": paper_name}

    prompt = extract_methodology_prompt(chunks)
    methodology = generate_response(prompt, temperature=0.2)

    return {"methodology": methodology, "paper": paper_name}


def extract_findings(
    paper_name: str,
    vector_store: FAISSVectorStore
) -> Dict[str, Any]:
   
    logger.info(f"Extracting findings from: {paper_name}")

    chunks = get_paper_chunks(paper_name, vector_store)
    if not chunks:
        return {"findings": "No content found.", "paper": paper_name}

    prompt = extract_findings_prompt(chunks)
    findings = generate_response(prompt, temperature=0.2)

    return {"findings": findings, "paper": paper_name}


def extract_future_work(
    paper_name: str,
    vector_store: FAISSVectorStore
) -> Dict[str, Any]:
  
    logger.info(f"Extracting future work from: {paper_name}")

    chunks = get_paper_chunks(paper_name, vector_store)
    if not chunks:
        return {"future_work": "No content found.", "paper": paper_name}

    prompt = extract_future_work_prompt(chunks)
    future_work = generate_response(prompt, temperature=0.2)

    return {"future_work": future_work, "paper": paper_name}