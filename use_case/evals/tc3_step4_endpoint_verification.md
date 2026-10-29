# TC3 Step 4 — MARA Endpoint Testing

## What I built

For Step 4, I added a new endpoint called `research_mainframe_incident_history` to the existing MARA application.

This endpoint takes a question about mainframe batch incidents, searches our 15 synthetic incident records, and sends the relevant information to Claude to prepare an investigation report.

For retrieval, I used the Hybrid approach from Step 3: BM25 + FastEmbed/Qdrant + RRF.

The response follows our existing Pydantic `Response` model and includes the source record IDs. The endpoint is only for research and does not perform production recovery actions.

## Testing results

I tested the endpoint using the same ten questions from Step 3.

| Test | Result | Sources |
|---|---|---|
| MARA-01 | COMPLETED_RESEARCH | INVUPD77 |
| MARA-02 | COMPLETED_RESEARCH | CLAIMSX12 |
| MARA-03 | COMPLETED_RESEARCH | ORDVAL88 |
| MARA-04 | COMPLETED_RESEARCH | CLMEXTR07, INVRECON14 |
| MARA-05 | COMPLETED_RESEARCH | CLAIMPROC07, INVUPDT22 |
| MARA-06 | COMPLETED_RESEARCH | INVCTL19 |
| MARA-07 | INSUFFICIENT_EVIDENCE | None |
| MARA-08 | COMPLETED_RESEARCH | INVTUPDT12 |
| MARA-09 | COMPLETED_RESEARCH | PAYDEDN27 |
| MARA-10 | COMPLETED_RESEARCH | CLMEXTR07, HRCOMP22, INVRECON14, INVCPROC08, INVUPDT22 |

All ten questions completed successfully after fixing the issues found during testing. The answers included the expected record IDs for the nine questions with supporting evidence.

For MARA-07 (PAYBATCH45), no matching incident was available. MARA returned `INSUFFICIENT_EVIDENCE`, left the root cause as null, set confidence to `NOT_ASSESSED`, and returned an empty sources list.

## Issues I encountered

I ran into a few issues while connecting the retrieval code to the API.

First, the existing application environment did not have FastEmbed, Qdrant Client, and BM25 installed. I added those dependencies using `uv`.

Next, Claude returned JSON inside Markdown code fences, which caused a parsing error. I reused the JSON cleanup approach from TC1 to fix it.

During MARA-04 testing, Claude's response was getting cut off because the output-token limit was too low. I checked the model's finish reason, confirmed it was stopping due to the length limit, and increased `max_tokens` from 1000 to 2500. The question then completed successfully.

## Where I saved the results

The full responses for MARA-05 through MARA-10 are saved in:

`use_case/evals/tc3_step4_endpoint_results.json`

MARA-01 through MARA-04 were verified through terminal output, but I did not save their full responses into the JSON file.

## What I learned

This step helped me understand how the retrieval functions from our S6 notebook connect to an actual API endpoint.

I also learned that getting a good response from Claude is not enough. The API needs to handle the response format, validate the output, and make sure the source IDs come from retrieved records.

The endpoint is now working for all ten test questions. I still need to improve how I save test results so that all responses are captured automatically, even if a test fails in the middle.