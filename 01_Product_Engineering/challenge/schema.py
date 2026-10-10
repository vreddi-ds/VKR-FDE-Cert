from pydantic import BaseModel, Field
from datetime import date 
from typing import Literal 

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
        description="Evidence-supported probable root cause, or None if undetermined")

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
    raise NotImplementedError("MARA investigation logic will be implemented in TC1 Step 8")

## Use the below syntax to verify required fields in VS Code Terminal
## print(Request.model_fields["job_name"].is_required()) 
## Expected output TRUE/FALSE

## Basic response test...I can't ask the model every time, so documenting here for future use.
# uv run python -c "from schema import Response; r = Response(failure_summary='Synthetic job PAYAUT12 failed with S806', 
# probable_root_cause=None, confidence_level='NOT_ASSESSED', recommended_next_steps=['Escalate to SME'], 
# investigation_status='INSUFFICIENT_EVIDENCE'); print(r.model_dump_json(indent=2))"

## Need to test....
## When investigation_status is INSUFFICIENT_EVIDENCE:
## - probable_root_cause should be None.
## - confidence_level should be NOT_ASSESSED.
## - recommended_next_steps should include SME escalation.