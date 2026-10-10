# Project charter

<!--
  Fill this in during TC1, from your Getting to Concreteness worksheet.
  Every week's Session 2 notebook reads this file and stops if it is still the
  template. That is on purpose.
-->

**Department:** Issuing Support 

**Working title:** Mainframe Abend Research Assistant (MARA)

---

## The problem

**Who has it?** 

Level 1 Production Support Engineer

**What are they trying to do?**

Identify the failed mainframe batch job, investigate the cause of the failure, and determine the appropriate next action. This may involve restarting the job from the correct step, correcting data before restarting, or escalating the issue to the SME for further advice. The engineer then communicates the recommended action to the Operations team.

**How do they handle it today?**

The on-shift Level 1 Production Support Engineer receives a call from the Operations team, along with an email notification about the job abend. The engineer locates the failed job, reviews JES messages, identifies the failed step, program, and abend code, and investigates the possible cause.

The engineer then searches team runbooks, knowledge base documents, and previous ServiceNow incidents to identify similar failures and their resolutions. If the cause or appropriate recovery action remains unclear, the engineer reaches out to the application SME for further guidance.

Based on the investigation and guidance, the engineer determines the appropriate remediation, restart, or escalation action and communicates the decision to the Operations team.

**What does that cost — time, money, risk, or relationships?**

Investigating a typical batch job abend takes at least 15–20 minutes of engineering effort, depending on the complexity of the failure and the engineer's experience. For jobs on the critical path, Level 1 engineers typically have only 5–10 minutes to investigate before escalating to an SME.

Manual investigation across multiple knowledge sources increases engineering effort and dependency on experienced SMEs. Delays in identifying the cause and determining the next action can affect critical batch processing, downstream jobs, and potentially client SLAs. Repeated investigations also add operational costs and increase the risk of inconsistent decisions.

**The problem in one sentence. No solution in it.**

Level 1 Production Support Engineers must manually investigate mainframe batch job failures across multiple information sources, delaying operational decisions and increasing the risk of missing critical batch processing SLAs.

---

## Success

**What does the new world look like for that person?**

The Level 1 Production Support Engineer can investigate mainframe batch job failures faster and more consistently without manually searching multiple knowledge sources. The engineer receives an evidence-based investigation summary identifying what failed, the probable cause, similar past incidents, and recommended next steps.

This helps the engineer make an informed operational decision and, where possible, resolve the issue within the 5–10-minute critical-path window. If the issue cannot be resolved within that window, the engineer can escalate to the SME with relevant evidence and investigation findings, reducing repeated research and helping speed up recovery.

Over time, validated incident resolutions and lessons learned can be added to MARA's knowledge base and made available through RAG. This creates a growing repository of operational knowledge, potentially improving the accuracy and consistency of future investigations and the strength of evidence supporting MARA's recommendations.

**How would the firm measure it? Which numbers should move?**

The primary KPI for MARA is Mean Time to Investigate (MTTI). Based on current operational experience, a typical mainframe batch job investigation takes at least 15–20 minutes.

The initial goal is to reduce investigation time to 10 minutes or less, representing a minimum improvement of approximately 33%, with a stretch goal of 50%.

For critical-path jobs, success will also be measured by whether the Level 1 engineer can identify an appropriate recovery action or prepare an evidence-based SME escalation within the 5–10-minute window.

Additional measures include the accuracy of investigation findings, the quality of supporting evidence, and reduced repetitive research. These targets will initially be evaluated using synthetic incidents and validated against real operational measurements when available.

---

## The first product

**Your solution in one sentence.**

Mainframe Abend Research Assistant (MARA) is an evidence-grounded research and decision-support system that helps Level 1 Production Support Engineers investigate mainframe batch job failures, identify probable causes using historical incidents and runbooks, and recommend next steps while keeping final operational decisions with the engineer.

**Input → Output.** Be specific enough that someone could build it wrong and you would notice.

| | |
| --- | --- |
| **In** | The Level 1 Production Support Engineer provides the failed batch job name, failure date, abend code, and one or more relevant JES error messages from the Operations email notification. MARA uses this information to investigate the failure against its available knowledge base. |
| **Out** | MARA generates a structured investigation report containing the failure summary, probable root cause, evidence and historical findings (including references to relevant JES messages, runbooks, knowledge base articles, and previous incidents), confidence level, recommended next steps, and investigation status. When sufficient evidence is unavailable, MARA explicitly reports "Insufficient Evidence" and identifies the additional information or escalation needed. Final remediation and restart decisions remain with the Production Support Engineer. |

---

## Decisions made later

<!--
  Amended as the cohort goes. Keep the reasoning, not just the choice — Week 5
  asks you to defend your architecture against the options you rejected, and
  Week 10's handoff doc is largely this section.
-->

| Week | Decision | Why, and what you rejected |
| --- | --- | --- |
| 3 | Retrieval approach | <!-- TC3 --> |
| 5 | Agent architecture | <!-- TC5 --> |
| 8 | Model | <!-- TC8 --> |
