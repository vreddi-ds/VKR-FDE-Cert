
import json
from pathlib import Path

from helpers.nb import bootstrap
from helpers.judge import Judge

# Evaluate completeness and factual consistency.
# Related to failures.md: MARA-08 and TC4-04.
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

root = Path("use_case/evals")

rows = [
    json.loads(line)
    for line in (root / "human_scores.jsonl").read_text().splitlines()
    if line.strip()
]

CFG = bootstrap(require=("ANTHROPIC_API_KEY",))

judge = Judge(
    CFG,
    rubric=AGREEMENT_RUBRIC,
    model="anthropic/claude-haiku-4-5-20251001",
)

# Calibrate the new rubric before using the judge.
goldens = [
    {"input": row["input"], "output": row["output"]}
    for row in rows
]

calibration = judge.calibrate(goldens)
print("Calibration:", calibration)

if not calibration.passed:
    print("Calibration failed. Do not use judge scores.")
    raise SystemExit(1)

results = []

for row in rows:
    case = {
        "input": row["input"],
        "output": row["output"],
    }

    score = judge.score(row["actual"], case)
    judge_pass = score >= 0.5
    human_pass = row["pass"]

    results.append({
        "id": row["id"],
        "approach": row["approach"],
        "human_pass": human_pass,
        "judge_pass": judge_pass,
        "judge_score": score,
        "agree": judge_pass == human_pass,
    })

matches = sum(result["agree"] for result in results)
total = len(results)
agreement = matches / total

print()
print(f"{'Case':<12} {'Approach':<13} {'Human':<8} {'Judge':<8} {'Agree'}")
print("-" * 55)

for result in results:
    print(
        f"{result['id']:<12} "
        f"{result['approach']:<13} "
        f"{'PASS' if result['human_pass'] else 'FAIL':<8} "
        f"{'PASS' if result['judge_pass'] else 'FAIL':<8} "
        f"{'YES' if result['agree'] else 'NO'}"
    )

print()
print(f"Agreement: {matches}/{total} = {agreement:.1%}")
print("Instructor comparison floor: 60%")

output = {
    "judge_model": "anthropic/claude-haiku-4-5-20251001",
    "rubric": "answer completeness and factual consistency",
    "calibration": {
        "accepted": calibration.accepted,
        "wrong": calibration.wrong,
        "passed": calibration.passed,
    },
    "matches": matches,
    "total": total,
    "agreement": agreement,
    "chance_floor": 0.60,
    "results": results,
}

output_path = root / "tc4_step3_agreement_results.json"
output_path.write_text(json.dumps(output, indent=2))

print(f"Saved: {output_path}")
