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
| 5 | **Direct Tool Calling (Implementation B)**. I selected direct Python tool calling for MARA's current architecture. It connects the outer agent to MARA's existing research API without requiring an additional FastMCP/OpenAPI adapter. | **UTCP/FastMCP (Implementation A)** was my closest alternative, and I built and tested it. I also considered the other architecture approaches from S10: MCP, skills, Code Mode, and keeping the existing fixed workflow without an outer tool-calling agent. I did not select these because MARA currently has one known caller, one research capability, and no confirmed need for additional tool discovery or sandbox execution. | **MARA** already has an HTTP research API, and its investigation knowledge remains in the application and retrieval corpus. Both A and B made one capability call. In my measured source-trace tests, A used 9,242 combined tokens, took 14.10 seconds, and returned 1,879 bytes; B used 9,257 tokens, took 15.45 seconds, and returned 1,662 bytes. These single-run differences do not establish a meaningful performance advantage for either architecture. Both also passed the final deterministic-rendering verification. I chose B because it has fewer integration components for MARA's current single-caller use case. Credentials and authorization would still need an approved enterprise design before deployment. | **I would reconsider UTCP/FastMCP or MCP** if a second independent application needs MARA's research capability and a shared tool interface provides a clear benefit. I would reconsider Code Mode if larger response payloads or repeated capability calls significantly increase context and token costs. Any switch would require evidence from comparable tests and an approved security design. |
| 6 | <!-- guardrail level --> | <!-- --> | <!-- --> | <!-- --> |
| 7 | <!-- memory type --> | <!-- --> | <!-- --> | <!-- --> |
| 8 | <!-- model --> | <!-- --> | <!-- --> | <!-- --> |

### TC5 Step 6 — Open Question from Step 1

**Status: OPEN — Not yet measured.**

**Question:** How much investigation time can MARA actually save compared with the current manual workflow?

I have not measured how much investigation time MARA saves compared with the manual workflow. To answer this, I need an approved evaluation using representative incidents, the same investigation tasks, and consistent timing measurements for manual and MARA-assisted investigations. Until then, I will not claim measured business time savings.

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

---

## TC5 Step 1 — S9 Demo Feedback and Unanswered Questions

### 1. Feedback Sources

I presented MARA during the S9 demo and received feedback from three members of the instructor team.

I also reviewed the S9 Demo Critique Rubric to identify additional questions I should be prepared to answer about MARA's business value, evaluation results, architecture, failures, and deployment readiness.

On November 6, 2026, I received additional operational information from a Senior Director of Production Support. This feedback included actual mainframe abend recovery examples and estimated recovery durations.

I documented the detailed stakeholder engagement separately in `use_case/stakeholders.md`.

The instructor feedback, S9 rubric questions, and operational stakeholder input are separate sources. I have not treated any of them as proof that MARA is ready for production.

### 2. Instructors' Feedback Turned into Questions

I converted the three instructors' comments into questions so I can address them systematically and improve future demonstrations.

These are questions I derived from the instructors' feedback, not necessarily their exact words.

#### Instructor 1 — Product, Evaluation, and Presentation

1. How can I measure whether MARA's JSON response is complete, with all required fields populated and evidence supported by source citations?
2. Why did I use a 30–35-minute investigation baseline when my charter states 15–20 minutes? Where did the higher estimate come from?
3. Have I collected questions from a real operational stakeholder and documented them in `stakeholders.md`?
4. What single endpoint metric should I lead with, and what is its measurement interval or confidence interval?
5. Can I demonstrate the inconsistent-job-name failure and explain why it matters?
6. How can I present the estimated business impact using my charter's assumptions: approximately 83–167 hours saved per 1,000 incidents, or 250 hours if the 30-minute assumption is validated, at an estimated labor rate of $75 per hour?

The business impact figures in Question 6 are not measured MARA savings. I still need to verify the per-incident savings assumptions behind these estimates.

#### Instructor 2 — Business Value and Historical Incidents

1. Can I explain MARA's purpose and value in simple, non-technical language?
2. How can I measure business impact beyond engineer time savings, including downtime, missed batch deadlines, and escalations to senior support engineers?
3. Could reducing a major overnight outage provide greater business value than routine investigation-time savings, and how would I measure that?
4. Why did MARA fail to find a matching historical incident during the demo?
5. How can I improve historical incident coverage so MARA can compare current failures with documented past incidents and resolutions?

#### Instructor 3 — Business Alignment and Architecture

1. What is the biggest business outcome MARA should achieve, and how can I confirm that priority with management?
2. If cost efficiency is the main objective, how can I optimize capability calls using the approaches covered in Session 10?
3. If faster incident resolution is the main objective, how can MARA identify outage causes more efficiently?
4. Would caching the last known working mainframe state be useful, feasible, and safe for this use case?
5. How would adding more historical incident examples improve MARA's investigation and retrieval quality?

The caching suggestion is an idea to evaluate, not an approved design change. MARA currently supports investigation and recommendations. It does not automatically change production systems or execute recovery actions.

### 3. Additional Operational Stakeholder Input — November 6, 2026

During TC1, I explained MARA to a Senior Director of Production Support and shared screenshots of the prototype.

On November 6, 2026, at 11:58 AM, I received an email from the Senior Director with mainframe batch abend recovery examples and estimates.

I replaced the actual job names with anonymized names before documenting the examples.

#### Recovery-Time Examples

| Scenario | Recovery duration | Details |
|---|---|---|
| XYZABC11 — September 17, 2026 | 78 minutes | First occurrence. The job failed because the trailer total did not balance with the detail records. The programmer researched the job flow and determined the corrective action. |
| XYZABC11 — October 6, 2026 | 45 minutes | Repeat occurrence. The same programmer had notes and previously prepared JCL available and confirmed that the previous correction was appropriate. |
| XYZABC11 — November 5, 2026 | 45 minutes | Third occurrence. The same programmer handled the abend again, but recovery time did not decrease further. |
| XYZABC12 — Posting abend | 46 minutes | Recovery involved placing code in PE to bypass backdating. |
| Repeat posting abends | 40–60 minutes (estimate) | The Director's general estimate for previously encountered posting abends requiring a PE correction. |
| First-time posting abends | 90–120 minutes (estimate) | The Director's general estimate for unfamiliar posting abends requiring investigation and correction. |

The first four durations are reported operational examples. The last two are estimates provided by the Senior Director.

The Director also explained that the Job History System (JHS) retains only 90 days of history. This may limit access to older incident information.

#### What I Learned from the Operational Examples

The first occurrence of XYZABC11 took 78 minutes, while the next two occurrences took 45 minutes each.

The first repeat was 33 minutes shorter than the original incident. However, I cannot attribute the entire difference to historical notes because other factors may have contributed.

The third occurrence still took 45 minutes, even though the same programmer handled it again.

These examples suggest that historical incident information may help engineers avoid repeating some investigation work. They also show that recovery involves activities that MARA cannot eliminate simply by providing an answer.

I need to distinguish three measurements:

- **Investigation time:** Time spent identifying the likely cause and determining the next action.
- **Recovery time:** Time from the abend to the job's recovery or restart, including investigation and corrective activities.
- **MARA time savings:** The reduction in investigation time that could be measured when engineers use MARA.

The Director's reported durations are not direct measurements of MARA's performance or time savings.

#### Impact on MARA

This feedback supports the importance of historical incident retrieval, especially for repeat failures.

MARA could potentially help engineers find previous incidents, review documented corrective actions, and prepare evidence-grounded recommendations.

However, any production file changes, JCL modifications, PE updates, or job restarts must remain under the organization's existing authorization and operational controls.

I plan to demonstrate MARA to the Senior Director after Thanksgiving weekend, once I have additional implementation and evaluation results.

This is real stakeholder engagement, but the Director has not yet completed a live or hands-on evaluation of MARA.

### 4. Consolidated Feedback — Seven Themes

I grouped the instructor feedback, relevant S9 rubric questions, and operational stakeholder input into seven themes.

| Theme | Questions I need to address | My next action |
|---|---|---|
| **1. Problem and Business Value** | What is MARA's primary business benefit? How do I distinguish investigation time from total recovery time? How do I support my baseline and impact assumptions? | Use the charter's 15–20-minute investigation baseline unless another value is validated. Keep the Director's recovery-time examples separate from projected MARA savings. |
| **2. Evaluation and Reliability** | Does my headline scorer detect missing evidence and incomplete JSON fields? What does the 7/7 baseline prove? Could an LLM judge reward an incorrect answer? | Review the scorer against documented failures, required response fields, and source citations. Clearly explain the denominator, measurement interval, and limitations. |
| **3. Data and Retrieval Quality** | Why did MARA fail to match a historical incident during the demo? Does the corpus contain the necessary evidence? How would the 90-day JHS retention limit affect historical retrieval? | Investigate the observed no-match case. Distinguish missing records, retrieval failures, and incomplete evidence. Consider historical data availability when evaluating future designs. |
| **4. Architecture Decisions** | Why did I choose the current approach? What alternative should I test? What happens to latency, cost, and response size as usage increases? | Compare two architecture approaches during TC5. Measure their behavior using the same evaluation inputs and document the tradeoffs and switch condition. |
| **5. Failures and Operational Safety** | What is MARA's worst observed failure? What should it do when evidence is missing or inconsistent? What actions must remain under human control? | Demonstrate a documented failure, explain its impact, and preserve human authorization for production recovery. |
| **6. Stakeholders and Deployment** | What feedback have I received from the Senior Director? Has MARA been independently validated? What security and deployment approvals are required? | Reference the November 6 engagement in `stakeholders.md`. Plan a live demonstration after Thanksgiving. Keep hands-on validation and enterprise deployment approval marked as pending. |
| **7. Demo, Impact, and Next Steps** | Can I explain MARA's value clearly, lead with one meaningful metric, show a known failure, and identify the next decision? | Improve the demo narrative using one primary endpoint metric, the evidence supporting it, business impact assumptions, known limitations, and next steps. |

### 5. Evaluation Baseline and Limitations

In TC4 Step 6, I selected **Completeness and Factual Consistency** as MARA's headline evaluation scorer.

The documented baseline passed 7 out of 7 evaluation cases, with a reported 95% bootstrap confidence interval of [100%, 100%].

This result describes a small synthetic evaluation set. It does not establish production accuracy or guarantee performance on unseen incidents.

The instructor feedback also highlighted an important gap: I need to verify that the scorer detects missing required JSON fields and unsupported source evidence.

A response can appear complete while still missing important evidence or containing unsupported claims.

I also documented citation traceability limitations during TC4. My earlier checks did not prove that every factual claim was supported by the exact retrieved passage.

I need to keep factual correctness, completeness, and citation grounding separate when interpreting evaluation results.

### 6. Business Impact Assumptions

My original charter used a 15–20-minute investigation baseline.

The instructor suggested presenting an impact range of approximately 83–167 hours saved per 1,000 incidents, or 250 hours if the 30-minute assumption is supported.

At an assumed labor cost of $75 per hour, these scenarios would represent:

| Scenario | Projected hours saved per 1,000 incidents | Estimated labor value |
|---|---:|---:|
| Lower scenario | 83 hours | $6,225 |
| Upper scenario | 167 hours | $12,525 |
| Alternative 30-minute scenario | 250 hours | $18,750 |

These are illustrative calculations based on assumed time savings. They are not measured MARA results.

The hours imply approximately 5, 10, and 15 minutes saved per incident, respectively. I still need to validate those savings assumptions and establish the actual baseline before using them as a business-value claim.

The Senior Director's November 6 examples provide additional operational context, but they measure total recovery duration rather than MARA-assisted investigation savings.

I also need to consider whether faster incident identification could reduce downtime, missed batch deadlines, or escalations. I do not currently have measured data to quantify those benefits.

### 7. What I Learned from the S9 Feedback

I learned that my demo needs to focus more on business value and less on the number of technical metrics I collected.

I need to explain where my baseline numbers came from, what each metric measures, and what the evaluation results do not prove.

The feedback also showed that historical incident retrieval is central to MARA's value. I need to investigate the no-match result and improve how I demonstrate evidence quality.

The Senior Director's examples helped me understand that repeat incidents can still require considerable recovery time, even when an engineer has previous notes and experience.

I also learned that choosing an architecture requires more than explaining why I built it. I need to compare alternatives, measure their behavior, and explain what would make me change my decision.

Finally, I need to distinguish instructor feedback, operational stakeholder input, and actual hands-on validation.

### 8. Questions I Still Need to Answer

1. What is the most important business outcome for MARA, according to an authorized operational stakeholder?
2. What caused the historical incident no-match result during the S9 demo?
3. Does my completeness scorer reliably detect missing required fields and unsupported evidence?
4. How much investigation time could MARA actually save, compared with the current workflow?
5. Which architecture performs better for MARA at realistic response sizes, and under what conditions would I switch?
6. How would limited historical retention affect MARA's ability to retrieve older incident resolutions?
7. What approvals and technical controls would be required to demonstrate and eventually deploy MARA within my employer's environment?

I will not treat these questions as resolved until I have supporting evidence.

### 9. Next Steps

For TC5, I will focus on comparing the current architecture with a second implementation, measuring their behavior, and documenting the decision and switch condition.

I will also improve the demo by leading with one meaningful evaluation metric, explaining its limitations, and showing a documented failure.

After Thanksgiving weekend, I plan to demonstrate MARA to the Senior Director of Production Support and collect feedback on its usefulness for the investigation workflow.

I will document the actual questions and feedback from that demonstration in `use_case/stakeholders.md`.

### 10. Stakeholder Validation and Deployment Limitations

The instructor feedback came from the bootcamp team. The November 6 operational examples came from a Senior Director of Production Support.

During TC1, I explained MARA and shared screenshots with the Senior Director. However, the Director has not yet completed a live or hands-on evaluation of the current prototype.

I have not tested MARA against actual employer production incidents, and no production incident data was transferred into the prototype.

Enterprise deployment and testing remain subject to the organization's security, architecture, data-handling, and operational approvals.

MARA remains an investigation assistant. It does not automatically execute production recovery actions.

I will continue to use synthetic data for bootcamp development until an approved enterprise testing option is available.

### 11. S9 Demo Critique Rubric — Questions and Answers

I reviewed the S9 Demo Critique Rubric and answered the questions below using my existing MARA implementation, evaluations, and stakeholder feedback. These are preparation answers based on the rubric, not additional questions I claim the instructors actually asked.

#### A. Problem and Business Value

**Q1. Who exactly has this problem?**

L1 Mainframe Production Support engineers who investigate batch job abends, identify probable causes, review previous incidents, and coordinate recovery with the appropriate teams.

**Q2. Have I shown MARA to someone who has this problem? What did they say?**

During TC1, I explained MARA and shared screenshots with a Senior Director of Production Support. On November 6, 2026, the Director provided operational recovery-time examples and estimates, including repeat and first-time abends.

This feedback helps me understand the problem, but the Director has not yet completed a live or hands-on evaluation of MARA.

**Q3. What does doing nothing cost?**

Engineers continue to investigate incidents manually, search historical information, and escalate when needed.

My charter uses a 15–20-minute investigation baseline. The Senior Director also provided examples of total recovery durations ranging from 45 to 78 minutes, with longer estimates for unfamiliar posting failures.

These numbers measure different things. I have not yet measured how much time MARA would save.

**Q4. Did I choose the biggest problem or the easiest one to build?**

I chose mainframe batch abend investigation because it is a familiar operational problem with a clear workflow and identifiable inputs. It was also a manageable starting point for building and evaluating MARA.

I have not established that it is the largest business problem. I still need to confirm management's primary priority.

#### B. Evaluation and Numbers

**Q5. What is the denominator behind my headline number?**

My TC4 Step 6 headline scorer, Completeness and Factual Consistency, passed 7 out of 7 synthetic evaluation cases.

The documented 95% bootstrap confidence interval was [100%, 100%]. Because the sample is small, I cannot treat this as evidence of production accuracy.

**Q6. Where did my evaluation data come from, and when was it collected?**

The evaluation data came from synthetic mainframe incident scenarios developed during TC1–TC4.

I used these scenarios to build golden examples, retrieval tests, and evaluation traces. They were not taken from employer production systems.

The evaluation work was completed during the bootcamp, with the TC4 results documented in November 2026.

**Q7. What does my evaluation not cover?**

My evaluations do not establish performance on actual production incidents, larger enterprise incident histories, unexpected data formats, or operational workload spikes.

I also have not completed claim-by-claim citation verification for every historical execution.

**Q8. What is my baseline, and how does MARA compare with it?**

My charter uses a 15–20-minute manual investigation baseline.

I have not yet performed a controlled comparison of manual investigation time against MARA-assisted investigation time.

The current evaluation results measure answer quality and retrieval behavior, not verified business time savings.

**Q9. Could my evaluation judge give a high score to an incorrect answer?**

Yes. During S7, I observed different correctness results depending on the judge rubric. This showed me that judge scores can be sensitive to how the evaluation criteria are written.

I need to validate the scorer against known failures, missing evidence, and human-reviewed examples before relying on it as a trustworthy measure.

#### C. Architecture and Tradeoffs

**Q10. What architecture did I choose, and what did I reject?**

For MARA's initial investigation workflow, I selected a fixed retrieval pipeline with one bounded retry.

I rejected a fully agentic or multi-agent approach because MARA's initial scope has predictable inputs and investigation steps. The fixed pipeline is simpler to test and control.

For retrieval, I selected Hybrid Retrieval using BM25, Dense Retrieval, and Reciprocal Rank Fusion (RRF).

I considered Agentic RAG and Dynamic Context Injection (DCI). Hybrid was my preferred starting point for combining exact identifiers with semantic search as the corpus grows.

These choices are documented in the TC1 and TC3 decision rows above.

**Q11. What would make me switch architectures?**

I would reconsider the fixed pipeline if MARA expands into incidents requiring dynamic investigation across multiple systems or tools.

I would reconsider Hybrid Retrieval if a larger evaluation shows that Agentic RAG or DCI provides better evidence coverage, correctness, latency, or cost.

TC5 will help me measure architecture alternatives before deciding whether to switch.

**Q12. What breaks first if usage increases by 10 times?**

I have not completed a 10-times-scale test.

Potential bottlenecks include model API latency, repeated retrieval calls, token consumption, and the size of the incident history being searched.

These are risks to investigate, not observed scaling failures.

**Q13. How large are the responses and tool calls, and what do they cost?**

TC3 recorded retrieval calls, characters read, and response latency for Agentic RAG and DCI.

However, I have not yet completed a comparable cost analysis using realistic response sizes and current model pricing.

I will measure these tradeoffs in TC5 before making a cost-efficiency claim.

**Q14. What would need to change before MARA could run at my employer?**

MARA would need an approved deployment environment, enterprise authentication and authorization, secure access to permitted incident data, appropriate model hosting, logging, monitoring, and security review.

The organization would also need to approve the data flows and operational use of the application.

I cannot deploy or test MARA with employer production data without the required permissions.

#### D. Failures, Safety, and Limitations

**Q15. What is the worst failure I observed?**

One important failure discussed during the S9 feedback was an inconsistent-job-name answer.

My TC4 evaluations also documented failures caused by incomplete retrieval evidence, truncated incident records, and an agent reaching its turn limit.

These failures matter because an investigation assistant can retrieve some correct information while still producing an incomplete or misleading answer.

**Q16. What does MARA do when it cannot find enough evidence?**

MARA is designed to identify insufficient evidence, attempt one bounded alternative search in its fixed workflow, and recommend escalation when the available information does not support a reliable conclusion.

It should not invent a probable cause or present an unsupported recovery action as confirmed.

**Q17. What should MARA never automate?**

MARA should not independently restart production jobs, modify production files, change JCL, update PE settings, or execute recovery procedures.

Those actions must remain under authorized human and operational controls.

#### E. Stakeholders and Next Steps

**Q18. Who needs to validate MARA next?**

An authorized Mainframe Production Support stakeholder should review MARA's investigation results, evidence, and recommended next steps.

I plan to demonstrate MARA to the Senior Director of Production Support after Thanksgiving weekend.

I will record actual feedback and questions in `stakeholders.md`.

**Q19. What is my next engineering decision?**

My next decision is to compare the current architecture with a second implementation during TC5.

I will measure the alternatives using comparable inputs and realistic response sizes, then document the selected approach and the conditions that would make me switch.

### Most Difficult Question — OPEN

**How much investigation time can MARA actually save compared with the current manual workflow?**

**Status: OPEN — Not yet measured.**

I have a charter baseline and real operational recovery-time examples, but I do not yet have a controlled manual-versus-MARA comparison.

The Senior Director's examples show total recovery duration, which includes investigation and corrective activities. They cannot be used directly as MARA time savings.

To answer this question, I would need an approved evaluation with representative incident scenarios, consistent start and end points, and measurements of manual versus MARA-assisted investigation time.

Until then, I will present business impact as a scenario based on assumptions, not as measured savings.

**TC5 Step 2 — Second-Best Architecture Decision**

**Selected second-best way: UTCP**

I selected UTCP because MARA already exposes HTTP endpoints, so Question 1 is the first "yes" in the S10 decision framework. There are no earlier questions to reject. UTCP would let me reuse an existing HTTP capability rather than rebuild it, provided I can describe the endpoint and handle authentication correctly.

**Closest alternative rejected: MCP**

I considered MCP because I may want to add more tools and make MARA's capabilities available to other clients in the future. I did not select it because I do not currently have a confirmed requirement for external MCP discovery. UTCP is a simpler alternative to evaluate against MARA's existing HTTP API.

### Architecture Decision: Sequential vs. Concurrent Tool Execution

**Decision:** I implemented sequential tool execution in MARA for TC5. Although the agent can request multiple tools in one model response, the current Python implementation executes each tool call one at a time using `await`.

**Why I chose this approach:**

- I reused the S10 agent-calling pattern to keep the implementation simple.
- Some incident investigations may depend on findings from earlier tool calls.
- I wanted to compare FastMCP/OpenAPI and direct Python tool calling without introducing concurrency as another variable.
- Sequential execution makes it easier to trace calls, troubleshoot failures, and validate token usage and latency measurements.

**Trade-off:** Independent tool calls may take longer because they execute one after another. Concurrent execution could reduce latency, but it would require additional testing for simultaneous requests, error handling, resource limits, and measurement accuracy.

**Future improvement:** I would consider concurrent execution using `asyncio.gather()` for independent investigations while keeping dependent investigations sequential. I would also add concurrency limits and test the behavior before using it in production.

**Current validation:** Both implementations have successfully completed a single-capability investigation. Multi-call execution and concurrent execution have not yet been validated.

**Conclusion:** Sequential execution is the current baseline for TC5. Concurrency remains a possible future optimization, not a tested capability.