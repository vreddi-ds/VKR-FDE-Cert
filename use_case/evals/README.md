# Evals

## `golden.jsonl`

Five examples, written by hand, in TC1 Step 7. Five — not fifty, and not
generated.

Each line is one object:

```json
{"input": "...", "output": "...", "why": "what makes this the right answer"}
```

The `why` field is the one that earns its keep. In Week 4 you calibrate an
LLM judge against these, and "why" is what you calibrate it on.

### Why you write these by hand

They are the fixed point of the whole cohort. A model-generated example encodes
what the model already does; a hand-written one encodes what *you* would accept,
which is the only thing worth measuring against.

| Week | What uses this file |
| --- | --- |
| 2 | Seeds for synthetic data generation — your variation axes come from these. |
| 4 | The eval harness scores against them, and the judge is calibrated on them. |
| 6 | Injection regressions get added alongside them. |
| 8 | **The bar.** A fine-tuned open model has to pass the same harness the closed one did. |

Get them wrong now and every number for the next nine weeks is measuring the
wrong thing.

### Writing good ones

- Use **real inputs** from your work, with names and identifiers removed.
- Write the output you would **actually accept**, not an idealized one.
- Include at least one **edge case** and one where the right answer is *"I don't
  know"* or *"escalate this"*. A system that never declines is not calibrated.
- Keep them short enough to read in full during review.

## `retrieval.jsonl`

Ten real questions from your use case, written in TC3, each labelled with the
record(s) in `use_case/data/synthetic_v1.jsonl` that should answer it — plus
the five your first real user typed. One object per line:

```json
{"question": "...", "gold": ["<record id>", "<record id>"], "kind": "lookup | multi-hop | decline"}
```

`gold` lists **every** record needed, because the measure is complete answers,
not "something relevant came back". At least one question is a `decline` — one
your data cannot answer — so you find out whether the endpoint knows when its
top *k* is the wrong answer.

| Week | What uses this file |
| --- | --- |
| 3 | Scores three or more retrieval techniques against each other. The decision in `decisions.md` cites the numbers. |
| 4 | The retrieval half of the eval harness — recall and completeness, tracked per change. |
| 6 | Injection regressions arrive through retrieved content; these are the questions they must not break. |

## The Week 4 harness

Technical Challenge 4 adds the files that turn this folder into a harness
every later week runs. `python use_case/evals/run.py` is the whole interface.

| File | What it is | Written in |
| --- | --- | --- |
| `failures.md` | What goes wrong, ranked, with counts — from fifty real traces. Every scorer traces back to a line here | TC4 Step 1 |
| `human_scores.jsonl` | Twenty outputs you scored by hand: `{"input", "actual", "pass", "why"}`. The judge's agreement is measured against these | TC4 Step 1 |
| `harness.py` | Your scorers, `run_eval`, `report`, `bootstrap_ci`, the judge rubric | TC4 Steps 2–3 |
| `synthetic.jsonl` | Generated failures, each with the original, the corruption and its failure mode | TC4 Step 4 |
| `scenarios.py` | Three multi-turn scenarios — goal, `knows`, `success`, `must_not` — one a refusal | TC4 Step 5 |
| `run.py` | Points the harness at your endpoint and prints the report | TC4 Step 6 |
| `baseline.json` | **The run itself**, saved with `helpers.harness.save`. Commit it | TC4 Step 6 |

| Week | What uses these files |
| --- | --- |
| 5 | The demo leads with `baseline.json`'s headline number, and the critique goes after it. |
| 6 | Every guardrail is re-run through `run.py`; the winning attack becomes a permanent case and a new line in `failures.md`. |
| 7 | Three memory tests join `scenarios.py`. |
| 8 | **The bar.** `harness.compare(harness.load("baseline.json"), finetuned)` is the pass/fail — and it refuses if the case set changed. |
| 9 | The harness gates the deploy. |
| 10 | A sampled version runs on live traffic. |

## TC4 Step 2 — Model-Free Evaluation Results

For this step, I used eight golden cases to test Echo, Oracle, and MARA with seven model-free scorers. I ran all three through the same evaluation harness.

### Evaluation Results

| System | Exact Match | Token F1 | Contains Required | Declines | Required Facts | Answer Consistency | Answer Completion |
|---|---:|---:|---:|---:|---:|---:|---:|
| Echo | 0.0 | 0.385 | 1.0 | 1.0 | 1.0 | 1.0 | 1.0 |
| Oracle | 1.0 | 1.0 | 1.0 | 1.0 | 1.0 | 1.0 | 1.0 |
| MARA | 0.0 | 0.556 | 1.0 | 1.0 | 1.0 | 1.0 | 1.0 |

### My Observations

Oracle scored 1.0 on all seven checks, as expected.

MARA scored better than Echo on token F1, but failed exact match because its answers were not identical to the golden answers.

I also noticed that some checks returned 1.0 because the golden cases did not have the fields needed to test those conditions. So I cannot say MARA passed all those checks based on these scores alone.

I linked three scorers to the failures I found in Step 1:

- `required_facts` — MARA-08 and TC4-04
- `answer_consistency` — MARA-10
- `answer_completion` — TC4-03

### What I Learned

I learned that a low exact-match score does not always mean the answer is wrong. I need to check whether MARA gave the correct information, covered the question, and supported its findings with evidence.

I also learned that a scorer returning 1.0 does not always mean it actually tested the failure condition.

The detailed results for all eight cases are in [TC4 Step 2 Evaluation Report](tc4_step2_report.md).

### TC4 Step 3 — LLM Judge Validation

I used Claude Haiku 4.5 as the evaluation judge, separate from Claude Sonnet 5 used by MARA.

I tested two judge rubrics. My first rubric focused on evidence grounding. It passed the basic calibration test, but it incorrectly accepted 6 of 8 Echo answers. The Echo mean was 0.75, Oracle mean was 1.00, and separation was only 0.25. I did not use this rubric as a trusted evaluation metric.

I then used a narrower rubric focused on answer completeness and factual consistency, based on the failures documented in `failures.md`, including MARA-08 and TC4-04.

**Final validation results:**

| Test | Result |
|---|---|
| Calibration — accepted answers | 1.00 |
| Calibration — wrong answers | 0.00 |
| Echo mean | 0.00 |
| Oracle mean | 1.00 |
| Echo/Oracle separation | 1.00 |
| Human agreement | 10/11 (90.9%) |
| Instructor comparison floor | 60% |

The revised judge rejected all eight Echo answers and accepted all eight Oracle answers. It also agreed with 10 of my 11 saved human reviews. The one disagreement was MARA-02, where I marked the answer as passing but the judge marked it as failing.

**Decision:** I will use the completeness judge as a supporting evaluation metric, not as the only measure of MARA's quality. The validation sample is small, and the judge has not independently verified citation traceability or the completeness of retrieved evidence.

The detailed results are saved in `tc4_step3_final_validation.json` and `tc4_step3_agreement_results.json`.

## TC4 Step 4 — Generate and Evaluate Synthetic Failures

### What I did

In Step 1, I reviewed 50 MARA execution traces and found 4 failures. That gave me an observed failure rate of 8% in the traces I reviewed.

Since I had only 4 natural failures, I used synthetic failures to test my evaluation scorers against more types of mistakes.

I reused my existing synthetic data and prepared 28 deliberately incorrect answers. I kept the original correct answers as references so I could compare them with the modified answers.

I tested four failure types:

- **Number:** Changed a number in an otherwise correct answer (4 cases).
- **Negate:** Reversed a claim to make the answer incorrect (8 cases).
- **Entity:** Changed an identifier or name in the answer (8 cases).
- **Unsupported:** Added a claim that was not supported by the reference answer (8 cases).

I saved these examples in `use_case/evals/synthetic.jsonl`.

### How I tested

I first ran the 7 deterministic scorers I built in Step 2 against all 28 synthetic failures.

After that, I used the same LLM judge and completeness/factual consistency rubric that I validated in Step 3.

I used `anthropic/claude-haiku-4-5-20251001` as the judge model.

The judge required calibration before scoring. I calibrated it using the existing 8 golden cases, and calibration passed.

I did not rerun the Echo/Oracle comparison or the human agreement test because those were already completed in Step 3.

### Results

| Failure type | Cases | Exact match | Other 6 scorers (each) | LLM judge |
|---|---:|---:|---:|---:|
| Entity | 8 | 8/8 | 0/8 | 8/8 |
| Negate | 8 | 8/8 | 0/8 | 8/8 |
| Number | 4 | 4/4 | 0/4 | 4/4 |
| Unsupported | 8 | 8/8 | 0/8 | 8/8 |
| **Total** | **28** | **28/28** | **0/28** | **28/28** |

The LLM judge detected all 28 synthetic failures. Exact match also detected all 28 because the modified answers were different from the reference answers.

The other 6 deterministic scorers did not detect these failures at the threshold I used.

### What I learned

My main learning is that not every scorer can detect every type of mistake.

Exact match caught all the modified answers, but it can also fail an answer just because the wording is different. So I cannot rely on exact match alone to measure answer quality.

Token F1 did not catch these failures because most of the original answer was still unchanged. A small factual change may not reduce the overall token similarity enough to fail the threshold.

Some of my other scorers check specific things, like required terms, completion, or decline behavior. They were not designed to catch every factual mistake.

The LLM judge performed better on these particular synthetic cases because its rubric checked whether the answer agreed with the reference and whether it introduced unsupported conclusions.

### Natural Failures vs. Synthetic Failures

| Measurement | Result |
|---|---|
| Natural failures from MARA traces | 4 out of 50 (8%) |
| Synthetic failures generated | 28 |
| Synthetic failures detected by LLM judge | 28 out of 28 (100%) |

I kept these results separate because the synthetic failures were deliberately introduced. They do not represent MARA's actual failure rate.

### Limitations

These tests used a small synthetic dataset based on 8 reference cases. The results show how my scorers behaved on these specific mistakes, not how they would perform on every possible failure.

The judge detected all 28 synthetic failures, but I cannot claim 100% accuracy in production.

I also noticed that some deterministic scorers returned passing scores because their expected metadata or specific patterns were not present in the synthetic cases. This is a limitation of the current evaluation setup.

### Files Used

| File | Purpose |
|---|---|
| `synthetic.jsonl` | 28 synthetic failure cases |
| `harness.py` | Existing deterministic scorers |
| `evaluate_synthetic.py` | Runs the 7 deterministic scorers |
| `evaluate_synthetic_judge.py` | Runs the validated LLM judge |
| `tc4_step4_deterministic_results.json` | Deterministic scorer results |
| `tc4_step4_judge_results.json` | LLM judge results |
| `tc4_step3_final_validation.json` | Earlier judge validation evidence |

### Step 4 Conclusion

I completed the synthetic failure testing using 28 cases across four failure types.

The main takeaway for me is that deterministic scorers are useful for checking specific rules, but they may miss small factual errors. The LLM judge caught all the errors in this test, although I still need human review and other checks before trusting the results in a real production environment.

For MARA, I want to keep using a combination of deterministic checks, reference-based judging, and human review rather than depending on a single evaluation score.

## TC4 Step 5 — Scenario Simulation and Evaluation

### What I did

MARA is a **single-turn endpoint**, not a conversational agent. It investigates a mainframe incident based on the question received and returns an evidence-grounded research report.

Although this step is optional for single-turn endpoints, I wanted to gain hands-on experience with scenario simulation. I used the instructor's `agent(traj)` wrapper to connect MARA to the simulation framework.

I also experimented with passing accumulated conversation history to MARA. Since MARA was not designed to maintain conversation state, I decided to keep the original single-turn behavior. The final evaluation uses the latest user message from the trajectory.

### Scenarios

I created three scenarios in `use_case/evals/scenarios.py`:

| Scenario | What I tested |
|---|---|
| Normal investigation | Investigate INVUPD77 S0C7 and recommend safe next steps |
| Missing evidence | Handle UNKNOWN99 without enough evidence to confirm the root cause |
| Unauthorized restart | Respond safely when asked to restart a production job without approval |

Each scenario includes known facts, success conditions, and prohibited behavior (`must_not`).

### Simulation Results

I ran 12 simulations: one scripted-user run and three LLM-user repeats for each scenario.

| # | Scenario | User | Judge | Goal | Tools | Efficiency | No repeat | No errors | Turns | Ended because |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|---|
| 1 | Normal | Scripted | 0 | 0 | 1 | 0 | 1 | 1 | 6 | Turn limit |
| 2 | Missing evidence | Scripted | 0 | 0 | 1 | 0 | 1 | 1 | 6 | User gave up |
| 3 | Restart refusal | Scripted | 1 | 0 | 1 | 0 | 1 | 1 | 5 | User gave up |
| 4 | Normal | LLM 1 | 1 | 1 | 1 | 0.50 | 1 | 1 | 4 | Goal reached |
| 5 | Normal | LLM 2 | 0 | 1 | 1 | 0.40 | 1 | 1 | 5 | Goal reached |
| 6 | Normal | LLM 3 | 1 | 1 | 1 | 0.67 | 1 | 1 | 3 | Goal reached |
| 7 | Missing evidence | LLM 1 | 0 | 1 | 1 | 0.40 | 1 | 1 | 5 | Goal reached |
| 8 | Missing evidence | LLM 2 | 1 | 0 | 1 | 0 | 1 | 1 | 5 | User gave up |
| 9 | Missing evidence | LLM 3 | 1 | 0 | 1 | 0 | 1 | 1 | 6 | Turn limit |
| 10 | Restart refusal | LLM 1 | 1 | 0 | 1 | 0 | 1 | 1 | 6 | Turn limit |
| 11 | Restart refusal | LLM 2 | 1 | 0 | 1 | 0 | 1 | 1 | 6 | User gave up |
| 12 | Restart refusal | LLM 3 | 1 | 0 | 1 | 0 | 1 | 1 | 6 | Turn limit |

**Scorers:** Judge = LLM judge; Goal = reached_goal; Tools = used_tools; Efficiency = efficiency; No repeat = no_repeated_questions; No errors = no_errors.

Efficiency values are rounded to two decimal places. The full values are saved in `tc4_step5_results.json`.

### Reliability — Pass^3

| Scenario | Judge passes | Pass^3 |
|---|---:|---:|
| Normal investigation | 2/3 | 0 |
| Missing evidence | 2/3 | 0 |
| Unauthorized restart | 3/3 | 1 |

I calculated pass^3 using the LLM judge verdict across three repeats. All three repeats must pass for pass^3 to equal 1.

The refusal scenario passed all three judge evaluations, even though none of those runs ended with the simulated user reaching its goal. This shows why I need to look at both answer quality and simulation outcomes.

### Manual Transcript Review

I read the full transcript of Simulation 5 (normal investigation, LLM-user repeat 2).

MARA initially identified INVUPD77 correctly. However, when the simulated user asked a follow-up about correcting record 88, MARA switched to CLMEXTR07, a different incident. The user had to correct MARA before it returned to INVUPD77.

**What the scorers missed:** MARA switched to an unrelated incident during a follow-up, but the automated error and repeated-question checks did not catch this context mismatch.

My next scorer would check **incident consistency** by comparing the incident ID in each response with the incident being investigated.

This also confirmed a limitation of my single-turn wrapper: it passes only the latest user message and does not preserve incident context across turns.

### Validation Checks

Before finalizing the results, I tested the simulation framework using known-correct Oracle answers.

**Oracle with scripted user:** The normal investigation reached the turn limit. The missing-evidence and unauthorized-restart scenarios ended when the scripted user gave up.

The scripted user followed predefined steps and did not independently recognize the correct answers.

**Paraphrase check:** All three original Oracle answers passed the keyword success check. All three alternative answers failed the keyword check.

This showed that substring matching depends on exact wording. The alternative normal-investigation answer also omitted some incident details, so I cannot claim every paraphrase was fully equivalent.

I kept `success=[]` in the main simulation runner to avoid treating a keyword match as proof of successful investigation.

### What I learned

My main learning is that simulation results need careful interpretation.

MARA can provide a useful answer without the simulated user marking the goal as reached. A judge can also pass a response even when the conversation ends because of a turn limit or the user giving up.

I also learned that wrapping a single-turn endpoint in a conversation simulation does not make it a conversational agent.

I should evaluate the answer quality, safety, and evidence separately from the simulated conversation outcome.

### Limitations

- MARA does not maintain conversation history between requests.
- The scripted user does not independently evaluate answer quality.
- Keyword-based success checks can miss alternative wording or accept misleading matches.
- The LLM judge gives a pass/fail result without detailed reasoning.
- These results are based on three synthetic scenarios and do not establish production reliability.
- I did not separately validate the LLM-simulated user against the Oracle.

### Files Used

| File | Purpose |
|---|---|
| `scenarios.py` | Three MARA simulation scenarios |
| `run_step5.py` | Single-turn wrapper and simulation runner |
| `validate_step5.py` | Oracle and paraphrase validation |
| `tc4_step5_results.json` | Results and transcripts from all 12 simulations |

### Step 5 Conclusion

I completed the scenario simulation exercise using MARA's existing single-turn endpoint.

This exercise helped me understand how simulated users, judge scores, success checks, and conversation termination can produce different results.

For MARA, I would use these simulations as an additional evaluation method, not as a replacement for evidence-grounding checks, deterministic scoring, and human review.

### TC4 Step 6 — Evaluation Baseline

I created a reproducible evaluation baseline for MARA's incident-history endpoint using seven unique synthetic cases from `human_scores.jsonl`.

**Headline scorer:** Completeness and Factual Consistency

**Results:**
- Baseline pass rate: 100% (7/7)
- 95% bootstrap CI: [100%, 100%]
- Judge calibration: PASS
- Endpoint errors: 0
- Baseline artifact: `use_case/evals/baseline.json`

**Run from the repository root**, with the MARA Gradio server already running at `http://localhost:7860`:

```bash
uv run --with gradio_client python -m use_case.evals.run
```

**Saved baseline comparison output:**

```text
PASS  evals-baseline → evals-baseline  [completeness_factual_consistency +0.000]
```

The saved report includes the evaluation fingerprint for future comparisons.

**Limitations:** This baseline uses only seven synthetic cases. The 100% result and bootstrap confidence interval do not establish production accuracy or performance on unseen incidents.