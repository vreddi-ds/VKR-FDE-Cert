# Your use case

**This directory is yours.** Everything else in this repository is teaching
material we wrote. This is the one place you work, and every technical challenge
across all ten weeks reads from it or writes to it.

> **One use case, all ten weeks, no restarts.**

That rule is the whole design. The most common way this cohort goes wrong is a
student switching use cases in Week 5 because the first one got hard — and then
Week 8 has nothing to fine-tune against and Week 10 has nobody to report to.
Choose something you actually own, at work, that annoys you weekly.

---

## The files

| File | Created in | Grows in | Collected in |
| --- | --- | --- | --- |
| [`CHARTER.md`](./CHARTER.md) | TC1 | TC3, TC5, TC8 | every week's Session 2 opens by reading it |
| [`stakeholders.md`](./stakeholders.md) | TC1 Step 6 | **every week** | **TC10** — the final report goes to these people |
| [`ecosystem.md`](./ecosystem.md) | TC1 Step 6 | **TC9** extends this same file | TC9, TC10 |
| [`decisions.md`](./decisions.md) | TC3 | TC5–TC8 | TC5's critique, TC10's handoff doc |
| [`evals/golden.jsonl`](./evals/) | Week 1 S2 | TC2, TC4, TC6 | **TC8** — the bar a fine-tuned model must clear |
| [`data/DATASHEET.md`](./data/DATASHEET.md) | TC2 | TC3, TC8 | reviewers |
| `app/` | TC1 | TC3, TC5–TC8 | TC10 handoff |

Nothing here is busywork. Each file exists because something later is impossible
without it. `stakeholders.md` is the clearest case: TC10 asks you to send a
client report to everyone you worked with during the cohort. If you did not keep
the log, you cannot write the report.

---

## 🔒 Never commit real company data

`data/` is gitignored except its datasheet. That is deliberate and it is not
negotiable — you are pushing this to a public fork.

| Don't commit | Do commit |
| --- | --- |
| Real records, tickets, documents, customer names | Synthetic data you generated |
| Internal hostnames, IPs, architecture diagrams | The *shape* of the answer: "on-prem k8s, SAML, no egress" |
| Credentials, tokens, connection strings | `.env.example` with placeholders |
| Screenshots of internal tools | Screenshots of your own app |

When describing your firm's infrastructure, describe the pattern, not the
specifics. "Images go to an internal registry; Docker Hub is blocked" is useful
to everyone and identifies nobody.

If in doubt, leave it out.

---

## TC1 Step 8 — MARA API Design

### 1. What is one thing you do at work this could take over?

MARA helps automate the initial research when a mainframe batch job abends. Today, an Level1 Production Support Engineer manually reviews JES messages, identifies the abend code, and researches possible causes before deciding the next steps. MARA takes the job details and diagnostic messages, analyzes the failure, and provides a structured investigation report with findings and recommended actions. The engineer still reviews the report and makes the final decision. MARA does not restart or fix production jobs.

### 2. What exactly goes in — a string, a file, several fields?

MARA accepts several structured fields through its API:

- **job_name (required):** Name of the failed mainframe batch job, such as PAYBATCH45.
- **failure_date (required):** Date of the job failure in YYYY-MM-DD format.
- **abend_code (required):** Mainframe abend code, such as S0C7, S806, or S322.
- **jes_messages (optional):** A list of JES diagnostic messages related to the failure.

The Level1 engineer enters these details through the MARA web interface. The frontend converts the date from MM/DD/YYYY to YYYY-MM-DD and sends the request to the Gradio API.

For TC1, we use synthetic job information and diagnostic messages. MARA does not directly access production mainframe systems.

### 3. What comes back, and who reads it?

MARA returns a structured investigation report containing six fields:

- **failure_summary:** A short description of the batch job failure.
- **probable_root_cause:** The likely cause of the failure, or null if it cannot be determined.
- **evidence_and_historical_findings:** A list of findings based on the supplied information.
- **confidence_level:** Indicates how strongly the available evidence supports MARA's probable root-cause assessment. Values are HIGH, MEDIUM, LOW, or NOT_ASSESSED. It does not measure confidence in the recommended next steps.
- **recommended_next_steps:** A list of suggested investigation or recovery steps for human review.
- **investigation_status:** COMPLETED_RESEARCH or INSUFFICIENT_EVIDENCE.

The primary user is the Level1 Production Support Engineer. The engineer reviews the report to understand the failure, identify missing information, and decide whether to investigate further or escalate to an SME.

The response is structured as JSON, so other applications or AI agents could also consume it in the future.

MARA provides research assistance only. It does not execute recovery actions. Historical incident research is not yet integrated into this TC1 prototype.

### 4. What is the API endpoint called, and why would an agent choose it?

The API endpoint is named `research_mainframe_batch_abend`.

I chose this name because it clearly describes what MARA does: research mainframe batch job abends. It also makes it clear that the endpoint is for batch processing, not CICS transactions.

An AI agent could choose this endpoint when a Level 1 Production Support Engineer needs help investigating a failed mainframe batch job.

The endpoint accepts job details and JES messages and returns a structured investigation report with a probable root cause, supporting findings, confidence level, recommended next steps, and investigation status.

MARA only provides research and recommendations. It does not restart jobs, modify production systems, or execute recovery actions.