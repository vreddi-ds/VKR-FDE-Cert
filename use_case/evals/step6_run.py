import json
from pathlib import Path
from helpers import harness
from helpers.nb import bootstrap
from helpers.judge import Judge
from gradio_client import Client
import numpy as np

root = Path("use_case/evals")

cases = [
    json.loads(line)
    for line in (root / "human_scores.jsonl").read_text().splitlines()
    if line.strip()
]

# Use each unique question and reference answer once.
eval_cases = []
seen = set()

for row in cases:
    key = (row["input"], row["output"])

    if key not in seen:
        seen.add(key)
        eval_cases.append({
            "input": row["input"],
            "output": row["output"],
        })

print(f"Evaluation cases: {len(eval_cases)}")

# try to keep ithe below rubric in sync judge_agreement.py rubric
AGREEMENT_RUBRIC = """
Evaluate whether the answer correctly and completely
addresses the question using the reference answer.

Question:
{input}

Reference answer:
{expected}

Answer to evaluate:
{actual}

Score 1 if the answer:
- Addresses every material part of the question.
- Agrees with the reference on important facts.
- Does not introduce important unsupported conclusions.

Score 0 if the answer:
- Omits a required finding.
- Contradicts the reference.
- Treats a documented outcome as unknown.
- Makes an important unsupported claim.

Do not award a passing score merely because the
answer is detailed or sounds technically reasonable.

Return JSON only:
{{"score": 0 or 1, "why": "one sentence"}}
"""

# Reuse the validated Step 3 judge configuration.
CFG = bootstrap(require=("ANTHROPIC_API_KEY",))

judge = Judge(
    CFG,
    rubric=AGREEMENT_RUBRIC,
    model="anthropic/claude-haiku-4-5-20251001",
)

# Calibrate the judge before evaluating MARA.
calibration = judge.calibrate(eval_cases)

print(calibration)

if not calibration.passed:
    raise SystemExit("Judge calibration failed. Baseline stopped.")

# Score each MARA answer using our validated Step 3 judge.
def completeness_judge(actual, case):
    return judge.score(actual, case)


SCORERS = {
    "completeness_factual_consistency": completeness_judge
}

# Connect to the running MARA Gradio server.
client = Client("http://localhost:7860")

# Call MARA's second endpoint using a natural-language question.
def mara(question):
    return client.predict(
        question=question,
        api_name="/research_mainframe_incident_history",
    )

def bootstrap_ci(
    scores, n_resamples: int = 5000, level: float = 0.95, seed: int = 0
):
    """Confidence interval for a mean, by resampling.

    Sample the results you have, with replacement, thousands of times. The
    spread of those means is how much your number would move if you had
    collected a different set of the same size. No distribution assumed --
    which matters, because eval scores are rarely normal.
    """
    rng = np.random.default_rng(seed)
    arr = np.asarray(scores, dtype=float)
    means = arr[
        rng.integers(0, len(arr), size=(n_resamples, len(arr)))
    ].mean(axis=1)
    lo, hi = np.percentile(
        means, [(1 - level) / 2 * 100, (1 + level) / 2 * 100]
    )
    return float(arr.mean()), float(lo), float(hi)


# Run the Step 6 baseline evaluation.
baseline_report = harness.run(
    eval_cases,
    mara,
    SCORERS,
    name="evals-baseline",
)

# Collect the individual judge scores.
scores = [
    result.scores["completeness_factual_consistency"]
    for result in baseline_report.results
]

# Calculate the baseline mean and 95% confidence interval.
mean, ci_low, ci_high = bootstrap_ci(scores)

print(f"Baseline pass rate: {mean:.1%}")
print(f"95% CI: [{ci_low:.1%}, {ci_high:.1%}]")
print(f"Evaluation cases: {len(scores)}")

# Save the complete baseline evaluation results.
harness.save(
    baseline_report,
    "use_case/evals/baseline.json",
)

# Reload the saved baseline and verify it matches this run.
print(
    harness.compare(
        harness.load("use_case/evals/baseline.json"),
        baseline_report,
    )
)