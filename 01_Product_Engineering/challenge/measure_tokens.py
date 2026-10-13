import os
from schema import Request, build_mara_prompt
from litellm import completion
from llm import build_messages

# Synthetic S0C7 example
job_name = "PAYPOST21"
failure_date = "2026-10-10"
abend_code = "S0C7"
jes_messages = [
    "Synthetic JES diagnostic: Job PAYPOST21 failed with S0C7 in STEP030, program PAYPOSTPG.",
    "Synthetic application diagnostic: Input file PAY.INPUT.DAILY, record position 142, field PAYMENT_AMOUNT, invalid value 12A45."
]

print("Model:", os.environ["LLM_MODEL"])
print("Measurement setup ready")

# Build the same request used by MARA.
request = Request(
    job_name=job_name,
    failure_date=failure_date,
    abend_code=abend_code,
    jes_messages=jes_messages,
)

# Reuse MARA's actual investigation prompt and system message.
prompt = build_mara_prompt(request)
messages = build_messages(prompt)

print("MARA prompt prepared for token measurement.")

# Run one non-streaming Claude API call to capture token usage.
response = completion(
    model=os.environ["LLM_MODEL"],
    messages=messages,
    stream=False,
)

# Read usage metadata without displaying investigation content.
usage = response.usage

print("Input tokens:", usage.prompt_tokens)
print("Output tokens:", usage.completion_tokens)
print("Total tokens:", usage.total_tokens)