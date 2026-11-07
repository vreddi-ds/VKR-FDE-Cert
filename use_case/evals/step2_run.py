
import json
from pathlib import Path
from gradio_client import Client

from use_case.evals.harness import (
    run_eval,
    report,
    exact_match,
    token_f1,
    contains_required,
    declines,
    required_facts,
    answer_consistency,
    answer_completion,
)

golden_path = Path("use_case/evals/golden.jsonl")

seeds = [
    json.loads(line)
    for line in golden_path.read_text().splitlines()
    if line.strip()
]

# Same JSON serialization approach used in S7 Task 3.
cases = [
    {
        **seed,
        "input": json.dumps(seed["input"]),
        "output": json.dumps(seed["output"]),
    }
    for seed in seeds
]

# Echo returns the input unchanged.
def echo(question):
    return question

# Oracle returns the known golden answer.
answer_by_input = {
    case["input"]: case["output"]
    for case in cases
}

def oracle(question):
    return answer_by_input[question]

scorers = {
    "exact_match": exact_match,
    "token_f1": token_f1,
    "contains_required": contains_required,
    "declines": declines,
    "required_facts": required_facts,
    "answer_consistency": answer_consistency,
    "answer_completion": answer_completion,
}

client = Client("http://localhost:7860")

# def mara(question):
#     request = json.loads(question)

#     return client.predict(
#         question=request["question"],
#         api_name="/research_mainframe_incident_history",
#     )

def mara(question):
    request = json.loads(question)

    return client.predict(
        job_name=request["job_name"],
        failure_date=request["failure_date"],
        abend_code=request["abend_code"],
        jes_messages=request["jes_messages"],
        api_name="/research_mainframe_batch_abend",
    )

all_results = {}

for name, system in [
    ("Echo", echo),
    ("Oracle", oracle),
    ("MARA", mara),
]:
    results = run_eval(cases, system, scorers)

    all_results[name] = {
        "summary": report(results),
        "cases": [
            {
                "input": json.loads(result.case["input"]),
                "expected": json.loads(result.case["output"]),
                "actual": (
                    json.loads(result.actual)
                    if name in ("Oracle", "MARA")
                    else result.actual
                ),
                "scores": result.scores,
                "passed": result.passed,
            }
            for result in results
        ],
    }

# Save complete machine-readable results
output_dir = Path("use_case/evals")
json_path = output_dir / "tc4_step2_results.json"

json_path.write_text(json.dumps(all_results, indent=2))

# Build the Markdown report
md = [
    "# TC4 Step 2 — MARA Evaluation Report",
    "",
    "## Evaluation Summary",
    "",
    f"Golden cases: {len(cases)}",
    "",
    # "| System | " + " | ".join(scorers.keys()) + " | Pass Rate |",
    # "|---|" + "|---:" * (len(scorers) + 1) + "|",
    "| System | " + " | ".join(scorers.keys()) + " | Pass Rate |",
    "|---|" + "---:|" * (len(scorers) + 1),
]

for name, data in all_results.items():
    summary = data["summary"]
    values = [
        f"{summary[metric]:.1%}"
        for metric in scorers
    ]
    md.append(
        f"| {name} | " +
        " | ".join(values) +
        f" | {summary['pass rate']:.1%} |"
    )

md.extend(["", "## Case-by-Case Comparison", ""])

for index, case in enumerate(all_results["MARA"]["cases"], start=1):
    job = case["input"]["job_name"]

    md.extend([
        f"### Case {index}: {job}",
        "",
        "| Check | Score |",
        "|---|---:|",
    ])

    for check, score in case["scores"].items():
        md.append(f"| {check} | {score:.1%} |")

    md.extend([
        "",
        f"**Overall:** {'PASS' if case['passed'] else 'FAIL'}",
        "",
        "#### Golden Expected vs MARA Actual",
        "",
        "| Field | Expected | MARA Actual |",
        "|---|---|---|",
    ])

    expected = case["expected"]
    actual = case["actual"]

    for field in expected:
        expected_value = json.dumps(expected[field], ensure_ascii=False)
        actual_value = json.dumps(actual.get(field, "MISSING"), ensure_ascii=False)

        # Escape Markdown table characters and line breaks
        expected_value = expected_value.replace("|", "\\|").replace("\n", " ")
        actual_value = actual_value.replace("|", "\\|").replace("\n", " ")

        md.append(
            f"| {field} | {expected_value} | {actual_value} |"
        )

    md.append("")

md_path = output_dir / "tc4_step2_report.md"
md_path.write_text("\n".join(md), encoding="utf-8")

print(f"Evaluated {len(cases)} cases across 3 systems.")
print(f"JSON results: {json_path}")
print(f"Markdown report: {md_path}")