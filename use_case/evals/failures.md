# TC4 Step 1 — Failure Analysis

I reviewed 50 execution traces (20 from TC3 and 30 from TC4) across Agentic RAG and DCI MARA. I identified four failed executions.

## Failures

| ID | Approach | Failure description |
|---|---|---|
| MARA-08 | Agentic RAG | Truncated retrieval evidence prevented MARA from confirming the documented successful restart of INVTUPDT12. |
| MARA-10 | DCI MARA | MARA initially counted two upstream-to-downstream failure relationships but later listed three, making its answer internally inconsistent. |
| TC4-03 | Agentic RAG | Repeated searches of truncated INVTUPDT12 evidence exhausted the agent's turn limit without producing an answer. |
| TC4-04 | Agentic RAG | MARA incorrectly reported the successful restart of INVTUPDT12 as unknown because the retrieved evidence was truncated. |

## Failure Categories — Ranked by Frequency

| Rank | Category | Count |
|---|---|---:|
| 1 | Retrieval truncation / incomplete evidence | 3 |
| 2 | Answer inconsistency | 1 |
| | **Total** | **4** |

## Summary

Four of the 50 executions failed (8%). Retrieval truncation was the most frequent problem, appearing in three failed executions.

The remaining 46 executions passed the review. I did not classify correct evidence-based declines as failures.

The human-scoring sampling limitation is documented separately in `decisions.md`.