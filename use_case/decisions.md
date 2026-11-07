# Decision log

One row per architectural decision, with the option you rejected and why.

> **Week 5 asks you to defend your agent architecture against the alternatives.**
> **Week 10's handoff doc is largely this file.** Both are much easier if you
> wrote the reasoning down while you still remembered it.

A decision without a rejected alternative is not a decision, it is a default.
If you cannot name what you did not do, you did not choose.

| Week | Decision | What you rejected | Why | What would change your mind |
| --- | --- | --- | --- | --- |
| TC1 | **Fixed retrieval pipeline with one bounded retry.** MARA will follow a predefined workflow: receive batch job failure details, retrieve evidence from synthetic knowledge sources, analyze the findings, and generate an investigation report. If the first search produces insufficient evidence, MARA will perform one alternative search before recommending SME escalation. | **Fully agentic or multi-agent architecture.** I considered a Supervisor Agent coordinating specialized Engineer Agents that could identify affected applications, dynamically select investigation tools, retrieve relevant evidence, and adjust their investigation based on intermediate findings. | MARA's initial scope is limited to known mainframe batch job abends. The job name, failure date, and abend code provide a clear starting point for a predictable investigation workflow. A fixed pipeline is simpler to develop, test, debug, and maintain, with more predictable latency and cost. An agentic workflow could add latency to time-sensitive investigations, especially critical-path jobs with a 5–10-minute escalation window. A multi-agent architecture would introduce unnecessary complexity at this stage. | I would reconsider an agentic architecture if MARA expands into incidents where the affected application or technical component is unknown, such as rising MQ queue depth or increased Failed Customer Interactions (FCI). These situations may require dynamically selecting tools, knowledge sources, and investigation steps. I would compare accuracy, evidence quality, latency, and cost before changing the architecture. |
| TC2 — S3 | **Use the hosted model as MARA's current prototype baseline while evaluating local open-weight models for future deployment.** Measured local inference: LiquidAI/LFM2.5-350M, 42.61 seconds for 80 generated tokens on MacBook Pro M1 Pro CPU (16 GB unified memory). Measured hosted inference: Anthropic Claude Sonnet 5, 3.17 seconds, 73 input and 80 output tokens, using provider-managed infrastructure. | **Immediately replacing the hosted model with the 350M local model.** | The hosted model was faster in this experiment and produced more coherent text, but this was not a like-for-like comparison. The hosted provider rejected temperature 0.7, limiting sampling control. Local inference provides direct access to weights and logits and keeps inference on-device. These are measured prototype observations, not production performance claims. API pricing was not measured and must be obtained from current provider pricing. | Reconsider the model architecture after evaluating an instruction-tuned 4B-class local model for MARA using evidence-grounding accuracy, schema compliance, latency, memory consumption, data-security constraints, and operating cost. |

| TC3 — Step 2 | **Kept the Request and Response models from TC1 and added a required `sources` field.** I also kept the existing `solve()` function signature. Since MARA is not retrieving historical incidents yet, I set `sources` to an empty list. I added validation for job name, failure date, and abend code, along with error messages in the UI. | **Changing the original schema completely or allowing the LLM to return source IDs without checking them.** I also decided not to depend only on UI validation. | I wanted to reuse what I built in TC1 instead of starting over. The `sources` field will help us identify which historical records support MARA's findings. Since retrieval is not implemented yet, returning an empty list is safer than showing incorrect sources. I added input validation to reduce mistakes before MARA starts its investigation. The five-year date limit is a starting value that we can change later. | Once retrieval is implemented, I will update MARA to return the actual record IDs used in the investigation. I may also change the validation rules based on feedback from production support engineers and our organization's requirements. |

| 3 | **Hybrid Retrieval (BM25 + Dense + RRF).** I selected this approach for MARA because it can find incidents using both exact job names and natural-language questions. | **Agentic RAG and Dynamic Context Injection (DCI).** I tested both approaches in Step 3. | MARA needs to search for exact values like job names, abend codes, and error messages, but also handle questions about similar incidents. Our corpus has only 15 synthetic records, so DCI works well today, but Hybrid gives us a better starting point as the dataset grows. With top-5 retrieval, Hybrid found the expected records for all nine answerable test questions. | I would reconsider if a larger dataset shows that Agentic RAG or DCI gives better results at an acceptable cost and response time. If the corpus stays small, I would revisit DCI because it is simpler. |
| 5 | <!-- agent architecture --> | <!-- --> | <!-- --> | <!-- --> |
| 6 | <!-- guardrail level --> | <!-- --> | <!-- --> | <!-- --> |
| 7 | <!-- memory type --> | <!-- --> | <!-- --> | <!-- --> |
| 8 | <!-- model --> | <!-- --> | <!-- --> | <!-- --> |

### TC3 — Non-Text Content

1. **Visual or text in pixels?** MARA currently uses text-based JSONL records. If we add JES spool screenshots or scanned incident reports, most of that information would be text displayed as pixels.

2. **Numbers available only in pixels?** I would find the screenshot using its incident metadata, use OCR or a vision model to read the abend code or other values, and check the extracted information against the original image before using it.

3. **Descriptions or one-time parsing?** I would extract and save the text and metadata when an image is added to the corpus, rather than processing the same image every time someone asks a question.

4. **Is a transcript enough for audio or video?** MARA does not have audio or video records today. A transcript might be enough for spoken incident explanations, but I would keep the original recording if screen activity or visual details are needed.


### TC1 — Strongest Counterargument for an Agentic Architecture

An agentic architecture could be more effective when production incidents require investigation across multiple applications and technologies, especially when the underlying technical cause is initially unknown. A Supervisor Agent could coordinate specialized Engineer Agents, allowing them to dynamically select relevant tools, retrieve evidence from different sources, and adjust their investigation based on intermediate findings.

However, MARA's initial batch-abend investigation scope does not currently justify the additional orchestration complexity and potential latency.

### TC1 — Agentic Assessment

| Question | Answer |
|---|---|
| Does the number of investigation steps depend on the input? | No |
| Must MARA retrieve information from external data sources? | Yes |
| Must MARA detect insufficient evidence and attempt another search? | Yes |
| Is the input too open-ended to enumerate possible cases? | No |

**Result:** 2 out of 4 — Borderline. Start simpler.

**Final Decision:** Fixed retrieval pipeline with one bounded retry. Reconsider an agentic architecture if future use cases require dynamic investigation and a fixed pipeline proves inadequate.

---

The last column is the one people skip and the one people ask about. "We chose
dense retrieval; we would switch to hybrid if exact-match queries went above ~20%
of traffic" is an engineering position. "We chose dense retrieval" is a
preference.

## TC1 Step 12 — User Feedback Decision

**Status:** Pending user feedback.

I have shared MARA's input screen and a synthetic investigation output with a mainframe Production Support colleague.

No application design changes have been made based on user feedback yet because I am awaiting the reviewer's response.

Once feedback is received, I will document:
- What the reviewer found useful or missing.
- Which of the five golden examples they would reject.
- What application changes were made, or why no change was needed.

I will not treat my own evaluation results as independent user feedback.

**Decision: Defer independent stakeholder validation**

I decided to defer TC3 Step 6 because I do not yet have approval to test MARA with colleagues in the enterprise environment.

No stakeholder-driven changes were made to the retrieval system because independent feedback has not been collected. I will revisit this step when an approved testing option becomes available.

### TC4-Step1: Evaluation Results, Human Scoring, and Citation Traceability Limitations

**Evaluation scope**

For TC4 Step 1, I reviewed 50 execution traces covering 25 evaluation questions across two retrieval approaches: Agentic RAG and DCI MARA.

- 20 existing execution traces from TC3 (10 questions × 2 approaches).
- 30 new execution traces from TC4 (15 questions × 2 approaches).

I used synthetic incident records and the saved execution traces to evaluate the factual correctness, completeness, and evidence-grounding of MARA's answers.

**Evaluation findings**

I identified four failed executions across the 50 traces, giving an observed failure rate of 8%.

- MARA-08 — Agentic RAG: Incomplete retrieval evidence caused MARA to miss a documented successful restart outcome.
- MARA-10 — DCI MARA: The answer contained an internal inconsistency when counting upstream-to-downstream failure relationships.
- TC4-03 — Agentic RAG: Repeated retrieval calls exhausted the agent's turn limit without producing an answer.
- TC4-04 — Agentic RAG: Truncated retrieval evidence caused MARA to incorrectly report a documented successful restart outcome as unknown.

Of the 30 new TC4 executions, 28 passed my review and 2 failed. I did not find additional substantive failures that justified a FAIL score.

The retrieval truncation issue appeared in multiple executions. Although these were separate failed executions, they shared a common underlying problem: Agentic RAG could find the correct incident but could not always retrieve the complete evidence needed to answer the question.

**Human-scoring decision**

The challenge requested 20 human-scored outputs, with at least one-third being failures (a minimum of 7 FAIL results).

My review identified only four supported failures across all 50 execution traces. I am closing this evaluation review with the actual findings rather than generating additional executions or reporting unsupported failures.

The required failure-stratified sample was therefore not achieved. The number of formally recorded human scores is tracked separately in `human_scores.jsonl`.

**Citation traceability limitation**

In TC3, I implemented source identifiers for retrieved chunks and pages. Agentic RAG returns chunk identifiers, and DCI reads incident pages by name.

My citation coverage check verifies whether MARA's answer mentions the expected incident record IDs. However, this does not prove that every factual claim is supported by the specific retrieved passage.

For TC4, I checked the reviewed answers against the synthetic reference records for factual correctness. I did not independently verify claim-by-claim citations against the exact retrieved text from every historical execution.

**Lessons learned**

I learned that:

- Finding the correct incident record does not guarantee that the agent has retrieved all the relevant evidence.
- Retrieval truncation can cause different failures, including an exhausted agent loop or an incomplete answer.
- Multiple failed executions can share the same underlying failure pattern.
- A correct decline due to missing evidence should be treated as a PASS, not a failure.
- Factual correctness and citation traceability are related but separate evaluation dimensions.

**Future improvement**

I would like to improve Agentic RAG so that it can retrieve a complete incident record when the initial chunk does not contain enough evidence. I also want to strengthen claim-level citation verification and add more challenging evaluation cases to better test the system's limitations.

### TC4 Step 6 — Evaluation Baseline Decision

| Field | Decision |
|---|---|
| **Decision** | I selected Completeness and Factual Consistency as the headline scorer for MARA's incident-history endpoint. The baseline passed 7/7 cases (100%), with a 95% bootstrap CI of [100%, 100%]. |
| **What I rejected** | I did not select Answer Relevancy as the headline because a relevant answer can still omit important findings or contradict the reference. My selected judge passed calibration. |
| **Why** | This scorer addresses the missing findings and factual inconsistencies documented in `failures.md`, including MARA-08 and MARA-10. It does not measure production accuracy, operational volume spikes, or performance on unseen incidents. |
| **What would change my mind** | I would reconsider the headline scorer if new held-out evaluations or human reviews show it misses important failures, or if another calibrated scorer provides better coverage of the documented failure cases. |