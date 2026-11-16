
import argparse
import asyncio
import json
from pathlib import Path

from mara_utcp import measure_mara_run


async def main():
    parser = argparse.ArgumentParser(
        description="Run MARA A/B tests and save measurement results."
    )
    parser.add_argument(
    "--implementation",
    choices=["A", "B", "both"],
    default="both",
)
    parser.add_argument(
        "--question",
        default="Why did INVUPD77 fail with S0C7?",
    )
    # parser.add_argument(
    #     "--output",
    #     required=True,
    # )
    parser.add_argument(
    "--output-dir",
    default="05_Agent_Architecture/challenge/results",
    )

    parser.add_argument(
        "--run-name",
        default="INVUPD77_source_trace",
    )

    args = parser.parse_args()

    implementations = (
        ["A", "B"]
        if args.implementation == "both"
        else [args.implementation]
    )

    output_dir = Path(args.output_dir)

    # Prepare one output filename per selected implementation.
    output_files = {
        implementation: output_dir / f"{implementation}_{args.run_name}.json"
        for implementation in implementations
    }

    # Validate every output filename before any paid model calls.
    for output in output_files.values():
        if output.exists():
            parser.error(
                f"Output already exists: {output}. "
                "Choose a different --run-name."
            )

    output_dir.mkdir(parents=True, exist_ok=True)

    # Run selected implementations sequentially.
    for implementation in implementations:
        print(f"\nRunning Implementation {implementation}...", flush=True)

        result = await measure_mara_run(
            question=args.question,
            implementation=implementation,
        )

        output = output_files[implementation]

        # Create a new file; never overwrite an existing result.
        with output.open("x", encoding="utf-8") as file:
            json.dump(result, file, indent=2)

        print(f"Saved: {output}")
        print(f"Implementation: {implementation}")
        print(f"Capability calls: {result['capability_calls']}")
        print(f"Raw reports: {len(result['raw_reports'])}")
        print(f"Tool messages: {len(result['tool_messages'])}")
        print(f"Combined tokens: {result['combined_tokens']}")

        for index, report in enumerate(result["raw_reports"], start=1):
            print(
                f"Report {index} supporting source IDs: "
                f"{report.get('sources', [])}"
            )

    print("\nSelected A/B tests completed.")



if __name__ == "__main__":
    asyncio.run(main())
