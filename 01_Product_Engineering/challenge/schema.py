import json
from datetime import date
from typing import Literal

from pydantic import BaseModel, Field, field_validator
from llm import stream_reply
from dateutil.relativedelta import relativedelta
import re

# MARA configuration
#
# Maximum age (in calendar years) allowed for the CURRENT job failure date.
# This is a provisional prototype business rule, initially set to 5 years.
#
# In production, this value should come from approved business requirements
# and potentially be loaded from an environment/configuration file.
#
# IMPORTANT:
# This restriction applies only to the incoming Request.failure_date.
# It does NOT limit how far back MARA can search historical incident records.
MAX_FAILURE_AGE_YEARS = 5

class Request(BaseModel):
    job_name: str = Field(
        min_length=1,
        max_length=8,
        description="Mainframe batch job name, maximum 8 characters"
    )
    failure_date: date = Field(description="Date of the current job failure")
    abend_code: str = Field(
        min_length=1,
        max_length=5,
        description="Mainframe abend code, maximum 5 characters"
    )
    jes_messages: list[str] = Field(
        default_factory=list,
        description="Optional JES error messages"
    )

    @field_validator("failure_date")
    @classmethod
    def validate_failure_date(cls, value: date) -> date:
        today = date.today()

        # Reject future dates because MARA investigates actual failures.
        if value > today:
            raise ValueError("Failure date cannot be in the future.")

        # Apply MARA's configured maximum age for the current failure.
        # Calendar-year subtraction handles leap years correctly.
        earliest_allowed = today - relativedelta(
            years=MAX_FAILURE_AGE_YEARS
        )

        if value < earliest_allowed:
            raise ValueError(
                f"Failure date cannot be more than "
                f"{MAX_FAILURE_AGE_YEARS} years old."
            )

        return value

    @field_validator("abend_code")
    @classmethod
    def validate_abend_code(cls, value: str) -> str:
        # Normalize the abend code to uppercase.
        code = value.strip().upper()

        # System abend: S followed by 1–4 hexadecimal characters.
        if code.startswith("S"):
            if re.fullmatch(r"S[0-9A-F]{1,4}", code) is None:
                raise ValueError(
                    "System abend code must be S followed by 1–4 hexadecimal characters."
                )
            return code

        # User abend: U followed by exactly four digits.
        if code.startswith("U"):
            if re.fullmatch(r"U[0-9]{4}", code) is None:
                raise ValueError(
                    "User abend code must be U followed by 4 digits."
                )
            return code

        raise ValueError("Abend Code must start with S or U.")


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

    # Required field
    sources: list[str] = Field(
        description="IDs of retrieved records used to support the investigation"
    )
        # COMPLETED_RESEARCH means MARA finished examining available evidence.
        # It does not mean the batch job has been recovered.
        # Insufficeint_Evidence == MARA could not establish an evidence-supported probable cause

def build_mara_prompt(request: Request) -> str:
    """Build the investigation prompt used by MARA."""
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
    8. Only cite record IDs that were actually retrieved and supplied as evidence.
       Never invent historical incident IDs or source references.

    Known Mainframe System Abend Definitions:
    - S0C7: Data Exception. Often caused by invalid decimal numeric data during arithmetic processing.
    - S806: Program/load module could not be located or loaded.
    - S322: CPU time limit exceeded.

    Use these definitions when interpreting the listed abend codes.
    Do not treat an abend-code definition as proof of the specific job's root cause.
    If diagnostic evidence is insufficient, report INSUFFICIENT_EVIDENCE.


    Output Requirements:
    Return only a valid JSON object containing these seven fields:
    - failure_summary: string
    - probable_root_cause: string or null
    - evidence_and_historical_findings: list of strings
    - confidence_level: HIGH, MEDIUM, LOW, or NOT_ASSESSED
    - recommended_next_steps: non-empty list of strings
    - investigation_status: COMPLETED_RESEARCH or INSUFFICIENT_EVIDENCE
    - sources: list of retrieved record IDs used to support the investigation; [] if none were retrieved

    Only include record IDs that were actually retrieved and provided as evidence.
    Never invent source IDs.

    When investigation_status is INSUFFICIENT_EVIDENCE:
    - Set probable_root_cause to null.
    - Set confidence_level to NOT_ASSESSED.
    - Set investigation_status to INSUFFICIENT_EVIDENCE.
    - Recommend collecting missing evidence and escalation when needed.

    Return valid JSON only.
    Do not include Markdown formatting or explanations outside the JSON.
    """
    return prompt

def solve(request: Request) -> Response:
    """Investigate a mainframe batch job failure and return a structured research report."""

    prompt = build_mara_prompt(request)

    #raise NotImplementedError("MARA investigation logic will be implemented in TC1 Step 8")

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

    # No historical records are retrieved in the current implementation.
    # Do not accept unverified source IDs from the LLM.
    response_data["sources"] = []

    # Validate the LLM output against MARA's seven-field Response schema.
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