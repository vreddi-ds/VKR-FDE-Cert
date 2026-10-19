
#!/usr/bin/env python3
"""Reorder MARA golden examples for the S4 difficulty ladder."""

import json
import shutil
from pathlib import Path

GOLDEN = Path("use_case/evals/golden.jsonl")
BACKUP = Path("use_case/evals/golden.jsonl.pre_s4")

FIRST_FIVE = [
    "PAYPOST21",   # 1. Plain
    "BATCHD13",   # 2. Detailed
    "BATCHD06",   # 3. Partial
    "BATCHD09",   # 4. Judgement
    "PAYBATCH45", # 5. Decline
]


def main():
    if not GOLDEN.is_file():
        raise SystemExit(f"File not found: {GOLDEN}")

    # Read the original lines without modifying JSON contents.
    lines = [
        line
        for line in GOLDEN.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]

    records = [json.loads(line) for line in lines]
    job_names = [record["input"]["job_name"] for record in records]

    # Safety checks before changing anything.
    if len(records) != 16:
        raise SystemExit(f"Expected 16 records, found {len(records)}.")

    if len(set(job_names)) != len(job_names):
        raise SystemExit("Duplicate job names found. File not modified.")

    missing = set(FIRST_FIVE) - set(job_names)
    if missing:
        raise SystemExit(f"Missing expected jobs: {sorted(missing)}")

    # Map each job to its complete, original JSONL line.
    by_job = dict(zip(job_names, lines))

    remaining = [
        job for job in job_names
        if job not in FIRST_FIVE
    ]

    new_order = FIRST_FIVE + remaining
    reordered_lines = [by_job[job] for job in new_order]

    # Create a backup before changing the original.
    if BACKUP.exists():
        raise SystemExit(
            f"Backup already exists: {BACKUP}. "
            "Refusing to overwrite it."
        )

    shutil.copy2(GOLDEN, BACKUP)

    GOLDEN.write_text(
        "\n".join(reordered_lines) + "\n",
        encoding="utf-8",
    )

    print(f"Reordered {len(records)} golden examples.")
    print(f"Backup: {BACKUP}")
    print("\nNew order:")

    for index, job in enumerate(new_order, start=1):
        print(f"{index:2}. {job}")


if __name__ == "__main__":
    main()
