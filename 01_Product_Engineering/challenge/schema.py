import json
from datetime import date
from typing import Literal

from pydantic import BaseModel, Field
from llm import stream_reply


class Request(BaseModel):
    job_name: str = Field(description="Failed Job Name")
    failure_date: date = Field(description="Job failed date")
    abend_code: str = Field(description="Job abend code")
    jes_messages: list[str] = Field(
        default_factory=list,
        description="Optional JES error messages"
    )

class Response(BaseModel):
    # Required field & must provide a value
    failure_summary: str = Field(
        description="Brief summary of the mainframe batch job failure"
    )

    # Optional field and allows None vlaue
    probable_root_cause: str | None = Field(
        default=None, # MARA to return None, when the investigation status is INSUFFICIENT_EVIDENCE, rather than inventing a cause
        description="Evidence-supported probable root cause, or None if undetermined"
    )

    # Optional field
    evidence_and_historical_findings: list[str] = Field(
        default_factory=list, #An empty list when no evidence
        description="Supporting JES messages, runbook references, knowledge base articles and historical incidents"
    )

    # Required field
    confidence_level: Literal[
        "HIGH",         # Strong, consistent supporting evidence
        "MEDIUM",       # Relevanr evidence exists, but uncertainty remains
        "LOW",          # Limited evidence supports a tentative cause
        "NOT_ASSESSED"  # No evidence-supported probable cause established
    ] = Field(
            description="Strength of evidence suppporting the probable root cause",
        )

    # Required field
    recommended_next_steps: list[str] = Field(
        min_length=1,
        description="Recommended investigation, recovery verification, or SME escalation"
    )
    # min_length=1, ensures the response contains at least one recommendation

    # Required field
    investigation_status: Literal[
        "COMPLETED_RESEARCH",
        "INSUFFICIENT_EVIDENCE"
    ] = Field(
            description="Outcome of MARA's evidence-based investigation"
        )
        # COMPLETED_RESEARCH means MARA finished examining available evidence.
        # It does not mean the batch job has been recovered.
        # Insufficeint_Evidence == MARA could not establish an evidence-supported probable cause

def solve(request: Request) -> Response:
    """Investigate a mainframe batch job failure and return a structured research report."""
    #raise NotImplementedError("MARA investigation logic will be implemented in TC1 Step 8")

# MARA Prompt Design Notes:
    # 1. Evidence grounding: Prevent the LLM from inventing root causes.
    # 2. Safety: MARA recommends actions but never executes recovery.
    # 3. Insufficient evidence: Return null instead of guessing.
    # 4. Structured output: Match the Pydantic Response schema.
    # 5. Escalation: Keep recovery decisions with authorized personnel.

    prompt = f"""
    You are MARA, a Mainframe Batch Abend Research Assistant.

    Investigate the following mainframe batch job failure.

    Job Name: {request.job_name}
    Failure Date: {request.failure_date}
    Abend Code: {request.abend_code}
    JES Messages: {request.jes_messages}

    Investigation Rules:
    1. Analyze the supplied JES messages and abend code.
    2. Identify a probable root cause only when supported by evidence.
    3. Do not invent JES messages, JCL details, runbooks, or historical incidents.
    4. If the evidence is insufficient, do not guess the root cause.
    5. Recommend safe investigation steps and SME escalation when appropriate.
    6. Do not perform or authorize production changes or job restarts.
    7. Distinguish the established technical meaning of an abend code from the root cause of this specific job failure.
       Do not invent abend-code definitions. If uncertain about an abend code's meaning, explicitly state the uncertainty.

    Known Mainframe System Abend Definitions:
    - S0C7: Data Exception. Often caused by invalid decimal numeric data during arithmetic processing.
    - S806: Program/load module could not be located or loaded.
    - S322: CPU time limit exceeded.

    Use these definitions when interpreting the listed abend codes.
    Do not treat an abend-code definition as proof of the specific job's root cause.
    If diagnostic evidence is insufficient, report INSUFFICIENT_EVIDENCE.


    Output Requirements:
    Return only a valid JSON object containing these six fields:
    - failure_summary: string
    - probable_root_cause: string or null
    - evidence_and_historical_findings: list of strings
    - confidence_level: HIGH, MEDIUM, LOW, or NOT_ASSESSED
    - recommended_next_steps: non-empty list of strings
    - investigation_status: COMPLETED_RESEARCH or INSUFFICIENT_EVIDENCE

    When investigation_status is INSUFFICIENT_EVIDENCE:
    - Set probable_root_cause to null.
    - Set confidence_level to NOT_ASSESSED.
    - Set investigation_status to INSUFFICIENT_EVIDENCE.
    - Recommend collecting missing evidence and escalation when needed.

    Return valid JSON only.
    Do not include Markdown formatting or explanations outside the JSON.
    """

    # Send the MARA investigation prompt to the LLM.
    # stream_reply() yields progressively longer response strings.
    # Keep the most recent value, which contains the complete response.
    llm_response = "" # Creates an empty strig to hold the LLM response

    for reply in stream_reply(prompt): #Sending the above prompt to the configured LLM and receiving the generated response as model streams
        llm_response = reply           #Saves the latest accumulated response

    # Convert the LLM-generated JSON text into a Python dictionary.
    # TEMPORARY DEBUG: Inspect Claude's response before JSON parsing.
    # print("MARA LLM response:", repr(llm_response))

    # Remove Markdown JSON code fences if the LLM includes them.
    llm_response = llm_response.strip()

    if llm_response.startswith("```"):
        llm_response = llm_response.split("\n", 1)[1]
        llm_response = llm_response.rsplit("```", 1)[0].strip()

    response_data = json.loads(llm_response)

    # Validate the LLM output against MARA's six-field Response schema.
    validated_response = Response.model_validate(response_data) # model_validate() is being inherited from base model

    # Return the validated investigation report.
    return validated_response

## Use the below syntax to verify required fields in VS Code Terminal
## print(Request.model_fields["job_name"].is_required())
## Expected output TRUE/FALSE

## Request class test...
#1. uv run python -c "from schema import Request; print(Request.model_json_schema())" - schema test to make sure Pydantic recorgnized
# the input fields.
#2. uv run python -c "from schema import Request; r = Request(job_name='PAYAUT12', failure_date='2026-10-10', abend_code='S806');
# print(r.model_dump_json(indent=2))" - Positive validation: supplied three required fields and omitted the optional filed.
#3. uv run python -c "from schema import Request; Request(job_name='PAYAUT12')" - supplied only one required field. Pydantic notfied
# about missing required fields.

## Response class test...I can't ask the model every time, so documenting here for future use.
#1. JSON Schema validation: uv run python -c "import json; from schema import Response; print(json.dumps(Response.model_json_schema(), indent=2))"

#2. +ve Response validation: uv run python -c "from schema import Response; r = Response(failure_summary='Synthetic job PAYAUT12 failed with S806',
# probable_root_cause=None, confidence_level='NOT_ASSESSED', recommended_next_steps=['Escalate to SME'],
# investigation_status='INSUFFICIENT_EVIDENCE'); print(r.model_dump_json(indent=2))"

#3. -Ve test: to raise a validation error when in violation with contract field requirements like min_length or zero items etc.,
# uv run python -c "from schema import Response; Response(failure_summary='Synthetic job failure', confidence_level='HIGH',
# recommended_next_steps=[], investigation_status='COMPLETED_RESEARCH')"

## Need to test....
## When investigation_status is INSUFFICIENT_EVIDENCE:
## - probable_root_cause should be None.
## - confidence_level should be NOT_ASSESSED.
## - recommended_next_steps should include SME escalation.

## Module Import test: to confirm that the module could be imported
# uv run python -c "import schema"
#