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
| 5 | **Senior Director, Production Support** | Requested actual mainframe abend recovery durations and examples of first-time versus repeat incidents. | Received recovery examples ranging from 45 to 78 minutes, estimates of 40–120 minutes for posting abends, and confirmation that JHS retains 90 days of history. These are recovery durations, not measured MARA time savings. | Refined MARA demonstration planned after Thanksgiving. Ask the three required Step 7 questions and record actual feedback. Hands-on validation remains pending. |
| 5 — Step 7 (planned) | Senior Director, Production Support | After the refined five-minute MARA demonstration, ask: (1) What would you do differently on Monday if this is right? (2) What did I say that you did not believe? (3) What is the worst thing this could do, from where you sit? | Pending — refined demonstration has not yet taken place. No Step 7 feedback collected. | Schedule an approved demonstration after Thanksgiving, record actual responses, and update `decisions.md` with what the feedback changed or why nothing changed. |

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

---
## TC5 Step 1 — Senior Director, Production Support Engagement

**Initial engagement:** TC1 — Explained MARA and shared screenshots.

**Follow-up email:** November 6, 2026, 11:58 AM.

**Feedback type:** Operational recovery-time examples and estimates.

**Validation status:** Real stakeholder engagement; hands-on MARA validation pending.

### Feedback Received

I explained MARA to the Senior Director during TC1 and shared screenshots of the prototype.

On November 6, I received an email with anonymized examples of mainframe batch abend recovery times.

| Scenario | Recovery duration | Details |
|---|---|---|
| XYZABC11 — September 17 | 78 minutes | First occurrence. The programmer had to research the job flow and determine the correction. |
| XYZABC11 — October 6 | 45 minutes | Repeat occurrence. The same programmer had previous notes and JCL available. |
| XYZABC11 — November 5 | 45 minutes | Third occurrence, handled by the same programmer. |
| XYZABC12 — Posting abend | 46 minutes | Recovery involved a PE code change to bypass backdating. |
| Repeat posting abends | 40–60 minutes (estimate) | Previously encountered posting failures requiring a PE correction. |
| First-time posting abends | 90–120 minutes (estimate) | Additional investigation and correction may be required. |

The Director also explained that JHS retains only 90 days of history, which limits access to older incident information.

### What I Learned

I learned that repeat incidents can still take considerable time to recover, even when the programmer has previous experience and notes.

Historical incident information may help MARA reduce repeated investigation work. However, these durations include investigation and recovery activities, so they are not direct measurements of potential MARA time savings.

### Next Steps

I plan to demonstrate MARA to the Senior Director after Thanksgiving weekend, once I have more implementation and evaluation results.

During the demonstration, I want to understand whether MARA's historical incident retrieval and investigation recommendations would help Production Support engineers.

I will document the Director's actual questions and feedback after the demonstration.

No production incident data was transferred into MARA, and I have not claimed that the Director has validated its accuracy or performance.