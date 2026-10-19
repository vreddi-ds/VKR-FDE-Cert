
import json
import shutil
from pathlib import Path

source = Path("use_case/evals/golden.jsonl")
heldout = Path("use_case/evals/heldout_backtest.jsonl")
backup = Path("use_case/evals/golden.jsonl.pre_split")

rows = [
    json.loads(line)
    for line in source.read_text(encoding="utf-8").splitlines()
    if line.strip()
]

assert len(rows) == 16, f"Expected 16 rows, found {len(rows)}"
assert not heldout.exists(), "Held-out file already exists"
assert not backup.exists(), "Backup already exists"

# Preserve original dataset.
shutil.copy2(source, backup)

generation = rows[:8]
backtest = rows[8:]

# Replace BATCHD12 with an independent decline example.
decline = {
    "input": {
        "job_name": "BATCHD19",
        "failure_date": "2026-10-18",
        "abend_code": "S0C7",
        "jes_messages": []
    },
    "output": {
        "failure_summary": (
            "Batch job BATCHD19 was reported to have failed with S0C7. "
            "No JES or application diagnostics were supplied."
        ),
        "probable_root_cause": None,
        "evidence_and_historical_findings": [
            "The supplied information identifies the job, date, and S0C7 code.",
            "No diagnostic evidence identifies the failing step, program, file, field, or record.",
            "The specific root cause cannot be established."
        ],
        "confidence_level": "NOT_ASSESSED",
        "recommended_next_steps": [
            "Obtain the JES output and relevant application diagnostics.",
            "Identify the failed step and program before investigating a specific data defect.",
            "Escalate to the responsible application SME if diagnostics remain unavailable.",
            "Do not recommend a data correction or production restart without supporting evidence and authorization."
        ],
        "investigation_status": "INSUFFICIENT_EVIDENCE"
    },
    "why": (
        "This independently authored synthetic decline case tests whether MARA "
        "refuses to identify a specific root cause when S0C7 is reported "
        "without supporting diagnostic evidence."
    )
}

replaced = False
for i, row in enumerate(backtest):
    if row["input"]["job_name"] == "BATCHD12":
        backtest[i] = decline
        replaced = True
        break

assert replaced, "BATCHD12 not found in held-out records"

def save(path, records):
    path.write_text(
        "".join(json.dumps(r, ensure_ascii=False) + "\n" for r in records),
        encoding="utf-8"
    )

save(source, generation)
save(heldout, backtest)

assert len(generation) == len(backtest) == 8
assert not (
    {r["input"]["job_name"] for r in generation}
    & {r["input"]["job_name"] for r in backtest}
)

print("PASS: 8 generation seeds in golden.jsonl")
print("PASS: 8 held-out backtesting records")
print("PASS: BATCHD12 replaced by synthetic decline case BATCHD19")
print("PASS: No duplicate job names across datasets")
print("Backup:", backup)
