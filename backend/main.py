# main.py
# FastAPI application — main entry point

from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
from loguru import logger
import os
import shutil
from pathlib import Path

from backend.src.document.processor import process_pdf
from backend.src.embeddings.embedder import embed_chunks
from backend.src.vectorstore.faiss_store import FAISSVectorStore
from backend.src.retrieval.bm25_retriever import BM25Retriever
from backend.src.features.qa import answer_question
from backend.src.features.summarizer import summarize_paper
from backend.src.features.extractor import (
    extract_methodology,
    extract_findings,
    extract_future_work
)
from backend.src.features.comparator import compare_papers
from backend.src.features.gap_analyzer import analyze_gaps

# Initialize FastAPI app
app = FastAPI(
    title="ResearchMind AI",
    description="Enterprise Research Paper Intelligence Platform",
    version="1.0.0"
)

# CORS — allows frontend to call backend
# NOTE: tighten allow_origins to your actual Vercel URL once deployed,
# e.g. ["https://your-app.vercel.app"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

# Global state — vector store and BM25 retriever
vector_store = FAISSVectorStore(index_path="./data/faiss_index")
bm25_retriever = BM25Retriever()
uploaded_papers = []

# Upload directory
UPLOAD_DIR = Path("./data/uploaded_papers")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

# Try loading existing index on startup
vector_store.load()

# Rebuild uploaded_papers list and BM25 index from existing FAISS data
all_chunks = vector_store.get_all_chunks()
if all_chunks:
    uploaded_papers = list(set(chunk["source"] for chunk in all_chunks))
    bm25_retriever.index(all_chunks)
    logger.info(f"Restored {len(uploaded_papers)} papers from existing index: {uploaded_papers}")


# ─── Request Models ───────────────────────────────────────

class QuestionRequest(BaseModel):
    question: str
    top_k: Optional[int] = 5
    paper_filter: Optional[List[str]] = None


class SummarizeRequest(BaseModel):
    paper_name: str


class ExtractRequest(BaseModel):
    paper_name: str
    extract_type: str  # "methodology", "findings", "future_work"


class CompareRequest(BaseModel):
    paper_names: List[str]


class GapRequest(BaseModel):
    paper_names: List[str]


# ─── Routes ───────────────────────────────────────────────

@app.get("/")
def root():
    return {
        "message": "ResearchMind AI is running!",
        "version": "1.0.0",
        "papers_loaded": len(uploaded_papers)
    }


@app.get("/api/papers")
def get_papers():
    return {
        "papers": uploaded_papers,
        "total": len(uploaded_papers)
    }


@app.post("/api/upload")
async def upload_paper(file: UploadFile = File(...)):
    # Validate file type
    if not file.filename.endswith(".pdf"):
        raise HTTPException(
            status_code=400,
            detail="Only PDF files are supported"
        )

    try:
        # Save uploaded file
        file_path = UPLOAD_DIR / file.filename
        with open(file_path, "wb") as f:
            shutil.copyfileobj(file.file, f)

        logger.info(f"File saved: {file.filename}")

        # Process PDF → chunks
        chunks = process_pdf(str(file_path))

        if not chunks:
            raise HTTPException(
                status_code=400,
                detail="Could not extract text from PDF"
            )

        # Embed chunks
        embedded_chunks = embed_chunks(chunks)

        # Add to FAISS index
        vector_store.add_chunks(embedded_chunks)

        # Update BM25 index
        all_chunks = vector_store.get_all_chunks()
        bm25_retriever.index(all_chunks)

        # Save index
        vector_store.save()

        # Track uploaded papers
        if file.filename not in uploaded_papers:
            uploaded_papers.append(file.filename)

        logger.info(f"Successfully processed: {file.filename}")

        return {
            "message": f"Successfully uploaded and processed {file.filename}",
            "paper": file.filename,
            "chunks_created": len(chunks),
            "total_papers": len(uploaded_papers)
        }

    except Exception as e:
        logger.error(f"Upload error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/ask")
def ask_question(request: QuestionRequest):
    """Answer a question using RAG pipeline."""
    if not uploaded_papers:
        raise HTTPException(
            status_code=400,
            detail="Please upload at least one paper first"
        )

    try:
        result = answer_question(
            query=request.question,
            vector_store=vector_store,
            bm25_retriever=bm25_retriever,
            top_k=request.top_k,
            paper_filter=request.paper_filter
        )
        return result

    except Exception as e:
        logger.error(f"QA error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/summarize")
def summarize(request: SummarizeRequest):
    if request.paper_name not in uploaded_papers:
        raise HTTPException(
            status_code=404,
            detail=f"Paper not found: {request.paper_name}"
        )

    try:
        result = summarize_paper(request.paper_name, vector_store)
        return result

    except Exception as e:
        logger.error(f"Summarize error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/extract")
def extract(request: ExtractRequest):
    if request.paper_name not in uploaded_papers:
        raise HTTPException(
            status_code=404,
            detail=f"Paper not found: {request.paper_name}"
        )

    try:
        if request.extract_type == "methodology":
            result = extract_methodology(request.paper_name, vector_store)
        elif request.extract_type == "findings":
            result = extract_findings(request.paper_name, vector_store)
        elif request.extract_type == "future_work":
            result = extract_future_work(request.paper_name, vector_store)
        else:
            raise HTTPException(
                status_code=400,
                detail="extract_type must be: methodology, findings, future_work"
            )
        return result

    except Exception as e:
        logger.error(f"Extract error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/compare")
def compare(request: CompareRequest):
    for paper in request.paper_names:
        if paper not in uploaded_papers:
            raise HTTPException(
                status_code=404,
                detail=f"Paper not found: {paper}"
            )

    try:
        result = compare_papers(request.paper_names, vector_store)
        return result

    except Exception as e:
        logger.error(f"Compare error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/gaps")
def gaps(request: GapRequest):
    try:
        result = analyze_gaps(request.paper_names, vector_store)
        return result

    except Exception as e:
        logger.error(f"Gap analysis error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/api/papers")
def clear_papers():
    vector_store.clear()
    bm25_retriever.__init__()
    uploaded_papers.clear()

    # Clear uploaded files
    for f in UPLOAD_DIR.glob("*.pdf"):
        f.unlink()

    return {"message": "All papers cleared successfully"}


# ─── Local/Production entrypoint ───────────────────────────
# Allows `python -m backend.main` as a fallback to uvicorn CLI.
# Render's actual start command (see Procfile) still uses uvicorn directly.

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("backend.main:app", host="0.0.0.0", port=port)