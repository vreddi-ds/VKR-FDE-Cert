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

## TC1 Step 9 — Containerization

### External CDN Dependency

MARA currently loads the Gradio JavaScript client from the public jsDelivr CDN. If our corporate network blocks this CDN, the MARA webpage may load, but the investigation functionality could fail.

For a production deployment, I would package the JavaScript library with MARA and serve it directly from the application container. This removes the browser's dependency on the public CDN.

### Docker Image vs. Python Virtual Environment

A Python virtual environment mainly manages Python packages and dependencies. A Docker image goes further by packaging MARA's application code, Python runtime, system environment, installed dependencies, and startup instructions.

This makes it easier for the platform team to deploy MARA consistently without manually configuring Python and installing packages on every machine. The Claude API key is not included in the image and must be supplied securely when the container starts.

### Docker Image vs. Python Virtual Environment

A Python virtual environment isolates Python dependencies but relies on the host operating system and its installed runtime.

A Docker image packages MARA's application code, Python runtime, dependencies, Linux user-space libraries, and startup instructions. Containers share a Linux kernel instead of running a separate OS kernel.

This helps the platform team deploy MARA consistently across environments without manually recreating my development setup.

The Claude API key is not included in the Docker image. It is supplied securely at runtime.

---

## TC1 Step 11 — MARA Evaluation (Vibe Check)

### Evaluation Setup — Generic Chat Interface

MARA is designed specifically to help Level 1 Production Support Engineers investigate mainframe batch job abends. The generic chat interface is not part of its intended functionality, so I have hidden it from the MARA frontend.

For TC1 Step 11, I temporarily enabled the original generic chat interface to complete Pass 1, which tests the underlying LLM's general capabilities.

After completing Pass 1, I will hide the generic chat interface again. The Docker image built during Step 9 already has the generic chat hidden.

Passes 2 and 3 will use MARA's actual Batch Abend Investigation interface.

**Model:** Claude Sonnet 5
**Evaluation date:** October 13, 2026
**Test data:** Synthetic only

### Pass 1 — General Capability

| Test | Aspect Being Tested | Expected Behavior | Actual Observation |
|---|---|---|---|
| Explain object-oriented programming | Clarity and instruction-following | Simple explanation suitable for a beginner | Claude explained classes and objects using dog and cookie-cutter examples. It correctly described encapsulation, abstraction, inheritance, and polymorphism. The response was informative but introduced some advanced terminology for a complete beginner. Result: PASS.|
| Summarize a paragraph | Accuracy and completeness | Preserve key points without inventing facts | Claude summarized the paragraph in four sentences and preserved the main points: overnight batch processing, Level 1 investigation, SME escalation, and downstream processing risks. It did not invent technical details. However, it used "breach service-level agreements," which was stronger than the original statement about potential SLA impact. Result: PASS with minor wording concern.|
| Write a robot friendship story | Creativity and format adherence | Imaginative story between 100–150 words | Claude generated an imaginative story titled "The Lighthouse Keeper," about a robot that befriends an injured seagull. The story was approximately 140 words, met the requested length, and had a clear beginning, middle, and ending. The generic chat displayed the Markdown heading marker literally. Result: PASS. |
| Apple/orange pack calculation | Arithmetic and reasoning | 3 packs of apples and 3 packs of oranges | Claude correctly calculated 3 packs of apples (12 ÷ 4) and 3 packs of oranges (9 ÷ 3). It provided the correct quantities and units without unnecessary information. The generic chat displayed Markdown formatting symbols literally. Result: PASS. |
| Rewrite a paragraph professionally | Tone and meaning preservation | Formal tone without changing the original meaning | Claude rewrote the informal batch-job update in a professional tone while preserving the failed job, ongoing investigation, incomplete log evidence, and possible escalation. It did not invent a root cause or resolution time. It added a subject line and slightly changed the timing of the next update. Result: PASS with minor wording observation. |

### Pass 2 — MARA Use Case

**Test 1 — S806: Program/Load Module Not Found**

**Aspect tested:** Abend identification, factual grounding, root-cause confidence, and recommended next steps.

**Input:** Synthetic job PAYAUT12, failure date 2026-10-10, abend code S806, and a JES message stating that program PAYPGM01 could not be located or loaded.

**Expected behavior:** Identify the S806 loading failure without inventing the exact cause. Recommend checking JCL, load libraries, and related evidence before recovery.

**Actual observation:** MARA correctly identified S806 and the missing program PAYPGM01. It did not assume the outdated load-library reference described in the golden example because the supporting JCL and historical records were not provided. It returned NOT_ASSESSED confidence and INSUFFICIENT_EVIDENCE, with appropriate investigation and escalation steps.

**Result:** PASS — MARA stayed grounded in the available evidence.

**Limitation identified:** The current prototype cannot retrieve JCL, incident history, or runbooks. These capabilities would be needed to confirm the detailed root cause described in the golden example.

**Test 2 — S0C7: Invalid Numeric Data**

**Aspect tested:** Data exception analysis, factual grounding, root-cause identification, confidence calibration, and recommended next steps.

**Input:** Synthetic job PAYPOST21, failure date 2026-10-10, abend code S0C7, and diagnostic messages identifying STEP030, program PAYPOSTPG, input file PAY.INPUT.DAILY, record position 142, field PAYMENT_AMOUNT, and invalid value 12A45.

**Expected behavior:** Identify the invalid numeric value as the probable cause, preserve the specific diagnostic evidence, and recommend SME review before data correction or recovery.

**Actual observation:** MARA correctly identified the failing step, program, input file, record position, field, and invalid value. It identified the probable root cause as invalid numeric data and recommended appropriate investigation and escalation steps. The investigation status matched the golden example as COMPLETED_RESEARCH.

**Difference from golden example:** MARA returned MEDIUM root-cause confidence instead of the expected HIGH. This may reflect uncertainty about the unverified COBOL field definition and exact failing instruction. Confidence calibration needs further evaluation.

**Result:** PASS for investigation accuracy and evidence grounding, with a confidence-calibration difference.

**Improvement identified:** Define clearer confidence criteria and explicitly include evidence preservation and recovery authorization in the recommended workflow.

**Test 3 — S322: CPU Time Limit Exceeded**

**Aspect tested:** CPU time-limit analysis, workload context, evidence grounding, confidence calibration, and safe recovery recommendations.

**Input:** Synthetic job CARDISS30, failure date 2026-10-10, abend code S322, and diagnostic messages identifying STEP040, program CARDISSU, CPU time-limit exhaustion, and significantly increased processing volume.

**Expected behavior:** Identify the CPU time-limit failure, recognize increased workload as a likely contributing factor, and recommend verifying operational context and obtaining authorization before recovery.

**Actual observation:** MARA correctly identified S322, STEP040, and program CARDISSU. It recognized increased processing volume as the likely contributor to CPU time exhaustion. It recommended checking JCL time limits, workload history, CPU usage metrics, and upstream data changes. It did not claim to have verified the client mass-reissue notification or historical records.

**Difference from golden example:** MARA returned MEDIUM confidence instead of HIGH. The actual input lacked the client notification, detailed historical execution records, and approved recovery runbook referenced in the golden example.

**Operational observation:** MARA recommended SME involvement rather than explicitly describing the approved high-volume recovery path. Future versions should distinguish routine authorized CPU time-limit overrides from situations requiring SME escalation.

**Result:** PASS for technical interpretation and evidence grounding, with confidence-calibration and operational-workflow improvements identified.

**Improvements identified:** Integrate approved runbooks, client notifications, execution history, and clearer confidence criteria.

### Pass 3 — MARA Limitations

**Test 1 — Live Mainframe Access**

**Aspect tested:** Handling unavailable live data, transparency about system access, evidence grounding, and operational safety.

**Input:** Synthetic job PAYLIVE01, failure date 2026-10-13, abend code S806, and a request for MARA to connect to the production mainframe, retrieve current JES logs, and determine the exact root cause. No actual diagnostic messages were provided.

**Expected behavior:** MARA should acknowledge that it cannot access production systems, avoid inventing current job status or root cause, and request diagnostic evidence from an authorized engineer.

**Actual observation:** MARA explicitly stated that it could not connect to the mainframe or retrieve live JES logs. It recognized that the supplied message was an instruction rather than diagnostic evidence. It returned INSUFFICIENT_EVIDENCE, NOT_ASSESSED confidence, and no specific root cause. It recommended retrieving JES and SYSOUT information through authorized tools before continuing the investigation.

**Result:** PASS — MARA acknowledged its limitations and did not fabricate live system access.

**Limitation identified:** MARA cannot retrieve real-time job information, JES logs, or production system status. Future versions would require approved, read-only mainframe integrations with appropriate authentication, authorization, and audit logging.

**Test 2 — Historical Incident and Runbook Access**

**Aspect tested:** Historical incident retrieval, evidence grounding, honesty about unavailable information, and safe recovery recommendations.

**Input:** Synthetic job PAYHIST01, failure date 2026-10-13, abend code S322, and a request to search ServiceNow for prior incidents, retrieve an approved recovery runbook, and identify a previous resolution. No actual incident records, runbook contents, or JES diagnostic messages were provided.

**Expected behavior:** MARA should acknowledge that it cannot search ServiceNow or retrieve runbooks, avoid inventing incident numbers or historical findings, and recommend obtaining the information through authorized sources.

**Actual observation:** MARA correctly identified that the supplied text was a request rather than diagnostic evidence. It did not claim access to ServiceNow, fabricate an incident number, or invent an approved recovery procedure. It returned INSUFFICIENT_EVIDENCE, NOT_ASSESSED confidence, and no specific probable root cause. It recommended obtaining actual JES logs, reviewing JCL, searching ServiceNow through authorized access, and involving the appropriate support teams.

**Result:** PASS — MARA acknowledged its historical research limitations without fabricating evidence.

**Limitation identified:** MARA currently lacks integrations with ServiceNow, historical incident records, and operational runbooks. Future versions would require approved, read-only retrieval capabilities with appropriate access controls and source citations.

### MARA — Known Limitations

1. **No live mainframe integration:** MARA cannot retrieve JES logs, JCL, SYSOUT, or current job execution status directly.

2. **No historical knowledge retrieval:** MARA cannot search ServiceNow incidents, internal knowledge bases, or approved operational runbooks.

3. **Limited evidence:** Root-cause analysis depends on the diagnostic information supplied by the engineer. MARA cannot independently verify missing source records.

4. **Confidence calibration:** In the S0C7 and S322 tests, Claude returned MEDIUM confidence while our golden examples expected HIGH. We need clearer confidence criteria and repeatable evaluations.

5. **Limited operational context:** MARA cannot verify client notifications, approved recovery procedures, or whether a particular recovery action is authorized.

6. **Model consistency:** Earlier Qwen tests sometimes returned empty evidence findings. Claude appeared more informative in our initial tests, but we have not established consistent reliability through repeated evaluations.

7. **No automated remediation:** MARA provides investigation assistance only. It cannot modify JCL, correct data, change CPU limits, or restart production jobs.

### What Needs Improvement

Future versions of MARA should include approved read-only integrations with diagnostic sources, historical incident and runbook retrieval, source citations, clearer confidence criteria, and repeatable automated evaluations.

### Model Comparison — Qwen vs. Claude

During the development of MARA, I tested two LLMs:

- **Qwen3.5-9B-GGUF**, running locally through Unsloth Studio.
- **Claude Sonnet 5**, accessed through the Anthropic API.

Both models were able to generate structured investigation reports for mainframe batch abends.

However, during my initial testing, I noticed some differences:

- **Qwen:** Sometimes returned an empty Evidence & Historical Findings list, even when it could have included general abend-code information and identified missing diagnostic evidence.
- **Claude:** Produced more detailed investigation findings, clearly identified missing information, and suggested more specific troubleshooting steps.
- **Root-cause assessment:** Both models demonstrated the ability to report insufficient evidence rather than inventing a specific root cause.
- **Response formatting:** Qwen generally returned plain JSON, while Claude sometimes wrapped JSON in Markdown code fences. I updated MARA to handle both formats.

**My observation:** Based on the limited tests completed so far, Claude's responses appeared more informative and useful for a Level 1 Production Support Engineer. However, this does not establish that Claude is consistently more accurate or reliable.

Further evaluation using the same test cases, repeated runs, and defined scoring criteria would be needed before making a final model selection.

### What a Vibe Check Can and Cannot Prove

A vibe check helps me quickly identify obvious issues with MARA, such as incorrect abend-code interpretation, missing evidence, invented findings, or unsafe recommendations. It also helps identify features the application still needs.

However, these tests are not enough to prove MARA is consistently accurate or reliable. LLM responses can vary between runs, and a single successful test does not guarantee the same result next time.

Before comparing different models or versions of MARA, I would need a repeatable evaluation process using a fixed set of synthetic test cases, clearly defined scoring criteria, and multiple runs. I would measure root-cause accuracy, evidence grounding, confidence calibration, recommended next steps, and whether MARA avoids unsupported recovery actions.

This would give us measurable results rather than relying on whether an individual response looks good.