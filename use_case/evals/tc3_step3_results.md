# TC3 Step 3 — MARA Retrieval Evaluation

## 1. Results

Ten evaluation questions were used to compare three retrieval techniques against a corpus of 15 synthetic mainframe batch incidents.

| Metric | Agentic RAG | DCI MARA | Hybrid BM25 + Dense + RRF |
|---|---|---|---|
| Questions evaluated | 10 | 10 | 10 |
| Evaluation pass rate | 10/10 | 10/10 | 9/9 answerable; 1/1 decline manually reviewed |
| Citation coverage | 9/9 | 9/9 | Not formally scored |
| Average retrieval/tool calls | 2.5 | 2.1 | 1 hybrid retrieval operation per question |
| Average evidence read | 10,203.8 characters | 5,344.0 characters | Not measured |
| Average latency | 10.187 seconds | 10.088 seconds | Not measured |

**Measurement notes**

- The S5 results reflect recorded evaluations from the Agentic RAG and DCI MARA implementations.
- The Hybrid evaluation uses the final `k=5`, `max_tokens=1000` experiment.
- Hybrid retrieval found all required gold incident IDs for nine answerable questions, and all nine answers contained their expected terms.
- The unsupported PAYBATCH45 question was manually reviewed and declined appropriately.
- Keyword coverage does not establish complete factual correctness, and some answers appeared to end mid-sentence.
- Tool-call counts and evidence-read measurements are not directly equivalent across all three techniques.

## 2. Configuration and Reproducibility

| Setting | Agentic RAG | DCI MARA | Hybrid |
|---|---|---|---|
| Generation model | Claude Sonnet 5 | Claude Sonnet 5 | Claude Sonnet 5 |
| Corpus | 15 synthetic incidents | 15 synthetic incidents | 15 synthetic incidents |
| Chunking | One incident per chunk | One incident per document | One incident per chunk |
| Retrieval | BM25 agent-selected retrieval | Direct corpus inspection | BM25 + dense retrieval with RRF |
| Embedding model | N/A | N/A | BAAI/bge-small-en-v1.5 |
| Embedding dimensions | N/A | N/A | 384 |
| First-stage candidate count | N/A | N/A | 5 per retriever |
| Final retrieval count | Agent-selected | Agent-selected | 5 |
| RRF rank constant | N/A | N/A | 60 |
| Hybrid maximum output tokens | N/A | N/A | 1,000 |
| Agent turn budget | Verify from S5 notebook | Verify from S5 notebook | N/A — single answer-generation call |

The exact S5 model parameters and tool budgets should be verified against the saved notebook before final submission.

## 3. Embedding Token Count

**Measured embedding-token count: 7,680 tokens.**

This measurement was obtained using the local FastEmbed tokenizer for the 15 synthetic incident texts.

Embedding model: `BAAI/bge-small-en-v1.5`.

This is a measurement of document-token inputs, excluding subsequent query tokens. It is not an API billing measurement.

Agentic RAG and DCI MARA did not use dense embeddings in their evaluated implementations; their embedding-token counts are marked N/A.

## 4. Hybrid Experiment Findings

| Metric | Initial Hybrid | Final Hybrid |
|---|---|---|
| Final retrieval count | 3 | 5 |
| Maximum output tokens | 400 | 1,000 |
| Gold-record retrieval completeness | 8/9 | 9/9 |
| Expected-term coverage | 6/9 | 9/9 |
| Unsupported-question decline | Appropriate | Appropriate |

The original experiment exhibited incomplete answers for MARA-04 and MARA-05, despite retrieving their required evidence. MARA-10 also missed one required incident.

The final configuration retrieved all required incidents and covered the expected technical terms for all nine answerable questions.

Both parameters changed simultaneously, so the experiment does not independently isolate the effect of retrieval depth from the effect of output-token budget.

**Experiment provenance limitation:** The original baseline JSON was overwritten during Marimo reactive execution. The initial measurements were preserved in terminal output and reviewed during the session, but the original per-answer JSON is no longer available. The final experiment is saved as `tc3_step3_hybrid_k5_tokens1000.json`.

## 5. Evidence Artifacts

- `use_case/evals/retrieval.jsonl` — evaluation questions and gold labels.
- `use_case/evals/tc3_step3_rag_dci_results.csv` — recorded S5 evaluation metrics.
- `use_case/evals/tc3_step3_rag_dci_traces.json` — recorded S5 investigation traces.
- `use_case/evals/tc3_step3_hybrid_k5_tokens1000.json` — final Hybrid experiment answers and retrieved IDs.

## 6. Conclusion

Agentic RAG and DCI MARA passed the evaluated questions with recorded citations, tool activity, evidence-read counts, and latency.

The Hybrid implementation demonstrated successful local dense retrieval combined with BM25 and Reciprocal Rank Fusion. Increasing the final retrieval count and output-token budget improved observed multi-hop coverage, but the experiment did not measure latency or evidence-read volume.

Future work should capture per-run configuration, token usage, finish reasons, latency, evidence volume, and immutable experiment results automatically.