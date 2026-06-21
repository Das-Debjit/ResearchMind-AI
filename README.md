---
title: ResearchMind AI Backend
emoji: 🧠
colorFrom: green
colorTo: blue
sdk: docker
pinned: false
---

# ResearchMind AI

**Research reading, with receipts.** Upload a paper, ask it anything, and get an answer that points to the exact page it came from — every time.

A production-grade Retrieval-Augmented Generation (RAG) platform built end-to-end: custom hybrid retrieval, citation-grounded answers, and multi-paper analysis, deployed live across two free-tier platforms.

🔗 **Live app:** [research-mind-ai-six.vercel.app](https://research-mind-ai-six.vercel.app/)
🔗 **Live API:** [debjit-007-researchmind-ai-backend.hf.space](https://debjit-007-researchmind-ai-backend.hf.space/docs)

---

## What it does

| Feature | Description |
|---|---|
| **Ask** | Question-answering across one or more papers, with page-level citations on every answer |
| **Analyze** | Structured summaries, plus targeted extraction of methodology, key findings, or future work |
| **Compare** | Side-by-side comparison of approach, data, and results across two or more papers |
| **Gap Analysis** | Surfaces research gaps and open questions across an uploaded paper collection |

---

## Architecture

```
PDF Upload
   │
   ▼
Text Extraction (PyMuPDF) → Chunking (overlapping windows)
   │
   ▼
Embedding (Sentence-Transformers, all-MiniLM-L6-v2)
   │
   ▼
Vector Store (FAISS) ──────┐
                            │
Keyword Index (BM25) ──────┤
                            ▼
              Reciprocal Rank Fusion (hybrid retrieval)
                            │
                            ▼
              Cross-Encoder Reranking (optional, memory-gated)
                            │
                            ▼
              Gemini (answer generation + citation grounding)
                            │
                            ▼
                    Answer + page-level sources
```

**Frontend** (HTML / CSS / vanilla JS) talks to the **backend** (FastAPI) over a REST API. No frontend framework, no build step — deployed as static files.

---

## Tech stack

- **Backend:** FastAPI, Python
- **Retrieval:** FAISS (dense), `rank-bm25` (sparse), custom Reciprocal Rank Fusion, Sentence-Transformers cross-encoder reranker
- **Embeddings:** `all-MiniLM-L6-v2`
- **LLM:** Google Gemini (`gemini-3.1-flash-lite`)
- **PDF parsing:** PyMuPDF
- **Frontend:** HTML, CSS, vanilla JavaScript
- **Deployment:** Backend on Hugging Face Spaces (Docker), frontend on Vercel

---

## Evaluation

Retrieval and answer quality were measured with a custom LLM-as-judge evaluation script (`backend/evaluation/eval.py`) against a held-out set of test questions with known ground-truth answers:

| Metric | Score |
|---|---|
| Faithfulness | 0.40 |
| Answer Relevancy | 1.00 |
| Factual Correctness | 0.86 |
| Avg. citations per answer | 5.0 |

> Faithfulness is scored against 200-character truncated citation snippets rather than full retrieved chunks, which under-penalizes correct answers that draw on detail outside the truncated preview — a known limitation of the current scoring approach, not the retrieval pipeline itself.

---

## Why hybrid retrieval

Dense retrieval (FAISS) captures semantic similarity but can miss exact technical terms. Sparse retrieval (BM25) catches exact keyword matches but misses paraphrases. Reciprocal Rank Fusion combines both ranked lists without needing to normalize incompatible similarity scores — a chunk that ranks well in *either* method gets credit, and chunks that rank well in *both* rise to the top.

---

## Local setup

```bash
git clone https://github.com/Das-Debjit/ResearchMind-AI.git
cd ResearchMind-AI

# Backend
cd backend
pip install -r requirements.txt
# Add GEMINI_API_KEY to a .env file in this folder
uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000

# Frontend (separate terminal, from project root)
cd frontend
python -m http.server 3000
```

Visit `http://localhost:3000`.

---

## Project structure

```
ResearchMind-AI/
├── backend/
│   ├── main.py                  # FastAPI app and routes
│   ├── src/
│   │   ├── document/            # PDF loading and chunking
│   │   ├── embeddings/          # Sentence-Transformers wrapper
│   │   ├── vectorstore/         # FAISS index management
│   │   ├── retrieval/           # Dense, BM25, hybrid RRF, reranker
│   │   ├── llm/                 # Gemini client and prompts
│   │   └── features/            # QA, summarization, extraction, comparison, gap analysis
│   ├── evaluation/eval.py       # LLM-as-judge evaluation script
│   └── requirements.txt
├── frontend/
│   ├── index.html               # Upload / library page
│   ├── chat.html                # Ask
│   ├── analyze.html             # Summarize / extract
│   ├── compare.html             # Compare / gap analysis
│   ├── css/main.css
│   └── js/
└── Dockerfile                    # Hugging Face Spaces deployment
```

---

## Author

**Debjit Das**
[GitHub](https://github.com/Das-Debjit) · [LinkedIn](https://linkedin.com/in/debjitdas82) · [Portfolio](https://debjit-das-portfolio.vercel.app/)