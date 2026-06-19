# backend/evaluation/eval.py
# Lightweight RAG evaluation for ResearchMind AI — no external eval framework needed.
# Uses Gemini itself as a judge, scoring Faithfulness, Relevancy, and Factual Correctness.

import sys
import time
import json
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent.parent))

from backend.src.vectorstore.faiss_store import FAISSVectorStore
from backend.src.retrieval.bm25_retriever import BM25Retriever
from backend.src.features.qa import answer_question
from backend.src.llm.gemini_client import generate_response
from loguru import logger


# ─── Test Set ───────────────────────────────────────────────

TEST_SET = [
    {
        "question": "What is MAPINN and what problem does it solve?",
        "ground_truth": "MAPINN is a Multi-Scale Adaptive Physics-Informed Neural Network designed to solve nonlinear PDEs with sharp interfaces and excitable dynamics, addressing spectral bias and inefficient collocation point distribution in standard PINNs."
    },
    {
        "question": "What is the relative L2 error of MAPINN on the FitzHugh-Nagumo system?",
        "ground_truth": "MAPINN achieves a relative L2 error of 0.78% on the FitzHugh-Nagumo system, compared to 92.13% for baseline PINN and 90.03% for Fourier PINN."
    },
    {
        "question": "What architecture does the MM-CMDS system use for counterfeit medicine detection?",
        "ground_truth": "MM-CMDS uses MobileNetV2 for visual feature extraction from images and a GRU-based encoder to process OCR text, fusing both streams through a softmax classifier."
    },
    {
        "question": "What accuracy did the counterfeit medicine detection system achieve?",
        "ground_truth": "The MM-CMDS system achieved a test accuracy of 87.50%, with precision of 0.3333 and recall of 0.6000 for the counterfeit class."
    },
    {
        "question": "What are the main limitations mentioned in the MAPINN paper?",
        "ground_truth": "Limitations include increased computational overhead from the multi-branch architecture, empirical/problem-dependent frequency scale selection, untested scalability to higher-dimensional PDEs, and lack of evaluation on inverse problems or noisy data."
    }
]


# ─── Judge Prompts ──────────────────────────────────────────

def faithfulness_prompt(answer, contexts):
    context_text = "\n---\n".join(contexts)
    return f"""You are a strict evaluator checking if an AI answer is fully supported by the given source context.

SOURCE CONTEXT:
{context_text}

AI ANSWER:
{answer}

Score the answer's faithfulness to the source context from 0.0 to 1.0:
- 1.0 = every claim in the answer is directly supported by the context
- 0.5 = some claims supported, some not verifiable from context
- 0.0 = answer contradicts or is unsupported by the context

Respond with ONLY a number between 0.0 and 1.0, nothing else."""


def relevancy_prompt(question, answer):
    return f"""You are evaluating if an answer actually addresses the question asked.

QUESTION:
{question}

ANSWER:
{answer}

Score relevancy from 0.0 to 1.0:
- 1.0 = directly and completely answers the question
- 0.5 = partially answers or is somewhat off-topic
- 0.0 = does not address the question at all

Respond with ONLY a number between 0.0 and 1.0, nothing else."""


def correctness_prompt(answer, ground_truth):
    return f"""Compare an AI-generated answer against a known correct reference answer.

REFERENCE ANSWER:
{ground_truth}

AI ANSWER:
{answer}

Score factual correctness from 0.0 to 1.0 based on whether the AI answer's key facts match the reference:
Respond with ONLY a number between 0.0 and 1.0, nothing else."""


def parse_score(response: str) -> float:
    """Extract a float score from the judge's response, defaulting to 0.0 on failure."""
    try:
        cleaned = response.strip().split()[0]
        score = float(cleaned)
        return max(0.0, min(1.0, score))
    except (ValueError, IndexError):
        logger.warning(f"Could not parse score from: '{response}' — defaulting to 0.0")
        return 0.0


# ─── Evaluation Runner ──────────────────────────────────────

def run_evaluation():
    logger.info("Loading vector store and BM25 index...")

    vector_store = FAISSVectorStore(index_path="./data/faiss_index")
    vector_store.load()

    bm25_retriever = BM25Retriever()
    all_chunks = vector_store.get_all_chunks()
    bm25_retriever.index(all_chunks)

    if not all_chunks:
        raise ValueError("No papers found in the vector store. Upload papers first.")

    results = []

    for i, item in enumerate(TEST_SET, 1):
        question = item["question"]
        ground_truth = item["ground_truth"]

        logger.info(f"[{i}/{len(TEST_SET)}] {question}")

        # Run the actual RAG pipeline
        rag_result = answer_question(
            query=question,
            vector_store=vector_store,
            bm25_retriever=bm25_retriever,
            top_k=5
        )

        answer = rag_result["answer"]
        contexts = [s["snippet"] for s in rag_result["sources"]] or ["No context retrieved"]

        # Judge with Gemini
        faithfulness = parse_score(
            generate_response(faithfulness_prompt(answer, contexts), temperature=0)
        )
        relevancy = parse_score(
            generate_response(relevancy_prompt(question, answer), temperature=0)
        )
        correctness = parse_score(
            generate_response(correctness_prompt(answer, ground_truth), temperature=0)
        )

        results.append({
            "question": question,
            "answer": answer,
            "num_sources": len(rag_result["sources"]),
            "faithfulness": faithfulness,
            "relevancy": relevancy,
            "correctness": correctness
        })

        logger.info(
            f"  Faithfulness: {faithfulness:.2f} | "
            f"Relevancy: {relevancy:.2f} | "
            f"Correctness: {correctness:.2f}"
        )

        time.sleep(15)  # stay under Gemini's 15 RPM free-tier limit

    # ─── Summary ────────────────────────────────────────────

    avg_faithfulness = sum(r["faithfulness"] for r in results) / len(results)
    avg_relevancy = sum(r["relevancy"] for r in results) / len(results)
    avg_correctness = sum(r["correctness"] for r in results) / len(results)
    avg_sources = sum(r["num_sources"] for r in results) / len(results)

    print("\n" + "=" * 70)
    print("RESEARCHMIND AI — RETRIEVAL & ANSWER QUALITY EVALUATION")
    print("=" * 70)
    print(f"Questions evaluated:        {len(results)}")
    print(f"Avg. Faithfulness:          {avg_faithfulness:.3f}")
    print(f"Avg. Answer Relevancy:      {avg_relevancy:.3f}")
    print(f"Avg. Factual Correctness:   {avg_correctness:.3f}")
    print(f"Avg. Citations per answer:  {avg_sources:.1f}")
    print("=" * 70)

    # Save detailed results
    output_path = Path(__file__).parent / "eval_results.json"
    with open(output_path, "w") as f:
        json.dump({
            "summary": {
                "avg_faithfulness": avg_faithfulness,
                "avg_relevancy": avg_relevancy,
                "avg_correctness": avg_correctness,
                "avg_sources": avg_sources
            },
            "details": results
        }, f, indent=2)

    print(f"\nDetailed results saved to: {output_path}\n")

    return results


if __name__ == "__main__":
    run_evaluation()