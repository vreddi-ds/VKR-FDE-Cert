import asyncio
import json

from fastmcp import Client

from mara_utcp import (
    MARA_INTERNAL_USAGE,
    MARA_TOOL_SPEC,
    mara_adapter_client,
)
from fastmcp import FastMCP


async def fake_research(question: str) -> str:
    """Return a synthetic investigation and record fake token usage."""
    measurements = MARA_INTERNAL_USAGE.get()

    if measurements is not None:
        measurements.append({
            "input_tokens": 100,
            "output_tokens": 50,
            "total_tokens": 150,
        })

    return json.dumps({
        "failure_summary": "Synthetic test result",
    })


async def main():
    """Verify collector propagation through the FastMCP tool path."""
    internal_usage = []
    token = MARA_INTERNAL_USAGE.set(internal_usage)

    try:
        server = FastMCP.from_openapi(
            MARA_TOOL_SPEC,
            client=mara_adapter_client(fake_research),
            name="mara",
        )

        async with Client(server) as client:
            result = await client.call_tool(
                "research_mara",
                {"question": "Synthetic test question"},
            )

        print("Tool error:", result.is_error)
        print("Internal usage:", internal_usage)

        passed = (
            not result.is_error
            and len(internal_usage) == 1
            and internal_usage[0]["total_tokens"] == 150
        )

        print("RESULT:", "PASS" if passed else "FAIL")

    finally:
        MARA_INTERNAL_USAGE.reset(token)


if __name__ == "__main__":
    asyncio.run(main())