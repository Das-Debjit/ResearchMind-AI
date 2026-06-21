# main.py
# FastAPI application — main entry point
# Each user (identified by an anonymous X-User-Id header) gets their own
# isolated FAISS index, BM25 index, and upload folder.

from fastapi import FastAPI, UploadFile, File, HTTPException, Header
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
from loguru import logger
import os
import re
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

app = FastAPI(
    title="ResearchMind AI",
    description="Enterprise Research Paper Intelligence Platform",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

BASE_DIR = Path(__file__).resolve().parent
USERS_DIR = BASE_DIR / "data" / "users"
USERS_DIR.mkdir(parents=True, exist_ok=True)

# Per-user state, created lazily and cached in memory per process.
# Each entry: { "vector_store": FAISSVectorStore, "bm25": BM25Retriever }
_user_state = {}


def safe_user_id(raw_user_id: Optional[str]) -> str:
    """Sanitize the incoming user id so it's safe to use as a folder name."""
    if not raw_user_id:
        raise HTTPException(status_code=400, detail="Missing X-User-Id header")
    cleaned = re.sub(r"[^a-zA-Z0-9_\-]", "", raw_user_id)[:80]
    if not cleaned:
        raise HTTPException(status_code=400, detail="Invalid X-User-Id header")
    return cleaned


def get_user_context(user_id: str):
    """Get (and lazily create) this user's isolated vector store, BM25 index,
    and upload folder. Always reloads from disk so multiple replicas stay
    consistent."""
    user_dir = USERS_DIR / user_id
    upload_dir = user_dir / "uploaded_papers"
    index_dir = user_dir / "faiss_index"
    upload_dir.mkdir(parents=True, exist_ok=True)
    index_dir.mkdir(parents=True, exist_ok=True)

    if user_id not in _user_state:
        _user_state[user_id] = {
            "vector_store": FAISSVectorStore(index_path=str(index_dir)),
            "bm25": BM25Retriever(),
        }

    ctx = _user_state[user_id]
    ctx["vector_store"].load()
    ctx["bm25"].index(ctx["vector_store"].get_all_chunks())
    ctx["upload_dir"] = upload_dir
    return ctx


def get_current_papers(vector_store: FAISSVectorStore) -> List[str]:
    chunks = vector_store.get_all_chunks()
    return list(set(chunk["source"] for chunk in chunks)) if chunks else []


# ─── Request Models ───────────────────────────────────────

class QuestionRequest(BaseModel):
    question: str
    top_k: Optional[int] = 5
    paper_filter: Optional[List[str]] = None


class SummarizeRequest(BaseModel):
    paper_name: str


class ExtractRequest(BaseModel):
    paper_name: str
    extract_type: str


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
    }


@app.get("/api/papers")
def get_papers(x_user_id: Optional[str] = Header(None)):
    user_id = safe_user_id(x_user_id)
    ctx = get_user_context(user_id)
    papers = get_current_papers(ctx["vector_store"])
    return {"papers": papers, "total": len(papers)}


@app.post("/api/upload")
async def upload_paper(
    file: UploadFile = File(...),
    x_user_id: Optional[str] = Header(None)
):
    user_id = safe_user_id(x_user_id)
    ctx = get_user_context(user_id)

    if not file.filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported")

    try:
        file_path = ctx["upload_dir"] / file.filename
        with open(file_path, "wb") as f:
            shutil.copyfileobj(file.file, f)

        logger.info(f"[{user_id}] File saved: {file.filename}")

        chunks = process_pdf(str(file_path))
        if not chunks:
            raise HTTPException(status_code=400, detail="Could not extract text from PDF")

        embedded_chunks = embed_chunks(chunks)

        vector_store = ctx["vector_store"]
        vector_store.load()
        vector_store.add_chunks(embedded_chunks)
        vector_store.save()

        ctx["bm25"].index(vector_store.get_all_chunks())

        current_papers = get_current_papers(vector_store)

        logger.info(f"[{user_id}] Successfully processed: {file.filename}")

        return {
            "message": f"Successfully uploaded and processed {file.filename}",
            "paper": file.filename,
            "chunks_created": len(chunks),
            "total_papers": len(current_papers)
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[{user_id}] Upload error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/ask")
def ask_question(request: QuestionRequest, x_user_id: Optional[str] = Header(None)):
    user_id = safe_user_id(x_user_id)
    ctx = get_user_context(user_id)
    papers = get_current_papers(ctx["vector_store"])

    if not papers:
        raise HTTPException(status_code=400, detail="Please upload at least one paper first")

    try:
        result = answer_question(
            query=request.question,
            vector_store=ctx["vector_store"],
            bm25_retriever=ctx["bm25"],
            top_k=request.top_k,
            paper_filter=request.paper_filter
        )
        return result
    except Exception as e:
        logger.error(f"[{user_id}] QA error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/summarize")
def summarize(request: SummarizeRequest, x_user_id: Optional[str] = Header(None)):
    user_id = safe_user_id(x_user_id)
    ctx = get_user_context(user_id)
    papers = get_current_papers(ctx["vector_store"])

    if request.paper_name not in papers:
        raise HTTPException(status_code=404, detail=f"Paper not found: {request.paper_name}")

    try:
        result = summarize_paper(request.paper_name, ctx["vector_store"])
        return result
    except Exception as e:
        logger.error(f"[{user_id}] Summarize error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/extract")
def extract(request: ExtractRequest, x_user_id: Optional[str] = Header(None)):
    user_id = safe_user_id(x_user_id)
    ctx = get_user_context(user_id)
    papers = get_current_papers(ctx["vector_store"])

    if request.paper_name not in papers:
        raise HTTPException(status_code=404, detail=f"Paper not found: {request.paper_name}")

    try:
        if request.extract_type == "methodology":
            result = extract_methodology(request.paper_name, ctx["vector_store"])
        elif request.extract_type == "findings":
            result = extract_findings(request.paper_name, ctx["vector_store"])
        elif request.extract_type == "future_work":
            result = extract_future_work(request.paper_name, ctx["vector_store"])
        else:
            raise HTTPException(
                status_code=400,
                detail="extract_type must be: methodology, findings, future_work"
            )
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[{user_id}] Extract error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/compare")
def compare(request: CompareRequest, x_user_id: Optional[str] = Header(None)):
    user_id = safe_user_id(x_user_id)
    ctx = get_user_context(user_id)
    papers = get_current_papers(ctx["vector_store"])

    for paper in request.paper_names:
        if paper not in papers:
            raise HTTPException(status_code=404, detail=f"Paper not found: {paper}")

    try:
        result = compare_papers(request.paper_names, ctx["vector_store"])
        return result
    except Exception as e:
        logger.error(f"[{user_id}] Compare error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/gaps")
def gaps(request: GapRequest, x_user_id: Optional[str] = Header(None)):
    user_id = safe_user_id(x_user_id)
    ctx = get_user_context(user_id)

    try:
        result = analyze_gaps(request.paper_names, ctx["vector_store"])
        return result
    except Exception as e:
        logger.error(f"[{user_id}] Gap analysis error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/api/papers")
def clear_papers(x_user_id: Optional[str] = Header(None)):
    user_id = safe_user_id(x_user_id)
    ctx = get_user_context(user_id)

    ctx["vector_store"].clear()
    ctx["bm25"].__init__()

    for f in ctx["upload_dir"].glob("*.pdf"):
        f.unlink()

    return {"message": "All papers cleared successfully"}


if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("backend.main:app", host="0.0.0.0", port=port)