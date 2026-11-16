import os
import json
import httpx
import logging
import litellm
import time

from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.routing import Route
from contextvars import ContextVar

from fastmcp import Client, FastMCP
from fastmcp.server.middleware import Middleware
from helpers import nb

logger = logging.getLogger(__name__)

CFG = nb.bootstrap()

# Collect internal MARA token usage for the current invocation.
MARA_INTERNAL_USAGE = ContextVar(
    "mara_internal_usage",
    default=None,
)

MARA_RAW_REPORTS = ContextVar(
    "mara_raw_reports",
    default=None,
)

MARA_TOOL_MESSAGES = ContextVar(
    "mara_tool_messages",
    default=None,
)

MARA_BASE_URL = os.getenv(
    "MARA_BASE_URL",
    "http://127.0.0.1:7860",
)

MARA_RESEARCH_PATH = "/gradio_api/call/v2/research_mainframe_incident_history"

MARA_TOOL_SPEC = {
    "openapi": "3.1.0",
    "info": {
        "title": "MARA Research API",
        "version": "1.0.0",
    },
    "paths": {
        "/research": {
            "post": {
                "operationId": "research_mara",
                "summary": (
                    "Research a mainframe batch incident using "
                    "MARA's evidence-grounded incident history."
                ),
                "requestBody": {
                    "required": True,
                    "content": {
                        "application/json": {
                            "schema": {
                                "type": "object",
                                "properties": {
                                    "question": {
                                        "type": "string",
                                        "description": (
                                            "Mainframe incident question "
                                            "to investigate."
                                        ),
                                    }
                                },
                                "required": ["question"],
                            }
                        }
                    },
                },
                "responses": {
                    "200": {
                        "description": "MARA research result",
                        "content": {
                            "application/json": {
                                "schema": {"type": "object"}
                            }
                        },
                    }
                },
            }
        }
    },
}
MARA_DIRECT_TOOL = {
    "type": "function",
    "function": {
        "name": "research_mara",
        "description": (
            "Research a mainframe batch incident using MARA "
            "and return an evidence-grounded investigation report."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "question": {
                    "type": "string",
                    "description": (
                        "The mainframe incident question to investigate."
                    ),
                }
            },
            "required": ["question"],
            "additionalProperties": False,
        },
    },
}

class Meter:
    """Track outer Claude model calls and token usage."""

    def __init__(self):
        """Initialize model call and token counters."""
        self.calls = 0
        self.input_tokens = 0
        self.output_tokens = 0
        self.tokens = 0
        self.first_turn_tool_calls = 0

    def track(self, response):
        """Record token usage from one Claude model response."""
        self.calls += 1

        usage = getattr(response, "usage", None)

        if usage is not None:
            self.input_tokens += (
                getattr(usage, "prompt_tokens", 0) or 0
            )
            self.output_tokens += (
                getattr(usage, "completion_tokens", 0) or 0
            )
            self.tokens += (
                getattr(usage, "total_tokens", 0) or 0
            )

class DirectCapabilityCounter:
    """Count direct MARA capability invocations."""

    def __init__(self):
        """Initialize the capability call counter."""
        self.calls = 0

async def dispatch_direct_mara(
    call,
    counter=None
) -> str:
    """
    Execute a Claude tool call directly through MARA's capability.

    Args:
        call: Tool call returned by the outer Claude agent.
        counter: Optional tracker for direct capability calls.

    Returns:
        str: JSON-encoded tool result or structured error.
    """
    try:
        arguments = json.loads(call.function.arguments)
    except (json.JSONDecodeError, TypeError):
        arguments = None

    if counter is not None and call.function.name == "research_mara":
        counter.calls += 1

    result = await dispatch_mara_tool(
        tool_name=call.function.name,
        arguments=arguments,
        capability=research_mara,
    )

    return json.dumps(result)

class CapabilityCounter(Middleware):
    """
    Count calls to a specific tool through FastMCP middleware.

    This counter is used by Implementation A.
    """

    def __init__(self, tool_name: str):
        """
        Initialize the capability counter.

        Args:
            tool_name: Name of the tool to count.
        """
        self.tool_name = tool_name
        self.calls = 0

    async def on_call_tool(self, context, call_next):
        """
        Count matching tool calls and continue tool execution.

        Args:
            context: FastMCP context containing the tool call.
            call_next: Function that executes the next middleware
                or the requested tool.

        Returns:
            Result of the tool execution.
        """
        if context.message.name.endswith(self.tool_name):
            self.calls += 1

        return await call_next(context)

def mara_http_client() -> httpx.AsyncClient:
    """
    Create an asynchronous HTTP client for MARA's API.

    Returns:
        httpx.AsyncClient: A client configured with MARA's base URL
        and request timeout.
    """
    return httpx.AsyncClient(
        base_url=MARA_BASE_URL,
        timeout=600.0,
    )

async def research_mara(question: str) -> str:
    """
    Send a question to MARA's existing research API.

    Submit the question using HTTP POST, retrieve the event ID,
    and read the completed research report from the SSE stream.

    Args:
        question (str): The mainframe incident question to investigate.

    Returns:
        str: MARA's completed research report as a JSON string.

    Raises:
        httpx.HTTPStatusError: If an HTTP request fails.
        RuntimeError: If MARA returns an error or no completed result.
    """
    async with mara_http_client() as client:
        response = await client.post(
            MARA_RESEARCH_PATH,
            json={
                "question": question,
                "include_usage": True
            },
        )
        response.raise_for_status()

        event_id = response.json()["event_id"]

        result_path = (
            "/gradio_api/call/"
            f"research_mainframe_incident_history/{event_id}"
        )

        async with client.stream("GET", result_path) as result:
            result.raise_for_status()

            event_type = None

            async for line in result.aiter_lines():
                if line.startswith("event:"):
                    event_type = line.removeprefix("event:").strip()

                elif line.startswith("data:"):
                    data = line.removeprefix("data:").strip()

                    if event_type == "complete":
                        payload = json.loads(data)[0]
                        envelope = json.loads(payload)

                        report = envelope["report"]
                        usage = envelope["usage"]

                        # Serialize the MARA report once for measurement and return.
                        report_json = json.dumps(report)

                        # Capture the complete structured report for this test run.
                        raw_reports = MARA_RAW_REPORTS.get()

                        if raw_reports is not None:
                            raw_reports.append(report.copy())

                        # Measure the report payload in UTF-8 bytes.
                        capability_response_bytes = len(report_json.encode("utf-8"))

                        # Collect internal token usage from this MARA invocation.
                        measurements = MARA_INTERNAL_USAGE.get()

                        if measurements is not None:
                            measurements.append({
                                **usage,
                                "capability_response_bytes": capability_response_bytes,
                            })

                        # Return the same report payload to the outer agent.
                        return report_json

                    if event_type == "error":
                        raise RuntimeError(
                            f"MARA research failed: {data}"
                        )

    raise RuntimeError("MARA returned no completed research result.")


async def dispatch_mara_tool(
    tool_name: str,
    arguments: dict,
    capability=research_mara,
) -> dict:
    """
    Validate and execute a MARA research tool request.

    Args:
        tool_name (str): Name of the requested tool.
        arguments (dict): Arguments supplied by the model.
        capability: Research function to execute.

    Returns:
        dict: A success result or a structured error message.
    """
    if tool_name != "research_mara":
        return {
            "status": "error",
            "error_type": "UNKNOWN_TOOL",
            "message": f"Unknown tool: {tool_name}",
        }

    if (
        not isinstance(arguments, dict)
        or not isinstance(arguments.get("question"), str)
        or not arguments["question"].strip()
    ):
        return {
            "status": "error",
            "error_type": "INVALID_ARGUMENTS",
            "message": "A non-empty string 'question' is required.",
        }

    try:
        report = await capability(arguments["question"])
        return {
            "status": "success",
            "result": report,
        }

    except Exception:
        logger.exception("MARA capability execution failed")
        return {
            "status": "error",
            "error_type": "CAPABILITY_FAILURE",
            "message": "MARA could not complete the research request.",
        }

async def call_with_mara_direct(
    question: str,
    meter=None,
    counter=None,
) -> dict:
    """
    Run MARA research through direct Python tool calling.

    Collect internal MARA token usage during the same invocation.

    Args:
        question: Mainframe incident question to investigate.
        meter: Optional tracker for outer Claude model usage.
        counter: Optional tracker for direct capability calls.

    Returns:
        dict: Final agent answer and internal MARA usage records.
    """
    internal_usage = []
    token = MARA_INTERNAL_USAGE.set(internal_usage)

    # Collect complete MARA reports during this direct agent run.
    raw_reports = []
    report_token = MARA_RAW_REPORTS.set(raw_reports)

    # Collect tool messages forwarded to outer Claude.
    tool_messages = []
    tool_token = MARA_TOOL_MESSAGES.set(tool_messages)

    if counter is None:
        counter = DirectCapabilityCounter()

    async def direct_dispatch(call) -> str:
        """Execute one direct tool call using the shared counter."""
        return await dispatch_direct_mara(
            call,
            counter=counter,
        )

    try:
        answer = await run_agent(
            client=None,
            question=question,
            meter=meter,
            tool_dispatcher=direct_dispatch,
            tool_definitions=[MARA_DIRECT_TOOL],
        )

        return {
            "answer": answer,
            "internal_usage": internal_usage,
            "raw_reports": raw_reports,
            "tool_messages": tool_messages,
        }

    finally:
        MARA_INTERNAL_USAGE.reset(token)
        MARA_RAW_REPORTS.reset(report_token)
        MARA_TOOL_MESSAGES.reset(tool_token)

async def measure_mara_run(question: str, implementation: str) -> dict:
    """
    Execute one MARA investigation and collect A/B measurements.

    Args:
        question: Mainframe incident question to investigate.
        implementation: "A" for FastMCP or "B" for direct Python.

    Returns:
        dict: Agent answer and measurements from the same invocation.
    """
    meter = Meter()

    if implementation == "A":
        counter = CapabilityCounter("research_mara")
        runner = call_with_mara_utcp
    elif implementation == "B":
        counter = DirectCapabilityCounter()
        runner = call_with_mara_direct
    else:
        raise ValueError("Implementation must be 'A' or 'B'.")

    start = time.perf_counter()

    result = await runner(
        question=question,
        meter=meter,
        counter=counter,
    )

    elapsed = time.perf_counter() - start
    internal_usage = result["internal_usage"]

    capability_response_bytes = sum(
    record.get("capability_response_bytes") or 0
    for record in internal_usage
    )

    internal_input = sum(
        record.get("input_tokens") or 0
        for record in internal_usage
    )
    internal_output = sum(
        record.get("output_tokens") or 0
        for record in internal_usage
    )

    return {
        "implementation": implementation,
        "question": question,
        "answer": result["answer"],
        "raw_reports": result["raw_reports"],
        "tool_messages": result["tool_messages"],
        "outer_model_calls": meter.calls,
        "internal_model_calls": len(internal_usage),
        "capability_calls": counter.calls,
        "first_turn_tool_calls": meter.first_turn_tool_calls,
        "outer_input_tokens": meter.input_tokens,
        "outer_output_tokens": meter.output_tokens,
        "internal_input_tokens": internal_input,
        "internal_output_tokens": internal_output,
        "combined_tokens": meter.tokens + sum(
            record.get("total_tokens") or 0
            for record in internal_usage
        ),
        "wall_time_seconds": round(elapsed, 2),
        "answer_bytes": len(result["answer"].encode("utf-8")),
        "capability_response_bytes": capability_response_bytes,
    }

def mara_adapter(capability=research_mara) -> Starlette:
    """
    Create an HTTP adapter for MARA's research capability.

    Expose POST /research through an in-process ASGI application.
    Validate requests using the safe dispatcher and return JSON
    responses without starting another HTTP server.

    Args:
        capability: Async research function to execute.

    Returns:
        Starlette: Application exposing the research route.
    """

    async def handle_research(request: Request) -> JSONResponse:
        """
        Process an HTTP research request through MARA's dispatcher.

        Args:
            request (Request): Incoming HTTP request.

        Returns:
            JSONResponse: Research result or structured error.
        """
        try:
            arguments = await request.json()
        except ValueError:
            arguments = None

        result = await dispatch_mara_tool(
            tool_name="research_mara",
            arguments=arguments,
            capability=capability,
        )

        status_code = 200 if result["status"] == "success" else 400

        return JSONResponse(
            content=result,
            status_code=status_code,
        )

    return Starlette(
        routes=[
            Route("/research", handle_research, methods=["POST"])
        ]
    )

def mara_adapter_client(capability=research_mara) -> httpx.AsyncClient:
    """
    Create an HTTP client for MARA's in-process adapter.

    Args:
        capability: Async research function used by the adapter.

    Returns:
        httpx.AsyncClient: Client connected to the Starlette adapter.
    """
    return httpx.AsyncClient(
        transport=httpx.ASGITransport(
            app=mara_adapter(capability)
        ),
        base_url="http://mara-adapter.internal",
        timeout=600.0,
    )

# async def call_with_mara_utcp(
#     question: str,
#     capability=research_mara,
#     meter=None,
#     counter=None,
# ) -> dict:
#     """
#     Run a MARA research question through OpenAPI-generated tools.

#     Args:
#         question: Mainframe incident question from the user.
#         capability: Async research function to execute.
#         meter: Optional model usage tracker.
#         counter: Optional capability-call counter.

#     Returns:
#         dict: Agent's answer.
#     """
#     described = FastMCP.from_openapi(
#         MARA_TOOL_SPEC,
#         client=mara_adapter_client(capability),
#         name="mara",
#     )

#     if counter:
#         described.add_middleware(counter)

#     async with Client(described) as described_client:
#         answer = await run_agent(
#             described_client,
#             question,
#             meter,
#         )

#     return {"answer": answer}
async def call_with_mara_utcp(
    question: str,
    capability=research_mara,
    meter=None,
    counter=None,
) -> dict:
    """
    Run a MARA research question through OpenAPI-generated tools.

    Collect internal MARA token usage during the same invocation.
    """
    internal_usage = []
    token = MARA_INTERNAL_USAGE.set(internal_usage)

    # Collect complete MARA reports during this agent run.
    raw_reports = []
    report_token = MARA_RAW_REPORTS.set(raw_reports)

    # Collect tool messages forwarded to outer Claude.
    tool_messages = []
    tool_token = MARA_TOOL_MESSAGES.set(tool_messages)

    try:
        described = FastMCP.from_openapi(
            MARA_TOOL_SPEC,
            client=mara_adapter_client(capability),
            name="mara",
        )

        if counter:
            described.add_middleware(counter)

        async with Client(described) as described_client:
            answer = await run_agent(
                described_client,
                question,
                meter,
            )

        return {
            "answer": answer,
            "internal_usage": internal_usage,
            "raw_reports": raw_reports,
            "tool_messages": tool_messages,
        }

    finally:
        MARA_INTERNAL_USAGE.reset(token)
        MARA_RAW_REPORTS.reset(report_token)
        MARA_TOOL_MESSAGES.reset(tool_token)

def openai_tools(mcp_tools) -> list[dict]:
    """
    Convert MCP tool definitions into the format expected
    by the OpenAI-compatible chat completions API.

    Args:
        mcp_tools: Tool definitions returned by an MCP client.

    Returns:
        list[dict]: Tool definitions formatted for the model.
    """
    return [
        {
            "type": "function",
            "function": {
                "name": tool.name,
                "description": tool.description or "",
                "parameters": tool.input_schema,
            },
        }
        for tool in mcp_tools
    ]

async def dispatch(client, call) -> str:
    """
    Execute a model-requested tool through the MCP client.

    Args:
        client: MCP client connected to the generated tools.
        call: Tool call returned by the language model.

    Returns:
        str: Tool result or a readable error message.
    """
    try:
        arguments = json.loads(call.function.arguments or "{}")
    except (ValueError, TypeError) as error:
        return f"Invalid tool arguments: {error}"

    if not isinstance(arguments, dict):
        return "Invalid tool arguments: expected a JSON object."

    try:
        result = await client.call_tool(
            call.function.name,
            arguments,
            raise_on_error=False,
        )

        text = "\n".join(
            getattr(block, "text", "")
            for block in result.content
        )

        if result.is_error and text.startswith("Unknown tool:"):
            available = await client.list_tools()
            text += ". Available tools: " + ", ".join(
                tool.name for tool in available
            )

        return text

    except Exception:
        logger.exception("MCP tool dispatch failed")
        return "Tool execution failed. Check application logs."

async def run_agent(
    client,
    question: str,
    meter=None,
    first_choice: str = "auto",
    tool_dispatcher=None,
    tool_definitions=None,
) -> str:
    """
    Run the agent's decision, tool execution, and answer loop.

    Args:
        client: MCP client providing the available tools.
        question: User's mainframe incident question.
        meter: Optional tracker for model usage.
        first_choice: Tool selection setting for the first round.
        tool_dispatcher: Optional direct tool execution function.
        tool_definitions: Optional tool definitions for direct calling.

    Returns:
        str: Final answer from the model or a round-limit message.
    """
    # tools = openai_tools(await client.list_tools())
    tools = (
        tool_definitions
        if tool_definitions is not None
        else openai_tools(await client.list_tools())
    )
    messages = [
    {
        "role": "system",
        "content": (
            "You are the outer agent for MARA, a mainframe incident "
            "research assistant. Use the research_mara tool to investigate "
            "mainframe incidents. Base your final incident findings only "
            "on the structured report returned by research_mara. "
            "Do not invent additional root causes, historical findings, "
            "recovery actions, field corrections, default values, bypass "
            "procedures, or restart instructions. "
            "Do not introduce operational recommendations that are not "
            "present in the report's recommended_next_steps field. "
            "Preserve all authorization and SME approval requirements. "
            "Explicitly list the source IDs supporting the findings "
            "under a 'Supporting Sources' heading. Use only IDs from "
            "the report's sources field. Do not invent source IDs or "
            "ticket links. If the report indicates insufficient evidence, "
            "preserve that uncertainty and do not assert a root cause."
        ),
    },
    {
        "role": "user",
        "content": question,
    },
]

    for round_number in range(6):
        reply = litellm.completion(
            **CFG.kwargs(),
            messages=messages,
            tools=tools,
            timeout=600,
            tool_choice=first_choice if round_number == 0 else "auto",
        )

        if meter:
            meter.track(reply)

        message = reply.choices[0].message

        if round_number == 0 and meter is not None:
             meter.first_turn_tool_calls = len(message.tool_calls or [])

        # if not message.tool_calls:
        #     return message.content or ""
        if not message.tool_calls:
            raw_reports = MARA_RAW_REPORTS.get()

            if raw_reports:
                return "\n\n---\n\n".join(
                    render_mara_report(report)
                    for report in raw_reports
                )

            return "No completed MARA research report is available."

        messages.append(message.model_dump())

        for call in message.tool_calls:
            tool_content = (
                await tool_dispatcher(call)
                if tool_dispatcher is not None
                else await dispatch(client, call)
            )
            # Capture the exact tool response sent to outer Claude.
            tool_messages = MARA_TOOL_MESSAGES.get()

            if tool_messages is not None:
                tool_messages.append({
                    "tool_name": call.function.name,
                    "tool_call_id": call.id,
                    "content": tool_content,
                })
            messages.append(
                {
                    "role": "tool",
                    "tool_call_id": call.id,
                    # "content": await dispatch(client, call),
                    "content": tool_content,
                }
            )

    return "Agent stopped after reaching the six-round limit."


def render_mara_report(report: dict) -> str:
    """
    Format one validated MARA report without generating new findings.

    Args:
        report: MARA's seven-field structured report.

    Returns:
        str: Human-readable incident report.
    """
    lines = [
        "## Failure Summary",
        report["failure_summary"],
        "",
        "## Probable Root Cause",
        report["probable_root_cause"] or "Not established.",
        "",
        "## Evidence and Historical Findings",
    ]

    for finding in report["evidence_and_historical_findings"]:
        lines.append(f"- {finding}")

    lines.extend([
        "",
        "## Confidence Level",
        report["confidence_level"],
        "",
        "## Recommended Next Steps",
    ])

    for index, step in enumerate(report["recommended_next_steps"], start=1):
        lines.append(f"{index}. {step}")

    lines.extend([
        "",
        "## Investigation Status",
        report["investigation_status"],
        "",
        "## Supporting Sources",
    ])

    sources = report["sources"]

    if sources:
        for source_id in sources:
            lines.append(f"- {source_id}")
    else:
        lines.append("No supporting source IDs available.")

    return "\n".join(lines)
