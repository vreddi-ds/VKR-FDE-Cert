"""Test the remaining eight TC3 questions through MARA's API."""

import json
from pathlib import Path
from urllib.request import Request, urlopen

API_URL = (
    "http://localhost:7860/gradio_api/call/"
    "research_mainframe_incident_history"
)

EVAL_DIR = Path(__file__).resolve().parent
LABELS_PATH = EVAL_DIR / "retrieval.jsonl"
OUTPUT_PATH = EVAL_DIR / "tc3_step4_endpoint_results.json"


def submit_question(question: str) -> str:
    """Submit a question and return its Gradio event ID."""

    payload = json.dumps({"data": [question]}).encode("utf-8")

    request = Request(
        API_URL,
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    with urlopen(request, timeout=120) as response:
        event = json.load(response)

    return event["event_id"]


def get_answer(event_id: str) -> dict:
    """Read the completed investigation from Gradio's event stream."""

    event_url = f"{API_URL}/{event_id}"

    with urlopen(event_url, timeout=600) as response:
        for raw_line in response:
            line = raw_line.decode("utf-8").strip()

            if line == "event: error":
                raise RuntimeError("Gradio reported an endpoint error.")

            if line.startswith("data: "):
                data = json.loads(line.removeprefix("data: "))

                if isinstance(data, list):
                    return json.loads(data[0])

    raise RuntimeError("No completed investigation was returned.")


labels = []

with LABELS_PATH.open("r", encoding="utf-8") as file:
    for line in file:
        if line.strip():
            labels.append(json.loads(line))


results = []

for index, label in enumerate(labels, start=1):
    # # MARA-01 and MARA-07 were already tested manually.
    # if index in (1, 7):
    if index <= 4:
        continue

    case_id = f"MARA-{index:02d}"

    print(f"Testing {case_id}...", flush=True)

    event_id = submit_question(label["question"])
    report = get_answer(event_id)

    result = {
        "id": case_id,
        "question": label["question"],
        "response": report,
    }

    results.append(result)
    # Preserve each successful result immediately.
    OUTPUT_PATH.write_text(
        json.dumps(results, indent=2),
        encoding="utf-8",
    )

    print(
        f"{case_id}: "
        f"status={report['investigation_status']}, "
        f"sources={report['sources']}",
        flush=True,
    )

print(f"\nSaved {len(results)} investigations to {OUTPUT_PATH}")