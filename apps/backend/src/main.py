"""FastAPI Entrypoint & Real-Time SSE Streaming API.

Provides:
- Health check (/health) endpoint
- Root metadata endpoint (/)
- Real-time Server-Sent Events stream (/api/generate-test/stream) for LangGraph state transitions
"""

from __future__ import annotations

import asyncio
import json
import os
from datetime import datetime, timezone
from typing import Any, AsyncGenerator, Dict, List, Optional

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

try:
    from fastapi import FastAPI, HTTPException, Request
    from fastapi.middleware.cors import CORSMiddleware
    from fastapi.responses import StreamingResponse
    from pydantic import BaseModel, Field
except ImportError:
    class FastAPI:  # type: ignore
        def __init__(self, *args, **kwargs): pass
        def add_middleware(self, *args, **kwargs): pass
        def get(self, *args, **kwargs): return lambda fn: fn
        def post(self, *args, **kwargs): return lambda fn: fn

    class CORSMiddleware: pass  # type: ignore
    class StreamingResponse:  # type: ignore
        def __init__(self, content, media_type=None, headers=None):
            self.content = content
            self.media_type = media_type
            self.headers = headers

    class BaseModel: pass  # type: ignore
    def Field(*args, **kwargs): return None  # type: ignore
    class Request: pass  # type: ignore
    class HTTPException(Exception): pass  # type: ignore

from src.config import settings
from src.graph.nodes import (
    analyze_and_patch_node,
    execute_test_node,
    generate_code_node,
    plan_node,
    retrieve_context_node,
)
from src.graph.state import AgentState
from src.graph.workflow import get_compiled_graph, should_continue

# ---------------------------------------------------------------------------
# Application Initialization
# ---------------------------------------------------------------------------
app = FastAPI(
    title="Autonomous Spec-to-Playwright Test Generator",
    description="Agentic Self-Healing Test Generation Engine with LangGraph, pgvector, and FastAPI SSE streaming",
    version="0.1.0",
)

# ---------------------------------------------------------------------------
# CORS Configuration
# ---------------------------------------------------------------------------
allowed_origins = list(settings.ALLOWED_ORIGINS)

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_origin_regex=r"https://.*\.vercel\.app",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------------------------
# Request Models
# ---------------------------------------------------------------------------
class GenerateTestRequest(BaseModel):
    spec: str = Field(
        ...,
        description="Target user story, PRD requirement, or manual test scenario",
        min_length=5,
        examples=["Verify user login with valid credentials, session token storage, and dashboard redirect"],
    )
    target_url: str = Field(
        ...,
        description="Base URL or route for the target web application under test",
        examples=["https://example.com/login"],
    )
    max_retries: int = Field(
        default=3,
        ge=0,
        le=5,
        description="Maximum self-healing retry iterations for broken locators or assertions",
    )


# ---------------------------------------------------------------------------
# Utility: SSE Formatting Helper
# ---------------------------------------------------------------------------
def format_sse(payload: Dict[str, Any], event: Optional[str] = None) -> str:
    """Format a dictionary payload into standard Server-Sent Event syntax."""
    event_line = f"event: {event}\n" if event else ""
    return f"{event_line}data: {json.dumps(payload)}\n\n"


# ---------------------------------------------------------------------------
# SSE Streaming Orchestrator
# ---------------------------------------------------------------------------
async def stream_langgraph_events(
    spec: str,
    target_url: str,
    max_retries: int = 3,
) -> AsyncGenerator[str, None]:
    """Execute the LangGraph workflow and yield real-time SSE progress events.

    Attempts execution via graph.astream_events(..., version='v2') if available,
    with an asynchronous node runner fallback.
    """
    initial_state: AgentState = {
        "spec": spec,
        "target_url": target_url,
        "max_retries": max_retries,
        "retrieved_context": [],
        "test_plan": "",
        "generated_code": "",
        "execution_output": {
            "passed": False,
            "stdout": "",
            "stderr": "",
            "error_type": "none",
        },
        "iteration_count": 0,
        "status": "initialized",
        "diff": None,
        "error_diagnosis": None,
    }

    # Signal workflow initiation
    yield format_sse(
        {
            "event": "workflow_started",
            "message": "Initializing Spec-to-Playwright agent...",
            "spec": spec,
            "target_url": target_url,
            "max_retries": max_retries,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        },
        event="step_change",
    )

    try:
        # Try compiling the graph
        compiled_graph = None
        try:
            compiled_graph = get_compiled_graph()
        except Exception as graph_init_err:
            print(f"[*] Note: LangGraph direct compile note ({graph_init_err}), using sequential agent loop.")

        if compiled_graph is not None and hasattr(compiled_graph, "astream_events"):
            # Native LangGraph astream_events pipeline
            async for event in compiled_graph.astream_events(initial_state, version="v2"):
                kind = event.get("event")
                name = event.get("name", "")

                # 1. Step transitions
                if kind == "on_chain_start" and name in [
                    "plan_node",
                    "retrieve_context_node",
                    "generate_code_node",
                    "execute_test_node",
                    "analyze_and_patch_node",
                ]:
                    labels = {
                        "plan_node": "Planning Test Suite",
                        "retrieve_context_node": "Searching Knowledge Base",
                        "generate_code_node": "Generating Playwright Spec",
                        "execute_test_node": "Executing Sandbox Test",
                        "analyze_and_patch_node": "Self-Healing & Patching",
                    }
                    yield format_sse(
                        {
                            "event": "step_change",
                            "node": name,
                            "label": labels.get(name, name),
                            "data": f"Entering {labels.get(name, name)}...",
                        },
                        event="step_change",
                    )

                # 2. Token-by-token code generation streaming
                elif kind == "on_chat_model_stream":
                    chunk = event.get("data", {}).get("chunk")
                    token_text = chunk.content if hasattr(chunk, "content") else str(chunk)
                    if token_text:
                        yield format_sse(
                            {"event": "code_stream", "token": token_text},
                            event="on_chat_model_stream",
                        )

                # 3. Node completion events
                elif kind == "on_chain_end" and name in [
                    "plan_node",
                    "retrieve_context_node",
                    "generate_code_node",
                    "execute_test_node",
                    "analyze_and_patch_node",
                ]:
                    output = event.get("data", {}).get("output", {})
                    yield format_sse(
                        {"event": "node_complete", "node": name, "output": output},
                        event="node_complete",
                    )

            # Retrieve final state from graph
            final_state = initial_state

        else:
            # Fallback direct async loop executing state nodes
            state = dict(initial_state)

            # Node 1: Plan
            yield format_sse(
                {"event": "step_change", "node": "plan_node", "label": "Planning Test Suite", "data": "Analyzing spec requirements & drafting test plan..."},
                event="step_change",
            )
            await asyncio.sleep(0.3)
            plan_res = plan_node(state)  # type: ignore
            state.update(plan_res)
            yield format_sse({"event": "plan_ready", "node": "plan_node", "test_plan": state["test_plan"]}, event="node_complete")

            # Node 2: RAG Retrieval
            yield format_sse(
                {"event": "step_change", "node": "retrieve_context_node", "label": "Searching Knowledge Base", "data": "Querying Supabase pgvector for page objects & locator patterns..."},
                event="step_change",
            )
            await asyncio.sleep(0.3)
            rag_res = retrieve_context_node(state)  # type: ignore
            state.update(rag_res)
            yield format_sse(
                {"event": "context_ready", "node": "retrieve_context_node", "snippets_count": len(state["retrieved_context"])},
                event="node_complete",
            )

            # Node 3: Generate Code
            yield format_sse(
                {"event": "step_change", "node": "generate_code_node", "label": "Generating Playwright Spec", "data": "Synthesizing complete TypeScript test suite..."},
                event="step_change",
            )
            await asyncio.sleep(0.4)
            gen_res = generate_code_node(state)  # type: ignore
            state.update(gen_res)

            # Stream code chunks
            code_preview = state["generated_code"]
            for chunk_part in [code_preview[i:i+40] for i in range(0, len(code_preview), 40)]:
                yield format_sse({"event": "code_stream", "token": chunk_part}, event="on_chat_model_stream")
                await asyncio.sleep(0.02)

            yield format_sse({"event": "code_ready", "node": "generate_code_node", "code": state["generated_code"]}, event="node_complete")

            # Self-Healing Execution Loop
            while True:
                # Node 4: Execute Test
                yield format_sse(
                    {
                        "event": "step_change",
                        "node": "execute_test_node",
                        "label": "Executing Sandbox Test",
                        "data": f"Running Playwright headless (iteration #{state['iteration_count']})...",
                    },
                    event="step_change",
                )
                exec_res = execute_test_node(state)  # type: ignore
                state.update(exec_res)

                exec_out = state["execution_output"]
                yield format_sse(
                    {
                        "event": "execution_result",
                        "node": "execute_test_node",
                        "passed": exec_out.get("passed", False),
                        "error_type": exec_out.get("error_type", "none"),
                        "error_message": exec_out.get("error_message"),
                        "stdout": exec_out.get("stdout", ""),
                        "stderr": exec_out.get("stderr", ""),
                    },
                    event="node_complete",
                )

                # Conditional edge check
                route = should_continue(state)  # type: ignore

                if route == "end_success":
                    state["status"] = "completed_success"
                    break
                elif route == "analyze_and_patch":
                    yield format_sse(
                        {
                            "event": "step_change",
                            "node": "analyze_and_patch_node",
                            "label": "Self-Healing & Patching",
                            "data": f"Diagnosing failure ({exec_out.get('error_type')}) and refactoring locators...",
                        },
                        event="step_change",
                    )
                    await asyncio.sleep(0.5)
                    patch_res = analyze_and_patch_node(state)  # type: ignore
                    state.update(patch_res)

                    yield format_sse(
                        {
                            "event": "patch_diff",
                            "node": "analyze_and_patch_node",
                            "diff": state.get("diff"),
                            "diagnosis": state.get("error_diagnosis"),
                            "iteration": state["iteration_count"],
                        },
                        event="node_complete",
                    )
                else:  # end_max_retries
                    state["status"] = "failed_max_retries"
                    break

            final_state = state

        # Final completion event
        yield format_sse(
            {
                "event": "complete",
                "status": final_state.get("status", "completed"),
                "passed": final_state.get("execution_output", {}).get("passed", False),
                "generated_code": final_state.get("generated_code", ""),
                "test_plan": final_state.get("test_plan", ""),
                "diff": final_state.get("diff"),
                "iterations": final_state.get("iteration_count", 0),
                "execution_output": final_state.get("execution_output", {}),
                "timestamp": datetime.now(timezone.utc).isoformat(),
            },
            event="complete",
        )

    except Exception as stream_err:
        yield format_sse(
            {
                "event": "error",
                "message": f"Agent workflow execution error: {str(stream_err)}",
                "timestamp": datetime.now(timezone.utc).isoformat(),
            },
            event="error",
        )


# ---------------------------------------------------------------------------
# API Routes
# ---------------------------------------------------------------------------
@app.post(
    "/api/generate-test/stream",
    summary="Generate Playwright Spec with Real-time SSE Streaming",
    response_description="Server-Sent Events stream yielding state changes, code tokens, and execution results",
)
async def generate_test_stream(request: GenerateTestRequest) -> StreamingResponse:
    """Stream LangGraph agent workflow events via Server-Sent Events (SSE).

    Clients receive:
    - step_change: Active node state updates for timeline visualization.
    - on_chat_model_stream: Token-by-token code synthesis.
    - node_complete: Results from planning, RAG, and execution sandbox.
    - complete: Final verified test code, diff, and execution telemetry.
    """
    return StreamingResponse(
        stream_langgraph_events(
            spec=request.spec,
            target_url=request.target_url,
            max_retries=request.max_retries,
        ),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@app.get("/health", summary="Service Health Check")
async def health_check() -> Dict[str, Any]:
    """Health check endpoint used for monitoring and uptime keep-alive."""
    return {
        "status": "healthy",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@app.get("/", summary="Root API Info")
async def root() -> Dict[str, Any]:
    """Root endpoint providing metadata about the API."""
    return {
        "name": "Autonomous Spec-to-Playwright Test Generator API",
        "status": "active",
        "docs_url": "/docs",
        "health_check": "/health",
        "stream_endpoint": "/api/generate-test/stream",
    }
