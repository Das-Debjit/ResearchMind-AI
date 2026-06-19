# src/document/loader.py
# Handles PDF loading and text extraction using PyMuPDF

import fitz  # PyMuPDF
from pathlib import Path
from loguru import logger
from typing import List, Dict, Any


def load_pdf(file_path: str) -> List[Dict[str, Any]]:

    pages = []
    path = Path(file_path)
    
    if not path.exists():
        logger.error(f"File not found: {file_path}")
        raise FileNotFoundError(f"File not found: {file_path}")
    
    if path.suffix.lower() != ".pdf":
        logger.error(f"Invalid file type: {path.suffix}")
        raise ValueError(f"Only PDF files supported. Got: {path.suffix}")
    
    try:
        doc = fitz.open(file_path)
        logger.info(f"Loading PDF: {path.name} ({len(doc)} pages)")
        
        for page_num in range(len(doc)):
            page = doc[page_num]
            text = page.get_text()
            
            # Skip empty pages
            if not text.strip():
                logger.warning(f"Empty page {page_num + 1} in {path.name}")
                continue
            
            pages.append({
                "page_number": page_num + 1,
                "text": text.strip(),
                "source": path.name,
                "file_path": str(file_path)
            })
        
        doc.close()
        logger.info(f"Successfully loaded {len(pages)} pages from {path.name}")
        return pages
    
    except Exception as e:
        logger.error(f"Error loading PDF {file_path}: {str(e)}")
        raise


def load_multiple_pdfs(file_paths: List[str]) -> List[Dict[str, Any]]:

    all_pages = []
    
    for file_path in file_paths:
        try:
            pages = load_pdf(file_path)
            all_pages.extend(pages)
            logger.info(f"Loaded {len(pages)} pages from {file_path}")
        except Exception as e:
            logger.error(f"Failed to load {file_path}: {str(e)}")
            continue
    
    logger.info(f"Total pages loaded: {len(all_pages)}")
    return all_pages