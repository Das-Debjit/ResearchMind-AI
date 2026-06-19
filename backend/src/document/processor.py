# src/document/processor.py
# Main pipeline: PDF → Pages → Chunks

from typing import List, Dict, Any
from loguru import logger
from backend.src.document.loader import load_pdf, load_multiple_pdfs
from backend.src.document.chunker import chunk_pages


def process_pdf(
    file_path: str,
    chunk_size: int = 1000,
    chunk_overlap: int = 200
) -> List[Dict[str, Any]]:

    logger.info(f"Processing PDF: {file_path}")
    
    # Step 1: Load PDF
    pages = load_pdf(file_path)
    
    if not pages:
        logger.warning(f"No content extracted from {file_path}")
        return []
    
    # Step 2: Chunk pages
    chunks = chunk_pages(pages, chunk_size, chunk_overlap)
    
    logger.info(
        f"Processed {file_path}: "
        f"{len(pages)} pages → {len(chunks)} chunks"
    )
    
    return chunks


def process_multiple_pdfs(
    file_paths: List[str],
    chunk_size: int = 1000,
    chunk_overlap: int = 200
) -> Dict[str, List[Dict[str, Any]]]:

    results = {}
    
    for file_path in file_paths:
        try:
            chunks = process_pdf(file_path, chunk_size, chunk_overlap)
            
            from pathlib import Path
            filename = Path(file_path).name
            results[filename] = chunks
            
        except Exception as e:
            logger.error(f"Failed to process {file_path}: {str(e)}")
            continue
    
    total_chunks = sum(len(c) for c in results.values())
    logger.info(
        f"Processed {len(results)} PDFs → "
        f"{total_chunks} total chunks"
    )
    
    return results