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
| 3 | <!-- retrieval approach --> | <!-- --> | <!-- --> | <!-- --> |
| 5 | <!-- agent architecture --> | <!-- --> | <!-- --> | <!-- --> |
| 6 | <!-- guardrail level --> | <!-- --> | <!-- --> | <!-- --> |
| 7 | <!-- memory type --> | <!-- --> | <!-- --> | <!-- --> |
| 8 | <!-- model --> | <!-- --> | <!-- --> | <!-- --> |

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

The last column is the one people skip and the one clients ask about. "We chose
dense retrieval; we would switch to hybrid if exact-match queries went above ~20%
of traffic" is an engineering position. "We chose dense retrieval" is a
preference.
