# Someone else's ecosystem

Where your application would actually run, inside your actual firm.

> **Week 1 starts this file. Week 9 finishes it.**
> TC1 Step 6 asks eight questions. The full Week 9 checklist has around thirty,
> and the eight are a strict subset — so nothing here gets thrown away.

Describe patterns, not specifics. "On-prem OpenShift, images from an internal
registry, no public egress" is useful to everyone and identifies nobody. Never
put real hostnames, IPs, or architecture diagrams in this file.

---

## Week 1 — the first eight questions

<!-- Answered in TC1 Step 6. Bring these back from a real conversation. -->

**Who did you ask?** (role, not name)

<!-- your answer here -->

| # | Question | Answer |
| :---: | --- | --- |
| 1 | Where do internal apps run? (k8s, ECS, App Service, a VM someone maintains) | <!-- --> |
| 2 | Which cloud? AWS, Azure, GCP, on-prem, several? | <!-- --> |
| 3 | Is there an internal container registry? | <!-- --> |
| 4 | How do users log in? (Okta, Entra ID, Ping, SAML, homegrown) | <!-- --> |
| 5 | Can the app reach the internet? Egress proxy? Allowlist? | <!-- --> |
| 6 | Where do secrets come from? (Vault, Secrets Manager, Key Vault) | <!-- --> |
| 7 | Who approves a deployment, and what review does it need? | <!-- --> |
| 8 | Is there an approved internal LLM endpoint already? | <!-- --> |

### TC1 Step 10 — FIS Total Issuing Solutions Deployment Research

**Research date:** October 13, 2026

**Method:** Public research. Internal stakeholder consultation pending.

**Organizational context**

FIS acquired Global Payments' Issuer Solutions business, formerly TSYS, in January 2026. The business is now branded FIS Total Issuing Solutions.

Because of the acquisition and ongoing integration, I have not yet identified the team responsible for deploying new internal applications for our division.

**Public findings**

- FIS describes Total Issuing Solutions as supporting cloud-native and API-first issuing technology.
- FIS has announced an enterprise AI partnership with Anthropic, including work involving forward-deployed engineers.
- These announcements suggest potential enterprise deployment and AI capabilities, but they do not establish the approved hosting environment for MARA.

**Information still requiring internal confirmation**

- Application hosting platform and cloud provider
- Approved container registry
- Employee authentication and SSO
- External LLM API connectivity
- Secrets management
- Deployment approvals and security reviews
- Availability of an approved enterprise LLM gateway

**Planned contact**

Platform Engineering Lead or Cloud Infrastructure Architect supporting FIS Total Issuing Solutions. Contact not yet identified.

**Sources**

- https://www.fisglobal.com/about-us/media-room/press-release/2026/fis-completes-strategic-acquisition-of-global-payments-issuer-solutions-business
- https://www.fisglobal.com/products/total-issuing
- https://www.investor.fisglobal.com/news-releases/news-release-details/fis-brings-agentic-ai-banking-anthropic-starting-financial

**Next action**

Identify the deployment owner, send the prepared infrastructure questionnaire, and update this document with verified answers. I will not publish confidential internal infrastructure details.

**What surprised you?**

It is an interesting coincidence that I independently purchased Anthropic API credits to build MARA using Claude, while FIS had already announced its partnership with Anthropic around April/May 2026, including collaboration with Forward-Deployed Engineers (FDEs).

What makes this even more interesting is that I am currently going through the FDE bootcamp and building MARA as my use case.

This makes me curious whether MARA could eventually leverage FIS's existing Anthropic partnership and approved enterprise AI platform rather than connecting directly to the Anthropic API. I would like to explore this further with our internal AI and Platform Engineering teams.

**What would you have to change about your app to deploy there?**

<!-- your answer here -->

---

## Week 1 — what your machine told you

<!--
  Paste the egress probe output from Session 1 here. It is evidence, and it
  frequently disagrees with what people believe about their own network.
-->

<!-- probe output here -->
### October 5, 2026

| host | why | status | signed by |
|---|---|---|---|
| pypi.org | Python packages | OK | GlobalSign nv-sa |
| files.pythonhosted.org | the actual wheel downloads | OK | GlobalSign nv-sa |
| api.openai.com | the model API | OK | Google Trust Services |
| cdn.jsdelivr.net | the CDN the Week 1 frontend uses | OK | GlobalSign nv-sa |
| huggingface.co | open weights, Weeks 2 and 8 | OK | Amazon |
| registry-1.docker.io | container images | OK | Amazon |
| github.com | this repository | OK | Sectigo Limited |

**Verdict:** Open network, public CAs, no proxy. Nothing here will bite you.

**Does this match what you were told in the table above?** Where it doesn't, that
gap is worth chasing — it usually means a proxy nobody documented.

---

## Week 9 — the full checklist

<!--
  TC9 extends this same file. Do not start a new one: the point is that the git
  history shows one continuous piece of work from Week 1 to Week 9.
-->

<!-- Week 9 -->
