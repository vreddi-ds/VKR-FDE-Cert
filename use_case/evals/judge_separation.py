
import json
from pathlib import Path

from helpers.nb import bootstrap
from helpers.judge import Judge

# Same rubric used in judge_agreement.py.
# failures.md: MARA-08 and TC4-04.
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

# Use the SAME completeness rubric as the human agreement test.

path = Path("use_case/evals")
data = json.loads(
    (path / "tc4_step2_results.json").read_text()
)

goldens = [
    {
        "input": json.dumps(case["input"]),
        "output": json.dumps(case["expected"]),
    }
    for case in data["Oracle"]["cases"]
]

CFG = bootstrap(require=("ANTHROPIC_API_KEY",))

judge = Judge(
    CFG,
    rubric=AGREEMENT_RUBRIC,
    model="anthropic/claude-haiku-4-5-20251001",
)

# Instructor's required calibration.
calibration = judge.calibrate(goldens)
print("Calibration:", calibration)

if not calibration.passed:
    raise SystemExit("Judge failed calibration.")

echo_scores = []
oracle_scores = []

for i, golden in enumerate(goldens):
    echo_actual = data["Echo"]["cases"][i]["actual"]
    oracle_actual = json.dumps(
        data["Oracle"]["cases"][i]["actual"]
    )

    echo_scores.append(judge.score(echo_actual, golden))
    oracle_scores.append(judge.score(oracle_actual, golden))

echo_mean = sum(echo_scores) / len(echo_scores)
oracle_mean = sum(oracle_scores) / len(oracle_scores)
separation = oracle_mean - echo_mean

print()
print(f"{'Case':<8} {'Echo':>10} {'Oracle':>10}")
print("-" * 30)

for i, (echo, oracle) in enumerate(
    zip(echo_scores, oracle_scores), 1
):
    print(f"{i:<8} {echo:>10.2f} {oracle:>10.2f}")

print("-" * 30)
print(f"Echo mean: {echo_mean:.3f}")
print(f"Oracle mean: {oracle_mean:.3f}")
print(f"Separation: {separation:.3f}")

agreement = json.loads(
    (path / "tc4_step3_agreement_results.json").read_text()
)

result = {
    "rubric": "answer completeness and factual consistency",
    "judge_model": "anthropic/claude-haiku-4-5-20251001",
    "calibration": {
        "accepted": calibration.accepted,
        "wrong": calibration.wrong,
        "passed": calibration.passed,
    },
    "echo_scores": echo_scores,
    "oracle_scores": oracle_scores,
    "echo_mean": echo_mean,
    "oracle_mean": oracle_mean,
    "separation": separation,
    "human_agreement": agreement["agreement"],
    "human_matches": agreement["matches"],
    "human_total": agreement["total"],
}

output = path / "tc4_step3_final_validation.json"
output.write_text(json.dumps(result, indent=2))

print(f"Human agreement: {agreement['agreement']:.1%}")
print(f"Saved: {output}")
