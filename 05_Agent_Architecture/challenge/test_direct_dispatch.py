import asyncio
import json
from types import SimpleNamespace
from unittest.mock import patch

from mara_utcp import (
    DirectCapabilityCounter,
    dispatch_direct_mara,
)


async def fake_research(question: str) -> str:
    """Return a synthetic MARA investigation."""
    return json.dumps({
        "failure_summary": "Synthetic test result",
    })


async def main():
    """Verify direct dispatch and capability counting."""
    counter = DirectCapabilityCounter()

    call = SimpleNamespace(
        function=SimpleNamespace(
            name="research_mara",
            arguments=json.dumps({
                "question": "Why did TESTJOB fail?"
            }),
        )
    )

    with patch("mara_utcp.research_mara", fake_research):
        result = await dispatch_direct_mara(
            call,
            counter=counter,
        )

    decoded = json.loads(result)

    print("Status:", decoded["status"])
    print("Capability calls:", counter.calls)

    passed = (
        decoded["status"] == "success"
        and counter.calls == 1
    )

    print("RESULT:", "PASS" if passed else "FAIL")


if __name__ == "__main__":
    asyncio.run(main())