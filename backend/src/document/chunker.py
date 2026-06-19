# src/document/chunker.py
# Splits pages into smaller chunks for better retrieval

from typing import List, Dict, Any
from loguru import logger


def chunk_pages(
    pages: List[Dict[str, Any]],
    chunk_size: int = 1000,
    chunk_overlap: int = 200
) -> List[Dict[str, Any]]:

    chunks = []
    chunk_id = 0
    
    for page in pages:
        text = page["text"]
        source = page["source"]
        page_number = page["page_number"]
        
        # If page is smaller than chunk_size, keep as is
        if len(text) <= chunk_size:
            chunks.append({
                "chunk_id": chunk_id,
                "text": text,
                "source": source,
                "page_number": page_number,
                "chunk_index": 0
            })
            chunk_id += 1
            continue
        
        # Split into overlapping chunks
        start = 0
        chunk_index = 0
        
        while start < len(text):
            end = start + chunk_size
            chunk_text = text[start:end]
            
            # Try to end at a sentence boundary
            if end < len(text):
                last_period = chunk_text.rfind(".")
                last_newline = chunk_text.rfind("\n")
                boundary = max(last_period, last_newline)
                
                if boundary > chunk_size // 2:
                    chunk_text = chunk_text[:boundary + 1]
                    end = start + boundary + 1
            
            if chunk_text.strip():
                chunks.append({
                    "chunk_id": chunk_id,
                    "text": chunk_text.strip(),
                    "source": source,
                    "page_number": page_number,
                    "chunk_index": chunk_index
                })
                chunk_id += 1
                chunk_index += 1
            
            # Move start with overlap
            start = end - chunk_overlap
        
    logger.info(f"Created {len(chunks)} chunks from {len(pages)} pages")
    return chunks