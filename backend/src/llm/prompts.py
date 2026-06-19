# src/llm/prompts.py
# All prompt templates for different features

from typing import List, Dict, Any


def format_context(chunks: List[Dict[str, Any]]) -> str:
    """Format retrieved chunks into context string."""
    context_parts = []
    for i, chunk in enumerate(chunks, 1):
        context_parts.append(
            f"[Source {i}: {chunk['source']}, Page {chunk['page_number']}]\n"
            f"{chunk['text']}\n"
        )
    return "\n---\n".join(context_parts)


def qa_prompt(query: str, chunks: List[Dict[str, Any]]) -> str:
    context = format_context(chunks)
    return f"""You are an expert research paper analyst.
Answer the question using ONLY the provided context.
Always cite the source document and page number.
If the answer is not in the context, say "I cannot find this in the provided papers."

CONTEXT:
{context}

QUESTION: {query}

ANSWER (with citations):"""


def summarize_prompt(chunks: List[Dict[str, Any]], paper_name: str) -> str:
    context = format_context(chunks)
    return f"""You are an expert research paper summarizer.
Provide a comprehensive summary of the research paper: {paper_name}

Structure your summary as:
1. **Research Objective** - What problem does this paper solve?
2. **Methodology** - What approach/methods were used?
3. **Key Findings** - What are the main results?
4. **Contributions** - What does this paper contribute to the field?
5. **Limitations** - What are the limitations mentioned?

PAPER CONTENT:
{context}

SUMMARY:"""


def extract_methodology_prompt(chunks: List[Dict[str, Any]]) -> str:
    context = format_context(chunks)
    return f"""You are a research methodology expert.
Extract and explain the methodology from the research paper.

Include:
- Research design and approach
- Datasets used
- Models/algorithms used
- Evaluation metrics
- Experimental setup

PAPER CONTENT:
{context}

METHODOLOGY:"""


def extract_findings_prompt(chunks: List[Dict[str, Any]]) -> str:
    context = format_context(chunks)
    return f"""Extract the key findings and results from this research paper.

Present findings as:
- Main results with specific numbers/metrics
- Comparisons with baselines
- Statistical significance if mentioned
- Key conclusions drawn

PAPER CONTENT:
{context}

KEY FINDINGS:"""


def extract_future_work_prompt(chunks: List[Dict[str, Any]]) -> str:
    context = format_context(chunks)
    return f"""Extract future work directions mentioned in this research paper.

Include:
- Explicit future work statements
- Limitations that suggest future directions
- Open questions identified by authors
- Potential extensions of this work

PAPER CONTENT:
{context}

FUTURE WORK:"""


def gap_analysis_prompt(chunks: List[Dict[str, Any]], paper_names: List[str]) -> str:
    context = format_context(chunks)
    papers = ", ".join(paper_names)
    return f"""You are a research gap analyst reviewing: {papers}

Identify research gaps and opportunities:
1. **Identified Gaps** - What problems remain unsolved?
2. **Methodological Gaps** - What approaches haven't been tried?
3. **Dataset Gaps** - What data is missing or underrepresented?
4. **Future Opportunities** - What research directions are most promising?

PAPERS CONTENT:
{context}

RESEARCH GAP ANALYSIS:"""


def compare_papers_prompt(
    chunks: List[Dict[str, Any]],
    paper_names: List[str]
) -> str:
    context = format_context(chunks)
    papers = ", ".join(paper_names)
    return f"""Compare the following research papers: {papers}

Provide a structured comparison:
1. **Research Objectives** - What each paper aims to solve
2. **Methodologies** - How each paper approaches the problem
3. **Datasets** - What data each paper uses
4. **Results** - Performance metrics and outcomes
5. **Strengths & Weaknesses** - Pros and cons of each approach
6. **Overall Verdict** - Which approach is most effective and why

PAPERS CONTENT:
{context}

COMPARISON:"""