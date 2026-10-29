"""The server.

`gradio.Server` is a FastAPI app with Gradio's API engine bolted in. You get
queueing, streaming, and MCP for free, but you bring your own frontend. That
split is the point: the API is the product, the UI is disposable.
"""

import os
from pathlib import Path

from fastapi.responses import HTMLResponse
from gradio import Server

from llm import stream_reply
from schema import Request, solve, MAX_FAILURE_AGE_YEARS
from pydantic import ValidationError
from fastapi import HTTPException
from datetime import date
from dateutil.relativedelta import relativedelta

import json

from litellm import completion
from schema import Response

from retrieval import initialize_retrieval, retrieve_hybrid

app = Server()

# MARA TC3: Initialize retrieval once when the application starts.
# Reuse these objects for all incoming retrieval questions.
CHUNKS, BM25_INDEX, QDRANT_CLIENT, TEXT_EMBEDDER = initialize_retrieval()

FRONTEND = Path(__file__).parent / "frontend" / "index.html"


# --- The API -----------------------------------------------------------------
# The `-> str` return annotation is REQUIRED. Without it Gradio infers zero
# output components and silently returns nothing. Ask us how we know.


@app.api(name="chat")
def chat(message: str, history: list | None = None) -> str:
    """Stream a reply to one user message."""
    yield from stream_reply(message, history)

# MARA's new Gradio endpoint
@app.api(name="research_mainframe_batch_abend")
def research_mainframe_batch_abend(
    job_name: str,
    failure_date: str,
    abend_code: str,
    jes_messages: list[str] | None = None,
) -> str: # Required return annotation for this Gradio API and it returns a string
    """Research a mainframe batch job abend and return a structured investigation report."""

    # Validate incoming API parameters against MARA's Request schema.
    try:
        request = Request(
            job_name=job_name,
            failure_date=failure_date,
            abend_code=abend_code,
            jes_messages=jes_messages if jes_messages is not None else []
        )
    except ValidationError as exc:
        # Return a controlled validation error instead of a traceback.
        message = exc.errors()[0]["msg"]
        if message.startswith("Value error, "):
            message = message.removeprefix("Value error, ")
        raise HTTPException(status_code=422, detail=message) from exc

    # Run MARA's investigation using the validated request.
    report = solve(request)

    # Return the structured investigation report
    # Convert the validated Pydantic Response to a JSON string.
    return report.model_dump_json()

@app.api(name="research_mainframe_incident_history")
def research_mainframe_incident_history(question: str) -> str:
    """
    Research a mainframe batch incident question using historical evidence.
    Use this tool when investigating past mainframe batch failures, comparing
    incidents, or identifying evidence-supported upstream causes.

    Accepts a natural-language question about mainframe batch failures.
    Retrieves relevant historical incident records using hybrid search
    (BM25, dense embeddings, and reciprocal rank fusion).

    Returns a JSON-serialized MARA Response containing the investigation
    findings, recommended next steps, and supporting source record IDs.

    This endpoint is research-only. It does not execute or authorize
    production changes or job restarts. When evidence is insufficient,
    it returns INSUFFICIENT_EVIDENCE rather than inventing a root cause.
    """

    if question.strip() == "":
        raise HTTPException(
            status_code=422,
            detail="Question cannot be empty.",
        )

    # Retrieve supporting incident records.
    hits = retrieve_hybrid(
        query=question,
        chunks=CHUNKS,
        bm25=BM25_INDEX,
        client=QDRANT_CLIENT,
        embedder=TEXT_EMBEDDER,
    )

    # Prepare source IDs and evidence for Claude.
    retrieved_ids = [hit["id"] for hit in hits]

    evidence = []

    for hit in hits:
        evidence.append(
            f"Source [{hit['id']}]:\n{hit['content']}"
        )

    context = "\n\n".join(evidence)

    prompt = f"""
    You are MARA, a mainframe batch incident research assistant.

    Answer the user's question using ONLY the retrieved evidence.

    Question:
    {question}

    Retrieved evidence:
    {context}

    Rules:
    - Do not invent incidents, root causes, or diagnostic messages.
    - Cite supporting incident IDs in your findings.
    - Do not authorize or perform production recovery.
    - If the evidence is insufficient, decline to establish a root cause.
    - Return only valid JSON matching MARA's seven-field Response schema.

    Required JSON fields:
    failure_summary
    probable_root_cause
    evidence_and_historical_findings
    confidence_level
    recommended_next_steps
    investigation_status
    sources
    """

    response = completion(
        model=os.getenv("LLM_MODEL", "anthropic/claude-sonnet-5"),
        messages=[{"role": "user", "content": prompt}],
        max_tokens=2500,
        timeout=600,
    )

    answer_text = response.choices[0].message.content or ""

    # TEMPORARY DEBUG: Check why Claude stopped generating its response.
    finish_reason = response.choices[0].finish_reason

    print("MARA TC3 finish reason:", finish_reason, flush=True)
    print("MARA TC3 response length:", len(answer_text), flush=True)

    # Remove surrounding whitespace.
    answer_text = answer_text.strip()

    # Remove Markdown JSON code fences, if Claude includes them.
    if answer_text.startswith("```"):
        answer_text = answer_text.split("\n", 1)[1]
        answer_text = answer_text.rsplit("```", 1)[0].strip()

    # Convert the cleaned JSON string into a Python dictionary.
    response_data = json.loads(answer_text)

    # Accept only source IDs that were actually retrieved.
    response_data["sources"] = [
        source_id
        for source_id in response_data.get("sources", [])
        if source_id in retrieved_ids
    ]

    # MARA TC3: Enforce the expected response fields
    # when no evidence-supported root cause was established.
    if response_data.get("investigation_status") == "INSUFFICIENT_EVIDENCE":
        response_data["probable_root_cause"] = None
        response_data["confidence_level"] = "NOT_ASSESSED"
        response_data["sources"] = []

    report = Response.model_validate(response_data)

    return report.model_dump_json()

# --- The frontend ------------------------------------------------------------
# Defining a route at "/" replaces Gradio's default UI with ours.


@app.get("/", response_class=HTMLResponse)
def homepage() -> str:
    return FRONTEND.read_text(encoding="utf-8")


@app.get("/health")
def health() -> dict:
    """Your future ops team will thank you. Load balancers need this."""
    return {"status": "ok", "model": os.getenv("LLM_MODEL", "gpt-4.1-mini")}

@app.get("/config/date-validation")
def date_validation_config() -> dict:
    """Expose allowed failure dates to MARA's frontend."""
    today = date.today()
    earliest = today - relativedelta(years=MAX_FAILURE_AGE_YEARS)

    return {
        "min_date": earliest.isoformat(),
        "max_date": today.isoformat(),
        "max_age_years": MAX_FAILURE_AGE_YEARS,
    }


if __name__ == "__main__":
    # 0.0.0.0 so the container is reachable from the host. On your laptop this
    # is fine. On a firm network, "reachable from where, exactly?" is the
    # question this challenge wants you to go ask.
    #
    # Read the port rather than hardcoding it, so a machine that already has
    # something on 7860 can move this one without editing code.
    port = int(os.getenv("GRADIO_SERVER_PORT", "7860"))

    # Gradio announces the address it BOUND to, which is 0.0.0.0 -- not an
    # address a browser can open. Windows rejects it outright; macOS and Linux
    # quietly redirect it to localhost, which is why it looks fine on some
    # machines and broken on others. Print the one that always works.
    print(f"\n  Open http://localhost:{port} in your browser\n", flush=True)
    app.launch(server_name="0.0.0.0", server_port=port)
