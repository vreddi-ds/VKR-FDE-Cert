# Stakeholders

Everyone you talk to about this project, from the first "where would this even
run?" to the final readout.

> **Week 10's technical challenge is a report to the people in this file.**
> You cannot write it later from memory. Add a row the day you have the
> conversation.

Use roles, not names. This is a public repo.

| Week | Who (role) | What you asked | What you learned | Follow-up |
| --- | --- | --- | --- | --- |
| 1 | <!-- e.g. Platform Engineering lead --> | <!-- where would a container run here? --> | <!-- --> | <!-- --> |

---

## Not everyone is an infrastructure contact

The useful list is wider than it first looks, and Week 10's report goes to all of
them:

- **The person with the problem** — the one from your charter. Have you shown
  them anything yet?
- **Whoever owns the data** you would need.
- **Whoever runs the platform** your app would deploy onto.
- **Whoever approves** a deployment, a spend, or a vendor.
- **Your own manager**, who will be asked whether this was worth the ten weeks.

If a week goes by with no conversation, add a row saying so and why. A visible
gap is more useful than a silent one.

## TC1 Step 10 — Deployment Stakeholder
**Date:** October 13, 2026

**Organization:** FIS Total Issuing Solutions

**Target contact:** Platform Engineering Lead or Cloud Infrastructure Architect responsible for internal application deployments.

**Contact status:** Not yet identified.

**Reason for contact:** To determine the approved deployment architecture for MARA, including container hosting, cloud infrastructure, authentication, secrets management, network access, and LLM connectivity.

**Current situation:** Following the acquisition of the former TSYS issuing business by FIS, I need to identify the appropriate infrastructure owner for the organization.

**Next action:** Identify the correct contact through management or the internal Platform Engineering team and send the prepared eight-question deployment questionnaire.

**Interview status:** Pending. No internal deployment information has been verified through a stakeholder interview.

## TC1 Step 12 — MARA User Feedback

**Contact:** Mainframe Production Support colleague
**Status:** Feedback requested — awaiting response
**Date contacted:** October 13, 2026

**Material shared:**
- Screenshot of MARA's Batch Abend Investigation input form.
- Screenshot of a synthetic investigation report.

**Planned follow-up:**
- Share additional screenshots showing MARA's evaluation results.
- Present all five synthetic golden examples.
- Ask the three required feedback questions.
- Document which golden examples the reviewer would reject and why.

**Feedback received:** Awaiting feedback.

**What I learned:** Pending actual feedback.

**Next action:** Follow up with the colleague and record their comments in their own words.

**Expected response:** May take several days, depending on availability.

### TC3 Step 6 — Stakeholder Validation (Deferred)

I was unable to complete independent stakeholder validation during TC3.

MARA is based on a real Mainframe Production Support use case, but I do not currently have permission to introduce or test this prototype within my company's environment. I also do not want to ask colleagues to access an unapproved application using their personal devices.

Although I work in Production Support and understand the investigation workflow, I am also developing MARA. My own testing would not count as independent stakeholder feedback.

For now, I have completed technical testing using synthetic data, but real stakeholder validation remains pending.

**Follow-up:** I will explore an appropriate, approved way to demonstrate MARA to a Production Support Engineer and collect five real questions and feedback. Until then, I will not claim that stakeholder validation has been completed.